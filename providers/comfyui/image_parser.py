class ComfyUIImageParser:

    @staticmethod
    def parse(result):

        outputs = result["outputs"]

        for node in outputs.values():

            if "images" in node:

                return node["images"][0]

        return None