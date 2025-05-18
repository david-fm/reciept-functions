from typing import Dict, List
from models import (
    Ticket, models_to_dict,
    Item, TicketData,
    Categoria, ItemData
)
import uuid
import traceback
from fastapi import HTTPException, status
from datetime import datetime, timezone
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List
import decimal
from models import TicketData
from core.file_processing.product_classiffier_agent import State as ClassifierState
from core.file_processing.product_classiffier_agent import build_graph
from core.config import settings

classifier = build_graph()

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
            "available_categories": settings.categories_data
        })

        item["categoria"] = classification["category"]
        item["sub_categoria"] = classification["subcategory"]


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
                    categoria_id=db.query(Categoria).filter(
                        Categoria.nombre == item_data.get("categoria")).first().id,
                    sub_categoria_id=db.query(Categoria).filter(
                        Categoria.nombre == item_data.get("sub_categoria")).first().id
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
