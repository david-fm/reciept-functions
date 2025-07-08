from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status, UploadFile
from fastapi.responses import JSONResponse, Response
from vertexai.generative_models import Image as VertexImage
from sqlalchemy.orm import Session
from typing import List, Dict, Annotated, Literal
from io import StringIO
from PIL import Image
import traceback
import tempfile
import json
import csv
from datetime import datetime
import uuid
import os

from database import get_db
from models import Ticket, Usuario, TicketData, ItemData, models_to_dict, TicketDataInput
from api.dependencies import get_current_active_user, log_operation
from services.receipt_service import (
    validate_ticket_data,
    create_ticket,
    update_ticket,
    delete_ticket,
    get_items,
    get_tickets
)
from services.subscription_service import verify_subscription
from services.quota_service import check_quota
from services.receipt_processing import (
    file_to_receipt_data
)
from core.config import settings

router = APIRouter()


@router.get("")
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


@router.get("/{receipt_id}")
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


@router.post("")
@check_quota(servicio_id=settings.CREATE_TICKET_SERVICE)
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


@router.put("")
@check_quota(servicio_id=settings.MODIFY_TICKET_SERVICE)
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
    if not ticket_data.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Receipt ID is required for updates"
        )

    try:
        update_ticket(db, user.id, ticket_data)

        # Log the operation
        if background_tasks:
            background_tasks.add_task(
                log_operation, user.id, "UPDATE", "receipt", ticket_data.id)

        return JSONResponse({"message": "Receipt updated successfully"})

    except HTTPException as e:
        raise e
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating receipt: {str(e)}"
        )


@router.delete("/{receipt_id}")
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
# Deactivated by now
# @router.post("/bulk")
# async def bulk_receipts_operations(
#     operations: List[Dict],
#     user: Annotated[Usuario, Depends(get_current_active_user)],
#     db: Session = Depends(get_db),
#     background_tasks: BackgroundTasks = None
# ):
#     """Perform bulk operations on receipts (create, update, delete)"""
#     is_active = await verify_subscription(user, db)

#     if not is_active:
#         raise HTTPException(
#             status_code=status.HTTP_402_PAYMENT_REQUIRED,
#             detail="Active subscription required"
#         )

#     results = []

#     try:
#         # Start transaction for all operations
#         for operation in operations:
#             op_type = operation.get("type")
#             data = operation.get("data", {})

#             if op_type == "create":
#                 # Validate data
#                 validation_errors = validate_ticket_data(data)
#                 if validation_errors:
#                     results.routerend({
#                         "success": False,
#                         "type": op_type,
#                         "errors": validation_errors
#                     })
#                     continue

#                 # Create ticket
#                 try:
#                     new_ticket = create_ticket(db, user.id, data)
#                     results.routerend({
#                         "success": True,
#                         "type": op_type,
#                         "id": str(new_ticket.id)
#                     })

#                     # Log operation
#                     if background_tasks:
#                         background_tasks.add_task(
#                             log_operation, user.id, "CREATE", "receipt (bulk)", str(new_ticket.id))

#                 except Exception as e:
#                     results.routerend({
#                         "success": False,
#                         "type": op_type,
#                         "error": str(e)
#                     })

#             elif op_type == "update":
#                 # Validate data
#                 validation_errors = validate_ticket_data(data)
#                 if validation_errors:
#                     results.routerend({
#                         "success": False,
#                         "type": op_type,
#                         "errors": validation_errors
#                     })
#                     continue

#                 # Check ticket ownership
#                 ticket = db.query(Ticket).filter(
#                     Ticket.id == data.get("id"),
#                     Ticket.usuario_id == user.id
#                 ).first()

#                 if not ticket:
#                     results.routerend({
#                         "success": False,
#                         "type": op_type,
#                         "id": data.get("id"),
#                         "error": "Receipt not found or not owned by user"
#                     })
#                     continue

#                 # Update ticket
#                 try:
#                     update_ticket(db, user.id, data)
#                     results.routerend({
#                         "success": True,
#                         "type": op_type,
#                         "id": data.get("id")
#                     })

#                     # Log operation
#                     if background_tasks:
#                         background_tasks.add_task(
#                             log_operation, user.id, "UPDATE", "receipt (bulk)", data.get("id"))

#                 except Exception as e:
#                     results.routerend({
#                         "success": False,
#                         "type": op_type,
#                         "id": data.get("id"),
#                         "error": str(e)
#                     })

#             elif op_type == "delete":
#                 ticket_id = data.get("id")
#                 if not ticket_id:
#                     results.routerend({
#                         "success": False,
#                         "type": op_type,
#                         "error": "Receipt ID is required"
#                     })
#                     continue

#                 # Delete ticket
#                 try:
#                     deleted = delete_ticket(db, user.id, uuid.UUID(ticket_id))

#                     if not deleted:
#                         results.routerend({
#                             "success": False,
#                             "type": op_type,
#                             "id": ticket_id,
#                             "error": "Receipt not found or not owned by user"
#                         })
#                         continue

#                     results.routerend({
#                         "success": True,
#                         "type": op_type,
#                         "id": ticket_id
#                     })

#                     # Log operation
#                     if background_tasks:
#                         background_tasks.add_task(
#                             log_operation, user.id, "DELETE", "receipt (bulk)", ticket_id)

#                 except Exception as e:
#                     results.routerend({
#                         "success": False,
#                         "type": op_type,
#                         "id": ticket_id,
#                         "error": str(e)
#                     })
#             else:
#                 results.routerend({
#                     "success": False,
#                     "type": op_type,
#                     "error": "Unknown operation type"
#                 })

#         return JSONResponse({
#             "results": results,
#             "successful": sum(1 for r in results if r.get("success", False)),
#             "failed": sum(1 for r in results if not r.get("success", False))
#         })

#     except Exception as e:
#         db.rollback()
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Error processing bulk operations: {str(e)}"
#         )


@router.post("/upload", response_model=TicketData)
@check_quota(servicio_id=settings.TICKET_PROCESSING_SERVICE)
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
        
        ticket_data = await file_to_receipt_data(file, file_type, file_extension)
        # print(ticket_data)
        ticket = create_ticket(db, user.id, ticket_data)
        # await post_processing(json_data)

        return TicketData.from_ticket(ticket)

    except Exception as e:
        full_error = traceback.format_exc()
        raise HTTPException(status_code=500, detail=str(e) + "\n" + full_error)


@router.get("/{receipt_id}/export")
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
            media_type="routerlication/json",
            headers={
                "Content-Disposition": f"attachment; filename={filename}.json"
            }
        )
