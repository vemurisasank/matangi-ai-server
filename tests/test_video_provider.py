from providers.comfyui.provider import ComfyUIProvider
from providers.comfyui.minimax_h3_r2v_workflow_loader import (
    MiniMaxH3R2VWorkflowLoader
)


def test_h3_multi_reference_submission_uses_native_r2v_loader(monkeypatch):
    class Client:
        def queue_prompt(self, workflow):
            self.workflow = workflow
            return "prompt-r2v"

    client = Client()
    provider = object.__new__(ComfyUIProvider)
    provider.client = client

    captured = {}

    def load(**kwargs):
        captured.update(kwargs)
        return {"6": {"inputs": {}}}

    monkeypatch.setattr(
        "providers.comfyui.minimax_h3_r2v_workflow_loader."
        "MiniMaxH3R2VWorkflowLoader.load",
        load
    )

    prompt_id = provider.submit_video(
        prompt="scene",
        duration=18,
        fps=24,
        width=512,
        height=512,
        reference_images=["one.png", "two.png"],
        model="minimax-h3"
    )

    assert prompt_id == "prompt-r2v"
    assert captured["references"] == ["one.png", "two.png"]
    assert captured["duration"] == 18
    assert captured["width"] == 512
    assert captured["height"] == 512


def test_production_r2v_defaults_to_1024x704():
    workflow = MiniMaxH3R2VWorkflowLoader.load(
        prompt="scene",
        references=["one.png"],
        duration=18
    )

    inputs = workflow["6"]["inputs"]
    assert inputs["width"] == 1024
    assert inputs["height"] == 704
    assert inputs["length"] == MiniMaxH3R2VWorkflowLoader._frame_count(18)
    assert inputs["ref_images.ref_image_0"] == ["21", 0]
    assert "ref_images.ref_image_9" not in inputs


def test_production_r2v_workflow_has_turbo_configuration():
    import json
    from pathlib import Path

    path = (
        Path(__file__).resolve().parents[1]
        / "workflows"
        / "minimax_h3_r2v_api.json"
    )
    workflow = json.loads(path.read_text(encoding="utf-8"))

    assert workflow["6"]["class_type"] == "MiniMaxH3ReferenceToVideo"
    assert workflow["10"]["class_type"] == "LoraLoaderModelOnly"
    assert workflow["10"]["inputs"]["lora_name"] == (
        "minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors"
    )
    assert workflow["10"]["inputs"]["strength_model"] == 1.0
    assert workflow["12"]["inputs"]["value"] == 8
    assert workflow["8"]["inputs"]["sampler_name"] == "res_multistep"
    assert workflow["9"]["inputs"]["scheduler"] == "simple"
    assert workflow["9"]["inputs"]["denoise"] == 1.0
    assert workflow["6"]["inputs"]["width"] == 1024
    assert workflow["6"]["inputs"]["height"] == 704


def test_h3_legacy_reference_submission_keeps_i2v_loader(monkeypatch):
    class Client:
        def queue_prompt(self, workflow):
            return "prompt-i2v"

    provider = object.__new__(ComfyUIProvider)
    provider.client = Client()
    captured = {}

    def load(**kwargs):
        captured.update(kwargs)
        return {"1": {"inputs": {}}}

    monkeypatch.setattr(
        "providers.comfyui.minimax_h3_video_workflow_loader."
        "MiniMaxH3VideoWorkflowLoader.load",
        load
    )

    prompt_id = provider.submit_video(
        prompt="scene",
        reference_image="frame.png",
        model="minimax-h3"
    )

    assert prompt_id == "prompt-i2v"
    assert captured["reference_image"] == "frame.png"
