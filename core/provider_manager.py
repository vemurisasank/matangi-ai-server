from core.logger import Logger
from providers.registry import ProviderRegistry


class ProviderManager:
    """
    Manages all AI providers registered in the server.
    """

    def __init__(self):

        Logger.info("Initializing Provider Manager")

        self.providers = ProviderRegistry.build()

    def register(
        self,
        name: str,
        provider
    ) -> None:
        """
        Register a new provider.
        """

        self.providers[name] = provider

        Logger.info(f"Provider Registered: {name}")

    def get(
        self,
        name: str
    ):
        """
        Get a provider by name.
        """

        provider = self.providers.get(name)

        if provider is None:

            raise ValueError(

                f"Provider '{name}' is not registered."

            )

        return provider

    def remove(
        self,
        name: str
    ) -> bool:
        """
        Remove a provider.
        """

        if name in self.providers:

            del self.providers[name]

            Logger.info(f"Provider Removed: {name}")

            return True

        Logger.warning(f"Provider '{name}' not found.")

        return False

    def list(self) -> list:
        """
        Return all registered provider names.
        """

        return list(self.providers.keys())

    def exists(
        self,
        name: str
    ) -> bool:
        """
        Check whether a provider exists.
        """

        return name in self.providers

    def clear(self) -> None:
        """
        Remove all providers.
        """

        self.providers.clear()

        Logger.info("All providers cleared.")