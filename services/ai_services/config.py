from vertexai.generative_models import SafetySetting, GenerationConfig
from .schemas import ticket_schema

def vertexai_config(response_schema):

    generation_config = GenerationConfig(
        max_output_tokens=8192,
        temperature=0,
        # top_p=0.95,
        response_mime_type="application/json",
        response_schema=response_schema,
    )
    return generation_config


safety_settings = [
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=SafetySetting.HarmBlockThreshold.OFF
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=SafetySetting.HarmBlockThreshold.OFF
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=SafetySetting.HarmBlockThreshold.OFF
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=SafetySetting.HarmBlockThreshold.OFF
    ),
]

system_instruction = """You are a document entity extraction specialist. Given a document, your task is to extract the text value of the following entities:
{
\"store_name\":\"\",
\"menu\": [{
	\"nm\":\"\",
	\"cnt\":\"\",
	\"price\":\"\"
}],
\"total\":{
	\"total_price\":\"\"
}
}

- The JSON schema must be followed during the extraction.
- The values must only include text found in the document
- Do not normalize any entity value.
- If an entity is not found in the document, set the entity value to null."""

pdf_config = vertexai_config(ticket_schema)
