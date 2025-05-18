from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated
import stripe

from models import Usuario, UserRegister, UserModify
from database import get_db
from core.security import get_password_hash, create_token
from api.dependencies import get_current_active_user
from core.config import settings

router = APIRouter()

@router.post("/register")
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
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_token(
            data={"sub": new_user.correo, "type": "access"},
            expires_delta=access_token_expires
        )

        # Create refresh token
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
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


@router.post("/modify")
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
