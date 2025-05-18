from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

ticket_schema = {
    "type": "object",
    "properties": {
        "menu": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "nm": {
                        "type": "string"
                    },
                    "cnt": {
                        "type": "string"
                    },
                    "price": {
                        "type": "string"
                    }
                }
            }
        },
        "total": {
            "type": "object",
            "properties": {
                "total_price": {
                    "type": "string"
                }
            }
        }
    }

}
# pdf_description = """
# ticket:
#     nombre_tienda: Nombre de la tienda o establecimiento
#     total: Monto total de la compra

# items: Lista de productos comprados que contiene para cada uno:
#     receipt_id: Identificador único del recibo
#     nombre: Nombre del producto
#     precio: Precio unitario del producto
#     cantidad: Cantidad de unidades del producto
# """

# ticket_schema = {
#     "type": "object",
#     "properties": {
#         "nombre_tienda": {
#             "type": "string"
#         },
#         "total": {
#             "type": "number"
#         },
#         "items": {
#             "type": "array",
#             "items": {
#                 "type": "object",
#                 "properties": {
#                     "receipt_id": {
#                         "type": "string"
#                     },
#                     "nombre": {
#                         "type": "string"
#                     },
#                     "precio": {
#                         "type": "number"
#                     },
#                     "cantidad": {
#                         "type": "integer"
#                     }
#                 }
#             }
#         }
#     },
#     "required": ["nombre_tienda", "total", "items"]
# }
