class ComfyUI3DParser:

    @staticmethod
    def parse(result):

        outputs = result.get("outputs", {})

        for node in outputs.values():

            if "3d" in node:

                for item in node["3d"]:

                    if item.get("type") == "output":

                        return item

            if "gltf" in node:

                for item in node["gltf"]:

                    if item.get("type") == "output":

                        return item

            if "glb" in node:

                for item in node["glb"]:

                    if item.get("type") == "output":

                        return item

            if "meshes" in node:

                for item in node["meshes"]:

                    if item.get("type") == "output":

                        return item

        return None
