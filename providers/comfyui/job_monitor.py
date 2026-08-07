import time

import requests
from config.settings import settings


class ComfyUIJobMonitor:

    def __init__(

        self,

        host=settings.COMFYUI_HOST

    ):

        self.host = host

    def wait(

        self,

        prompt_id,

        interval=1

    ):

        while True:

            response = requests.get(

                f"{self.host}/history/{prompt_id}"

            )

            data = response.json()

            if prompt_id in data:

                return data[prompt_id]

            time.sleep(interval)