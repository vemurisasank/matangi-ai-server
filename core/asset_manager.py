from core.logger import Logger


class AssetManager:

    def __init__(self):

        Logger.info("Initializing Asset Manager")

    def save_asset(self, asset):

        Logger.info(f"Saving Asset : {asset}")

    def delete_asset(self, asset):

        Logger.info(f"Deleting Asset : {asset}")