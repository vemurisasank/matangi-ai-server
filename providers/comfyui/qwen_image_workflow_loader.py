import json
import random
from pathlib import Path

from PIL import Image, ImageOps


class QwenImageWorkflowLoader:

    WORKFLOW_PATH = (
        Path(__file__).resolve().parents[2]
        / "workflows"
        / "qwen_image_edit_2511_api.json"
    )

    COMFY_INPUT_DIR = (
        Path(__file__).resolve().parents[2]
        / "comfyui"
        / "input"
    )

    MAX_REFERENCES = 3
    DIMENSION_MULTIPLE = 16

    @classmethod
    def _reference_filename(cls, reference):
        if isinstance(reference, dict):
            filename = (
                reference.get("filename")
                or reference.get("file")
                or reference.get("path")
                or reference.get("file_path")
            )
        elif isinstance(reference, str):
            filename = reference
        else:
            filename = None

        if not filename:
            raise ValueError(
                "Each Qwen reference must contain a filename."
            )

        safe_filename = Path(str(filename)).name
        source = cls.COMFY_INPUT_DIR / safe_filename

        if not source.is_file():
            raise FileNotFoundError(
                "Qwen reference image was not found in ComfyUI input: "
                f"{safe_filename}"
            )

        return safe_filename, source

    @classmethod
    def _normalize_reference(
        cls,
        filename,
        source,
        width,
        height,
        index
    ):
        width = max(
            cls.DIMENSION_MULTIPLE,
            round(width / cls.DIMENSION_MULTIPLE)
            * cls.DIMENSION_MULTIPLE
        )
        height = max(
            cls.DIMENSION_MULTIPLE,
            round(height / cls.DIMENSION_MULTIPLE)
            * cls.DIMENSION_MULTIPLE
        )

        normalized_name = (
            f"matangi_qwen2511_ref_{index}_"
            f"{Path(filename).stem}_{width}x{height}.png"
        )
        destination = cls.COMFY_INPUT_DIR / normalized_name

        with Image.open(source) as image:
            image = image.convert("RGB")

            if index == 1:
                normalized = ImageOps.fit(
                    image,
                    (width, height),
                    method=Image.Resampling.LANCZOS,
                    centering=(0.5, 0.5)
                )
            else:
                normalized = Image.new(
                    "RGB",
                    (width, height),
                    (0, 0, 0)
                )
                contained = ImageOps.contain(
                    image,
                    (width, height),
                    method=Image.Resampling.LANCZOS
                )
                offset = (
                    (width - contained.width) // 2,
                    (height - contained.height) // 2
                )
                normalized.paste(contained, offset)

            normalized.save(destination, format="PNG")

        return normalized_name

    @classmethod
    def build(
        cls,
        prompt,
        width,
        height,
        seed,
        steps=20,
        cfg=4.0,
        sampler="euler",
        scheduler="simple",
        reference_images=None
    ):
        references = reference_images or []

        if not 1 <= len(references) <= cls.MAX_REFERENCES:
            raise ValueError(
                "Qwen-Image-Edit-2511 requires 1 to 3 reference images; "
                f"received {len(references)}."
            )

        if width <= 0 or height <= 0:
            raise ValueError("Qwen image width and height must be positive.")

        if steps <= 0:
            raise ValueError("Qwen image steps must be greater than zero.")

        if cfg < 0:
            raise ValueError("Qwen image cfg must be non-negative.")

        with cls.WORKFLOW_PATH.open("r", encoding="utf-8") as file:
            workflow = json.load(file)

        normalized = []
        for index, reference in enumerate(references, start=1):
            filename, source = cls._reference_filename(reference)
            normalized.append(
                cls._normalize_reference(
                    filename,
                    source,
                    width,
                    height,
                    index
                )
            )

        role_lines = [
            (
                "Reference 1 is the main character identity. "
                "Preserve the character's recognizable identity, face, "
                "body, costume, and distinctive visual features."
            )
        ]
        if len(normalized) >= 2:
            role_lines.append(
                "Reference 2 is the environment. Preserve its architecture, "
                "setting, atmosphere, and spatial character."
            )
        if len(normalized) >= 3:
            role_lines.append(
                "Reference 3 is the important prop, costume, or property. "
                "Preserve its shape, material, colors, and distinctive details."
            )

        workflow["load_1"]["inputs"]["image"] = normalized[0]
        workflow["scale_1"]["inputs"]["image"] = ["load_1", 0]
        workflow["positive"]["inputs"]["image1"] = ["scale_1", 0]
        workflow["negative"]["inputs"]["image1"] = ["scale_1", 0]
        workflow["latent"]["inputs"]["pixels"] = ["load_1", 0]

        for index in range(2, 4):
            load_id = f"load_{index}"
            scale_id = f"scale_{index}"
            if index <= len(normalized):
                workflow[load_id]["inputs"]["image"] = normalized[index - 1]
                workflow[scale_id]["inputs"]["image"] = [load_id, 0]
                workflow["positive"]["inputs"][f"image{index}"] = [
                    scale_id,
                    0
                ]
                workflow["negative"]["inputs"][f"image{index}"] = [
                    scale_id,
                    0
                ]
            else:
                workflow.pop(load_id, None)
                workflow.pop(scale_id, None)
                workflow["positive"]["inputs"].pop(f"image{index}", None)
                workflow["negative"]["inputs"].pop(f"image{index}", None)

        if seed < 0:
            seed = random.randint(0, 2**32 - 1)

        workflow["positive"]["inputs"]["prompt"] = (
            "\n".join(role_lines)
            + "\n\n"
            + prompt
        )
        workflow["negative"]["inputs"]["prompt"] = ""
        workflow["unet"]["inputs"] = {
            "unet_name": "qwen_image_edit_2511_fp8mixed.safetensors",
            "weight_dtype": "default"
        }
        workflow["clip"]["inputs"] = {
            "clip_name": "qwen_2.5_vl_7b_fp8_scaled.safetensors",
            "type": "qwen_image",
            "device": "default"
        }
        workflow["vae"]["inputs"]["vae_name"] = "qwen_image_vae.safetensors"
        workflow["aura"]["inputs"]["shift"] = 3.1
        workflow["sampler"]["inputs"].update({
            "seed": seed,
            "steps": steps,
            "cfg": cfg,
            "sampler_name": sampler,
            "scheduler": scheduler
        })
        workflow["save"]["inputs"]["filename_prefix"] = (
            "qwen2511/image"
        )

        return workflow
