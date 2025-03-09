# models.py
from sqlalchemy import Column, ForeignKey, Integer, String, Date, Numeric, UniqueConstraint, Boolean, DateTime
from typing import Annotated, TypedDict, Optional, List, Union, Literal
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from database import Base
from pydantic import BaseModel, StringConstraints, EmailStr, SecretStr
from datetime import datetime, date
import decimal
import json

# DB MODELS


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    correo = Column(String(100), unique=True, nullable=False)
    passw = Column(String(72), nullable=False)
    customer_id = Column(String(255), nullable=False)
    subscription_id = Column(String(255), nullable=True)
    active = Column(Boolean())
    last_verified = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    sistema_usos = relationship("SistemaUso", back_populates="usuario")
    tiendas = relationship("Tienda", back_populates="usuario")

    def to_dict(self, include_relationships=False):
        """Convert model to dictionary, optionally including relationships"""
        result = {
            "id": str(self.id),
            "nombre": self.nombre,
            "apellidos": self.apellidos,
            "correo": self.correo,
            # Exclude password for security
            "customer_id": self.customer_id,
            "subscription_id": self.subscription_id,
            "active": self.active,
            "last_verified": self.last_verified.isoformat() if self.last_verified else None
        }

        if include_relationships:
            result["sistema_usos"] = [uso.to_dict()
                                      for uso in self.sistema_usos]
            result["tiendas"] = [tienda.to_dict() for tienda in self.tiendas]

        return result


class SistemaUso(Base):
    __tablename__ = "sistema_uso"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sistema = Column(String(50), nullable=False)
    uso = Column(String(100))
    fecha = Column(Date, nullable=False)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey('usuarios.id'))

    # Relationship
    usuario = relationship("Usuario", back_populates="sistema_usos")

    __table_args__ = (
        UniqueConstraint('sistema', 'fecha', 'usuario_id',
                         name='sistema_uso_key'),
    )

    def to_dict(self, include_relationships=False):
        """Convert model to dictionary, optionally including relationships"""
        result = {
            "id": str(self.id),
            "sistema": self.sistema,
            "uso": self.uso,
            "fecha": self.fecha.isoformat() if isinstance(self.fecha, date) else self.fecha,
            "usuario_id": str(self.usuario_id)
        }

        if include_relationships:
            # Avoid circular references
            result["usuario"] = {
                "id": str(self.usuario.id),
                "nombre": self.usuario.nombre,
                "apellidos": self.usuario.apellidos,
                "correo": self.usuario.correo
            } if self.usuario else None

        return result


class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(50), nullable=False)
    mes_ano = Column(Date, nullable=False)

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "nombre": self.nombre,
            "mes_ano": self.mes_ano.isoformat() if isinstance(self.mes_ano, date) else self.mes_ano
        }


class Ticket(Base):
    __tablename__ = "ticket"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre_tienda = Column(String(100), nullable=False)
    total = Column(Numeric(10, 2), nullable=False)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey('usuarios.id', ondelete='CASCADE'))
    created_at = Column(DateTime(timezone=True), nullable=False)
    modified_at = Column(DateTime(timezone=True), nullable=False)

    # Relationships
    usuario = relationship("Usuario", back_populates="tiendas")
    items = relationship("Item", back_populates="tienda")

    def to_dict(self, include_relationships=False):
        """Convert model to dictionary, optionally including relationships"""
        result = {
            "id": str(self.id),
            "nombre_tienda": self.nombre_tienda,
            "total": float(self.total) if isinstance(self.total, decimal.Decimal) else self.total,
            "usuario_id": str(self.usuario_id),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None
        }

        if include_relationships:
            # Avoid circular references
            result["usuario"] = {
                "id": str(self.usuario.id),
                "nombre": self.usuario.nombre,
                "apellidos": self.usuario.apellidos
            } if self.usuario else None

            result["items"] = [item.to_dict() for item in self.items]

        return result


class Item(Base):
    __tablename__ = "items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receipt_id = Column(UUID(as_uuid=True), ForeignKey('ticket.id', ondelete='CASCADE'))
    nombre = Column(String(100), nullable=False)
    precio = Column(Numeric(10, 2), nullable=False)
    cantidad = Column(Integer, nullable=False)
    categoria = Column(String(50))
    sub_categoria = Column(String(50))

    # Relationship
    tienda = relationship("Ticket", back_populates="items")

    def to_dict(self, include_relationships=False):
        """Convert model to dictionary, optionally including relationships"""
        result = {
            "id": str(self.id),
            "receipt_id": str(self.receipt_id),
            "nombre": self.nombre,
            "precio": float(self.precio) if isinstance(self.precio, decimal.Decimal) else self.precio,
            "cantidad": self.cantidad,
            "categoria": self.categoria,
            "sub_categoria": self.sub_categoria
        }

        if include_relationships:
            # Avoid circular references - minimal info
            result["tienda"] = {
                "id": str(self.tienda.id),
                "nombre_tienda": self.tienda.nombre_tienda
            } if self.tienda else None

        return result


# Custom JSON encoder for handling SQLAlchemy specific types
class SQLAlchemyJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super(SQLAlchemyJSONEncoder, self).default(obj)


def model_to_dict(instance, include_relationships=False):
    """Convert a model instance to dictionary"""
    if hasattr(instance, "to_dict"):
        result = instance.to_dict(include_relationships=include_relationships)
    else:
        # Fallback method for models without to_dict method
        result = {c.name: getattr(instance, c.name)
                  for c in instance.__table__.columns}

    return result


def models_to_dict(instances, include_relationships=False):
    """Convert a list of model instances to dictionary"""
    result = []
    for instance in instances:
        if hasattr(instance, "to_dict"):
            result.append(instance.to_dict(
                include_relationships=include_relationships))
        else:
            # Fallback method for models without to_dict method
            result.append({c.name: getattr(instance, c.name)
                          for c in instance.__table__.columns})

    return result

# Utility function to convert a model instance to JSON


def model_to_json(instance, include_relationships=False):
    """Convert a model instance to JSON string"""
    result = model_to_dict(
        instance, include_relationships=include_relationships)

    return json.dumps(result, cls=SQLAlchemyJSONEncoder)


# Utility function to convert a list of model instances to JSON
def models_to_json(instances, include_relationships=False):
    """Convert a list of model instances to JSON string"""
    result = models_to_dict(
        instances, include_relationships=include_relationships)

    return json.dumps(result, cls=SQLAlchemyJSONEncoder)

# AUTH MODELS


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


# class User(BaseModel):
#     username: str
#     name: str | None = None
#     surname: str | None = None
#     active: bool | None = None
#     customer_id: str


# class UserInDB(User):
#     hashed_password: str


class UserRegister(BaseModel):
    email: EmailStr
    password: Annotated[
        SecretStr,
        StringConstraints(min_length=8)
    ]
    name: str
    surnames: str


class UserModify(BaseModel):
    email: EmailStr | None = None
    password: Annotated[
        SecretStr,
        StringConstraints(min_length=8)
    ] | None = None
    name: str | None = None
    surnames: str | None = None


class ItemData(TypedDict):
    id: Optional[str]
    receipt_id: Optional[str]
    nombre: Optional[str]
    precio: Optional[float]
    cantidad: Optional[int]
    categoria: Optional[str]
    sub_categoria: Optional[str]
    operation: Optional[Literal['create', 'update', 'delete']]


class TicketData(TypedDict):
    id: Optional[str]
    nombre_tienda: str
    total: float
    usuario_id: str
    items: List[ItemData]
