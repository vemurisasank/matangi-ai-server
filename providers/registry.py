from providers.ollama.provider import OllamaProvider
from providers.flux.provider import FluxProvider
from providers.comfyui.provider import ComfyUIProvider
from providers.musicgen.provider import MusicGenProvider


class ProviderRegistry:

    @staticmethod
    def build():

        providers = {}

        providers["ollama"] = OllamaProvider()

        comfyui = ComfyUIProvider()

        providers["comfyui"] = comfyui
        providers["flux"] = comfyui

        providers["musicgen"] = MusicGenProvider()

        return providers
