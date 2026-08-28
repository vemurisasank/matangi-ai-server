import json
import re

from core.logger import Logger


class ResponseParser:

    # =========================================================
    # CLEAN
    # =========================================================

    @staticmethod
    def clean(text):

        if text is None:
            return ""

        text = str(text)

        # Remove markdown fences
        text = text.replace(
            "```json",
            ""
        )

        text = text.replace(
            "```JSON",
            ""
        )

        text = text.replace(
            "```",
            ""
        )

        return text.strip()

    # =========================================================
    # EXTRACT JSON
    # =========================================================

    @staticmethod
    def extract_json(text):

        if not text:
            return ""

        text = text.strip()

        # -----------------------------------------------------
        # Already looks like JSON
        # -----------------------------------------------------

        if text.startswith("{") and text.endswith("}"):

            return text

        if text.startswith("[") and text.endswith("]"):

            return text

        # -----------------------------------------------------
        # Find first JSON object/array using bracket matching
        # -----------------------------------------------------

        start_positions = []

        object_start = text.find("{")

        array_start = text.find("[")

        if object_start >= 0:
            start_positions.append(
                (object_start, "{", "}")
            )

        if array_start >= 0:
            start_positions.append(
                (array_start, "[", "]")
            )

        if not start_positions:
            return text

        start, opening, closing = min(
            start_positions,
            key=lambda item: item[0]
        )

        depth = 0

        in_string = False

        escape = False

        for index in range(
            start,
            len(text)
        ):

            char = text[index]

            # -------------------------------------------------
            # Handle JSON strings
            # -------------------------------------------------

            if char == '"' and not escape:

                in_string = not in_string

            if char == "\\" and not escape:

                escape = True

            else:

                escape = False

            if in_string:
                continue

            # -------------------------------------------------
            # Track brackets
            # -------------------------------------------------

            if char == opening:

                depth += 1

            elif char == closing:

                depth -= 1

                if depth == 0:

                    return text[
                        start:index + 1
                    ]

        return text[start:]

    # =========================================================
    # REPAIR
    # =========================================================

    @staticmethod
    def repair(text):

        if not text:
            return ""

        text = text.strip()

        # -----------------------------------------------------
        # Remove markdown fences
        # -----------------------------------------------------

        text = text.replace(
            "```json",
            ""
        )

        text = text.replace(
            "```",
            ""
        )

        # -----------------------------------------------------
        # Remove common control characters
        # -----------------------------------------------------

        text = re.sub(
            r"[\x00-\x08\x0b\x0c\x0e-\x1f]",
            "",
            text
        )

        # -----------------------------------------------------
        # Remove trailing commas
        #
        # Example:
        #
        # "name": "Parvati",
        # }
        #
        # becomes:
        #
        # "name": "Parvati"
        # }
        # -----------------------------------------------------

        text = re.sub(
            r",\s*([}\]])",
            r"\1",
            text
        )

        # -----------------------------------------------------
        # Quote unquoted object keys
        # -----------------------------------------------------

        text = re.sub(
            r'([{\[,]\s*)([A-Za-z_][A-Za-z0-9_-]*)(\s*:)',
            r'\1"\2"\3',
            text
        )

        # -----------------------------------------------------
        # Fix common unquoted string values
        #
        # Example:
        #
        # "name": Parvati
        #
        # becomes:
        #
        # "name": "Parvati"
        #
        # We deliberately keep this conservative.
        # -----------------------------------------------------

        text = re.sub(
            r'(:\s*)([A-Za-z][A-Za-z0-9 _\'-]*)(\s*[,}])',
            lambda m: (
                m.group(1)
                + '"'
                + m.group(2).strip()
                + '"'
                + m.group(3)
            ),
            text
        )

        return text.strip()

    # =========================================================
    # JSON LOAD WITH REPAIR
    # =========================================================

    @staticmethod
    def _try_load(text):

        try:

            return json.loads(text)

        except Exception:

            return None

    # =========================================================
    # SPECIAL REPAIR FOR COMMON LLM DIALOGUE ERRORS
    # =========================================================

    @staticmethod
    def repair_dialogue_arrays(text):

        if not text:
            return text

        # -----------------------------------------------------
        # LLMs sometimes produce:
        #
        # "dialogue": [
        #     "Parvati: Hello",
        #     Shiva: "Hello"
        # ]
        #
        # Convert the second item into a normal string.
        # -----------------------------------------------------

        pattern = re.compile(
            r'([A-Za-z][A-Za-z0-9 _-]*)\s*:\s*"([^"]*)"'
        )

        def replace_dialogue(match):

            speaker = match.group(1).strip()

            speech = match.group(2).strip()

            return (
                '"'
                + speaker
                + ': '
                + speech
                + '"'
            )

        text = pattern.sub(
            replace_dialogue,
            text
        )

        return text

    # =========================================================
    # VALIDATE
    # =========================================================

    @staticmethod
    def validate(data):

        return isinstance(
            data,
            (dict, list)
        )

    # =========================================================
    # PARSE
    # =========================================================

    @staticmethod
    def parse(text):

        try:

            # -------------------------------------------------
            # CLEAN
            # -------------------------------------------------

            cleaned = (
                ResponseParser.clean(
                    text
                )
            )

            # -------------------------------------------------
            # EXTRACT
            # -------------------------------------------------

            extracted = (
                ResponseParser.extract_json(
                    cleaned
                )
            )

            # -------------------------------------------------
            # FIRST ATTEMPT
            # -------------------------------------------------

            parsed = (
                ResponseParser._try_load(
                    extracted
                )
            )

            if parsed is not None:

                if ResponseParser.validate(
                    parsed
                ):

                    return parsed

            # -------------------------------------------------
            # GENERAL REPAIR
            # -------------------------------------------------

            repaired = (
                ResponseParser.repair(
                    extracted
                )
            )

            parsed = (
                ResponseParser._try_load(
                    repaired
                )
            )

            if parsed is not None:

                if ResponseParser.validate(
                    parsed
                ):

                    return parsed

            # -------------------------------------------------
            # DIALOGUE REPAIR
            # -------------------------------------------------

            dialogue_repaired = (
                ResponseParser.repair_dialogue_arrays(
                    repaired
                )
            )

            dialogue_repaired = re.sub(
                r",\s*([}\]])",
                r"\1",
                dialogue_repaired
            )

            parsed = (
                ResponseParser._try_load(
                    dialogue_repaired
                )
            )

            if parsed is not None:

                if ResponseParser.validate(
                    parsed
                ):

                    return parsed

            # -------------------------------------------------
            # FINAL ERROR
            # -------------------------------------------------

            return {

                "parsed": False,

                "error":
                    "Unable to parse valid JSON.",

                "raw":
                    text

            }

        except Exception as e:

            Logger.error(

                f"Response Parser Error : {e}"

            )

            return {

                "parsed": False,

                "error":
                    str(e),

                "raw":
                    text

            }