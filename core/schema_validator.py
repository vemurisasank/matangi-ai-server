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

    @staticmethod
    def validate_scene(data):

        if not isinstance(data, dict):

            Logger.error("Scene response is not a dictionary.")

            return False

        if "scenes" not in data:

            Logger.error("'scenes' field is missing.")

            return False

        if not isinstance(data["scenes"], list):

            Logger.error("'scenes' is not a list.")

            return False

        required_fields = [

            "number",
            "title",
            "script",
            "duration"

        ]

        for scene in data["scenes"]:

            if not isinstance(scene, dict):

                Logger.error("Scene item is not a dictionary.")

                return False

            for field in required_fields:

                if field not in scene:

                    Logger.error(
                        f"Missing scene field : {field}"
                    )

                    return False

        return True


    @staticmethod
    def validate_character(data):

        if not isinstance(data, dict):

            Logger.error(
                "Character response is not a dictionary."
            )

            return False

        required_fields = [

            "name",
            "role",
            "gender",
            "age",
            "appearance",
            "costume",
            "accessories",
            "hairstyle",
            "face",
            "eyes",
            "body",
            "personality",
            "powers",
            "style",
            "negative_prompt"

        ]

        for field in required_fields:

            if field not in data:

                Logger.error(
                    f"Missing character field : {field}"
                )

                return False

        return True
