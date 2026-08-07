import json
import re

from core.logger import Logger


class ResponseParser:

    @staticmethod
    def clean(text):

        if text is None:

            return ""

        text = text.replace("```json", "")

        text = text.replace("```", "")

        text = text.strip()

        return text

    @staticmethod
    def extract_json(text):

        match = re.search(

            r"\{.*\}",

            text,

            re.DOTALL

        )

        if match:

            return match.group()

        return text

    @staticmethod
    def repair(text):

        # Remove trailing commas

        text = re.sub(

            r",(\s*[}\]])",

            r"\1",

            text

        )

        # Quote unquoted keys

        text = re.sub(

            r'([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*:)',

            r'\1"\2"\3',

            text

        )

        return text

    @staticmethod
    def validate(data):

        return isinstance(

            data,

            (dict, list)

        )

    @staticmethod
    def parse(text):

        try:

            cleaned = ResponseParser.clean(text)

            extracted = ResponseParser.extract_json(cleaned)

            repaired = ResponseParser.repair(extracted)

            parsed = json.loads(repaired)

            if ResponseParser.validate(parsed):

                return parsed

            return {

                "parsed": False,

                "raw": text

            }

        except Exception as e:

            Logger.error(

                f"Response Parser Error : {e}"

            )

            return {

                "parsed": False,

                "error": str(e),

                "raw": text

            }