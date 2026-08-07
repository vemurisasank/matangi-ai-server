from core.logger import Logger


class ResponseManager:

    @staticmethod
    def success(

        data=None,

        message="Success"

    ):

        return {

            "success": True,

            "message": message,

            "data": data

        }

    @staticmethod
    def failure(

        message="Failed",

        data=None

    ):

        Logger.error(message)

        return {

            "success": False,

            "message": message,

            "data": data

        }