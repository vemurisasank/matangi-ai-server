from config.logger import logger


class Logger:

    @staticmethod
    def info(message):

        logger.info(message)

    @staticmethod
    def warning(message):

        logger.warning(message)

    @staticmethod
    def error(message):

        logger.error(message)

    @staticmethod
    def debug(message):

        logger.debug(message)