import json
import random
from pathlib import Path

from PIL import Image


class WorkflowLoader:

    WORKFLOW_DIR = (
        Path(__file__).resolve().parents[2]
        / "workflows"
    )

    COMFY_INPUT_DIR = (
        Path(__file__).resolve().parents[2]
        / "comfyui"
        / "input"
    )

    # ---------------------------------------------------------
    # Z-IMAGE REFERENCE SETTINGS
    # ---------------------------------------------------------

    REFERENCE_TARGET_PIXELS = 1024 * 1024

    # Z-Image VAE has an 8x spatial reduction.
    # Lumina/Z-Image uses a patch size of 2 on the latent.
    # Therefore reference pixels must be divisible by 16.
    REFERENCE_PIXEL_MULTIPLE = 16

    MAX_REFERENCES = 3

    # ---------------------------------------------------------
    # REFERENCE NORMALIZATION
    # ---------------------------------------------------------

    @staticmethod
    def _normalize_reference_image(filename):
        """
        Prepare a reference image for native Z-Image Omni
        reference conditioning.

        The original reference image is never modified.

        The normalized copy is written into ComfyUI input/
        and is then used by LoadImage.

        Dimensions are rounded to multiples of 16 so that:

            pixels / 8 = VAE latent
            latent / 2 = Z-Image patch grid

        always produces integer dimensions.
        """

        source_path = (
            WorkflowLoader.COMFY_INPUT_DIR
            / filename
        )

        if not source_path.exists():
            raise FileNotFoundError(
                "Reference image not found in "
                "ComfyUI input directory: "
                f"{filename}"
            )

        with Image.open(source_path) as image:

            # -------------------------------------------------
            # Convert to RGB/RGBA-compatible image
            # -------------------------------------------------

            if image.mode not in ("RGB", "RGBA"):
                image = image.convert("RGB")

            original_width, original_height = image.size

            # -------------------------------------------------
            # Calculate approximately 1MP dimensions
            # -------------------------------------------------

            scale = (
                WorkflowLoader.REFERENCE_TARGET_PIXELS
                / (original_width * original_height)
            ) ** 0.5

            target_width = round(
                original_width * scale
            )

            target_height = round(
                original_height * scale
            )

            # -------------------------------------------------
            # CRITICAL:
            #
            # Round to multiples of 16 instead of 8.
            #
            # This guarantees:
            #
            # pixel dimension
            #      ↓ /8
            # VAE latent dimension
            #      ↓ /2
            # Z-Image patch dimension
            # -------------------------------------------------

            target_width = max(
                WorkflowLoader.REFERENCE_PIXEL_MULTIPLE,
                round(
                    target_width
                    / WorkflowLoader.REFERENCE_PIXEL_MULTIPLE
                )
                * WorkflowLoader.REFERENCE_PIXEL_MULTIPLE
            )

            target_height = max(
                WorkflowLoader.REFERENCE_PIXEL_MULTIPLE,
                round(
                    target_height
                    / WorkflowLoader.REFERENCE_PIXEL_MULTIPLE
                )
                * WorkflowLoader.REFERENCE_PIXEL_MULTIPLE
            )

            # -------------------------------------------------
            # Resize only when necessary
            # -------------------------------------------------

            if (
                target_width != original_width
                or target_height != original_height
            ):

                image = image.resize(
                    (
                        target_width,
                        target_height
                    ),
                    Image.Resampling.LANCZOS
                )

            # -------------------------------------------------
            # Create deterministic normalized filename
            # -------------------------------------------------

            normalized_name = (
                f"matangi_zimage_ref_"
                f"{Path(filename).stem}_"
                f"{target_width}x{target_height}.png"
            )

            normalized_path = (
                WorkflowLoader.COMFY_INPUT_DIR
                / normalized_name
            )

            # -------------------------------------------------
            # Save normalized reference
            # -------------------------------------------------

            image.save(
                normalized_path,
                format="PNG"
            )

        # -----------------------------------------------------
        # Verify resulting dimensions
        # -----------------------------------------------------

        with Image.open(normalized_path) as check_image:

            final_width, final_height = check_image.size

        latent_width = final_width // 8
        latent_height = final_height // 8

        if (
            final_width % 16 != 0
            or final_height % 16 != 0
            or latent_width % 2 != 0
            or latent_height % 2 != 0
        ):
            raise ValueError(
                "Normalized Z-Image reference dimensions "
                "are invalid: "
                f"{final_width}x{final_height} "
                f"(latent {latent_width}x{latent_height})"
            )

        print(
            "Reference normalized:",
            filename,
            "→",
            normalized_name
        )

        print(
            "Reference dimensions:",
            f"{final_width}x{final_height}"
        )

        print(
            "Reference latent:",
            f"{latent_width}x{latent_height}"
        )

        return normalized_name

    # ---------------------------------------------------------
    # WORKFLOW LOADER
    # ---------------------------------------------------------

    @staticmethod
    def load(
        prompt,
        width,
        height,
        seed,
        reference_images=None
    ):

        if reference_images is None:
            reference_images = []

        # -----------------------------------------------------
        # LOAD BASE WORKFLOW
        # -----------------------------------------------------

        path = (
            WorkflowLoader.WORKFLOW_DIR
            / "z_image_text_to_image_api.json"
        )

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            workflow = json.load(f)

        # -----------------------------------------------------
        # Z-IMAGE TURBO MODEL
        # -----------------------------------------------------

        workflow["57:28"]["class_type"] = "UNETLoader"

        workflow["57:28"]["inputs"] = {
            "unet_name": (
                "z_image_turbo_nvfp4.safetensors"
            ),
            "weight_dtype": "default"
        }

        # -----------------------------------------------------
        # Z-IMAGE OMNI TEXT ENCODER
        # -----------------------------------------------------

        workflow["57:27"] = {
            "class_type": "TextEncodeZImageOmni",

            "inputs": {
                "clip": [
                    "57:30",
                    0
                ],

                "prompt": prompt,

                "auto_resize_images": True,

                "vae": [
                    "57:29",
                    0
                ]
            },

            "_meta": {
                "title": (
                    "Z-Image Omni Text + References"
                )
            }
        }

        # -----------------------------------------------------
        # VALIDATE REFERENCE COUNT
        # -----------------------------------------------------

        if len(reference_images) > WorkflowLoader.MAX_REFERENCES:

            raise ValueError(
                "Z-Image TextEncodeZImageOmni supports "
                "a maximum of 3 reference images. "
                f"Received: {len(reference_images)}"
            )

        # -----------------------------------------------------
        # PROCESS REFERENCES
        # -----------------------------------------------------

        valid_references = []

        for reference in reference_images:

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
                continue

            # -------------------------------------------------
            # We only want the filename.
            # -------------------------------------------------

            filename = Path(
                str(filename)
            ).name

            # -------------------------------------------------
            # Verify original exists.
            # -------------------------------------------------

            original_path = (
                WorkflowLoader.COMFY_INPUT_DIR
                / filename
            )

            if not original_path.exists():

                raise FileNotFoundError(
                    "Reference image not found in "
                    "ComfyUI input directory: "
                    f"{filename}"
                )

            # -------------------------------------------------
            # Normalize reference dimensions.
            # -------------------------------------------------

            normalized_filename = (
                WorkflowLoader
                ._normalize_reference_image(
                    filename
                )
            )

            valid_references.append(
                normalized_filename
            )

        # -----------------------------------------------------
        # CREATE LOAD IMAGE NODES
        # -----------------------------------------------------

        for index, filename in enumerate(
            valid_references,
            start=1
        ):

            load_node_id = (
                f"matangi_ref_load_{index}"
            )

            workflow[load_node_id] = {

                "class_type": "LoadImage",

                "inputs": {
                    "image": filename,
                    "upload": "image"
                },

                "_meta": {
                    "title": (
                        f"Matangi Reference {index}"
                    )
                }
            }

            # -------------------------------------------------
            # Connect image directly to native
            # TextEncodeZImageOmni.
            # -------------------------------------------------

            workflow["57:27"]["inputs"][
                f"image{index}"
            ] = [
                load_node_id,
                0
            ]

        # -----------------------------------------------------
        # SEED
        # -----------------------------------------------------

        if seed < 0:

            seed = random.randint(
                0,
                2**32 - 1
            )

        workflow["57:3"]["inputs"]["seed"] = seed

        # -----------------------------------------------------
        # OUTPUT RESOLUTION
        # -----------------------------------------------------

        workflow["57:13"]["inputs"]["width"] = width

        workflow["57:13"]["inputs"]["height"] = height

        workflow["57:13"]["inputs"]["batch_size"] = 1

        # -----------------------------------------------------
        # POSITIVE CONDITIONING
        # -----------------------------------------------------

        workflow["57:3"]["inputs"]["positive"] = [
            "57:27",
            0
        ]

        # -----------------------------------------------------
        # NEGATIVE CONDITIONING
        # -----------------------------------------------------

        workflow["57:33"]["inputs"]["conditioning"] = [
            "57:27",
            0
        ]

        # -----------------------------------------------------
        # REMOVE OLD MANUAL REFERENCE NODES
        # -----------------------------------------------------

        nodes_to_remove = []

        for node_id in workflow:

            if (
                str(node_id).startswith(
                    "matangi_ref_encode_"
                )
                or
                str(node_id).startswith(
                    "matangi_ref_latent_"
                )
            ):

                nodes_to_remove.append(
                    node_id
                )

        for node_id in nodes_to_remove:

            del workflow[node_id]

        # -----------------------------------------------------
        # DIAGNOSTIC OUTPUT
        # -----------------------------------------------------

        print("=" * 70)

        print(
            "MATANGI Z-IMAGE WORKFLOW"
        )

        print("=" * 70)

        print(
            "Reference images received:",
            len(reference_images)
        )

        print(
            "Reference images validated:",
            len(valid_references)
        )

        print(
            "Target resolution:",
            f"{width}x{height}"
        )

        print(
            "Seed:",
            seed
        )

        if len(valid_references) == 0:

            print(
                "Mode: TEXT-TO-IMAGE"
            )

        else:

            print(
                "Mode: NATIVE Z-IMAGE "
                "REFERENCE CONDITIONING"
            )

            print(
                "Reference nodes:",
                len(valid_references)
            )

            print(
                "Reference pipeline:",
                "LoadImage → "
                "TextEncodeZImageOmni"
            )

            for index, filename in enumerate(
                valid_references,
                start=1
            ):

                print(
                    f"Reference {index}:",
                    filename
                )

        print("=" * 70)

        return workflow