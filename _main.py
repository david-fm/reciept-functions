from vertexai.generative_models import Image as VertexImage
from contextlib import asynccontextmanager
from io import StringIO
import csv
from dotenv import load_dotenv
print("LOADED? ", load_dotenv('.env'))


from services.ai_services.models import model
from services.ai_services.config import pdf_config
from file_processing.process_pdf import convert_pdf_to_images, image_to_bytes
from file_processing.product_classiffier_agent import build_graph
from file_processing.product_classiffier_agent import State as ClassifierState
from file_processing.categories import CategoryLoader
from database import engine, get_db
from models import (
    Usuario, TokenData,
    Token, UserRegister,
    UserModify, Ticket,
    Item, models_to_dict,
    TicketData, ItemData,
    Categoria, get_categories_data,
    TicketDataInput)
from services.receipt_processing import (
    clean_int,
    clean_price
)
from fastapi import FastAPI, Form, Depends, Request, Query, BackgroundTasks, UploadFile
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.exceptions import HTTPException
from fastapi.responses import (
    JSONResponse, RedirectResponse, 
    FileResponse, Response)
from fastapi.staticfiles import StaticFiles
from typing import Annotated, List, Dict, Optional, Literal
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from zoneinfo import ZoneInfo
import jwt
import uuid
from fastapi import status
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import stripe
import os
import decimal
from PIL import Image
import tempfile
import traceback
import json
import os




SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 180

categories = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load categories from database
    global categories

    print("Initializing categories...")

    # Get a database session
    db = next(get_db())
    try:
        # Initialize categories using your function
        categories = get_categories_data(db)
        print(
            f"Categories loaded: {len(categories.categories)} main categories found")
    except Exception as e:
        print(f"Error loading categories: {e}")
    finally:
        db.close()

    yield

    # Shutdown: Clear the categories data
    print("Clearing categories...")
    categories = None


# Create the FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)
oauth2_schema = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# YOUR_DOMAIN = 'myapp://'
YOUR_DOMAIN = 'http://localhost:4242'
PRICE_ID = os.getenv("STRIPE_PRICE_ID")
ENDPOINT_SECRET = os.getenv("STRIPE_ENDPOINT_SECRET")
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Classify product
classifier = build_graph()

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
               # Latest first
               .order_by(Ticket.modified_at.desc(), Ticket.created_at.desc())
               .limit(per_page)
               .offset(page * per_page)
               .all())

    return {
        "items": models_to_dict(tickets, include_relationships=True),
        "total": total_count,
        "page": page,
        "per_page": per_page,
        # Ceiling division for total pages
        "pages": (total_count + per_page - 1) // per_page
    }


def get_items(
    db: Session,
    ticket_id: uuid.UUID,
    user_id: uuid.UUID
) -> Dict[str, any]:
    # Verify ownership
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id,
        Ticket.usuario_id == user_id
    ).first()

    if not ticket:
        return {"items": []}

    query = db.query(Item).filter(Item.receipt_id == ticket_id)
    items = query.all()

    return {
        "items": models_to_dict(items)
    }


def validate_ticket_data(ticket_data: TicketData) -> List[str]:
    """Validate ticket data and return list of errors"""
    errors = []

    # Validate required fields
    if not ticket_data.get("nombre_tienda"):
        errors.append("Store name is required")

    # Validate numeric fields
    try:
        total = decimal.Decimal(str(ticket_data.get("total", 0)))
        if total < 0:
            errors.append("Total cannot be negative")
    except (decimal.InvalidOperation, TypeError):
        errors.append("Total must be a valid number")

    # Validate items if present
    if "items" in ticket_data and ticket_data["items"]:
        for i, item in enumerate(ticket_data["items"]):
            # Validate item name
            if not item.get("nombre"):
                errors.append(f"Item {i+1}: Name is required")

            # Validate price
            try:
                price = decimal.Decimal(str(item.get("precio", 0)))
                if price < 0:
                    errors.append(f"Item {i+1}: Price cannot be negative")
            except (decimal.InvalidOperation, TypeError):
                errors.append(f"Item {i+1}: Price must be a valid number")

            # Validate quantity
            try:
                qty = int(item.get("cantidad", 0))
                if qty <= 0:
                    errors.append(f"Item {i+1}: Quantity must be positive")
            except (ValueError, TypeError):
                errors.append(f"Item {i+1}: Quantity must be a valid integer")

    return errors

def classify_products(ticket_data: TicketData):
    """
    Classify products in the ticket data
    """
    for item in ticket_data["items"]:
        classification: ClassifierState = classifier.invoke({
            "product": item["nombre"],
            "available_categories": categories
        })

        item["categoria"] = classification["category"]
        item["sub_categoria"] = classification["subcategory"]

    
def create_ticket(
    db: Session,
    user_id: uuid.UUID,
    ticket_data: TicketData
) -> Ticket:
    """Create a new ticket with items in a transaction"""
    
    try:
        classify_products(ticket_data)
        # Start transaction
        new_ticket = Ticket(
            nombre_tienda=ticket_data["nombre_tienda"],
            total=ticket_data["total"],
            usuario_id=user_id,
            created_at=datetime.now(timezone.utc),
            modified_at=datetime.now(timezone.utc)
        )

        db.add(new_ticket)
        db.flush()  # Get ID but don't commit yet

        if "items" in ticket_data and ticket_data["items"]:
            for item_data in ticket_data["items"]:
                new_item = Item(
                    nombre=item_data["nombre"],
                    precio=item_data["precio"],
                    cantidad=item_data["cantidad"],
                    receipt_id=new_ticket.id,
                    categoria_id=db.query(Categoria).filter(Categoria.nombre == item_data.get("categoria")).first().id,
                    sub_categoria_id=db.query(Categoria).filter(Categoria.nombre == item_data.get("sub_categoria")).first().id
                )
                db.add(new_item)

        db.commit()
        db.refresh(new_ticket)
        return new_ticket
    except Exception as e:
        full_error_with_traceback = traceback.format_exc()
        print(full_error_with_traceback)
        raise e


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
            receipt_id=item_data["receipt_id"],
            categoria=item_data.get("categoria"),
            sub_categoria=item_data.get("sub_categoria")
        )
        db.add(new_item)

    if commit:
        db.commit()


def delete_items(
    db: Session,
    items_id: List[uuid.UUID],
    commit: bool = True
) -> None:
    if not items_id:
        return

    db.query(Item).filter(Item.id.in_(items_id)
                          ).delete(synchronize_session=False)
    if commit:
        db.commit()


def update_items(
    db: Session,
    items_data: List[ItemData],
    commit: bool = True
) -> None:
    for item_data in items_data:
        item = db.query(Item).filter(Item.id == item_data["id"]).first()
        print(f"Item Subcategory: {item.sub_categoria_rel.nombre}")
        print(f"Item Subcategory ID: {item.sub_categoria_id}")
        if item:
            item.nombre = item_data["nombre"]
            item.precio = item_data["precio"]
            item.cantidad = item_data["cantidad"]
            if "categoria_id" in item_data:
                item.categoria_id = item_data["categoria_id"]
            if "sub_categoria_id" in item_data:
                item.sub_categoria_id = item_data["sub_categoria_id"]
                print(f"Item Subcategory ID: {item.sub_categoria_id}")
    if commit:
        db.commit()


def delete_ticket(
    db: Session,
    user_id: uuid.UUID,
    ticket_id: uuid.UUID,
    commit: bool = True
) -> bool:
    try:
        # Check if ticket exists and belongs to user
        ticket = db.query(Ticket).filter(
            Ticket.id == ticket_id,
            Ticket.usuario_id == user_id
        ).first()

        if not ticket:
            return False

        # Delete related items first
        db.query(Item).filter(Item.receipt_id == ticket_id).delete(
            synchronize_session=False)

        # Then delete ticket
        db.delete(ticket)

        if commit:
            db.commit()
        return True
    except Exception as e:
        if commit:
            db.rollback()
        raise e


def update_ticket(
    db: Session,
    user_id: uuid.UUID,
    ticket_data: TicketData
) -> None:
    try:
        # Begin transaction
        ticket = db.query(Ticket).filter(
            Ticket.id == ticket_data["id"],
            Ticket.usuario_id == user_id
        ).first()

        if not ticket:
            raise HTTPException(
                status_code=404, detail="Receipt not found or access denied")

        ticket.nombre_tienda = ticket_data["nombre_tienda"]
        ticket.total = ticket_data["total"]
        ticket.modified_at = datetime.now(timezone.utc)
        items = ticket_data.get("items", [])

        items_to_create = [
            item for item in items if item.get("operation") == "create"]
        items_to_update = [
            item for item in items if item.get("operation") == "update"]
        items_to_delete = [
            item for item in items if item.get("operation") == "delete"]

        # Create new items
        create_items(db, items_to_create, commit=False)

        # Update existing items
        update_items(db, items_to_update, commit=False)

        # Delete items
        delete_items(db, [uuid.UUID(item["id"])
                     for item in items_to_delete if "id" in item], commit=False)

        db.commit()

    except HTTPException as http_ex:
        db.rollback()
        print(traceback.format_exc())
        raise http_ex
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating ticket: {str(e)}"
        )


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


# Background task to log API operations
def log_operation(user_id: uuid.UUID, operation: str, resource: str, resource_id: Optional[str] = None):
    timestamp = datetime.now(timezone.utc).isoformat()
    log_entry = f"{timestamp} - User {user_id} - {operation} - {resource}"
    if resource_id:
        log_entry += f" - ID: {resource_id}"

    # In a real app, you'd log to a proper logging system
    print(log_entry)


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


# ------ RECEIPTS ENDPOINTS ------
# These endpoints have been improved for better security, error handling, validation and transaction management


@app.get("/receipts")
async def get_receipts(
    user: Annotated[Usuario, Depends(get_current_active_user)],
    page: int = Query(0, ge=0, description="Page number, zero-indexed"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """Get paginated list of receipts for the current user"""
    is_active = await verify_subscription(user, db)

    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )

    # Log the operation
    if background_tasks:
        background_tasks.add_task(log_operation, user.id, "GET", "receipts")

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
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """Get items for a specific receipt, verifying ownership"""
    is_active = await verify_subscription(user, db)

    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )

    # Verify receipt exists and belongs to user
    ticket = db.query(Ticket).filter(
        Ticket.id == receipt_id,
        Ticket.usuario_id == user.id
    ).first()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receipt not found or not owned by user"
        )

    # Log the operation
    if background_tasks:
        background_tasks.add_task(
            log_operation, user.id, "GET", "receipt_items", str(receipt_id))

    items = get_items(db, receipt_id, user.id)

    return JSONResponse(items)


@app.post("/receipts")
async def create_receipt(
    ticket_data: TicketData,
    user: Annotated[Usuario, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """Create a new receipt with items"""
    is_active = await verify_subscription(user, db)

    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )

    # Validate ticket data
    validation_errors = validate_ticket_data(ticket_data)
    if validation_errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Invalid receipt data",
                "errors": validation_errors
            }
        )

    try:
        new_ticket = create_ticket(db, user.id, ticket_data)

        # Log the operation
        if background_tasks:
            background_tasks.add_task(
                log_operation, user.id, "CREATE", "receipt", str(new_ticket.id))

        return JSONResponse(models_to_dict(new_ticket))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating receipt: {str(e)}"
        )

@app.put("/test")
async def test(
    ticket_data: TicketDataInput):
    """Test endpoint"""
    return ticket_data

@app.put("/receipts")
async def update_receipt(
    ticket_data: TicketDataInput,
    user: Annotated[Usuario, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """Update an existing receipt and its items"""
    is_active = await verify_subscription(user, db)

    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )
    ticket_data = ticket_data.model_dump()
    # Validate ticket data
    validation_errors = validate_ticket_data(ticket_data)
    if validation_errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Invalid receipt data",
                "errors": validation_errors
            }
        )

    # Check if the ticket ID is provided
    if not ticket_data.get("id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Receipt ID is required for updates"
        )

    try:
        update_ticket(db, user.id, ticket_data)

        # Log the operation
        if background_tasks:
            background_tasks.add_task(
                log_operation, user.id, "UPDATE", "receipt", ticket_data.get("id"))

        return JSONResponse({"message": "Receipt updated successfully"})

    except HTTPException as e:
        raise e
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating receipt: {str(e)}"
        )


@app.delete("/receipts/{receipt_id}")
async def delete_receipt(
    receipt_id: uuid.UUID,
    user: Annotated[Usuario, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """Delete a receipt and all its items, verifying ownership"""
    is_active = await verify_subscription(user, db)

    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )

    try:
        deleted = delete_ticket(db, user.id, receipt_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Receipt not found or not owned by user"
            )

        # Log the operation
        if background_tasks:
            background_tasks.add_task(
                log_operation, user.id, "DELETE", "receipt", str(receipt_id))

        return JSONResponse({"message": "Receipt deleted successfully"})

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting receipt: {str(e)}"
        )


# Bulk operations endpoint for more efficient processing
@app.post("/receipts/bulk")
async def bulk_receipts_operations(
    operations: List[Dict],
    user: Annotated[Usuario, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """Perform bulk operations on receipts (create, update, delete)"""
    is_active = await verify_subscription(user, db)

    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )

    results = []

    try:
        # Start transaction for all operations
        for operation in operations:
            op_type = operation.get("type")
            data = operation.get("data", {})

            if op_type == "create":
                # Validate data
                validation_errors = validate_ticket_data(data)
                if validation_errors:
                    results.append({
                        "success": False,
                        "type": op_type,
                        "errors": validation_errors
                    })
                    continue

                # Create ticket
                try:
                    new_ticket = create_ticket(db, user.id, data)
                    results.append({
                        "success": True,
                        "type": op_type,
                        "id": str(new_ticket.id)
                    })

                    # Log operation
                    if background_tasks:
                        background_tasks.add_task(
                            log_operation, user.id, "CREATE", "receipt (bulk)", str(new_ticket.id))

                except Exception as e:
                    results.append({
                        "success": False,
                        "type": op_type,
                        "error": str(e)
                    })

            elif op_type == "update":
                # Validate data
                validation_errors = validate_ticket_data(data)
                if validation_errors:
                    results.append({
                        "success": False,
                        "type": op_type,
                        "errors": validation_errors
                    })
                    continue

                # Check ticket ownership
                ticket = db.query(Ticket).filter(
                    Ticket.id == data.get("id"),
                    Ticket.usuario_id == user.id
                ).first()

                if not ticket:
                    results.append({
                        "success": False,
                        "type": op_type,
                        "id": data.get("id"),
                        "error": "Receipt not found or not owned by user"
                    })
                    continue

                # Update ticket
                try:
                    update_ticket(db, user.id, data)
                    results.append({
                        "success": True,
                        "type": op_type,
                        "id": data.get("id")
                    })

                    # Log operation
                    if background_tasks:
                        background_tasks.add_task(
                            log_operation, user.id, "UPDATE", "receipt (bulk)", data.get("id"))

                except Exception as e:
                    results.append({
                        "success": False,
                        "type": op_type,
                        "id": data.get("id"),
                        "error": str(e)
                    })

            elif op_type == "delete":
                ticket_id = data.get("id")
                if not ticket_id:
                    results.append({
                        "success": False,
                        "type": op_type,
                        "error": "Receipt ID is required"
                    })
                    continue

                # Delete ticket
                try:
                    deleted = delete_ticket(db, user.id, uuid.UUID(ticket_id))

                    if not deleted:
                        results.append({
                            "success": False,
                            "type": op_type,
                            "id": ticket_id,
                            "error": "Receipt not found or not owned by user"
                        })
                        continue

                    results.append({
                        "success": True,
                        "type": op_type,
                        "id": ticket_id
                    })

                    # Log operation
                    if background_tasks:
                        background_tasks.add_task(
                            log_operation, user.id, "DELETE", "receipt (bulk)", ticket_id)

                except Exception as e:
                    results.append({
                        "success": False,
                        "type": op_type,
                        "id": ticket_id,
                        "error": str(e)
                    })
            else:
                results.append({
                    "success": False,
                    "type": op_type,
                    "error": "Unknown operation type"
                })

        return JSONResponse({
            "results": results,
            "successful": sum(1 for r in results if r.get("success", False)),
            "failed": sum(1 for r in results if not r.get("success", False))
        })

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing bulk operations: {str(e)}"
        )


@app.post("/receipts/upload", response_model=TicketData)
async def upload_receipt(
    file: UploadFile, 
    user: Annotated[Usuario, Depends(get_current_active_user)],
    db: Session = Depends(get_db)):

    is_active = await verify_subscription(user, db)

    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )

    # Get file extension (lowercase)
    file_extension = file.filename.split('.')[-1].lower()

    # Validate file type
    if file_extension == 'pdf':
        file_type = 'pdf'
    elif file_extension in ['jpeg', 'jpg', 'png']:
        file_type = 'image'
    else:
        raise HTTPException(
            status_code=400, detail="File must be a PDF, JPEG, or PNG")

    try:
        # Create a temporary file to save the uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Add the instruction prompt
        inp = ["Extract the information from the images"]

        if file_type == 'pdf':
            # Process PDF
            images = convert_pdf_to_images(temp_file_path, in_bytes=True)
            # Create input for the model
            inp.append(VertexImage.from_bytes(image) for image in images)
        else:
            # Process image
            image = Image.open(temp_file_path)
            inp.append(VertexImage.from_bytes(image_to_bytes(image)))

        # Call the model
        response = await model.ainvoke(
            inp,
            generation_config=pdf_config)
        json_data = json.loads(response.text)
        print(json_data)
        ticket_data = TicketData(
            nombre_tienda=json_data.get("store_name", "Unknown"),
            total=clean_price(json_data.get("total").get("total_price")),
            items=[
                ItemData(
                    nombre=item.get("nm"), 
                    precio=clean_price(item.get("price")), 
                    cantidad=clean_int(item.get("cnt")))
                for item in json_data.get("menu")],
        )
        print(ticket_data)
        ticket = create_ticket(db, user.id, ticket_data)
        # Clean up the temporary file
        os.unlink(temp_file_path)

        # Run post-processing
        # await post_processing(json_data)

        return TicketData.from_ticket(ticket)

    except Exception as e:
        full_error = traceback.format_exc()
        raise HTTPException(status_code=500, detail=str(e) + "\n" + full_error)


@app.get("/receipts/{receipt_id}/export")
async def export_receipt(
    receipt_id: uuid.UUID,
    user: Annotated[Usuario, Depends(get_current_active_user)],
    format: Literal["csv", "json"] = Query(
        "csv", description="Export format (csv or json)"),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """Export receipt data in CSV or JSON format"""
    is_active = await verify_subscription(user, db)

    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )

    # Verify receipt exists and belongs to user
    ticket = db.query(Ticket).filter(
        Ticket.id == receipt_id,
        Ticket.usuario_id == user.id
    ).first()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receipt not found or not owned by user"
        )

    # Get receipt items
    items_result = get_items(db, receipt_id, user.id)
    items = items_result.get("items", [])

    # Log the operation
    if background_tasks:
        background_tasks.add_task(
            log_operation, user.id, "EXPORT", f"receipt_{format}", str(receipt_id))

    # Generate filename based on store name and date
    store_name = ticket.nombre_tienda.replace(" ", "_")
    date_str = ticket.created_at.strftime(
        "%Y-%m-%d") if ticket.created_at else datetime.now().strftime("%Y-%m-%d")
    filename = f"{store_name}_{date_str}"

    if format == "csv":
        # Generate CSV
        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "Receipt ID", "Store", "Total", "Date",
            "Item Name", "Price", "Quantity", "Item Total", "Category", "Subcategory"
        ])

        # Write items
        for item in items:
            item_total = float(item["precio"]) * int(item["cantidad"])
            writer.writerow([
                receipt_id,
                ticket.nombre_tienda,
                float(ticket.total),
                ticket.created_at.isoformat() if ticket.created_at else "",
                item["nombre"],
                float(item["precio"]),
                int(item["cantidad"]),
                item_total,
                item.get("categoria", ""),
                item.get("sub_categoria", "")
            ])

        # Return CSV response
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}.csv"
            }
        )
    else:
        # Generate JSON
        export_data = {
            "receipt": ticket.to_dict(),
            "items": items
        }

        # Return JSON response
        return Response(
            content=export_data,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={filename}.json"
            }
        )


@app.get("/categories/stats")
async def get_category_stats(
    user: Annotated[Usuario, Depends(get_current_active_user)],
    parent_category_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """
    Get statistics for categories including count of items and total money spent.
    
    Args:
        user: The authenticated user
        parent_category_id: If provided, only returns stats for subcategories of this category.
                           If not provided, returns stats for main categories (level 0).
        db: Database session
        background_tasks: For logging operations
        
    Returns:
        A list of categories with their statistics
    """
    # Verify subscription status
    is_active = await verify_subscription(user, db)

    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )

    # Log the operation
    if background_tasks:
        background_tasks.add_task(
            log_operation, user.id, "GET", "category_stats",
            str(parent_category_id) if parent_category_id else "all"
        )

    # Build our query to get categories based on parent_category_id
    if parent_category_id:
        # Check if the parent category exists
        parent_category = db.query(Categoria).filter(
            Categoria.id == parent_category_id
        ).first()

        if not parent_category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent category not found"
            )

        # We want direct children of this parent category
        categories_query = db.query(Categoria).filter(
            Categoria.parent_id == parent_category_id
        )
    else:
        # If no parent_category_id, get main categories (level 0)
        categories_query = db.query(Categoria).filter(
            Categoria.nivel == 0
        )

    # Get all targeted categories
    categories = categories_query.all()

    # If no categories found, return empty result
    if not categories:
        return JSONResponse({
            "categories": [],
            "total_categories": 0,
            "filtered_by_parent": str(parent_category_id) if parent_category_id else None
        })

    category_ids = [category.id for category in categories]

    # Single optimized query to get all items and their counts/totals
    # This joins the Item table with Ticket to ensure we only get items from the user's tickets
    # We use a left join with Categoria to get the category information
    result = db.query(
        Item.categoria_id,
        Item.sub_categoria_id,
        func.sum(Item.cantidad).label("item_count"),
        func.sum(Item.precio * Item.cantidad).label("total_spent"),
        Categoria.nombre,
        Categoria.parent_id,
        Categoria.nivel
    ).join(
        Ticket, Ticket.id == Item.receipt_id
    ).join(
        Categoria,
        or_(
            Categoria.id == Item.categoria_id,
            Categoria.id == Item.sub_categoria_id
        ),
        isouter=True
    ).filter(
        Ticket.usuario_id == user.id,
        or_(
            Item.categoria_id.in_(category_ids),
            Item.sub_categoria_id.in_(category_ids)
        )
    ).group_by(
        Item.categoria_id,
        Item.sub_categoria_id,
        Categoria.nombre,
        Categoria.parent_id,
        Categoria.nivel
    ).all()

    # Process the result into the expected format
    stats = {}

    for row in result:
        cat_id = str(
            row.categoria_id if row.categoria_id else row.sub_categoria_id)
        if not cat_id or cat_id == "None":
            continue

        if cat_id not in stats:
            stats[cat_id] = {
                "id": cat_id,
                "name": row.nombre or "Unknown",
                "item_count": int(row.item_count),
                "total_spent": float(row.total_spent),
                "is_subcategory": row.nivel > 0,
                "parent_id": str(row.parent_id) if row.parent_id else None
            }
        else:
            # Update existing stats (in case both categoria_id and sub_categoria_id are populated)
            stats[cat_id]["item_count"] += int(row.item_count)
            stats[cat_id]["total_spent"] += float(row.total_spent)

    # Convert to list for response
    results = list(stats.values())

    return JSONResponse({
        "categories": results,
        "total_categories": len(results),
        "filtered_by_parent": str(parent_category_id) if parent_category_id else None
    })


@app.get("/categories")
async def get_all_categories(
    user: Annotated[Usuario, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    """Get all active categories with their subcategories"""
    is_active = await verify_subscription(user, db)

    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )

    # Since categories are already loaded globally, we can use that
    global categories

    # If for some reason categories aren't loaded, get them
    if not categories:
        categories = get_categories_data(db)

    # Format the response
    return JSONResponse({
        "categories": [
            {
                "id": str(category.id),
                "name": category.name,
                "subcategories": [
                    {"name": subcategory.name, "id": str(subcategory.id)}
                    for subcategory in category.subcategories
                ]
            }
            for category in categories.categories
        ]
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
