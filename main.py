from fastapi import FastAPI, Form, Depends, Request, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Annotated, List, Dict
from sqlalchemy.orm import Session
from models import (
    Usuario, TokenData,
    Token, UserRegister,
    UserModify, Ticket,
    Item, models_to_dict,
    TicketData, ItemData)
from database import engine, get_db
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import jwt
import uuid
from fastapi import status
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from dotenv import load_dotenv
import stripe
import os


load_dotenv('.env')

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 180

app = FastAPI()
oauth2_schema = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# YOUR_DOMAIN = 'myapp://'
YOUR_DOMAIN = 'http://localhost:4242'
PRICE_ID = os.getenv("STRIPE_PRICE_ID")
ENDPOINT_SECRET = os.getenv("STRIPE_ENDPOINT_SECRET")
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


def verify_password(plain_password, hashed_pashword):
    return pwd_context.verify(plain_password, hashed_pashword)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db: Session, username: str):
    found = db.query(Usuario).filter(Usuario.correo == username)
    user = found.first()
    if user:
        return user


def get_tickets(
    db: Session,
    user_id: uuid.UUID,
    page: int,
    per_page: int = 10
) -> Dict[str, any]:
    query = db.query(Ticket).filter(Ticket.usuario_id == user_id)

    # Get total count for pagination metadata
    total_count = query.count()

    # Apply pagination
    tickets = (query
               .order_by(Ticket.modified_at, Ticket.created_at)
               .limit(per_page)
               # Fix: page * per_page instead of just page
               .offset(page * per_page)
               .all())

    return {
        "items": models_to_dict(tickets),
        "total": total_count,
        "page": page,
        "per_page": per_page,
        # Ceiling division for total pages
        "pages": (total_count + per_page - 1) // per_page
    }


def get_items(
    db: Session,
    ticket_id: uuid.UUID
) -> Dict[str, any]:
    query = db.query(Item).filter(Item.receipt_id == ticket_id)

    items = query.all()

    return {
        "items": models_to_dict(items)
    }


def create_ticket(
    db: Session,
    user_id: uuid.UUID,
    ticket_data: TicketData
) -> Ticket:
    new_ticket = Ticket(
        nombre_tienda=ticket_data["nombre_tienda"],
        total=ticket_data["total"],
        usuario_id=user_id,
        created_at=datetime.now(timezone.utc),
        modified_at=datetime.now(timezone.utc)
    )

    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    if "items" in ticket_data and ticket_data["items"]:
        for item_data in ticket_data["items"]:
            new_item = Item(
                nombre=item_data["nombre"],
                precio=item_data["precio"],
                cantidad=item_data["cantidad"],
                receipt_id=new_ticket.id
            )
            db.add(new_item)

    db.commit()

    return new_ticket


def create_items(
    db: Session,
    item_datas: List[ItemData],
    commit: bool = True
) -> None:
    for item_data in item_datas:
        new_item = Item(
            nombre=item_data["nombre"],
            precio=item_data["precio"],
            cantidad=item_data["cantidad"],
            receipt_id=item_data["receipt_id"]
        )
        db.add(new_item)

    if commit:
        db.commit()


def delete_items(
    db: Session,
    items_id: List[uuid.UUID],
    commit: bool = True
) -> None:
    db.query(Item).filter(Item.id.in_(items_id)).delete()
    if commit:
        db.commit()


def update_items(
    db: Session,
    items_data: List[ItemData],
    commit: bool = True
) -> None:
    for item_data in items_data:
        item = db.query(Item).filter(Item.id == item_data["id"]).first()
        if item:
            item.nombre = item_data["nombre"]
            item.precio = item_data["precio"]
            item.cantidad = item_data["cantidad"]
    if commit:
        db.commit()


def delete_ticket(
    db: Session,
    user_id: uuid.UUID,
    ticket_id: uuid.UUID,
    commit: bool = True
) -> bool:
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id,
                                     Ticket.usuario_id == user_id).delete()
    if commit:
        db.commit()
    return ticket > 0


def update_ticket(
    db: Session,
    user_id: uuid.UUID,
    ticket_data: TicketData
) -> None:
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_data["id"], Ticket.usuario_id == user_id).first()
    if not ticket:
        raise HTTPException(
            status_code=404, detail="Receipt not found or access denied")

    ticket.nombre_tienda = ticket_data["nombre_tienda"]
    ticket.total = ticket_data["total"]
    ticket.modified_at = datetime.now(timezone.utc)
    items = ticket_data.get("items", [])

    items_to_create = [item for item in items if item["operation"] == "create"]
    items_to_update = [item for item in items if item["operation"] == "update"]
    items_to_delete = [item for item in items if item["operation"] == "delete"]

    # Create new items
    create_items(db, items_to_create, commit=False)

    # Update existing items
    update_items(db, items_to_update, commit=False)

    # Delete items
    delete_items(db, [item["id"] for item in items_to_delete], commit=False)

    db.commit()


def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.passw):
        return False
    return user


def create_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: Annotated[str, Depends(oauth2_schema)],
    db: Session = Depends(get_db)
):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


def activate_by_customer_id(
        customer_id: str,
        db: Session):
    user = db.query(Usuario).filter(Usuario.customer_id == customer_id).first()
    if user:
        user.active = True
        db.commit()
        return True
    return False


async def get_current_active_user(
    current_user: Annotated[Usuario, Depends(get_current_user)]
):
    if not current_user.active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token", response_model=Token)
async def login_for_tokens(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Token:
    user = authenticate_user(
        db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_token(
        data={"sub": user.correo, "type": "access"},
        expires_delta=access_token_expires
    )

    # Create refresh token
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_token(
        data={"sub": user.correo, "type": "refresh"},
        expires_delta=refresh_token_expires
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@app.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str = Form(...), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")

        if username is None or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        db_user = db.query(Usuario).filter(Usuario.correo == username).count()
        print(db_user)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="The user does not exist"
            )

        # Create new access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_token(
            data={"sub": username, "type": "access"},
            expires_delta=access_token_expires
        )

        # Create new refresh token
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        new_refresh_token = create_token(
            data={"sub": username, "type": "refresh"},
            expires_delta=refresh_token_expires
        )

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }

    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


@app.get("/has-payed", response_model=dict)
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


@app.post("/register")
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    try:
        # Check if user already exists
        if db.query(Usuario).filter(Usuario.correo == user_data.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create customer for stripe
        full_name = user_data.name.strip() + " " + user_data.surnames.strip()

        customer = stripe.Customer.create(
            name=full_name,
            email=user_data.email,
        )

        # Create new user
        hashed_password = get_password_hash(
            user_data.password.get_secret_value())
        new_user = Usuario(
            correo=user_data.email,
            passw=hashed_password,
            nombre=user_data.name,
            apellidos=user_data.surnames,
            customer_id=customer.id,  # TODO
            active=False  # Set user as active by default
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user, can't process user data"
        )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Create access token for the new user
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_token(
            data={"sub": new_user.correo, "type": "access"},
            expires_delta=access_token_expires
        )

        # Create refresh token
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_token = create_token(
            data={"sub": new_user.correo, "type": "refresh"},
            expires_delta=refresh_token_expires
        )

        return {
            "message": "User registered successfully",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    except Exception as e:
        # print(e)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user"
        )


@app.post("/modify")
async def modify_user(
    user_data: UserModify,
    current_user: Annotated[Usuario, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    if not user_data.email and not user_data.password and not user_data.name and not user_data.surnames:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data to modify"
        )
    try:
        if user_data.email:
            current_user.correo = user_data.email
        if user_data.password:
            current_user.passw = get_password_hash(
                user_data.password.get_secret_value())
        if user_data.name:
            current_user.nombre = user_data.name
        if user_data.surnames:
            current_user.apellidos = user_data.surnames

        db.commit()
        print(current_user)
        customer = stripe.Customer.modify(
            current_user.customer_id,
            email=current_user.correo,
            name=current_user.nombre + " " + current_user.apellidos
        )
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error modifying user in stripe"
            )
        return JSONResponse({"message": "User modified successfully"})
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error modifying user"+str(e)
        )


@app.get("/")
async def get_index():
    return FileResponse('public/checkout.html')


@app.post('/create-subscription')
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
                    'price': PRICE_ID,
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


@app.get("/key")
async def get_key():
    return JSONResponse({"publicKey": os.getenv("STRIPE_PUBLIC_KEY")})


@app.post("/webhook")
async def webhook_received(request: Request, db: Session = Depends(get_db)):
    # Replace this endpoint secret with your endpoint's unique secret
    # If you are testing with the CLI, find the secret by running 'stripe listen'
    # If you are using an endpoint defined with the API or dashboard, look in your webhook settings
    webhook_secret = ENDPOINT_SECRET

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


@app.post('/cancel-subscription')
def cancelSubscription(user: Annotated[Usuario, Depends(get_current_user)]):
    try:
        # Cancel the subscription by deleting it
        deletedSubscription = stripe.Subscription.delete(
            user.subscription_id)
        return JSONResponse({"status": "Subscription cancelled"})
    except Exception as e:
        return JSONResponse({"error": {'message': str(e)}}, 400)


@app.get("/receipts")
async def get_receipt(
    user: Annotated[Usuario, Depends(get_current_active_user)],
    page: int = Query(0, ge=0, description="Page number, zero-indexed"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    is_active = await verify_subscription(user, db)

    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )

    pagination_data = get_tickets(db, user.id, page, per_page)

    return JSONResponse({
        "receipts": pagination_data["items"],
        "pagination": {
            "total": pagination_data["total"],
            "page": pagination_data["page"],
            "per_page": pagination_data["per_page"],
            "pages": pagination_data["pages"]
        }
    })


@app.get("/receipts/{receipt_id}")
async def get_receipt_items(
    receipt_id: uuid.UUID,
    user: Annotated[Usuario, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    is_active = await verify_subscription(user, db)

    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )

    items = get_items(db, receipt_id)

    return JSONResponse(items)


@app.post("/receipts")
async def create_receipt(
    ticket_data: TicketData,
    user: Annotated[Usuario, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    is_active = await verify_subscription(user, db)

    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )

    new_ticket = create_ticket(db, user.id, ticket_data)

    return JSONResponse(models_to_dict(new_ticket))


@app.put("/receipts")
async def update_receipt(
    ticket_data: TicketData,
    user: Annotated[Usuario, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    is_active = await verify_subscription(user, db)

    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )
    try:
        update_ticket(db, ticket_data)
        return JSONResponse({"message": "Ticket updated successfully"})

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating ticket"
        )


@app.delete("/receipts/{receipt_id}")
async def delete_receipt(
    receipt_id: uuid.UUID,
    user: Annotated[Usuario, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    is_active = await verify_subscription(user, db)

    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )

    deleted = delete_ticket(db, user.id, receipt_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receipt not found or not owned by user"
        )

    return JSONResponse({"message": "Receipt deleted successfully"})
