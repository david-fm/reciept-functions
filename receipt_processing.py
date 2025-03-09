import uuid
from .models import Receipt, Item
from typing import Dict, List
from django.contrib.auth.models import AbstractBaseUser
from ninja import Schema
from typing import TypedDict
from pydantic import Field, field_validator
from typing_extensions import Annotated
from datetime import datetime
import re
from asgiref.sync import sync_to_async


class ItemSchema(Schema):
    """
    Schema for an item.
    """
    name: Annotated[str, Field(max_length=255)]
    price: Annotated[float, Field()]
    quantity: Annotated[int, Field(ge=0)]

    # @field_validator('name')
    # @classmethod
    # def name_must_not_be_empty(cls, v: str) -> str:
    #     if v.strip() == '':
    #         raise ValueError('Name must not be empty or just whitespace')
    #     return v.strip()


class ReceiptSchema(Schema):
    """
    Schema for a receipt.
    """
    total: Annotated[float, Field()]
    created: str
    id: uuid.UUID
    shop_name: Annotated[str, Field(min_length=0, max_length=255)]
    items: Annotated[List[ItemSchema], Field(min_length=0)]

    @field_validator('created')
    @classmethod
    def validate_created_date(cls, v: str) -> str:
        try:
            datetime.strptime(v, '%Y-%m-%d %H:%M:%S.%f%z')
        except ValueError:
            raise ValueError(
                "Incorrect date format, should be YYYY-MM-DD HH:MM:SS")
        return v

    # @field_validator('total')
    # @classmethod
    # def validate_total(cls, v: float, values) -> float:
    #     items = values.data.get('items', [])
    #     calculated_total = sum(item.price * item.quantity for item in items)
    #     if abs(v - calculated_total) > 0.01:  # Allow for small float precision errors
    #         raise ValueError(f"Total {v} does not match sum of item prices {calculated_total}")
    #     return v


def clean_number(value: str) -> str:
    """
    Clean a number string by removing any non-numeric characters.

    Args:
        value (str): The number string to clean.

    Returns:
        str: The cleaned number string.

    """
    return re.sub(r"[^\d.,]", "", value)


def clean_price(price: str) -> float:
    if not price:
        return 0.0

    price = clean_number(price)
    return float(price.replace(",", "."))


def clean_int(value: str) -> int:
    if not value:
        return 1
    value = clean_number(value)
    return int(value)


async def create_receipt(data: Dict, user: AbstractBaseUser) -> Receipt:
    """
    Create a receipt with the given data and user.

    Args:
        data (Dict): The data for creating the receipt.
        user (AbstractBaseUser): The user associated with the receipt.

    Returns:
        Receipt: The created receipt.

    """
    total = data.get("total", {}).get("total_price")
    total = clean_price(total)
    receipt = await Receipt.objects.acreate(total=total, user=user)
    # print(data)
    # if data["menu"] is empty, return receipt
    if not data.get("menu"):
        return receipt
    # if data["menu"] has only one item, create it and return receipt it won't be a list

    if isinstance(data["menu"], dict):
        item = data["menu"]
        await Item.objects.acreate(
            receipt=receipt,
            name=item.get("nm"),
            price=clean_price(item.get("price")),
            quantity=clean_int(item.get("cnt")))
        return receipt
    for item in data["menu"]:
        await Item.objects.acreate(
            receipt=receipt,
            name=item.get("nm"),
            price=clean_price(item.get("price")),
            quantity=clean_int(item.get("cnt")))
    return receipt


async def modify_receipt(data: ReceiptSchema, user: AbstractBaseUser) -> Receipt:
    """
    Modify a receipt with the given data and user.

    Args:
        data (Dict): The data for modifying the receipt.
        user (AbstractBaseUser): The user associated with the receipt.

    Returns:
        Receipt: The modified receipt.

    """
    receipt = await Receipt.objects.aget(id=data.id)
    if not receipt:
        return None
    if await sync_to_async(lambda: receipt.user != user)():
        return None
    receipt.total = clean_price(data.total) if isinstance(
        data.total, str) else data.total
    receipt.shop_name = data.shop_name
    await receipt.asave()
    await receipt.items.all().adelete()
    for item in data.items:
        await Item.objects.acreate(
            receipt=receipt,
            name=item.name,
            price=clean_price(item.price) if isinstance(
                item.price, str) else item.price,
            quantity=clean_int(item.quantity) if isinstance(item.quantity, str) else item.quantity)
    return receipt


class ItemDict(TypedDict):
    name: str
    price: float
    quantity: int


class ReceiptDict(TypedDict):
    total: float
    created: str
    id: uuid.UUID
    shop_name: str
    items: List[ItemDict]


async def receipt_to_json(receipt: Receipt) -> ReceiptDict:
    """
    Convert a Receipt object to a JSON-compatible dictionary.

    Args:
        receipt (Receipt): The Receipt object to convert.

    Returns:
        ReceiptDict: A dictionary representing the Receipt object in JSON format.
    """
    items = []
    async for item in receipt.items.all():
        items.append({
            "name": item.name,
            "price": item.price,
            "quantity": item.quantity
        })
    return {
        "total": receipt.total,
        "created": str(receipt.created),
        "id": receipt.id,
        "shop_name": receipt.shop_name,
        "items": items
    }


async def receipt_json_to_csv(receipt: ReceiptDict) -> bytes:
    """
    Convert a receipt in JSON format to a CSV file.

    Args:
        receipt (ReceiptDict): The receipt in JSON format.

    Returns:
        bytes: The CSV file content encoded as UTF-8.

    """
    import csv
    import io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "price", "quantity"])
    for item in receipt["items"]:
        writer.writerow([item["name"], item["price"], item["quantity"]])
    return output.getvalue().encode("utf-8")
