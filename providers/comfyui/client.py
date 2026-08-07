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

        data = response.json()

        return data["prompt_id"]