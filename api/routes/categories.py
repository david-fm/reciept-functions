from typing import Optional, Annotated
import uuid
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from fastapi.responses import JSONResponse
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from models import Usuario, Categoria, Item, Ticket, get_categories_data
from database import get_db
from api.dependencies import get_current_active_user, log_operation
from services.subscription_service import verify_subscription

router = APIRouter()


@router.get("/stats")
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


@router.get("/")
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
