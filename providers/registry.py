from providers.ollama.provider import OllamaProvider
from providers.flux.provider import FluxProvider
from providers.comfyui.provider import ComfyUIProvider
from providers.musicgen.provider import MusicGenProvider
from providers.voice.local_tts import LocalTeluguTTSProvider


class ProviderRegistry:

    @staticmethod
    def build():

        providers = {}

        providers["ollama"] = OllamaProvider()

        comfyui = ComfyUIProvider()

        providers["comfyui"] = comfyui
        providers["flux"] = comfyui

        providers["musicgen"] = MusicGenProvider()
        providers["local-tts"] = LocalTeluguTTSProvider()

        return providers
