from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import Depends, status, APIRouter, Depends
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
import stripe
import traceback

from api.dependencies import get_current_user
from models import Usuario
from database import get_db
from core.config import settings


router = APIRouter()


@router.get("/has-payed")
async def has_payed(user: Annotated[Usuario, Depends(get_current_user)], db: Session = Depends(get_db)):
    """
    Check if a user has an active subscription and update their status accordingly.
    """
    try:
        # 1. Get the user's active subscriptions from Stripe
        subscriptions = stripe.Subscription.list(
            customer=user.customer_id,
            status='active',
            limit=1
        )

        active_sub = subscriptions.data[0] if subscriptions.data else None

        # 2. Case: User has an active subscription in Stripe
        if active_sub:
            # If user was marked as inactive in our DB, reactivate them.
            if not user.active:
                user.active = True
                user.subscription_id = active_sub.id
                db.commit()

            # Optional: If you want to show a specific message for subscriptions
            # that will cancel soon, you can check the `cancel_at_period_end` flag.
            if active_sub.cancel_at_period_end:
                return {"status": "active", "message": "Subscription is active but will cancel at period end."}

            return {"status": "active", "message": "Subscription is active."}

        # 3. Case: User has no active subscription in Stripe
        else:
            # If user was marked as active in our DB, deactivate them.
            if user.active:
                user.active = False
                # It's good practice to clear the old subscription ID
                user.subscription_id = None
                db.commit()

            return JSONResponse(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                content={"status": "inactive",
                         "message": "No active subscription found."}
            )

    except stripe.error.StripeError as e:
        print(f"Stripe error: {str(e)} - {traceback.format_exc()}")
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
        print(f"Subscription check error: {str(e)} - {traceback.format_exc()}")
        
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
