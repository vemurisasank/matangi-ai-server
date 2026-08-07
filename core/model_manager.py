from core.logger import Logger


class ModelManager:
    """
    Manages all AI models registered in the server.
    """

    def __init__(self):

        Logger.info("Initializing Model Manager")

        self.models = {

            "text": [],

            "image": [],

            "video": [],

            "voice": [],

            "music": []

        }

    def register(
        self,
        category: str,
        model_name: str
    ) -> None:
        """
        Register a model under a category.
        """

        if category not in self.models:

            self.models[category] = []

        if model_name not in self.models[category]:

            self.models[category].append(model_name)

            Logger.info(

                f"Model Registered: {model_name}"

            )

    def get(
        self,
        category: str
    ) -> list:
        """
        Get all models in a category.
        """

        return self.models.get(

            category,

            []

        )

    def get_all(self) -> dict:
        """
        Get all registered models.
        """

        return self.models

    def remove(
        self,
        category: str,
        model_name: str
    ) -> bool:
        """
        Remove a model from a category.
        """

        if category in self.models:

            if model_name in self.models[category]:

                self.models[category].remove(

                    model_name

                )

                Logger.info(

                    f"Model Removed: {model_name}"

                )

                return True

        Logger.warning(

            f"Model '{model_name}' not found."

        )

        return False

    def list(self) -> list:
        """
        List all model categories.
        """

        return list(

            self.models.keys()

        )

    def exists(
        self,
        category: str,
        model_name: str
    ) -> bool:
        """
        Check if a model exists.
        """

        return (

            category in self.models

            and

            model_name in self.models[category]

        )

    def clear(self) -> None:
        """
        Remove all registered models.
        """

        for category in self.models:

            self.models[category].clear()

        Logger.info(

            "All models cleared."

        )