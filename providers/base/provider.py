from abc import ABC, abstractmethod

from core.logger import Logger


class BaseProvider(ABC):

    def __init__(self, name):

        self.name = name

        Logger.info(

            f"{self.name} Provider Initialized"

        )

    @abstractmethod
    def generate(self, *args, **kwargs):

        pass

    def health(self):

        return {

            "provider": self.name,

            "status": "Available"

        }
    def info(self):

        return {

            "provider": self.name

        }