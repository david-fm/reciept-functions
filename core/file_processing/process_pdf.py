from typing import List, Dict, Literal, Optional
from pydantic import BaseModel, Field
from pdf2image import convert_from_path
from langfuse.openai import OpenAI
from base64 import b64encode
from io import BytesIO
from PIL import Image
import asyncio
import json
import re
import os

# from langchain_core.messages import HumanMessage, BaseMessage, SystemMessage
# from langchain_openai import ChatOpenAI
# from langchain_core.runnables.base import Runnable
# from langchain_core.language_models import LanguageModelInput
# from langchain_openai.chat_models.base import _DictOrPydantic
# from openai import OpenAI

# def process_photo(photo: Image.Image) -> List[BaseMessage]:
#     # Convert image to base64 for storage/processing if needed
#     photo_bytes = BytesIO()
#     photo.save(photo_bytes, format="JPEG")
#     image_base64 = b64encode(photo_bytes.getvalue()).decode('utf-8')
#     system_message = SystemMessage(
#         content="You are an medical assistant. Your task is to extract relevant information from the image.")
#     input_message = HumanMessage(
#         content=[
#             {
#                 "type": "image_url",
#                 "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
#             },
#         ]
#     )
#     return [system_message, input_message]


def convert_pdf_to_images(pdf_path: str, output_dir: str = None, dpi: int = 300, in_bytes: bool = False) -> List[Image.Image | bytes]:
    """
    Convierte un archivo PDF en una lista de imágenes.

    Args:
        pdf_path (str): Ruta al archivo PDF
        output_dir (str, opcional): Directorio donde guardar las imágenes. Si es None, no se guardan.
        dpi (int, opcional): Resolución de las imágenes generadas. Por defecto es 300.

    Returns:
        List[Image.Image]: Lista de objetos imagen de PIL

    Raises:
        FileNotFoundError: Si el archivo PDF no existe
        Exception: Si hay un error durante la conversión
    """
    try:
        # Verificar que el archivo existe
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(
                f"No se encontró el archivo PDF: {pdf_path}")

        # Convertir PDF a imágenes
        images = convert_from_path(
            pdf_path,
            dpi=dpi,
            # Usar primera página como 1, no 0
            first_page=1,
            # Convertir todas las páginas
            last_page=None
        )

        # Si se especifica un directorio de salida, guardar las imágenes
        if output_dir:
            # Crear el directorio si no existe
            os.makedirs(output_dir, exist_ok=True)

            # Guardar cada imagen
            for i, image in enumerate(images, start=1):
                image_path = os.path.join(output_dir, f'pagina_{i}.jpg')
                image.save(image_path, 'JPEG')
                print(f"Imagen guardada: {image_path}")

        return images_to_bytes(images) if in_bytes else images

    except Exception as e:
        raise Exception(f"Error al convertir PDF a imágenes: {str(e)}")


def image_to_base64(image: Image.Image) -> str:
    if image.mode != 'RGB':
        image = image.convert('RGB')
    image_bytes = BytesIO()
    image.save(image_bytes, format="JPEG")
    return b64encode(image_bytes.getvalue()).decode('utf-8')


def images_to_base64(images: List[Image.Image]) -> List[str]:
    return [image_to_base64(image) for image in images]


def image_to_bytes(image: Image.Image) -> bytes:
    if image.mode != 'RGB':
        image = image.convert('RGB')
    image_bytes = BytesIO()
    image.save(image_bytes, format="JPEG")
    return image_bytes.getvalue()


def images_to_bytes(images: List[Image.Image]) -> List[bytes]:
    return [image_to_bytes(image) for image in images]


def images_to_json(
        images: List[Image.Image],
        client: OpenAI,
        response_format: BaseModel,
        format_documentation: str,
        model="gpt-4o-mini") -> Dict:

    messages = create_message(
        images_to_base64(images),
        """
You are a medical assistant. Your task is to extract relevant information from the images.
The relevant information to extract is the following:
{}
        """.format(format_documentation))

    response = client.beta.chat.completions.parse(
        messages=messages,
        model=model,
        temperature=0,
        response_format=response_format,
    )
    # print(response)
    # res = response.choices[0].content
    # if res.refusal:
    #     print(res.refusal)
    # else:
    #     print(res.parsed)
    return response.choices[0].message.parsed


def create_message(images_data, system_message, assistance_message=None):
    to_return = [
        {
            "role": "system",
            "content": system_message
        },
        {"role": "user", "content": [
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
            }
            for image_data in images_data
        ]},
    ]
    if assistance_message:
        to_return.append({"role": "assistant", "content": assistance_message})
        to_return = {
            "messages": to_return
        }
    return to_return


# async def is_month(text, classifier_model: VertexAILLM):
#     response = await classifier_model.ainvoke([text], classifier_config)
#     # print("IS MONTH RESPONSE", response)
#     text = response.text
#     return text if text in ['m', 'd'] else 'd'


# async def process_date(text, date_model: VertexAILLM):
#     if (text == 'null' or text == None):
#         return text
#     response = await date_model.ainvoke([text])
#     # print("DATE RESPONSE", response)
#     return extract_date_iso_format(response.text)


# async def process_medicamento(medicamento, classifier_model: VertexAILLM):
#     print("MEDICAMENTO", medicamento)
#     if not ('duracionTratamiento' not in medicamento
#         or medicamento['duracionTratamiento'] == 'null'
#         or medicamento['duracionTratamiento'] == None):
        
#         duracion_n = get_number(medicamento['duracionTratamiento'])
#         if duracion_n:
#             is_month_ = await is_month(medicamento['duracionTratamiento'], classifier_model)
#             if is_month_:
#                 medicamento['duracionTratamiento'] = months_to_days(duracion_n)
#         medicamento['duracionTratamiento'] = duracion_n
#     else:
#         medicamento['duracionTratamiento'] = 0

    if not ('cantidad' not in medicamento
            or medicamento['cantidad'] == 'null'
            or medicamento['cantidad'] == None):
        medicamento['cantidad'] = get_number(medicamento['cantidad'])
    else:
        medicamento['cantidad'] = 0
    
    return medicamento


# def get_number(text):
#     found = re.findall(r'\d+', text)
#     return found[0] if found else 0


# def months_to_days(months):
#     return months * 30


# def extract_date_iso_format(text):
#     date_extracted = re.findall(r'\d{4}-\d{2}-\d{2}', text)
#     return date_extracted[0] if date_extracted else 'null'

# async def post_processing(
#         pre,
#         date_model=date_model,
#         classifier_model=classifier_model):
#     medicamentos_task = asyncio.gather(
#         *[process_medicamento(medicamento, classifier_model)
#           for medicamento in pre['medicamentos']]
#     )
#     formulaMedica_fecha_task = process_date(pre['formulaMedica']['fecha'], date_model)

#     pre['medicamentos'], pre['formulaMedica']['fecha'] = await asyncio.gather(
#         medicamentos_task, formulaMedica_fecha_task
#     )
