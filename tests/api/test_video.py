from api.routes.video import generate_video
from api.schemas.video_schema import VideoRequest
from providers.comfyui.minimax_h3_video_workflow_loader import (
    MiniMaxH3VideoWorkflowLoader
)


def test_video_request_accepts_scene_and_project():
    request = VideoRequest(
        prompt="A cinematic scene",
        scene_id="scene-001",
        project="project-001"
    )

    assert request.scene_id == "scene-001"
    assert request.project == "project-001"


def test_video_request_scene_and_project_are_optional():
    request = VideoRequest(prompt="A cinematic scene")

    assert request.scene_id is None
    assert request.project is None


def test_video_request_defaults_remain_unchanged():
    request = VideoRequest(prompt="A cinematic scene")

    assert request.duration == 5
    assert request.fps == 24
    assert request.width == 1280
    assert request.height == 720
    assert request.reference_image is None
    assert request.model is None
    assert request.seed is None


def test_video_request_accepts_model_and_seed():
    request = VideoRequest(
        prompt="A cinematic scene",
        model="minimax-h3",
        seed=1
    )

    assert request.model == "minimax-h3"
    assert request.seed == 1


def test_h3_loader_injects_test_parameters():
    workflow = MiniMaxH3VideoWorkflowLoader.load(
        prompt="A cinematic scene",
        reference_image="/workspace/ComfyUI/input/example.png",
        width=512,
        height=512,
        duration=5,
        fps=24,
        seed=1
    )

    assert len(workflow) == 20
    assert workflow["1"]["inputs"]["image"] == "example.png"
    assert workflow["6"]["inputs"]["prompt"] == "A cinematic scene"
    assert workflow["6"]["inputs"]["width"] == 512
    assert workflow["6"]["inputs"]["height"] == 512
    assert workflow["6"]["inputs"]["length"] == 124
    assert workflow["7"]["inputs"]["noise_seed"] == 1


def test_h3_loader_rejects_non_24_fps():
    try:
        MiniMaxH3VideoWorkflowLoader.load(
            prompt="A cinematic scene",
            reference_image="example.png",
            fps=25
        )
    except ValueError as error:
        assert str(error) == "MiniMax H3 requires fps=24."
    else:
        raise AssertionError("Expected MiniMax H3 FPS validation error")


def test_h3_workflow_uses_expected_models_and_video_output():
    workflow = MiniMaxH3VideoWorkflowLoader.load(
        prompt="A cinematic scene",
        reference_image="example.png"
    )

    assert workflow["2"]["inputs"]["unet_name"] == (
        "minimax_h3_fl2va_pruned_int8_convrot.safetensors"
    )
    assert workflow["3"]["inputs"]["clip_name"] == (
        "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors"
    )
    assert workflow["4"]["inputs"]["vae_name"] == (
        "minimax_h3_video_vae_fp16.safetensors"
    )
    assert workflow["5"]["inputs"]["vae_name"] == (
        "minimax_h3_audio_vae_fp32.safetensors"
    )
    assert workflow["10"]["inputs"]["lora_name"] == (
        "minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors"
    )
    assert workflow["11"]["inputs"]["switch"] is False
    assert workflow["12"]["inputs"]["switch"] is False
    assert workflow["20"]["inputs"]["format"] == "mp4"
    assert workflow["20"]["inputs"]["codec"] == {"codec": "h264"}


def test_video_route_preserves_response_envelope(monkeypatch):
    expected_result = {
        "success": True,
        "provider": "ComfyUI",
        "video": {
            "filename": "scene.mp4",
            "subfolder": "video",
            "type": "output"
        }
    }

    def generate(_request):
        return expected_result

    monkeypatch.setattr(
        "api.routes.video.VideoEngine.generate",
        generate
    )

    response = generate_video(
        VideoRequest(
            prompt="A cinematic scene",
            scene_id="scene-001",
            project="project-001"
        )
    )

    assert response == {
        "success": True,
        "message": "Video Generated Successfully",
        "data": expected_result
    }
