class ThreeDWorkflowLoader:

    @staticmethod
    def build(
        image,
        resolution=3072,
        batch_size=1,
        seed=12345,
        steps=30,
        cfg=5.0,
        octree_resolution=256,
        threshold=0.6,
        filename_prefix="matangi_3d"
    ):

        if seed < 0:
            seed = 0

        return {
            "1": {
                "class_type": "LoadImage",
                "inputs": {
                    "image": image
                }
            },

            "2": {
                "class_type": "ImageOnlyCheckpointLoader",
                "inputs": {
                    "ckpt_name": "hunyuan_3d_v2.1.safetensors"
                }
            },

            "3": {
                "class_type": "CLIPVisionEncode",
                "inputs": {
                    "clip_vision": ["2", 1],
                    "image": ["1", 0],
                    "crop": "center"
                }
            },

            "4": {
                "class_type": "Hunyuan3Dv2Conditioning",
                "inputs": {
                    "clip_vision_output": ["3", 0]
                }
            },

            "5": {
                "class_type": "EmptyLatentHunyuan3Dv2",
                "inputs": {
                    "resolution": resolution,
                    "batch_size": batch_size
                }
            },

            "6": {
                "class_type": "ModelSamplingAuraFlow",
                "inputs": {
                    "model": ["2", 0],
                    "shift": 1
                }
            },

            "7": {
                "class_type": "KSampler",
                "inputs": {
                    "model": ["6", 0],
                    "positive": ["4", 0],
                    "negative": ["4", 1],
                    "latent_image": ["5", 0],
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1
                }
            },

            "8": {
                "class_type": "VAEDecodeHunyuan3D",
                "inputs": {
                    "samples": ["7", 0],
                    "vae": ["2", 2],
                    "num_chunks": 8000,
                    "octree_resolution": octree_resolution
                }
            },

            "9": {
                "class_type": "VoxelToMesh",
                "inputs": {
                    "voxel": ["8", 0],
                    "algorithm": "surface net",
                    "threshold": threshold
                }
            },

            "10": {
                "class_type": "SaveGLB",
                "inputs": {
                    "mesh": ["9", 0],
                    "filename_prefix": filename_prefix
                }
            }
        }
