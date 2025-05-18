from sqlalchemy.orm import Session
from core.security import verify_password
from models import Usuario

def get_user(db: Session, username: str):
    found = db.query(Usuario).filter(Usuario.correo == username)
    user = found.first()
    if user:
        return user


def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.passw):
        return False
    return user
