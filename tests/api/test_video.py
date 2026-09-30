from api.routes.video import generate_video
from api.schemas.video_schema import VideoRequest


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
