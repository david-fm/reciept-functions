from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
import stripe
from models import Usuario
def activate_by_customer_id(
        customer_id: str,
        db: Session):
    user = db.query(Usuario).filter(Usuario.customer_id == customer_id).first()
    if user:
        user.active = True
        db.commit()
        return True
    return False


async def verify_subscription(user: Usuario, db: Session) -> bool:
    """
    Verify if a user has an active subscription and update their status in the database.
    Returns True if the user has an active subscription, False otherwise.

    This function should be called from protected endpoints that require an active subscription.
    """
    try:
        # Quick check - if user is marked as inactive, verify with Stripe
        if not user.active:
            # Check for active subscriptions
            active_subs = stripe.Subscription.list(
                customer=user.customer_id,
                status='active',
                limit=1
            )

            if active_subs and active_subs.data:
                # Active subscription found, activate user
                user.active = True
                user.subscription_id = active_subs.data[0].id
                db.commit()
                return True
            return False

        # User is active, but verify subscription status periodically
        # Check if we need to verify with Stripe (e.g., once a day)
        should_verify = user.last_verified is None or \
            (datetime.now(timezone.utc) - user.last_verified) > timedelta(days=1)

        if should_verify:
            # Check for active subscriptions
            active_subs = stripe.Subscription.list(
                customer=user.customer_id,
                status='active',
                limit=1
            )

            # Update last verified timestamp
            user.last_verified = datetime.now(timezone.utc)

            if not active_subs or not active_subs.data:
                # Check if there's a canceled subscription that matches our record
                canceled_subs = stripe.Subscription.list(
                    customer=user.customer_id,
                    status='canceled',
                    limit=1
                )

                if canceled_subs and canceled_subs.data and user.subscription_id == canceled_subs.data[0].id:
                    # Check if the subscription period is still valid
                    if canceled_subs.data[0].current_period_end > int(datetime.now(timezone.utc).timestamp()):
                        # Still within paid period, keep active
                        db.commit()
                        return True

                # No active subscription and not in valid period, deactivate
                user.active = False
                user.subscription_id = None
                db.commit()
                return False
            else:
                # Update subscription ID if needed
                if user.subscription_id != active_subs.data[0].id:
                    user.subscription_id = active_subs.data[0].id

                # Ensure user is marked active
                user.active = True
                db.commit()

        return user.active

    except stripe.error.StripeError:
        # On Stripe errors, use cached status
        return user.active
    except Exception as e:
        print(f"Error verifying subscription: {str(e)}")
        # Default to cached status on other errors
        return user.active
