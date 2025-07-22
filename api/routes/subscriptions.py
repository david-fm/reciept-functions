from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import Depends, status, APIRouter, Depends
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
import stripe
import traceback
import os

from api.dependencies import get_current_user
from models import Usuario
from database import get_db
from core.config import settings


router = APIRouter()


@router.get("/key")
async def get_key():
    return JSONResponse({"publicKey": os.getenv("STRIPE_PUBLIC_KEY")})

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
        subscription = None  # Initialize subscription to None

        # --- Handle existing subscription ---
        if user.subscription_id:
            try:
                # Always try to retrieve with full expansion to get the latest state
                subscription = stripe.Subscription.retrieve(
                    id=user.subscription_id,
                    expand=['latest_invoice.payment_intent',
                            'latest_invoice.confirmation_secret'],
                )

                if subscription.status == 'active':
                    return JSONResponse({
                        "subscriptionId": user.subscription_id,
                        "status": "active"
                    })

                # Check if there's an existing actionable payment intent or confirmation secret
                # The 'latest_invoice' can be an ID, so ensure it's expanded before accessing attributes
                if hasattr(subscription, 'latest_invoice') and subscription.latest_invoice:
                    # Prefer confirmation_secret for incomplete subscriptions
                    if hasattr(subscription.latest_invoice, 'confirmation_secret') and \
                       subscription.latest_invoice.confirmation_secret and \
                       subscription.latest_invoice.confirmation_secret.client_secret:

                        return JSONResponse({
                            "subscriptionId": user.subscription_id,
                            "clientSecret": subscription.latest_invoice.confirmation_secret.client_secret,
                            "status": subscription.status
                        })
                    # Fallback to payment_intent if confirmation_secret is not available but payment_intent is
                    elif hasattr(subscription.latest_invoice, 'payment_intent') and \
                            subscription.latest_invoice.payment_intent and \
                            subscription.latest_invoice.payment_intent.client_secret:

                        payment_intent = subscription.latest_invoice.payment_intent
                        # Handle problematic payment intents by re-modifying
                        if payment_intent.status in ['canceled', 'failed', 'requires_payment_method']:
                            subscription = stripe.Subscription.modify(
                                user.subscription_id,
                                cancel_at_period_end=False,
                                billing_cycle_anchor='now',
                                proration_behavior='none',
                                # Re-expand
                                expand=['latest_invoice.payment_intent',
                                        'latest_invoice.confirmation_secret']
                            )
                            # Re-fetch payment_intent/confirmation_secret after modification
                            if hasattr(subscription, 'latest_invoice') and \
                               (hasattr(subscription.latest_invoice, 'confirmation_secret') and subscription.latest_invoice.confirmation_secret and subscription.latest_invoice.confirmation_secret.client_secret):
                                return JSONResponse({
                                    "subscriptionId": user.subscription_id,
                                    "clientSecret": subscription.latest_invoice.confirmation_secret.client_secret,
                                    "status": subscription.status
                                })
                            elif hasattr(subscription.latest_invoice, 'payment_intent') and subscription.latest_invoice.payment_intent.client_secret:
                                return JSONResponse({
                                    "subscriptionId": user.subscription_id,
                                    "clientSecret": subscription.latest_invoice.payment_intent.client_secret,
                                    "status": subscription.status
                                })
                            else:
                                # If still no client_secret, cancel the problematic subscription to create a new one
                                stripe.Subscription.modify(
                                    user.subscription_id, cancel_at_period_end=True)
                                user.subscription_id = None
                                db.commit()  # This will cause a new subscription to be created below
                                # Continue to the new subscription creation block

                    # If subscription is incomplete/past_due but no actionable client_secret found,
                    # consider it problematic and proceed to create a new one.
                    elif subscription.status in ['incomplete', 'past_due']:
                        print(
                            f"Existing incomplete/past_due subscription {user.subscription_id} has no actionable client secret. Attempting to re-create.")
                        stripe.Subscription.modify(
                            user.subscription_id, cancel_at_period_end=True)
                        user.subscription_id = None
                        db.commit()

                if user.subscription_id:  # If we haven't reset it due to problems
                    # If we reached here, and subscription_id is still set,
                    # it means the existing subscription is in a state we can't immediately action
                    # (e.g., pending_update without a client_secret).
                    # We'll return an informative message.
                    return JSONResponse({
                        "subscriptionId": user.subscription_id,
                        "status": subscription.status,
                        "message": "Existing subscription found but requires further action. Please check your Stripe account or try again."
                        # 202 Accepted, indicates processing is ongoing or needs external action.
                    }, 202)

            except stripe.error.StripeError as e:
                print(
                    f"Stripe Error retrieving existing subscription {user.subscription_id}: {e}")
                # If subscription_id is invalid or deleted, clear it to create a new one
                user.subscription_id = None
                db.commit()
                # Continue to create a new subscription

        # --- Logic for creating a new subscription if no valid one exists or previous was problematic ---
        if not user.subscription_id:
            # Check for existing active subscriptions that might not be in our DB (unlikely if DB is source of truth, but good for robustness)
            existing_active_subscriptions = stripe.Subscription.list(
                customer=user.customer_id,
                status='active',
                limit=1
            )

            if existing_active_subscriptions and existing_active_subscriptions.data:
                subscription = existing_active_subscriptions.data[0]
                # Retrieve fully to ensure we have necessary details
                subscription = stripe.Subscription.retrieve(
                    id=subscription.id,
                    expand=['latest_invoice.payment_intent',
                            'latest_invoice.confirmation_secret']
                )
                user.subscription_id = subscription.id
                db.commit()
                print(
                    f"Found and adopted existing active subscription: {subscription.id}")
            else:
                # Create a new subscription
                subscription = stripe.Subscription.create(
                    customer=user.customer_id,
                    items=[{
                        'price': settings.STRIPE_PRICE_ID,
                    }],
                    currency='eur',
                    payment_behavior='default_incomplete',
                    payment_settings={
                        'save_default_payment_method': 'on_subscription'
                    },
                    # CRITICAL: Expand latest_invoice AND its confirmation_secret or payment_intent
                    expand=['latest_invoice.payment_intent',
                            'latest_invoice.confirmation_secret'],
                )

                user.subscription_id = subscription.id
                db.commit()
                print(f"Created new subscription: {subscription.id}")

        # --- Final response handling ---
        # Ensure subscription is not None before proceeding
        if not subscription:
            return JSONResponse({"error": {'message': "Subscription could not be created or retrieved after all attempts."}}, 500)

        # Prioritize confirmation_secret for the client_secret
        if hasattr(subscription, 'latest_invoice') and subscription.latest_invoice:
            if hasattr(subscription.latest_invoice, 'confirmation_secret') and \
               subscription.latest_invoice.confirmation_secret and \
               subscription.latest_invoice.confirmation_secret.client_secret:
                print(
                    f"Returning clientSecret from latest_invoice.confirmation_secret for subscription {subscription.id}")
                return JSONResponse({
                    "subscriptionId": user.subscription_id,
                    "clientSecret": subscription.latest_invoice.confirmation_secret.client_secret,
                    "status": subscription.status
                })
            elif hasattr(subscription.latest_invoice, 'payment_intent') and \
                    subscription.latest_invoice.payment_intent and \
                    subscription.latest_invoice.payment_intent.client_secret:
                # Fallback to payment_intent if confirmation_secret is not present but payment_intent is
                print(
                    f"Returning clientSecret from latest_invoice.payment_intent for subscription {subscription.id}")
                return JSONResponse({
                    "subscriptionId": user.subscription_id,
                    "clientSecret": subscription.latest_invoice.payment_intent.client_secret,
                    "status": subscription.status
                })
            else:
                # This case means latest_invoice exists, but neither confirmation_secret nor payment_intent
                # had a client_secret. This is likely the "incomplete" scenario the frontend needs to handle.
                print(
                    f"Subscription {subscription.id} in status '{subscription.status}' has latest_invoice but no immediate client_secret for payment. Signaling action required.")
                return JSONResponse({
                    "subscriptionId": user.subscription_id,
                    "status": subscription.status,
                    "message": "Subscription created, but payment requires additional action. Please add a payment method or verify existing one."
                }, 202)  # Use 202 Accepted, as subscription is created but payment needs action
        else:
            # This case means latest_invoice itself is missing or not expanded correctly, which indicates a deeper issue
            print(
                f"Error: latest_invoice missing or not expanded for subscription {subscription.id}. Status: {subscription.status}")
            return JSONResponse({"error": {'message': "Subscription created but invoice details are missing unexpectedly. Please try again or contact support."}}, 500)

    except stripe.error.StripeError as e:
        print(f"Stripe Error in create_subscription: {str(e)}")
        return JSONResponse({"error": {'message': str(e)}}, 400)
    except Exception as e:
        print(f"Unexpected Error in create_subscription: {str(e)}")
        return JSONResponse({"error": {'message': "An unexpected error occurred: " + str(e)}}, 500)


@router.post('/cancel-subscription')
def cancelSubscription(user: Annotated[Usuario, Depends(get_current_user)]):
    try:
        # Cancel the subscription by deleting it
        deletedSubscription = stripe.Subscription.delete(
            user.subscription_id)
        return JSONResponse({"status": "Subscription cancelled"})
    except Exception as e:
        return JSONResponse({"error": {'message': str(e)}}, 400)
