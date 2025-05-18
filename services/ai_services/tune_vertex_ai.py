import os
import uuid
import jsonlines
import json
import tempfile
from typing import List, Dict, Set, Callable, Optional, Any
from google.cloud import storage
import zipfile
from vertexai.tuning import sft
import time
from functools import partial


class VertexAITuner:
    def __init__(
        self,
        bucket_name: str,
        project_id: str,
        message_creator: Optional[Callable] = None,
        **message_creator_kwargs
    ):
        """
        Initialize the VertexAITuner.

        Args:
            bucket_name: Name of the GCS bucket
            project_id: Google Cloud project ID
            message_creator: Optional function to create training messages
            **message_creator_kwargs: Additional kwargs for message_creator
        """
        self.bucket_name = bucket_name
        self.project_id = project_id
        self.temp_id = uuid.uuid4().hex
        self.temp_folder_name = f"temp_{self.temp_id}"

        # Set default message creator if none provided
        if message_creator is None:
            self.message_creator = self._default_message_creator
        else:
            # Validate the message creator function has required parameters
            self._validate_message_creator(message_creator)
            self.message_creator = partial(
                message_creator, **message_creator_kwargs)

        self.storage_client = storage.Client()

    def _validate_message_creator(self, func: Callable) -> None:
        """
        Validate that the message creator function has the required parameters.

        Args:
            func: The message creator function to validate

        Raises:
            ValueError: If the function doesn't have the required parameters
        """
        import inspect
        params = inspect.signature(func).parameters
        required_params = {'images_file_path',
                           'system_message', 'assistant_message'}
        missing_params = required_params - set(params.keys())

        if missing_params:
            raise ValueError(
                f"Message creator function must have parameters: {required_params}. "
                f"Missing: {missing_params}"
            )

    def _default_message_creator(
        self,
        images_file_path: List[str],
        system_message: str,
        assistant_message: str
    ) -> Dict:
        """
        Default message creator function that matches the original implementation.
        """
        return {
            "systemInstruction": {
                "role": "system",
                "parts": [
                    {"text": system_message}
                ]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "fileData": {
                                "mimeType": "image/jpeg",
                                "fileUri": f"{image_file_path}"
                            }
                        }
                        for image_file_path in images_file_path
                    ]
                },
                {
                    "role": "model",
                    "parts": [
                        {
                            "text": assistant_message
                        }
                    ]
                }
            ]
        }

    def _upload_files(
        self,
        filenames: List[str],
        source_directory: str = "",
        workers: int = 8
    ) -> List[tuple[str, Any]]:
        """
        Upload multiple files to GCS bucket concurrently.
        """
        from google.cloud.storage import transfer_manager

        bucket = self.storage_client.bucket(self.bucket_name)
        results = transfer_manager.upload_many_from_filenames(
            bucket,
            filenames,
            source_directory=source_directory,
            max_workers=workers
        )

        upload_results = []
        for name, result in zip(filenames, results):
            if isinstance(result, Exception):
                print(f"Failed to upload {name} due to exception: {result}")
            else:
                print(f"Uploaded {name} to {bucket.name}")
            upload_results.append((name, result))

        return upload_results

    def _get_gcs_url(self, blob_name: str) -> str:
        """Generate complete GCS URL for a file."""
        return f"gs://{self.bucket_name}/{blob_name}"

    def _validate_uploaded_images(
        self,
        upload_results: List[tuple[str, Any]],
        image_sets: List[List[str]]
    ) -> tuple[Set[str], Dict[str, str]]:
        """
        Validate which image sets were completely uploaded and create filename to GCS URL mapping.
        """
        upload_success = {}
        for filename, result in upload_results:
            upload_success[os.path.basename(
                filename)] = not isinstance(result, Exception)

        file_to_gcs_url = {}
        for filename, _ in upload_results:
            if upload_success[os.path.basename(filename)]:
                file_to_gcs_url[os.path.basename(filename)] = \
                    self._get_gcs_url(os.path.basename(filename))

        valid_image_sets = set()
        for img_set in image_sets:
            img_set_basenames = [os.path.basename(img) for img in img_set]
            if all(upload_success.get(img, False) for img in img_set_basenames):
                valid_image_sets.add(tuple(img_set_basenames))

        return valid_image_sets, file_to_gcs_url

    def create_dataset(self, zip_path: str) -> str:
        """
        Create and upload the training dataset from a zip file.

        Args:
            zip_path: Path to the zip file containing images and jsonl data

        Returns:
            GCS URL of the formatted dataset
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract zip contents
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            # Find images and jsonl file
            images = []
            jsonl_path = None
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                        images.append(os.path.join(root, file))
                    elif file.lower().endswith(('jsonl')):
                        jsonl_path = os.path.join(root, file)

            if not jsonl_path:
                raise FileNotFoundError("No jsonl file found in zip")

            # Upload images
            dir_name = os.path.basename(temp_dir)
            base_dir = os.path.dirname(temp_dir)
            send_filenames = [os.path.join(
                dir_name, os.path.basename(img)) for img in images]
            upload_results = self._upload_files(
                filenames=send_filenames,
                source_directory=base_dir
            )

            # Extract image sets from jsonl
            image_sets = []
            with jsonlines.open(jsonl_path) as reader:
                for obj in reader:
                    image_sets.append(obj['images'])

            # Validate uploads and get URL mapping
            valid_image_sets, file_to_gcs_url = self._validate_uploaded_images(
                upload_results=upload_results,
                image_sets=image_sets
            )

            # Process jsonl data
            formatted_data = []
            with jsonlines.open(jsonl_path) as reader:
                for obj in reader:
                    current_images = [os.path.basename(
                        img) for img in obj['images']]
                    if tuple(current_images) in valid_image_sets:
                        gcs_urls = [file_to_gcs_url[img]
                                    for img in current_images]
                        example = self.message_creator(
                            images_file_path=gcs_urls,
                            system_message=obj.get('system_message', ''),
                            assistant_message=json.dumps(
                                obj['assistant_message'])
                        )
                        formatted_data.append(example)

            print(f"Processed {len(formatted_data)} valid examples out of {len(image_sets)} total")

            # Test if there is a base_formatted_data.jsonl file in .env
            # indicated in the environment variable BASE_FORMATTED_DATA
            if os.getenv('BASE_FORMATTED_DATA'):
                with jsonlines.open(os.getenv('BASE_FORMATTED_DATA')) as reader:
                    base_data = [obj for obj in reader]
                formatted_data = base_data + formatted_data

            # Save and upload formatted data
            formatted_data_path = os.path.join(
                temp_dir, 'formatted_data.jsonl')
            with jsonlines.open(formatted_data_path, mode='w') as writer:
                writer.write_all(formatted_data)

            formatted_data_results = self._upload_files(
                filenames=[os.path.join(dir_name, 'formatted_data.jsonl')],
                source_directory=base_dir
            )

            for filename, result in formatted_data_results:
                if not isinstance(result, Exception):
                    return self._get_gcs_url('formatted_data.jsonl')

            raise RuntimeError("Failed to upload formatted dataset")

    def train_model(
        self,
        dataset_url: str,
        source_model: str = 'gemini-1.5-flash-002',
        epochs: int = 2,
        learning_rate_multiplier: float = 1.0
    ) -> Optional[str]:
        """
        Train a model using Vertex AI.

        Args:
            dataset_url: GCS URL of the training dataset
            source_model: Base model to fine-tune
            epochs: Number of training epochs
            learning_rate_multiplier: Learning rate multiplier

        Returns:
            The tuned model endpoint name or None if training failed
        """
        sft_tuning_job = sft.train(
            source_model=source_model,
            train_dataset=dataset_url,
            epochs=epochs,
            learning_rate_multiplier=learning_rate_multiplier
        )

        while not sft_tuning_job.has_ended:
            time.sleep(60)
            sft_tuning_job.refresh()

        if not sft_tuning_job.error:
            return sft_tuning_job.tuned_model_endpoint_name

        return None

    def train_from_zip(
        self,
        zip_path: str,
        source_model: str = 'gemini-1.5-flash-002',
        epochs: int = 2,
        learning_rate_multiplier: float = 1.0
    ) -> Optional[str]:
        """
        Convenience method to create dataset and train model in one step.

        Args:
            zip_path: Path to training data zip file
            source_model: Base model to fine-tune
            epochs: Number of training epochs
            learning_rate_multiplier: Learning rate multiplier

        Returns:
            The tuned model endpoint name or None if training failed
        """
        dataset_url = self.create_dataset(zip_path)
        return self.train_model(
            dataset_url,
            source_model,
            epochs,
            learning_rate_multiplier
        )


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Train a model with image and text data')
    parser.add_argument('--zip_path', required=True,
                        help='Path to data zip file')
    parser.add_argument('--bucket_name', required=True, help='GCS bucket name')
    parser.add_argument('--project_id', required=True,
                        help='Google Cloud project ID')

    args = parser.parse_args()

    tuner = VertexAITuner(args.bucket_name, args.project_id)
    model_endpoint = tuner.train_from_zip(args.zip_path)

    if model_endpoint:
        print(f"Model trained successfully. Endpoint: {model_endpoint}")
    else:
        print("Error during model training")


if __name__ == "__main__":
    main()
