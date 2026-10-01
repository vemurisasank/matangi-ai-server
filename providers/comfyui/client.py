import requests
from config.settings import settings


class ComfyUIClient:

    def __init__(

        self,

        host=settings.COMFYUI_HOST

    ):

        self.host = host

    def queue_prompt(

        self,

        workflow

    ):

        response = requests.post(

            f"{self.host}/prompt",

            json={

                "prompt": workflow

            }

        )

        try:
            data = response.json()
        except ValueError as error:
            raise RuntimeError(
                "ComfyUI /prompt returned a non-JSON response: "
                f"HTTP {response.status_code} {response.text}"
            ) from error

        print("=" * 60)
        print("COMFYUI STATUS:", response.status_code)
        print("COMFYUI RESPONSE:", data)
        print("=" * 60)

        if "prompt_id" not in data:
            raise RuntimeError(
                "ComfyUI /prompt rejected the workflow: "
                f"HTTP {response.status_code}; response={data}"
            )

        return data["prompt_id"]
    def get_image(
        self,
        filename,
        subfolder="",
        image_type="output"
    ):

        response = requests.get(

            f"{self.host}/view",

            params={
                "filename": filename,
                "subfolder": subfolder,
                "type": image_type
            },

            timeout=300

        )

        response.raise_for_status()

        return response.content
    def get_output(
        self,
        filename,
        subfolder="",
        output_type="output"
    ):

        response = requests.get(

            f"{self.host}/view",

            params={
                "filename": filename,
                "subfolder": subfolder,
                "type": output_type
            },

            timeout=600

        )

        response.raise_for_status()

        return response.content

    def get_history(self, prompt_id):
        response = requests.get(
            f"{self.host}/history/{prompt_id}",
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return data.get(prompt_id)
