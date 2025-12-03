"""Subscription management endpoints for Stripe integration."""

import logging
from datetime import datetime, timezone
from uuid import UUID

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.db import get_session
from app.dependencies import get_current_user
from app.models.user import SubscriptionTier, User

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize Stripe
if settings.stripe_secret_key:
    stripe.api_key = settings.stripe_secret_key


class CheckoutSessionResponse(BaseModel):
    """Response model for checkout session creation."""

    url: str


class SubscriptionStatus(BaseModel):
    """Response model for subscription status."""

    tier: SubscriptionTier
    status: str | None
    expires_at: datetime | None
    interviews_this_month: int
    interviews_limit: int | None
    can_create_interview: bool


class CheckoutRequest(BaseModel):
    """Request model for checkout session creation."""

    price_id: str


@router.post("/checkout", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    payload: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CheckoutSessionResponse:
    """Create Stripe Checkout session for subscription upgrade.

    Args:
        price_id: Stripe price ID for the subscription tier
        current_user: Authenticated user
        session: Database session

    Returns:
        CheckoutSessionResponse with redirect URL

    Raises:
        HTTPException: If Stripe API call fails
    """
    if not settings.stripe_secret_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe is not configured",
        )

    try:
        # Get or create Stripe customer
        customer_id = current_user.stripe_customer_id
        if not customer_id:
            customer = stripe.Customer.create(
                email=current_user.email,
                name=current_user.full_name,
                metadata={"user_id": str(current_user.id)},
            )
            customer_id = customer.id
            current_user.stripe_customer_id = customer_id
            await session.commit()

        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[
                {
                    "price": payload.price_id,
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=f"{settings.frontend_url}/settings?success=true",
            cancel_url=f"{settings.frontend_url}/settings?canceled=true",
            metadata={"user_id": str(current_user.id)},
        )

        return CheckoutSessionResponse(url=checkout_session.url)

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating checkout session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create checkout session: {str(e)}",
        ) from e


@router.post("/webhook")
async def stripe_webhook(request: Request) -> dict:
    """Handle Stripe webhook events.

    Processes:
    - checkout.session.completed: Upgrade user subscription
    - customer.subscription.updated: Update subscription status
    - customer.subscription.deleted: Downgrade to free tier

    Args:
        request: FastAPI request with Stripe webhook payload

    Returns:
        Success response
    """
    if not settings.stripe_webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe webhook secret not configured",
        )

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload"
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature"
        )

    # Get database session
    async for db_session in get_session():
        try:
            if event["type"] == "checkout.session.completed":
                await _handle_checkout_completed(event["data"]["object"], db_session)
            elif event["type"] == "customer.subscription.updated":
                await _handle_subscription_updated(event["data"]["object"], db_session)
            elif event["type"] == "customer.subscription.deleted":
                await _handle_subscription_deleted(event["data"]["object"], db_session)
            else:
                logger.debug(f"Ignoring webhook event type: {event['type']}")

            logger.info(f"Processed Stripe webhook: {event['type']}")
        except Exception as e:
            logger.error(
                f"Error processing webhook {event['type']}: {e}",
                exc_info=True,
                extra={"event_id": event.get("id"), "event_type": event.get("type")},
            )
            # Return 500 to have Stripe retry
            raise
        finally:
            await db_session.close()
        break

    return {"status": "success"}


async def _handle_checkout_completed(session_obj: dict, db_session: AsyncSession) -> None:
    """Handle checkout.session.completed event."""
    customer_id = session_obj.get("customer")
    user_id = session_obj.get("metadata", {}).get("user_id")

    if not customer_id or not user_id:
        logger.warning("Missing customer_id or user_id in checkout session")
        return

    # Find user
    result = await db_session.exec(
        select(User).where(User.id == UUID(user_id))
    )
    user = result.first()
    if not user:
        logger.warning(f"User not found: {user_id}")
        return

    # Get subscription details
    subscription_id = session_obj.get("subscription")
    if subscription_id:
        subscription = stripe.Subscription.retrieve(subscription_id)
        tier = _get_tier_from_price(subscription.items.data[0].price.id)

        user.stripe_subscription_id = subscription_id
        user.subscription_tier = tier
        user.subscription_status = subscription.status
        user.subscription_expires_at = datetime.fromtimestamp(
            subscription.current_period_end, tz=timezone.utc
        )

        await db_session.commit()
        logger.info(f"Upgraded user {user_id} to {tier.value}")


async def _handle_subscription_updated(subscription_obj: dict, db_session: AsyncSession) -> None:
    """Handle customer.subscription.updated event."""
    customer_id = subscription_obj.get("customer")
    subscription_id = subscription_obj.get("id")

    if not customer_id:
        return

    # Find user by customer ID
    result = await db_session.exec(
        select(User).where(User.stripe_customer_id == customer_id)
    )
    user = result.first()
    if not user:
        return

    tier = _get_tier_from_price(subscription_obj["items"]["data"][0]["price"]["id"])

    user.stripe_subscription_id = subscription_id
    user.subscription_tier = tier
    user.subscription_status = subscription_obj.get("status")
    user.subscription_expires_at = datetime.fromtimestamp(
        subscription_obj.get("current_period_end", 0), tz=timezone.utc
    )

    await db_session.commit()


async def _handle_subscription_deleted(subscription_obj: dict, db_session: AsyncSession) -> None:
    """Handle customer.subscription.deleted event."""
    customer_id = subscription_obj.get("customer")

    if not customer_id:
        return

    # Find user by customer ID
    result = await db_session.exec(
        select(User).where(User.stripe_customer_id == customer_id)
    )
    user = result.first()
    if not user:
        return

    # Downgrade to free tier
    user.subscription_tier = SubscriptionTier.FREE
    user.subscription_status = "canceled"
    user.stripe_subscription_id = None
    user.subscription_expires_at = None

    await db_session.commit()
    logger.info(f"Downgraded user {user.id} to free tier")


def _get_tier_from_price(price_id: str) -> SubscriptionTier:
    """Map Stripe price ID to subscription tier."""
    if (
        price_id == settings.stripe_price_id_pro_monthly
        or price_id == settings.stripe_price_id_pro_annual
    ):
        return SubscriptionTier.PRO
    # Add more mappings as needed
    return SubscriptionTier.FREE


@router.get("/status", response_model=SubscriptionStatus)
async def get_subscription_status(
    current_user: User = Depends(get_current_user),
) -> SubscriptionStatus:
    """Get current subscription status and usage limits.

    Args:
        current_user: Authenticated user

    Returns:
        SubscriptionStatus with tier, limits, and usage
    """
    # Determine interview limit based on tier
    interviews_limit = None
    if current_user.subscription_tier == SubscriptionTier.FREE:
        interviews_limit = 3
    # Pro and Team have unlimited

    can_create_interview = True
    if current_user.subscription_tier == SubscriptionTier.FREE:
        can_create_interview = current_user.interviews_this_month < 3

    return SubscriptionStatus(
        tier=current_user.subscription_tier,
        status=current_user.subscription_status,
        expires_at=current_user.subscription_expires_at,
        interviews_this_month=current_user.interviews_this_month,
        interviews_limit=interviews_limit,
        can_create_interview=can_create_interview,
    )


class PricingConfig(BaseModel):
    """Response model for pricing configuration."""

    pro_monthly_price_id: str | None
    pro_annual_price_id: str | None


@router.get("/pricing", response_model=PricingConfig)
async def get_pricing_config() -> PricingConfig:
    """Get Stripe pricing configuration.

    Returns price IDs for subscription tiers. Frontend should use these
    when creating checkout sessions.
    """
    return PricingConfig(
        pro_monthly_price_id=settings.stripe_price_id_pro_monthly or None,
        pro_annual_price_id=settings.stripe_price_id_pro_annual or None,
    )


class PortalSessionResponse(BaseModel):
    """Response model for customer portal session."""

    url: str


@router.post("/portal", response_model=PortalSessionResponse)
async def create_portal_session(
    current_user: User = Depends(get_current_user),
) -> PortalSessionResponse:
    """Create Stripe Customer Portal session for managing subscription.

    Allows users to view invoices, update payment methods, and cancel subscription.

    Args:
        current_user: Authenticated user

    Returns:
        PortalSessionResponse with redirect URL to Stripe portal
    """
    if not settings.stripe_secret_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe is not configured",
        )

    if not current_user.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Stripe customer found. Please subscribe first.",
        )

    try:
        portal_session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=f"{settings.frontend_url}/settings",
        )
        return PortalSessionResponse(url=portal_session.url)
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating portal session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create portal session: {str(e)}",
        ) from e


@router.post("/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Cancel active subscription and downgrade to free tier.

    Args:
        current_user: Authenticated user
        session: Database session

    Returns:
        Success message
    """
    if not current_user.stripe_subscription_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active subscription to cancel",
        )

    try:
        # Cancel subscription in Stripe
        stripe.Subscription.modify(
            current_user.stripe_subscription_id,
            cancel_at_period_end=True,
        )

        # Update user status
        current_user.subscription_status = "cancel_at_period_end"
        await session.commit()

        return {"message": "Subscription will be canceled at the end of the billing period"}

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error canceling subscription: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to cancel subscription: {str(e)}",
        ) from e

