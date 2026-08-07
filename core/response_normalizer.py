class ResponseNormalizer:

    @staticmethod
    def normalize_prompt(data):

        if "scenes" not in data:

            data["scenes"] = []

        for scene in data["scenes"]:

            scene.setdefault(

                "scene",

                0

            )

            scene.setdefault(

                "title",

                ""

            )

            scene.setdefault(

                "environment",

                ""

            )

            scene.setdefault(

                "character",

                ""

            )

            scene.setdefault(

                "camera",

                ""

            )

            scene.setdefault(

                "lighting",

                ""

            )

            scene.setdefault(

                "mood",

                ""

            )

            scene.setdefault(

                "image_prompt",

                ""

            )

        return data