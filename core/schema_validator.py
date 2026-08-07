from core.logger import Logger


class SchemaValidator:

    @staticmethod
    def validate_prompt(data):

        if not isinstance(data, dict):

            Logger.error("Prompt response is not a dictionary.")

            return False

        if "scenes" not in data:

            Logger.error("'scenes' key missing.")

            return False

        if not isinstance(data["scenes"], list):

            Logger.error("'scenes' is not a list.")

            return False

        required_fields = [

            "scene",

            "title",

            "environment",

            "character",

            "camera",

            "lighting",

            "mood",

            "image_prompt"

        ]

        for scene in data["scenes"]:

            for field in required_fields:

                if field not in scene:

                    Logger.error(

                        f"Missing field : {field}"

                    )

                    return False

        return True