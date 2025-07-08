# models.py
from sqlalchemy import Column, ForeignKey, Integer, String, Date, Numeric, UniqueConstraint, Boolean, DateTime
from typing import Annotated, Optional, List, Union, Literal, Dict
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.session import Session
from sqlalchemy.orm import declarative_base
import uuid
from pydantic import BaseModel, StringConstraints, EmailStr, SecretStr, Field
from typing_extensions import TypedDict
from datetime import datetime, date
import decimal
import json

# DB MODELS
Base = declarative_base()

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
    tickets = relationship(
        "Ticket", back_populates="usuario", cascade="all, delete-orphan")
    
    usos_servicio = relationship(
        "UsoServicio", back_populates="usuario", cascade="all, delete-orphan")

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
            result["tickets"] = [tickets.to_dict() for tickets in self.tickets]

        return result


class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(100), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey(
        'categorias.id'), nullable=True)  # Self-reference for hierarchy
    # Level in hierarchy (0 for main category, 1 for subcategory)
    nivel = Column(Integer, default=0)
    activo = Column(Boolean, default=True)
    # Note: mes_ano column has been removed

    # Self-referential relationship
    subcategorias = relationship("Categoria",
                                 backref=backref(
                                     "categoria_padre", remote_side=[id]),
                                 cascade="all, delete-orphan")

    # Items that belong to this category - specify which foreign key to use
    items_as_main_category = relationship(
        "Item", foreign_keys="Item.categoria_id", back_populates="categoria_rel")
    items_as_subcategory = relationship(
        "Item", foreign_keys="Item.sub_categoria_id", back_populates="sub_categoria_rel")

    def to_dict(self, include_relationships=False):
        """Convert model to dictionary"""
        result = {
            "id": str(self.id),
            "nombre": self.nombre,
            "nivel": self.nivel,
            "activo": self.activo,
            "parent_id": str(self.parent_id) if self.parent_id else None
        }

        if include_relationships:
            result["subcategorias"] = [subcat.to_dict()
                                       for subcat in self.subcategorias] if self.subcategorias else []

        return result


class Ticket(Base):
    __tablename__ = "ticket"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre_tienda = Column(String(100), nullable=False)
    total = Column(Numeric(10, 2), nullable=False)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey(
        'usuarios.id', ondelete='CASCADE'))
    created_at = Column(DateTime(timezone=True), nullable=False)
    modified_at = Column(DateTime(timezone=True), nullable=False)

    # Relationships
    usuario = relationship("Usuario", back_populates="tickets")
    items = relationship("Item", back_populates="ticket",
                         cascade="all, delete-orphan")

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
    receipt_id = Column(UUID(as_uuid=True), ForeignKey(
        'ticket.id', ondelete='CASCADE'))
    nombre = Column(String(100), nullable=False)
    precio = Column(Numeric(10, 2), nullable=False)
    cantidad = Column(Integer, nullable=False)

    # Only keep the foreign key columns to categories
    categoria_id = Column(UUID(as_uuid=True), ForeignKey(
        'categorias.id'), nullable=True)
    sub_categoria_id = Column(
        UUID(as_uuid=True), ForeignKey('categorias.id'), nullable=True)

    # Relationships
    ticket = relationship("Ticket", back_populates="items")
    categoria_rel = relationship("Categoria", foreign_keys=[
                                 categoria_id], back_populates="items_as_main_category")
    sub_categoria_rel = relationship("Categoria", foreign_keys=[
                                     sub_categoria_id], back_populates="items_as_subcategory")

    def to_dict(self, include_relationships=False):
        """Convert model to dictionary, optionally including relationships"""
        result = {
            "id": str(self.id),
            "receipt_id": str(self.receipt_id),
            "nombre": self.nombre,
            "precio": float(self.precio) if isinstance(self.precio, decimal.Decimal) else self.precio,
            "cantidad": self.cantidad,
            "categoria_id": str(self.categoria_id) if self.categoria_id else None,
            "sub_categoria_id": str(self.sub_categoria_id) if self.sub_categoria_id else None
        }

        if include_relationships:
            # Include category objects
            if self.categoria_rel:
                result["categoria_id"] = self.categoria_rel.nombre
                result["categoria_obj"] = self.categoria_rel.to_dict()

            if self.sub_categoria_rel:
                result["sub_categoria"] = self.sub_categoria_rel.nombre
                result["sub_categoria_obj"] = self.sub_categoria_rel.to_dict()

            # Avoid circular references - minimal info
            result["ticket"] = {
                "id": str(self.ticket.id),
                "nombre_tienda": self.ticket.nombre_tienda,
                "total": float(self.ticket.total) if isinstance(self.ticket.total, decimal.Decimal) else self.ticket.total,
                "usuario_id": str(self.ticket.usuario_id),
                "created_at": self.ticket.created_at.isoformat() if self.ticket.created_at else None,
                "modified_at": self.ticket.modified_at.isoformat() if self.ticket.modified_at else None
            } if self.ticket else None

        return result

# Nuevas tablas para el sistema de cuotas

class Servicio(Base):
    __tablename__ = "servicios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(String(255), nullable=True)
    activo = Column(Boolean, default=True)

    # Relationships
    cuotas = relationship("Cuota", back_populates="servicio",
                          cascade="all, delete-orphan")
    usos = relationship("UsoServicio", back_populates="servicio")

    def to_dict(self, include_relationships=False):
        """Convert model to dictionary"""
        result = {
            "id": str(self.id),
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "activo": self.activo
        }

        if include_relationships:
            result["cuotas"] = [cuota.to_dict() for cuota in self.cuotas]
            result["usos"] = [uso.to_dict() for uso in self.usos]

        return result


class Cuota(Base):
    __tablename__ = "cuotas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    servicio_id = Column(UUID(as_uuid=True), ForeignKey(
        'servicios.id', ondelete='CASCADE'))
    nombre = Column(String(100), nullable=False)
    limite_uso = Column(Integer, nullable=False, default=0)  # 0 = ilimitado
    # ID del plan en Stripe al que está asociada esta cuota
    plan_stripe = Column(String(255), nullable=True)
    activo = Column(Boolean, default=True)

    # Relationships
    servicio = relationship("Servicio", back_populates="cuotas")
    usos = relationship("UsoServicio", back_populates="cuota")

    def to_dict(self, include_relationships=False):
        """Convert model to dictionary"""
        result = {
            "id": str(self.id),
            "servicio_id": str(self.servicio_id),
            "nombre": self.nombre,
            "limite_uso": self.limite_uso,
            "plan_stripe": self.plan_stripe,
            "activo": self.activo
        }

        if include_relationships:
            result["servicio"] = self.servicio.to_dict(
            ) if self.servicio else None
            result["usos"] = [uso.to_dict() for uso in self.usos]

        return result


class UsoServicio(Base):
    __tablename__ = "uso_servicios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey(
        'usuarios.id', ondelete='CASCADE'))
    servicio_id = Column(UUID(as_uuid=True), ForeignKey(
        'servicios.id', ondelete='CASCADE'))
    cuota_id = Column(UUID(as_uuid=True), ForeignKey(
        'cuotas.id', ondelete='CASCADE'))
    uso_actual = Column(Integer, default=0)
    ultimo_reset = Column(DateTime(timezone=True),
                          nullable=True)  # Para fines de registro

    # Unique constraint to ensure one record per user-service-quota
    __table_args__ = (
        UniqueConstraint('usuario_id', 'servicio_id',
                         'cuota_id', name='uc_usuario_servicio_cuota'),
    )

    # Relationships
    usuario = relationship("Usuario", back_populates="usos_servicio")
    servicio = relationship("Servicio", back_populates="usos")
    cuota = relationship("Cuota", back_populates="usos")

    def to_dict(self, include_relationships=False):
        """Convert model to dictionary"""
        result = {
            "id": str(self.id),
            "usuario_id": str(self.usuario_id),
            "servicio_id": str(self.servicio_id),
            "cuota_id": str(self.cuota_id),
            "uso_actual": self.uso_actual,
            "ultimo_reset": self.ultimo_reset.isoformat() if self.ultimo_reset else None
        }

        if include_relationships:
            result["usuario"] = {
                "id": str(self.usuario.id),
                "nombre": self.usuario.nombre,
                "apellidos": self.usuario.apellidos,
                "correo": self.usuario.correo
            } if self.usuario else None

            result["servicio"] = self.servicio.to_dict(
            ) if self.servicio else None
            result["cuota"] = self.cuota.to_dict() if self.cuota else None

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


class ItemDataInput(BaseModel):
    id: Optional[str]
    receipt_id: Optional[str]
    nombre: Optional[str]
    precio: Optional[float]
    cantidad: Optional[int]
    categoria_id: Optional[str]
    sub_categoria_id: Optional[str]
    operation: Optional[Literal['create', 'update', 'delete']] = None


class TicketDataInput(BaseModel):
    id: Optional[str]
    nombre_tienda: str
    total: float
    usuario_id: str | None = None
    items: List[ItemDataInput]


class ItemData(BaseModel):
    id: Optional[str] = None
    receipt_id: Optional[str] = None
    nombre: Optional[str] = None
    precio: Optional[float] = 0.0
    cantidad: Optional[int] = 0
    categoria_id: Optional[str] = None
    sub_categoria_id: Optional[str] = None
    operation: Union[Literal['create', 'update', 'delete'], None] = None


class TicketData(BaseModel):
    id: Optional[str] = None
    nombre_tienda: str
    total: float = 0.0
    usuario_id: str | None = None
    items: List[ItemData] = []

    @staticmethod
    def from_ticket(ticket: Ticket):
        return TicketData(
            id=str(ticket.id),
            nombre_tienda=ticket.nombre_tienda,
            total=float(ticket.total),
            usuario_id=str(ticket.usuario_id),
            items=[ItemData(
                id=str(item.id),
                receipt_id=str(item.receipt_id),
                nombre=item.nombre,
                precio=float(item.precio),
                cantidad=item.cantidad,
                categoria_id=str(item.categoria_id),
                sub_categoria_id=str(item.sub_categoria_id),
                operation=None
            ) for item in ticket.items]
        )


class Subcategory(BaseModel):
    """Modelo para las subcategorías"""
    name: str
    id: Optional[uuid.UUID]


class Category(BaseModel):
    """Modelo para las categorías principales"""
    name: str
    id: Optional[uuid.UUID]
    subcategories: List[Subcategory]


class CategoriesData(BaseModel):
    """Modelo para el conjunto completo de datos de categorías"""
    categories: List[Category] = Field(default_factory=list)

    def __str__(self):
        return '- '+'\n- '.join([category.name for category in self.categories])


def get_categories_data(db: Session) -> CategoriesData:
    """
    Optimized version that retrieves all categories in a single query
    and structures them using dictionary mapping.

    Args:
        db: SQLAlchemy database session

    Returns:
        models.CategoriesData: Structured category data
    """
    # Get all active categories
    all_categories = db.query(Categoria).filter(
        Categoria.activo == True
    ).all()

    # Group by main categories and subcategories
    main_categories: Dict[uuid.UUID, Categoria] = {}
    subcategories: Dict[uuid.UUID, List[Categoria]] = {}

    for cat in all_categories:
        if cat.nivel == 0:
            main_categories[cat.id] = cat
            subcategories[cat.id] = []
        elif cat.nivel == 1 and cat.parent_id is not None:
            if cat.parent_id not in subcategories:
                subcategories[cat.parent_id] = []
            subcategories[cat.parent_id].append(cat)

    # Build CategoriesData
    categories_data = CategoriesData(categories=[])

    for main_id, main_cat in main_categories.items():
        # Convert subcategories to Pydantic model
        subcat_models = [
            Subcategory(name=subcat.nombre, id=subcat.id)
            for subcat in subcategories.get(main_id, [])
        ]

        # Create main category with its subcategories
        category = Category(
            id=main_cat.id,
            name=main_cat.nombre,
            subcategories=subcat_models
        )

        # Add to categories list
        categories_data.categories.append(category)

    return categories_data

# Nuevos modelos Pydantic para el sistema de cuotas


class ServicioBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    activo: bool = True


class ServicioCreate(ServicioBase):
    pass


class ServicioUpdate(ServicioBase):
    nombre: Optional[str] = None
    activo: Optional[bool] = None


class ServicioRead(ServicioBase):
    id: str


class CuotaBase(BaseModel):
    servicio_id: str
    nombre: str
    limite_uso: int = 0  # 0 significa ilimitado
    plan_stripe: Optional[str] = None
    activo: bool = True


class CuotaCreate(CuotaBase):
    pass


class CuotaUpdate(CuotaBase):
    servicio_id: Optional[str] = None
    nombre: Optional[str] = None
    limite_uso: Optional[int] = None
    plan_stripe: Optional[str] = None
    activo: Optional[bool] = None


class CuotaRead(CuotaBase):
    id: str
    servicio: Optional[ServicioRead] = None


class UsoServicioBase(BaseModel):
    usuario_id: str
    servicio_id: str
    cuota_id: str
    uso_actual: int = 0
    ultimo_reset: Optional[datetime] = None


class UsoServicioCreate(UsoServicioBase):
    pass


class UsoServicioUpdate(BaseModel):
    uso_actual: Optional[int] = None
    ultimo_reset: Optional[datetime] = None


class UsoServicioRead(UsoServicioBase):
    id: str
