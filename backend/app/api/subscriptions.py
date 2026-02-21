"""Subscription management endpoints for Stripe integration.

Migrated to use forge-shared billing for webhook handling (2026-02).
Checkout still uses local price IDs for interview-simulator-specific tiers.
"""

import logging
from datetime import datetime
from uuid import UUID

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from forge_shared.billing import handle_webhook
from forge_shared.billing.models import BillingError
from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.db import get_session
from app.dependencies import get_current_user
from app.models.user import SubscriptionTier, User
from app.services.analytics import Events, get_analytics

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize Stripe client for checkout operations (uses local price IDs)
_stripe_client = None


def get_stripe_client():
    """Get or create the Stripe client."""
    global _stripe_client
    if _stripe_client is None and settings.stripe_secret_key:
        from forge_shared.billing import StripeClient

        _stripe_client = StripeClient(
            api_key=settings.stripe_secret_key,
            webhook_secret=settings.stripe_webhook_secret,
        )
    return _stripe_client


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
    referral_code: str | None = None  # Rewardful referral code for affiliate tracking


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
        client = get_stripe_client()
        if not client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Stripe is not configured",
            )

        customer_id = current_user.stripe_customer_id
        if not customer_id:
            # Create customer using forge-shared client
            customer = await client.create_customer(
                user_id=str(current_user.id),
                email=current_user.email,
                name=current_user.full_name,
            )
            customer_id = customer.id
            current_user.stripe_customer_id = customer_id
            await session.commit()
        else:
            # Check for existing active subscription using forge-shared client
            existing_subs = await client.get_customer_subscriptions(
                customer_id=customer_id,
                active_only=True,
            )
            if existing_subs:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You already have an active subscription. Use 'Manage Subscription' to make changes.",
                )

        # Build checkout session params
        checkout_params = {
            "customer": customer_id,
            "payment_method_types": ["card"],
            "line_items": [
                {
                    "price": payload.price_id,
                    "quantity": 1,
                }
            ],
            "mode": "subscription",
            "success_url": f"{settings.frontend_url}/settings?success=true",
            "cancel_url": f"{settings.frontend_url}/settings?canceled=true",
            "metadata": {"user_id": str(current_user.id)},
        }

        # Add trial days if configured
        trial_days = getattr(settings, "stripe_trial_days", 0)
        if isinstance(trial_days, int) and trial_days > 0:
            checkout_params["subscription_data"] = {
                "metadata": {"user_id": str(current_user.id)},
                "trial_period_days": trial_days,
            }
        else:
            checkout_params["subscription_data"] = {
                "metadata": {"user_id": str(current_user.id)},
            }

        # Add Rewardful referral code for affiliate tracking
        if payload.referral_code:
            checkout_params["client_reference_id"] = payload.referral_code

        # Create checkout session using raw stripe for local price ID support
        import stripe

        checkout_session = stripe.checkout.Session.create(**checkout_params)

        get_analytics().capture(
            user_id=str(current_user.id),
            event=Events.UPGRADE_STARTED,
            properties={
                "price_id": payload.price_id,
                "referral_code": payload.referral_code,
                "checkout_session_id": checkout_session.id,
            },
        )

        return CheckoutSessionResponse(url=checkout_session.url)

    except BillingError as e:
        logger.error(f"Billing error creating checkout session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session",
        ) from e


@router.post("/webhook")
async def stripe_webhook(request: Request) -> dict:
    """Handle Stripe webhook events.

    Processes:
    - checkout.session.completed: Upgrade user subscription
    - customer.subscription.updated: Update subscription status
    - customer.subscription.deleted: Downgrade to free tier

    Uses forge-shared billing webhook handling for signature verification.

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

    if not sig_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header",
        )

    # Use forge-shared webhook handling for signature verification
    try:
        event = handle_webhook(payload, sig_header, settings.stripe_webhook_secret)
    except BillingError as e:
        logger.warning(f"Webhook verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    # Get database session
    async for db_session in get_session():
        try:
            event_type = event.type
            event_data = event.data

            if event_type == "checkout.session.completed":
                await _handle_checkout_completed(event_data, db_session)
            elif event_type == "customer.subscription.updated":
                await _handle_subscription_updated(event_data, db_session)
            elif event_type == "customer.subscription.deleted":
                await _handle_subscription_deleted(event_data, db_session)
            else:
                logger.debug(f"Ignoring webhook event type: {event_type}")

            logger.info(f"Processed Stripe webhook: {event_type}")
        except Exception as e:
            logger.error(
                f"Error processing webhook {event.type}: {e}",
                exc_info=True,
                extra={"event_id": event.id, "event_type": event.type},
            )
            # Return 500 to have Stripe retry
            raise
        finally:
            await db_session.close()
        break

    return {"status": "success"}


async def _handle_checkout_completed(event_data: dict, db_session: AsyncSession) -> None:
    """Handle checkout.session.completed event."""
    from forge_shared.billing.models import SubscriptionStatus

    customer_id = event_data.get("customer_id")
    user_id = event_data.get("user_id")

    if not customer_id or not user_id:
        logger.warning("Missing customer_id or user_id in checkout session")
        return

    # Find user
    try:
        result = await db_session.exec(select(User).where(User.id == UUID(user_id)))
    except ValueError:
        logger.warning(f"Invalid user_id format: {user_id}")
        return
    user = result.first()
    if not user:
        logger.warning(f"User not found: {user_id}")
        return

    # Get subscription details from Stripe
    subscription_id = event_data.get("subscription_id")
    if subscription_id:
        # Use forge-shared client to get subscription
        client = get_stripe_client()
        subscription = await client.get_subscription(subscription_id)
        if subscription:
            tier = _map_pricing_tier(subscription.tier)
            status_enum = subscription.status

            user.stripe_subscription_id = subscription_id
            user.subscription_tier = tier
            user.subscription_status = status_enum.value if isinstance(status_enum, SubscriptionStatus) else status_enum
            user.subscription_expires_at = subscription.current_period_end

            await db_session.commit()
            logger.info(f"Upgraded user {user_id} to {tier.value}")

            # Track subscription created event
            get_analytics().capture(
                user_id=user_id,
                event=Events.SUBSCRIPTION_CREATED,
                properties={
                    "tier": tier.value,
                    "subscription_id": subscription_id,
                },
            )
            get_analytics().capture(
                user_id=user_id,
                event=Events.UPGRADE_COMPLETED,
                properties={
                    "tier": tier.value,
                    "subscription_id": subscription_id,
                },
            )


async def _handle_subscription_updated(event_data: dict, db_session: AsyncSession) -> None:
    """Handle customer.subscription.updated event.

    Supports both forge-shared format (customer_id, subscription_id)
    and legacy format (customer, id) for backward compatibility.
    """
    from forge_shared.billing.models import SubscriptionStatus

    # Support both forge-shared format and legacy format
    customer_id = event_data.get("customer_id") or event_data.get("customer")
    subscription_id = event_data.get("subscription_id") or event_data.get("id")

    if not customer_id:
        return

    # Find user by customer ID
    result = await db_session.exec(select(User).where(User.stripe_customer_id == customer_id))
    user = result.first()
    if not user:
        return

    # Get subscription tier and status from forge-shared parsed data
    # Note: event_data comes from webhook parsing, subscription status may need refresh
    client = get_stripe_client()
    if subscription_id and client:
        subscription = await client.get_subscription(subscription_id)
        if subscription:
            tier = _map_pricing_tier(subscription.tier)
            user.subscription_tier = tier
            user.subscription_status = subscription.status.value if isinstance(subscription.status, SubscriptionStatus) else subscription.status
            user.subscription_expires_at = subscription.current_period_end
            await db_session.commit()
            return

    # Fallback: use raw status from webhook if client not available
    user.stripe_subscription_id = subscription_id
    status_raw = event_data.get("status")
    if status_raw:
        user.subscription_status = status_raw
    await db_session.commit()


async def _handle_subscription_deleted(event_data: dict, db_session: AsyncSession) -> None:
    """Handle customer.subscription.deleted event."""
    customer_id = event_data.get("customer_id")

    if not customer_id:
        return

    # Find user by customer ID
    result = await db_session.exec(select(User).where(User.stripe_customer_id == customer_id))
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

    # Track subscription canceled event
    get_analytics().capture(
        user_id=str(user.id),
        event=Events.SUBSCRIPTION_CANCELED,
        properties={
            "previous_tier": str(user.subscription_tier) if user.subscription_tier else "unknown",
        },
    )


def _map_pricing_tier(pricing_tier) -> SubscriptionTier:
    """Map forge_shared.billing.PricingTier to local SubscriptionTier.

    forge_shared uses: FREE, STARTER, PRO, ENTERPRISE
    Local uses: FREE, PRO, TEAM

    Mapping:
    - FREE -> FREE
    - STARTER -> FREE (no equivalent)
    - PRO -> PRO
    - ENTERPRISE -> PRO (maps to highest tier)
    """
    from forge_shared.billing.models import PricingTier

    if isinstance(pricing_tier, str):
        tier_str = pricing_tier
    elif hasattr(pricing_tier, "value"):
        tier_str = pricing_tier.value
    else:
        tier_str = str(pricing_tier)

    tier_map = {
        PricingTier.FREE.value: SubscriptionTier.FREE,
        PricingTier.STARTER.value: SubscriptionTier.FREE,  # STARTER -> FREE
        PricingTier.PRO.value: SubscriptionTier.PRO,
        PricingTier.ENTERPRISE.value: SubscriptionTier.PRO,  # ENTERPRISE -> PRO (highest local tier)
    }

    return tier_map.get(tier_str, SubscriptionTier.FREE)


def _get_tier_from_price(price_id: str) -> SubscriptionTier:
    """Map Stripe price ID to subscription tier.

    Used for backward compatibility with tests and legacy code.
    """
    if (
        price_id == settings.stripe_price_id_pro_monthly
        or price_id == settings.stripe_price_id_pro_annual
    ):
        return SubscriptionTier.PRO
    if (
        price_id == settings.stripe_price_id_team_monthly
        or price_id == settings.stripe_price_id_team_annual
    ):
        return SubscriptionTier.TEAM
    # Add more mappings as needed
    return SubscriptionTier.FREE


@router.get("/status", response_model=SubscriptionStatus)
async def get_subscription_status(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SubscriptionStatus:
    """Get current subscription status and usage limits.

    Syncs subscription data from Stripe if the user has a customer ID.

    Args:
        current_user: Authenticated user
        session: Database session

    Returns:
        SubscriptionStatus with tier, limits, and usage
    """
    # Sync subscription status from Stripe if customer exists
    if current_user.stripe_customer_id and settings.stripe_secret_key:
        try:
            await _sync_subscription_from_stripe(current_user, session)
        except Exception as e:
            logger.warning(f"Failed to sync subscription from Stripe: {e}")

    # Free tier limit: 3 interviews per month
    FREE_TIER_LIMIT = 3

    # Determine interview limit based on tier
    interviews_limit = None
    if current_user.subscription_tier == SubscriptionTier.FREE:
        interviews_limit = FREE_TIER_LIMIT
    # Pro and Team have unlimited

    can_create_interview = True
    if current_user.subscription_tier == SubscriptionTier.FREE:
        can_create_interview = current_user.interviews_this_month < FREE_TIER_LIMIT

    return SubscriptionStatus(
        tier=current_user.subscription_tier,
        status=current_user.subscription_status,
        expires_at=current_user.subscription_expires_at,
        interviews_this_month=current_user.interviews_this_month,
        interviews_limit=interviews_limit,
        can_create_interview=can_create_interview,
    )


async def _sync_subscription_from_stripe(user: User, session: AsyncSession) -> None:
    """Sync subscription status from Stripe API.

    Fetches the latest subscription data from Stripe and updates the user record.
    This provides a fallback when webhooks aren't configured or fail.
    Prioritizes active subscriptions over canceled ones.
    Uses forge-shared StripeClient for API calls.
    """
    if not user.stripe_customer_id:
        return

    client = get_stripe_client()
    if not client:
        return

    # First try to get active subscription
    subscriptions = await client.get_customer_subscriptions(
        customer_id=user.stripe_customer_id,
        active_only=True,
    )

    # If no active, check for any subscription (including canceled)
    if not subscriptions:
        all_subs = await client.get_customer_subscriptions(
            customer_id=user.stripe_customer_id,
            active_only=False,
        )
        subscriptions = all_subs

    if subscriptions:
        sub = subscriptions[0]
        tier = _map_pricing_tier(sub.tier)

        # Determine subscription status - check for scheduled cancellation
        status_val = sub.status.value if hasattr(sub.status, "value") else sub.status
        if status_val == "active" and sub.cancel_at_period_end:
            status_val = "cancel_at_period_end"

        # Update user subscription data
        user.stripe_subscription_id = sub.id
        user.subscription_tier = tier
        user.subscription_status = status_val
        user.subscription_expires_at = sub.current_period_end

        await session.commit()
        logger.info(f"Synced subscription for user {user.id}: {tier.value} ({status_val})")
    else:
        # No active subscription found - downgrade to free if currently has subscription
        if user.subscription_tier != SubscriptionTier.FREE:
            user.subscription_tier = SubscriptionTier.FREE
            user.subscription_status = "canceled"
            user.stripe_subscription_id = None
            user.subscription_expires_at = None
            await session.commit()
            logger.info(f"No subscription found for user {user.id}, downgraded to free")


class PricingConfig(BaseModel):
    """Response model for pricing configuration."""

    pro_monthly_price_id: str | None
    pro_annual_price_id: str | None
    team_monthly_price_id: str | None
    team_annual_price_id: str | None


@router.get("/pricing", response_model=PricingConfig)
async def get_pricing_config() -> PricingConfig:
    """Get Stripe pricing configuration.

    Returns price IDs for subscription tiers. Frontend should use these
    when creating checkout sessions.
    """
    return PricingConfig(
        pro_monthly_price_id=settings.stripe_price_id_pro_monthly or None,
        pro_annual_price_id=settings.stripe_price_id_pro_annual or None,
        team_monthly_price_id=settings.stripe_price_id_team_monthly or None,
        team_annual_price_id=settings.stripe_price_id_team_annual or None,
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
    client = get_stripe_client()
    if not client:
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
        import stripe

        portal_session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=f"{settings.frontend_url}/settings",
        )
        return PortalSessionResponse(url=portal_session.url)
    except Exception as e:
        logger.error(f"Error creating portal session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create portal session",
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

    client = get_stripe_client()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe is not configured",
        )

    try:
        # Cancel subscription using forge-shared client
        await client.cancel_subscription(
            subscription_id=current_user.stripe_subscription_id,
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
