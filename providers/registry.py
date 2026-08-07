from providers.ollama.provider import OllamaProvider
from providers.flux.provider import FluxProvider
from providers.comfyui.provider import ComfyUIProvider

class ProviderRegistry:

    @staticmethod
    def build():

        providers = {}

        providers["ollama"] = OllamaProvider()

        providers["flux"] = ComfyUIProvider()

        return providers