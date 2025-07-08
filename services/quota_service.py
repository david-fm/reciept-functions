import functools
from models import Usuario, UsoServicio, Cuota, Servicio
from fastapi import HTTPException
import stripe
from sqlalchemy.orm import Session
from typing import Optional, Callable, Any, Coroutine
from datetime import datetime, timezone
from models import (
    UsoServicio,
    Cuota
)
from sqlalchemy.orm.session import Session
import uuid

def verificar_cuota_disponible(db: Session, usuario_id: uuid.UUID, servicio_id: uuid.UUID) -> bool:
    """
    Verifica si un usuario tiene cuota disponible para un servicio específico.
    
    Args:
        db: Sesión de base de datos
        usuario_id: ID del usuario
        servicio_id: ID del servicio a verificar
    
    Returns:
        bool: True si el usuario tiene cuota disponible, False si ha alcanzado el límite
    """
    # Obtener el uso actual del servicio para el usuario
    uso = db.query(UsoServicio).filter(
        UsoServicio.usuario_id == usuario_id,
        UsoServicio.servicio_id == servicio_id
    ).first()

    if not uso:
        # Si no existe registro de uso, el usuario no está suscrito a este servicio
        return False

    # Obtener la cuota asociada
    cuota = db.query(Cuota).filter(
        Cuota.id == uso.cuota_id
    ).first()

    if not cuota:
        # Si no hay una cuota definida, no permitimos el uso
        return False

    # Si el límite es 0, significa uso ilimitado
    if cuota.limite_uso == 0:
        return True

    # Verificar si el uso actual es menor que el límite
    return uso.uso_actual < cuota.limite_uso


def incrementar_uso_servicio(db: Session, usuario_id: uuid.UUID, servicio_id: uuid.UUID) -> bool:
    """
    Incrementa el contador de uso de un servicio para un usuario.
    
    Args:
        db: Sesión de base de datos
        usuario_id: ID del usuario
        servicio_id: ID del servicio
    
    Returns:
        bool: True si el incremento fue exitoso, False si el usuario ya alcanzó el límite
    """
    # Verificar primero si hay cuota disponible
    if not verificar_cuota_disponible(db, usuario_id, servicio_id):
        return False

    # Obtener el registro de uso
    uso = db.query(UsoServicio).filter(
        UsoServicio.usuario_id == usuario_id,
        UsoServicio.servicio_id == servicio_id
    ).first()

    # Incrementar el contador
    if uso:
        uso.uso_actual += 1
        db.commit()

        # Verificar si con este incremento se alcanzó el límite
        cuota = db.query(Cuota).filter(Cuota.id == uso.cuota_id).first()
        if cuota and cuota.limite_uso > 0:
            # Si el límite no es 0 (ilimitado) y se alcanzó el límite
            return uso.uso_actual < cuota.limite_uso

        return True

    return False


def reset_uso_servicio(db: Session, usuario_id: uuid.UUID, servicio_id: uuid.UUID = None) -> bool:
    """
    Resetea el contador de uso de servicios para un usuario.
    Si se especifica un servicio_id, solo se resetea ese servicio.
    
    Args:
        db: Sesión de base de datos
        usuario_id: ID del usuario
        servicio_id: ID del servicio (opcional)
    
    Returns:
        bool: True si el reset fue exitoso
    """
    query = db.query(UsoServicio).filter(UsoServicio.usuario_id == usuario_id)

    if servicio_id:
        query = query.filter(UsoServicio.servicio_id == servicio_id)

    usos = query.all()

    for uso in usos:
        uso.uso_actual = 0
        uso.ultimo_reset = datetime.now()

    db.commit()
    return True


# Configuración de Stripe (esto debería estar en un archivo de configuración)
# stripe.api_key = "tu_clave_api_de_stripe"


# def check_quota(servicio_id: str):
#     """
#     Decorador que verifica y gestiona las cuotas de un servicio específico.
    
#     Este decorador:
#     1. Verifica si el usuario tiene cuota disponible para el servicio
#     2. Si el período de suscripción ha cambiado, resetea el contador de uso
#     3. Incrementa el contador de uso si hay cuota disponible
#     4. Ejecuta la función decorada solo si hay cuota disponible
    
#     Args:
#         servicio_id: ID del servicio a verificar (como string)
        
#     Raises:
#         HTTPException: Si el usuario no tiene cuota disponible o hay otro error
#     """
#     def decorator(func: Callable) -> Callable:
#         @functools.wraps(func)
#         def wrapper(*args, **kwargs):
#             user = kwargs.get('user')
#             db = kwargs.get('db')
#             # Convertir servicio_id a UUID
#             servicio_uuid = uuid.UUID(servicio_id)

#             # Verificar si el usuario está activo y tiene suscripción
#             if not user.active:
#                 raise HTTPException(
#                     status_code=403,
#                     detail="Usuario inactivo"
#                 )

#             if not user.subscription_id:
#                 raise HTTPException(
#                     status_code=403,
#                     detail="Usuario sin suscripción activa"
#                 )

#             # Obtener el uso de servicio
#             uso = db.query(UsoServicio).filter(
#                 UsoServicio.usuario_id == user.id,
#                 UsoServicio.servicio_id == servicio_uuid
#             ).first()

#             # Si no existe un registro de uso, verificar si el usuario tiene acceso a este servicio según su suscripción
#             if not uso:
#                 # Obtener datos de la suscripción de Stripe
#                 try:
#                     subscription = stripe.Subscription.retrieve(
#                         user.subscription_id)
#                     print("subscriptions", subscription)
#                     print("subscriptions items ",
#                           subscription.get("items", {}))
#                     plan_id = subscription.get("items", {}).get("data", {})[0].get("price", {}).get(
#                         "id", "") if subscription.get("items", {}).get("data", {}) else None

#                     if not plan_id:
#                         raise HTTPException(
#                             status_code=403,
#                             detail="No se pudo determinar el plan de suscripción"
#                         )

#                     # Buscar la cuota correspondiente al plan y servicio
#                     cuota = db.query(Cuota).filter(
#                         Cuota.servicio_id == servicio_uuid,
#                         Cuota.plan_stripe == plan_id,
#                         Cuota.activo == True
#                     ).first()

#                     if not cuota:
#                         servicio = db.query(Servicio).filter(
#                             Servicio.id == servicio_uuid).first()
#                         servicio_nombre = servicio.nombre if servicio else "desconocido"

#                         raise HTTPException(
#                             status_code=403,
#                             detail=f"El servicio '{servicio_nombre}' no está disponible en su plan actual"
#                         )

#                     # Crear un nuevo registro de uso
#                     uso = UsoServicio(
#                         usuario_id=user.id,
#                         servicio_id=servicio_uuid,
#                         cuota_id=cuota.id,
#                         uso_actual=0,
#                         ultimo_reset=datetime.now(timezone.utc)
#                     )
#                     db.add(uso)
#                     db.commit()
#                     db.refresh(uso)

#                 except stripe.error.StripeError as e:
#                     raise HTTPException(
#                         status_code=500,
#                         detail=f"Error al verificar la suscripción: {str(e)}"
#                     )

#             # Verificar si el período de suscripción ha cambiado y resetear si es necesario
#             try:
#                 subscription = stripe.Subscription.retrieve(
#                     user.subscription_id)
#                 current_period_start = datetime.fromtimestamp(
#                     subscription["items"]["data"][0]["current_period_start"],
#                     tz=timezone.utc)
#                 print("current_period_start ", current_period_start)

#                 # Si último reset es anterior al inicio del período actual, resetear contador
#                 if not uso.ultimo_reset or uso.ultimo_reset < current_period_start:
#                     uso.uso_actual = 0
#                     uso.ultimo_reset = datetime.now(timezone.utc)
#                     db.commit()
#                     db.refresh(uso)
#             except stripe.error.StripeError as e:
#                 # Registrar el error pero continuar
#                 print(f"Error al verificar período de suscripción: {str(e)}")

#             # Obtener la cuota asociada
#             cuota = db.query(Cuota).filter(Cuota.id == uso.cuota_id).first()
#             if not cuota:
#                 raise HTTPException(
#                     status_code=500,
#                     detail="No se encontró la información de cuota"
#                 )

#             # Verificar si hay cuota disponible
#             cuota_disponible = True
#             if cuota.limite_uso > 0:  # Si no es ilimitado
#                 cuota_disponible = uso.uso_actual < cuota.limite_uso

#             if not cuota_disponible:
#                 servicio = db.query(Servicio).filter(
#                     Servicio.id == servicio_uuid).first()
#                 servicio_nombre = servicio.nombre if servicio else "desconocido"

#                 raise HTTPException(
#                     status_code=429,  # Too Many Requests
#                     detail=f"Ha alcanzado el límite de uso para el servicio: {servicio_nombre}. Límite: {cuota.limite_uso}, Uso actual: {uso.uso_actual}"
#                 )

#             # Incrementar uso
#             uso.uso_actual += 1
#             db.commit()
#             print("FINISHED")
#             # Ejecutar la función decorada
#             return func(*args, **kwargs)

#         return wrapper
#     return decorator


# def validate_subscription(func: Callable) -> Callable:
#     """
#     Decorador más simple que solo verifica si el usuario tiene una suscripción activa.
#     No incrementa contadores de uso ni verifica cuotas específicas.
    
#     Raises:
#         HTTPException: Si el usuario no tiene una suscripción activa
#     """
#     @functools.wraps(func)
#     def wrapper(user: Usuario, db: Session, *args, **kwargs):
#         # Verificar si está activo
#         if not user.active:
#             raise HTTPException(
#                 status_code=403,
#                 detail="Usuario inactivo"
#             )

#         # Verificar si tiene suscripción
#         if not user.subscription_id:
#             raise HTTPException(
#                 status_code=403,
#                 detail="Usuario sin suscripción"
#             )

#         # Verificar si la suscripción está activa en Stripe
#         try:
#             subscription = stripe.Subscription.retrieve(user.subscription_id)
#             if subscription.status not in ['active', 'trialing']:
#                 raise HTTPException(
#                     status_code=403,
#                     detail=f"Suscripción no activa (estado: {subscription.status})"
#                 )
#         except stripe.error.StripeError as e:
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"Error al verificar la suscripción: {str(e)}"
#             )

#         # Ejecutar la función decorada
#         return func(user, db, *args, **kwargs)

#     return wrapper

def check_quota(servicio_id: str):
    """
    Decorador asíncrono que verifica y gestiona las cuotas de un servicio.
    
    Este decorador:
    1. Verifica si el usuario tiene cuota disponible.
    2. Resetea el contador de uso si el período de suscripción ha cambiado.
    3. Incrementa el contador si hay cuota disponible.
    4. Ejecuta la función asíncrona decorada solo si hay cuota.
    
    Args:
        servicio_id: ID del servicio a verificar.
        
    Raises:
        HTTPException: Si el usuario no tiene cuota o hay otro error.
    """
    # El tipo de la función decorada es una Corutina
    def decorator(func: Callable[..., Coroutine[Any, Any, Any]]) -> Callable[..., Coroutine[Any, Any, Any]]:
        @functools.wraps(func)
        # 1. El wrapper ahora es una función 'async def'
        async def wrapper(*args, **kwargs):
            user = kwargs.get('user')
            db = kwargs.get('db')

            if not user or not db:
                raise ValueError(
                    "Los argumentos 'user' y 'db' son requeridos en kwargs")

            servicio_uuid = uuid.UUID(servicio_id)

            if not user.active:
                # Reemplazar con HTTPException
                raise Exception("Usuario inactivo")

            if not user.subscription_id:
                # Reemplazar con HTTPException
                raise Exception("Usuario sin suscripción activa")

            uso = db.query(UsoServicio).filter(
                UsoServicio.usuario_id == user.id,
                UsoServicio.servicio_id == servicio_uuid
            ).first()

            if not uso:
                try:
                    subscription = stripe.Subscription.retrieve(
                        user.subscription_id)
                    plan_id = subscription.get("items", {}).get("data", [{}])[
                        0].get("price", {}).get("id")

                    if not plan_id:
                        raise Exception(
                            "No se pudo determinar el plan de suscripción")

                    cuota = db.query(Cuota).filter(
                        Cuota.servicio_id == servicio_uuid,
                        Cuota.plan_stripe == plan_id,
                        Cuota.activo == True
                    ).first()

                    if not cuota:
                        servicio = db.query(Servicio).filter(
                            Servicio.id == servicio_uuid).first()
                        servicio_nombre = servicio.nombre if servicio else "desconocido"
                        raise Exception(
                            f"El servicio '{servicio_nombre}' no está disponible en su plan actual")

                    uso = UsoServicio(
                        usuario_id=user.id,
                        servicio_id=servicio_uuid,
                        cuota_id=cuota.id,
                        uso_actual=0,
                        ultimo_reset=datetime.now(timezone.utc)
                    )
                    db.add(uso)
                    db.commit()
                    db.refresh(uso)
                except stripe.error.StripeError as e:
                    raise Exception(
                        f"Error al verificar la suscripción: {str(e)}")

            try:
                subscription = stripe.Subscription.retrieve(
                    user.subscription_id)
                current_period_start = datetime.fromtimestamp(
                    subscription["items"]["data"][0]["current_period_start"], tz=timezone.utc
                )

                if not uso.ultimo_reset or uso.ultimo_reset < current_period_start:
                    uso.uso_actual = 0
                    uso.ultimo_reset = datetime.now(timezone.utc)
                    db.commit()
                    db.refresh(uso)
            except stripe.error.StripeError as e:
                print(
                    f"Advertencia: Error al verificar período de suscripción: {str(e)}")

            cuota = db.query(Cuota).filter(Cuota.id == uso.cuota_id).first()
            if not cuota:
                raise Exception("No se encontró la información de cuota")

            cuota_disponible = cuota.limite_uso <= 0 or uso.uso_actual < cuota.limite_uso

            if not cuota_disponible:
                servicio = db.query(Servicio).filter(
                    Servicio.id == servicio_uuid).first()
                servicio_nombre = servicio.nombre if servicio else "desconocido"
                raise Exception(
                    f"Límite de uso alcanzado para el servicio: {servicio_nombre}")

            uso.uso_actual += 1
            db.commit()

            # 2. Se usa 'await' para llamar a la función asíncrona original
            return await func(*args, **kwargs)

        return wrapper
    return decorator


def validate_subscription(func: Callable[..., Coroutine[Any, Any, Any]]) -> Callable[..., Coroutine[Any, Any, Any]]:
    """
    Decorador asíncrono que verifica si el usuario tiene una suscripción activa.
    
    Raises:
        HTTPException: Si el usuario no tiene una suscripción activa.
    """
    @functools.wraps(func)
    # 1. El wrapper ahora es una función 'async def'
    async def wrapper(user: Usuario, db: Session, *args, **kwargs):
        if not user.active:
            raise Exception("Usuario inactivo")  # Reemplazar con HTTPException

        if not user.subscription_id:
            # Reemplazar con HTTPException
            raise Exception("Usuario sin suscripción")

        try:
            subscription = stripe.Subscription.retrieve(user.subscription_id)
            if subscription.get('status') not in ['active', 'trialing']:
                raise Exception(
                    f"Suscripción no activa (estado: {subscription.get('status')})")
        except stripe.error.StripeError as e:
            raise Exception(f"Error al verificar la suscripción: {str(e)}")

        # 2. Se usa 'await' para llamar a la función asíncrona original
        return await func(user, db, *args, **kwargs)

    return wrapper
