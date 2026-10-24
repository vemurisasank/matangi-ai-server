import pytest

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


def test_h3_media_references_reach_r2v_loader_in_order(monkeypatch):
    class Client:
        def queue_prompt(self, workflow):
            return "prompt-media"

    provider = object.__new__(ComfyUIProvider)
    provider.client = Client()
    captured = {}

    def load(**kwargs):
        captured.update(kwargs)
        return {"6": {"inputs": {}}}

    monkeypatch.setattr(
        "providers.comfyui.minimax_h3_r2v_workflow_loader."
        "MiniMaxH3R2VWorkflowLoader.load",
        load
    )

    assert provider.submit_video(
        prompt="scene",
        reference_images=["one.png"],
        audio_references=["one.wav", "two.mp3"],
        video_references=["one.mp4", "two.webm"],
        model="minimax-h3"
    ) == "prompt-media"
    assert captured["references"] == ["one.png"]
    assert captured["audio_references"] == ["one.wav", "two.mp3"]
    assert captured["video_references"] == ["one.mp4", "two.webm"]


def test_h3_media_with_legacy_image_uses_r2v_loader(monkeypatch):
    class Client:
        def queue_prompt(self, workflow):
            return "prompt-media"

    provider = object.__new__(ComfyUIProvider)
    provider.client = Client()
    captured = {}

    def load(**kwargs):
        captured.update(kwargs)
        return {"6": {"inputs": {}}}

    monkeypatch.setattr(
        "providers.comfyui.minimax_h3_r2v_workflow_loader."
        "MiniMaxH3R2VWorkflowLoader.load",
        load
    )

    provider.submit_video(
        prompt="scene",
        reference_image="frame.png",
        audio_references=["voice.wav"],
        model="minimax-h3"
    )

    assert captured["references"] == ["frame.png"]
    assert captured["audio_references"] == ["voice.wav"]
    assert captured["video_references"] == []


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
    assert all(
        node["class_type"] not in {
            "LoadAudio",
            "LoadVideo",
            "GetVideoComponents"
        }
        for node in workflow.values()
    )


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


def test_r2v_audio_reference_adds_load_audio_node():
    workflow = MiniMaxH3R2VWorkflowLoader.load(
        prompt="scene",
        references=["one.png"],
        audio_references=["dialogue.wav"]
    )

    inputs = workflow["6"]["inputs"]
    audio_node_id = inputs["ref_audios.ref_audio_0"][0]
    assert workflow[audio_node_id] == {
        "class_type": "LoadAudio",
        "inputs": {"audio": "dialogue.wav"}
    }


def test_r2v_three_audio_references_use_distinct_slots_and_nodes():
    workflow = MiniMaxH3R2VWorkflowLoader.load(
        prompt="scene",
        references=["one.png"],
        audio_references=["one.wav", "two.mp3", "three.flac"]
    )

    inputs = workflow["6"]["inputs"]
    node_ids = [
        inputs[f"ref_audios.ref_audio_{index}"][0]
        for index in range(3)
    ]
    assert len(set(node_ids)) == 3
    assert [workflow[node_id]["class_type"] for node_id in node_ids] == [
        "LoadAudio",
        "LoadAudio",
        "LoadAudio"
    ]


def test_r2v_video_reference_adds_loader_and_components_nodes():
    workflow = MiniMaxH3R2VWorkflowLoader.load(
        prompt="scene",
        references=["one.png"],
        video_references=["reference.mp4"]
    )

    inputs = workflow["6"]["inputs"]
    components_node_id = inputs["ref_videos.ref_video_0"][0]
    load_node_id = workflow[components_node_id]["inputs"]["video"][0]
    assert workflow[load_node_id] == {
        "class_type": "LoadVideo",
        "inputs": {"file": "reference.mp4"}
    }
    assert workflow[components_node_id]["class_type"] == "GetVideoComponents"
    assert inputs["ref_video_audios.ref_video_audio_0"] == [
        components_node_id,
        1
    ]


def test_r2v_three_video_references_use_distinct_node_ids_and_slots():
    workflow = MiniMaxH3R2VWorkflowLoader.load(
        prompt="scene",
        references=["one.png"],
        video_references=["one.mp4", "two.webm", "three.mkv"]
    )

    inputs = workflow["6"]["inputs"]
    component_ids = [
        inputs[f"ref_videos.ref_video_{index}"][0]
        for index in range(3)
    ]
    load_ids = [
        workflow[component_id]["inputs"]["video"][0]
        for component_id in component_ids
    ]
    assert len(set(component_ids + load_ids)) == 6
    assert all(
        workflow[node_id]["class_type"] == "GetVideoComponents"
        for node_id in component_ids
    )
    assert all(
        workflow[node_id]["class_type"] == "LoadVideo"
        for node_id in load_ids
    )


def test_r2v_zero_images_with_optional_media_allocates_unique_active_nodes():
    workflow = MiniMaxH3R2VWorkflowLoader.load(
        prompt="scene",
        references=[],
        audio_references=["voice.wav"],
        video_references=["reference.mp4"]
    )

    inputs = workflow["6"]["inputs"]
    audio_id = inputs["ref_audios.ref_audio_0"][0]
    video_components_id = inputs["ref_videos.ref_video_0"][0]
    video_loader_id = workflow[video_components_id]["inputs"]["video"][0]
    active_ids = [
        node_id for node_id in workflow
        if str(node_id).isdigit()
    ]

    assert len(active_ids) == len(set(active_ids))
    assert {audio_id, video_components_id, video_loader_id}.isdisjoint(
        {"2", "3", "4", "5", "6", "7", "8", "9", "10", "12",
         "15", "16", "17", "18", "19", "20"}
    )
    assert audio_id == "21"
    assert video_loader_id == "22"
    assert video_components_id == "23"


def test_r2v_one_image_with_optional_media_preserves_image_node():
    workflow = MiniMaxH3R2VWorkflowLoader.load(
        prompt="scene",
        references=["character.png"],
        audio_references=["voice.wav"],
        video_references=["reference.mp4"]
    )

    inputs = workflow["6"]["inputs"]
    audio_id = inputs["ref_audios.ref_audio_0"][0]
    video_components_id = inputs["ref_videos.ref_video_0"][0]
    video_loader_id = workflow[video_components_id]["inputs"]["video"][0]
    assert inputs["ref_images.ref_image_0"] == ["21", 0]
    assert workflow["21"] == {
        "class_type": "LoadImage",
        "inputs": {"image": "character.png"}
    }
    assert len({"21", audio_id, video_components_id, video_loader_id}) == 4
    assert all(
        node_id not in {"21"}
        for node_id in (audio_id, video_components_id, video_loader_id)
    )


def test_r2v_nine_images_with_optional_media_allocates_outside_image_range():
    references = [f"reference_{index}.png" for index in range(9)]
    workflow = MiniMaxH3R2VWorkflowLoader.load(
        prompt="scene",
        references=references,
        audio_references=["voice.wav"],
        video_references=["reference.mp4"]
    )

    inputs = workflow["6"]["inputs"]
    assert [
        inputs[f"ref_images.ref_image_{index}"]
        for index in range(9)
    ] == [[str(21 + index), 0] for index in range(9)]
    assert [
        workflow[str(21 + index)]["inputs"]["image"]
        for index in range(9)
    ] == references

    audio_id = inputs["ref_audios.ref_audio_0"][0]
    video_components_id = inputs["ref_videos.ref_video_0"][0]
    video_loader_id = workflow[video_components_id]["inputs"]["video"][0]
    assert {audio_id, video_components_id, video_loader_id}.isdisjoint(
        {str(index) for index in range(21, 30)}
    )
    assert len({
        *[str(index) for index in range(21, 30)],
        audio_id,
        video_components_id,
        video_loader_id
    }) == 12


def test_r2v_optional_media_limits_and_filenames_are_validated():
    with pytest.raises(ValueError, match="at most 3 audio"):
        MiniMaxH3R2VWorkflowLoader.load(
            prompt="scene",
            references=["one.png"],
            audio_references=["1.wav", "2.wav", "3.wav", "4.wav"]
        )
    with pytest.raises(ValueError, match="at most 3 video"):
        MiniMaxH3R2VWorkflowLoader.load(
            prompt="scene",
            references=["one.png"],
            video_references=["1.mp4", "2.mp4", "3.mp4", "4.mp4"]
        )
    with pytest.raises(ValueError, match="staged audio filename"):
        MiniMaxH3R2VWorkflowLoader.load(
            prompt="scene",
            references=["one.png"],
            audio_references=["../dialogue.wav"]
        )
    with pytest.raises(ValueError, match="staged video filename"):
        MiniMaxH3R2VWorkflowLoader.load(
            prompt="scene",
            references=["one.png"],
            video_references=["/tmp/reference.mp4"]
        )
    with pytest.raises(ValueError, match="staged audio filename"):
        MiniMaxH3R2VWorkflowLoader.load(
            prompt="scene",
            references=["one.png"],
            audio_references=[""]
        )
    with pytest.raises(ValueError, match="staged audio filename"):
        MiniMaxH3R2VWorkflowLoader.load(
            prompt="scene",
            references=["one.png"],
            audio_references=["voice.txt"]
        )
    with pytest.raises(ValueError, match="staged audio filename"):
        MiniMaxH3R2VWorkflowLoader.load(
            prompt="scene",
            references=["one.png"],
            audio_references=[r"..\dialogue.wav"]
        )
    with pytest.raises(ValueError, match="staged video filename"):
        MiniMaxH3R2VWorkflowLoader.load(
            prompt="scene",
            references=["one.png"],
            video_references=[""]
        )
    with pytest.raises(ValueError, match="staged video filename"):
        MiniMaxH3R2VWorkflowLoader.load(
            prompt="scene",
            references=["one.png"],
            video_references=["reference.txt"]
        )
    with pytest.raises(ValueError, match="staged video filename"):
        MiniMaxH3R2VWorkflowLoader.load(
            prompt="scene",
            references=["one.png"],
            video_references=[r"..\reference.mp4"]
        )


def test_r2v_image_references_reject_path_components():
    with pytest.raises(ValueError, match="valid image path"):
        MiniMaxH3R2VWorkflowLoader.load(
            prompt="scene",
            references=["../character.png"]
        )
    with pytest.raises(ValueError, match="valid image path"):
        MiniMaxH3R2VWorkflowLoader.load(
            prompt="scene",
            references=[r"..\character.png"]
        )


def test_r2v_loader_does_not_check_missing_staged_file_existence():
    workflow = MiniMaxH3R2VWorkflowLoader.load(
        prompt="scene",
        references=[],
        audio_references=["missing-staged-audio.wav"],
        video_references=["missing-staged-video.mp4"]
    )

    inputs = workflow["6"]["inputs"]
    audio_id = inputs["ref_audios.ref_audio_0"][0]
    video_id = inputs["ref_videos.ref_video_0"][0]
    assert workflow[audio_id]["inputs"]["audio"] == "missing-staged-audio.wav"
    assert workflow[workflow[video_id]["inputs"]["video"][0]]["inputs"]["file"] == (
        "missing-staged-video.mp4"
    )


@pytest.mark.parametrize(
    ("audio_references", "video_references"),
    [
        ([], []),
        (["voice.wav"], []),
        ([], ["reference.mp4"]),
        (["voice.wav"], ["reference.mp4"]),
        (["one.wav", "two.mp3", "three.flac"], []),
        ([], ["one.mp4", "two.webm", "three.mkv"]),
    ],
)
def test_r2v_graph_combinations_connect_only_supplied_media(
    audio_references,
    video_references,
):
    workflow = MiniMaxH3R2VWorkflowLoader.load(
        prompt="scene",
        references=["character.png"],
        audio_references=audio_references,
        video_references=video_references,
    )

    inputs = workflow["6"]["inputs"]
    assert [
        inputs[f"ref_audios.ref_audio_{index}"][0]
        for index in range(len(audio_references))
    ] == [
        node_id
        for node_id, node in workflow.items()
        if node["class_type"] == "LoadAudio"
    ]
    assert [
        workflow[inputs[f"ref_videos.ref_video_{index}"][0]]
        ["inputs"]["video"][0]
        for index in range(len(video_references))
    ] == [
        node_id
        for node_id, node in workflow.items()
        if node["class_type"] == "LoadVideo"
    ]
    assert "ref_audios.ref_audio_0" not in inputs or audio_references
    assert "ref_videos.ref_video_0" not in inputs or video_references
    assert sum(
        node["class_type"] == "LoadAudio" for node in workflow.values()
    ) == len(audio_references)
    assert sum(
        node["class_type"] == "LoadVideo" for node in workflow.values()
    ) == len(video_references)
    assert sum(
        node["class_type"] == "GetVideoComponents"
        for node in workflow.values()
    ) == len(video_references)


def test_r2v_video_audio_pair_uses_components_audio_output():
    workflow = MiniMaxH3R2VWorkflowLoader.load(
        prompt="scene",
        references=["character.png"],
        video_references=["reference.mp4"],
    )

    inputs = workflow["6"]["inputs"]
    components_id = inputs["ref_videos.ref_video_0"][0]
    assert inputs["ref_videos.ref_video_0"] == [components_id, 0]
    assert inputs["ref_video_audios.ref_video_audio_0"] == [
        components_id,
        1,
    ]


def test_r2v_media_nodes_do_not_collide_with_template_or_image_nodes():
    workflow = MiniMaxH3R2VWorkflowLoader.load(
        prompt="scene",
        references=[f"image-{index}.png" for index in range(9)],
        audio_references=["one.wav", "two.wav", "three.wav"],
        video_references=["one.mp4", "two.mp4", "three.mp4"],
    )

    assert len(workflow) == len(set(workflow))
    dynamic_ids = {
        node_id
        for node_id, node in workflow.items()
        if node["class_type"] in {
            "LoadAudio",
            "LoadVideo",
            "GetVideoComponents",
        }
    }
    assert dynamic_ids.isdisjoint({str(index) for index in range(2, 30)})
    assert dynamic_ids == {
        "30",
        "31",
        "32",
        "33",
        "34",
        "35",
        "36",
        "37",
        "38",
    }


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
