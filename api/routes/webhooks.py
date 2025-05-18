from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import stripe

from core.config import settings
from services.subscription_service import activate_by_customer_id
from database import get_db

router = APIRouter()

@router.post("/webhook")
async def webhook_received(request: Request, db: Session = Depends(get_db)):
    # Replace this endpoint secret with your endpoint's unique secret
    # If you are testing with the CLI, find the secret by running 'stripe listen'
    # If you are using an endpoint defined with the API or dashboard, look in your webhook settings
    webhook_secret = settings.ENDPOINT_SECRET

    try:
        data = await request.json()
        if webhook_secret:
            # Retrieve the event by verifying the signature using the raw body and secret if webhook signing is configured.
            signature = request.headers.get('stripe-signature')
            try:
                event = stripe.Webhook.construct_event(
                    payload=await request.body(),
                    sig_header=signature,
                    secret=webhook_secret
                )
                data = event['data']
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

            # Get the type of webhook event sent - used to check the status of PaymentIntents.
            event_type = event['type']
        else:
            data = data['data']
            event_type = data['type']

        data_object = data['object']

        print('event ' + event_type)

        if event_type == 'invoice.paid':
            print('🔔 Payment succeeded!')
            customer = data_object['customer']
            result = activate_by_customer_id(customer, db)
            if result:
                print('User activated')
            else:
                print('User not activated')

        elif event_type == 'customer.subscription.trial_will_end':
            print('Subscription trial will end')
        elif event_type == 'customer.subscription.created':
            print('Subscription created %s', event.id)
        elif event_type == 'customer.subscription.updated':
            print('Subscription created %s', event.id)
        elif event_type == 'customer.subscription.deleted':
            print('Subscription canceled: %s', event.id)
        elif event_type == 'entitlements.active_entitlement_summary.updated':
            print('Active entitlement summary updated: %s', event.id)

        return JSONResponse(content={'status': 'success'})
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
