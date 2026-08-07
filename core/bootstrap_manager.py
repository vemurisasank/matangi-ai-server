from core.logger import Logger

from core.server_context import server

from providers.ollama.provider import OllamaProvider
from providers.registry import ProviderRegistry
from models.registry import ModelRegistry


class BootstrapManager:

    @staticmethod
    def initialize():

        Logger.info("=" * 60)
        Logger.info("BOOTSTRAP INITIALIZATION")
        Logger.info("=" * 60)

        BootstrapManager.register_providers()

        BootstrapManager.register_models()

        Logger.info("BOOTSTRAP COMPLETED")

    @staticmethod
    def register_providers():

        providers = ProviderRegistry.build()

        for name, provider in providers.items():

            server.provider_manager.register(

                name,

                provider

            )

    
    @staticmethod
    def register_models():

        models = ModelRegistry.get()

        for category, model_list in models.items():

            for model in model_list:

                server.model_manager.register(

                    category,

                    model

                )