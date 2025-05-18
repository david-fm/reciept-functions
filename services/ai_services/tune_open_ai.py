"""TO TRANSFORM LIKE VERTEX_AI

Returns:
    _type_: _description_
"""
from collections import defaultdict
from typing import List, Dict
import json
from time import sleep
import openai
import os
from PIL import Image
from app.process_pdf import create_message, image_to_base64
from app.schemas import pdf_description

format_errors = defaultdict(int)

def validate_dataset(dataset: List):
    for ex in dataset:
        if not isinstance(ex, dict):
            format_errors["data_type"] += 1
            continue

        messages = ex.get("messages", None)
        if not messages:
            format_errors["missing_messages_list"] += 1
            continue

        for message in messages:
            if "role" not in message or "content" not in message:
                format_errors["message_missing_key"] += 1

            if any(k not in ("role", "content", "name", "function_call", "weight") for k in message):
                format_errors["message_unrecognized_key"] += 1

            if message.get("role", None) not in ("system", "user", "assistant", "function"):
                format_errors["unrecognized_role"] += 1

            content = message.get("content", None)
            function_call = message.get("function_call", None)

            if (not content and not function_call) or not isinstance(content, str):
                format_errors["missing_content"] += 1

        if not any(message.get("role", None) == "assistant" for message in messages):
            format_errors["example_missing_assistant_message"] += 1

    if format_errors:
        print("Found errors:")
        for k, v in format_errors.items():
            print(f"{k}: {v}")
    else:
        print("No errors found")


def saving_dataset(dataset, path):
	with open(path, 'w') as f:
		for message in dataset:
			f.write(json.dumps(message) + '\n')

def load_images(dataset, dataset_path):
    images = []
    for ex in dataset:
        ex_image = ex.get("fileName", None)
        if ex_image:
            ex_image = os.path.join(dataset_path, ex_image)
            image = Image.open(ex_image)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            images.append(image)
            del ex["fileName"]
        else:
            images.append(None)

    return images


def import_dataset(dataset_path, format_documentation):
    content = """
You are a medical assistant. Your task is to extract relevant information from the images.
The relevant information to extract is the following:
{}
        """.format(format_documentation)
    jsonl_file = os.path.join(dataset_path, 'formulas_medicas.jsonl')
    with open(jsonl_file, 'r') as f:
        dataset = f.readlines()
        dataset = [json.loads(ex) for ex in dataset if ex.strip().startswith('{')]
    images = load_images(dataset, dataset_path)
    clean_dataset = [json.dumps(dataset[i]) for i in range(len(dataset)) if images[i] is not None]
    clean_images = [image for image in images if image is not None]
    messages = [
        create_message(
            [image_to_base64(image)],
            content,
            assistance_message=ex
        )
        for image, ex in zip(clean_images, clean_dataset)
    ]
    return messages
    
if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    dataset = import_dataset(
    	'/home/dflorez/Descargas/dataset/', pdf_description)
    client = openai.OpenAI()
    dataset_file = 'fine_tune_dataset.jsonl'
    val_dataset_file = 'fine_tune_val_dataset_processQuery.jsonl'
    saving_dataset(dataset, dataset_file)
    # saving_dataset(dataset, val_dataset_file)

    fine_tune_input_file = client.files.create(
        file=open(dataset_file, 'rb'),
        purpose="fine-tune"
    )
    # fine_tune_val_input_file = client.files.create(
    #     file=open(val_dataset_file, 'rb'),
    #     purpose="fine-tune"
    # )

    response = client.fine_tuning.jobs.create(
        # model="gpt-4o-mini-2024-07-18",
        model="gpt-4o-2024-08-06",
        training_file=fine_tune_input_file.id,
        seed=42,  # reproducibility
        # validation_file=fine_tune_val_input_file.id,
        hyperparameters={
            # hyperparam depends on the size and complexity of your data
            "n_epochs": 2,
            "batch_size": 8,
        }
    )
    while response.status != 'succeeded' and response.status != 'failed':
        response = client.fine_tuning.jobs.retrieve(
            fine_tuning_job_id=response.id)
        sleep(5)
    
    print("Fine-tuning job completed")
    print("Status:", response.status)
    if response.status == 'failed':
        print("Error:", response.error)
    else:
        print("Model ID:", response.fine_tuned_model)
