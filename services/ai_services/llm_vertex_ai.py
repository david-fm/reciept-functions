from .config import safety_settings
import vertexai
from vertexai.generative_models import GenerativeModel, Part, GenerationResponse
from typing import List, Optional


class VertexAILLM:
    """A class to abstract the initialization and prompt creation for Vertex AI LLMs."""

    def __init__(
        self,
        project_id: str,
        location: str,
        model_name: str,
        system_instruction: str,
    ):
        """
        Initialize the VertexAI LLM.

        Args:
            project_id: The GCP project ID
            location: The GCP location (e.g., 'us-central1')
            model_name: The name of the model to use (e.g., 'gemini-1.5-flash-001')
            system_instruction: The system instruction to use for the model
        """
        # Initialize Vertex AI
        vertexai.init(project=project_id, location=location)

        # Create the model instance
        self.model = GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction
        )

    def invoke(
        self,
        inp: List[Part],
        generation_config: Optional[dict] = None,
        safety_settings: Optional[List[dict]] = safety_settings,
    ) -> GenerationResponse:
        """
        Generate content using the model.

        Args:
            inp: List of Part objects (can include text and images)
            generation_config: Optional generation configuration
            safety_settings: Optional safety settings

        Returns:
            The generated response as a string
        """
        # Generate content with the model
        response = self.model.generate_content(
            inp,
            generation_config=generation_config,
            safety_settings=safety_settings,
        )

        return response

    async def ainvoke(
        self,
        inp: List[Part],
        generation_config: Optional[dict] = None,
        safety_settings: Optional[List[dict]] = safety_settings,
    ) -> GenerationResponse:
        """
        Generate content using the model asynchronously.

        Args:
            inp: List of Part objects (can include text and images)
            generation_config: Optional generation configuration
            safety_settings: Optional safety settings

        Returns:
            The generated response as a string
        """
        # Generate content with the model
        try:
            print(inp)
            response = await self.model.generate_content_async(
                inp,
                generation_config=generation_config,
                safety_settings=safety_settings,
            )

            return response
        except Exception as e:
            print(f"Error generating content: {e}")
            raise e
