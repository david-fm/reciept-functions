from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import Depends, status, APIRouter, Depends
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
import stripe

from api.dependencies import get_current_user
from models import Usuario
from database import get_db
from core.config import settings


router = APIRouter()


@router.get("/has-payed")
async def has_payed(user: Annotated[Usuario, Depends(get_current_user)], db: Session = Depends(get_db)):
    """
    Check if a user has an active subscription and update their status accordingly.
    Returns the subscription status and appropriate HTTP status code.
    """
    try:
        # Get current subscriptions from Stripe
        active_subscriptions = stripe.Subscription.list(
            customer=user.customer_id,
            status='active',
            limit=1
        )

        canceled_subscriptions = stripe.Subscription.list(
            customer=user.customer_id,
            status='canceled',
            limit=1
        )

        # Case 1: User has active subscription in Stripe
        if active_subscriptions and active_subscriptions.data:
            active_sub = active_subscriptions.data[0]

            # Update subscription_id if it has changed
            if user.subscription_id != active_sub.id:
                user.subscription_id = active_sub.id
                db.commit()

            # Activate user if they were inactive
            if not user.active:
                user.active = True
                db.commit()

            return {"status": "active", "message": "Subscription is active"}

        # Case 2: User has canceled subscription that matches our record
        elif canceled_subscriptions and canceled_subscriptions.data:
            canceled_sub = canceled_subscriptions.data[0]

            # Only deactivate if this is the subscription we were tracking
            # and user is still marked as active
            if user.active and user.subscription_id == canceled_sub.id:
                # Check if the subscription period is still valid
                if canceled_sub.current_period_end > int(datetime.now(timezone.utc).timestamp()):
                    # Subscription period still valid despite cancellation
                    return {"status": "active", "message": "Subscription is active until period end"}
                else:
                    # Subscription period has ended, deactivate user
                    user.active = False
                    db.commit()
                    return JSONResponse(
                        {"status": "inactive",
                            "message": "Subscription period has ended"},
                        status_code=status.HTTP_402_PAYMENT_REQUIRED
                    )

        # Case 3: No active subscription but user is marked active
        if user.active and not active_subscriptions.data:
            user.active = False
            user.subscription_id = None
            db.commit()
            return JSONResponse(
                {"status": "inactive", "message": "No active subscription found"},
                status_code=status.HTTP_402_PAYMENT_REQUIRED
            )

        # Case 4: User is already inactive and has no active subscription
        if not user.active:
            return JSONResponse(
                {"status": "inactive", "message": "User is inactive"},
                status_code=status.HTTP_402_PAYMENT_REQUIRED
            )

        # Fallback case
        return {"status": "active" if user.active else "inactive",
                "message": "Using cached status"}

    except stripe.error.StripeError as e:
        print(f"Stripe error: {str(e)}")
        # If we can't connect to Stripe, default to the stored user status
        if user.active:
            return {"status": "active", "message": "Using cached status (Stripe unavailable)"}
        else:
            return JSONResponse(
                {"status": "inactive",
                    "message": "Using cached status (Stripe unavailable)"},
                status_code=status.HTTP_402_PAYMENT_REQUIRED
            )
    except Exception as e:
        print(f"Subscription check error: {str(e)}")
        return JSONResponse(
            {"status": "error", "message": "Could not verify subscription status"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post('/create-subscription')
def create_subscription(user: Annotated[Usuario, Depends(get_current_user)], db: Session = Depends(get_db)):
    if user.active:
        return JSONResponse({"error": {'message': 'User already active'}}, 400)

    try:
        # Check if user already has a valid subscription
        if user.subscription_id:
            # Retrieve existing subscription with expanded invoice and payment intent
            try:
                subscription = stripe.Subscription.retrieve(
                    id=user.subscription_id,
                    expand=['latest_invoice.payment_intent'],
                )

                # Check subscription status
                if subscription.status == 'active':
                    # Subscription is already active
                    return JSONResponse({
                        "subscriptionId": user.subscription_id,
                        "status": "active"
                    })

                # Handle problematic payment intents
                if hasattr(subscription, 'latest_invoice') and subscription.latest_invoice:
                    if hasattr(subscription.latest_invoice, 'payment_intent') and subscription.latest_invoice.payment_intent:
                        payment_intent = subscription.latest_invoice.payment_intent

                        # Handle different payment intent statuses
                        if payment_intent.status in ['canceled', 'failed', 'requires_payment_method']:
                            # Reset the subscription billing cycle to create a fresh invoice and payment intent
                            subscription = stripe.Subscription.modify(
                                user.subscription_id,
                                cancel_at_period_end=False,
                                billing_cycle_anchor='now',
                                proration_behavior='none',
                                expand=['latest_invoice.payment_intent']
                            )
                            payment_intent = subscription.latest_invoice.payment_intent

                        # Return the client secret for payment processing
                        return JSONResponse({
                            "subscriptionId": user.subscription_id,
                            "clientSecret": payment_intent.client_secret,
                            "status": subscription.status
                        })

                # If we reached here, something is wrong with the subscription
                # It's safer to create a new one (after canceling the problematic one)
                stripe.Subscription.modify(
                    user.subscription_id,
                    cancel_at_period_end=True,
                )
                # Reset the subscription ID so we'll create a new one below
                user.subscription_id = None
                db.commit()

            except stripe.error.StripeError as e:
                # Handle case where subscription_id is invalid or deleted on Stripe
                user.subscription_id = None
                db.commit()
                # Continue to create a new subscription

        # Create a new subscription if needed
        # First check for any existing ones that might not be in our DB
        existing_subscriptions = stripe.Subscription.list(
            customer=user.customer_id,
            status='active',
            limit=1
        )

        if existing_subscriptions and existing_subscriptions.data:
            # Use existing active subscription
            subscription = existing_subscriptions.data[0]
            subscription = stripe.Subscription.retrieve(
                id=subscription.id,
                expand=['latest_invoice.payment_intent']
            )
            user.subscription_id = subscription.id
            db.commit()

        else:
            # Check for and remove any canceled subscriptions
            canceled_subscriptions = stripe.Subscription.list(
                customer=user.customer_id,
                status='canceled',
                limit=5
            )

            # Create a new subscription
            subscription = stripe.Subscription.create(
                customer=user.customer_id,
                items=[{
                    'price': settings.PRICE_ID,
                }],
                currency='eur',
                payment_behavior='default_incomplete',
                payment_settings={
                    'save_default_payment_method': 'on_subscription'
                },
                expand=['latest_invoice.payment_intent'],
            )

            user.subscription_id = subscription.id
            db.commit()

        # Get payment intent for client-side confirmation
        payment_intent = subscription.latest_invoice.payment_intent

        return JSONResponse({
            "subscriptionId": user.subscription_id,
            "clientSecret": payment_intent.client_secret,
            "status": subscription.status
        })

    except Exception as e:
        print(f"Error creating subscription: {str(e)}")
        return JSONResponse({"error": {'message': str(e)}}, 400)


@router.post('/cancel-subscription')
def cancelSubscription(user: Annotated[Usuario, Depends(get_current_user)]):
    try:
        # Cancel the subscription by deleting it
        deletedSubscription = stripe.Subscription.delete(
            user.subscription_id)
        return JSONResponse({"status": "Subscription cancelled"})
    except Exception as e:
        return JSONResponse({"error": {'message': str(e)}}, 400)
