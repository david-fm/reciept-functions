import os
from . import VertexAILLM
from .config import system_instruction
from core.config import settings

print("Project ID: ", settings.GOOGLE_CLOUD_PROJECT)
print("Region: ", settings.GOOGLE_CLOUD_REGION)
print("Model Name: ", settings.VERTEXAI_MODEL_NAME)
model = VertexAILLM(
    project_id=settings.GOOGLE_CLOUD_PROJECT,
    location=settings.GOOGLE_CLOUD_REGION,
    model_name=settings.VERTEXAI_MODEL_NAME,
    system_instruction=system_instruction
)

