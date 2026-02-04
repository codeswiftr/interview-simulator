"""Stripe webhook handler for Interview Simulator."""
from fastapi import APIRouter, Request, HTTPException, Header
import stripe
from app.config import settings

router = APIRouter()
stripe.api_key = settings.stripe_secret_key


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
):
    """Handle Stripe webhook events.

    Configure webhook URL in Stripe Dashboard:
    https://dashboard.stripe.com/webhooks

    Endpoint: https://your-api-domain.com/api/v1/stripe/webhook

    Events to enable:
    - checkout.session.completed
    - customer.subscription.updated
    - customer.subscription.deleted
    """
    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.stripe_webhook_secret
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle events
    if event.type == "checkout.session.completed":
        session = event.data.object
        # TODO: Update user subscription based on session.customer and session.subscription
        # Example:
        # customer_id = session.customer
        # subscription_id = session.subscription
        # user = await get_user_by_stripe_customer_id(customer_id)
        # user.stripe_subscription_id = subscription_id
        # user.subscription_tier = SubscriptionTier.PRO
        # user.subscription_status = "active"
        # await session.commit()
        pass

    elif event.type == "customer.subscription.updated":
        subscription = event.data.object
        # TODO: Update subscription status
        # Example:
        # subscription_id = subscription.id
        # status = subscription.status  # "active", "past_due", "canceled", etc.
        # user = await get_user_by_stripe_subscription_id(subscription_id)
        # user.subscription_status = status
        # if status == "canceled":
        #     user.subscription_tier = SubscriptionTier.FREE
        # await session.commit()
        pass

    elif event.type == "customer.subscription.deleted":
        subscription = event.data.object
        # TODO: Cancel subscription
        # Example:
        # subscription_id = subscription.id
        # user = await get_user_by_stripe_subscription_id(subscription_id)
        # user.subscription_tier = SubscriptionTier.FREE
        # user.subscription_status = "canceled"
        # user.stripe_subscription_id = None
        # await session.commit()
        pass

    return {"status": "success"}
