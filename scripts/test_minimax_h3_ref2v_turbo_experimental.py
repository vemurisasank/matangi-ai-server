import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
COMFY_INPUT_DIR = Path("/workspace/ComfyUI/input")
sys.path.insert(0, str(REPOSITORY_ROOT))

from providers.comfyui.client import ComfyUIClient
from providers.comfyui.minimax_h3_r2v_ref2v_turbo_experimental_loader import (
    MiniMaxH3R2VRef2VTurboExperimentalLoader,
)
from providers.comfyui.provider import ComfyUIProvider


def _timestamp():
    return datetime.now(timezone.utc).isoformat()


def _build_parser():
    parser = argparse.ArgumentParser(
        description="Submit the isolated MiniMax H3 Ref2V Turbo workflow once."
    )
    parser.add_argument("--prompt", required=True)
    parser.add_argument(
        "--reference",
        action="append",
        dest="references",
        required=True,
        help=(
            "Reference filename or path already available in ComfyUI input/. "
            "Repeat 1-9 times; use three for the first test."
        ),
    )
    parser.add_argument("--seed", type=int, default=20261008)
    parser.add_argument("--poll-interval", type=float, default=2.0)
    parser.add_argument("--timeout", type=float, default=3600.0)
    return parser


def _validate_references(references):
    if not 1 <= len(references) <= 9:
        raise ValueError("Provide between 1 and 9 references.")
    normalized = []
    for reference in references:
        path = Path(reference)
        if not path.name:
            raise ValueError(f"Invalid reference path: {reference!r}")
        input_path = COMFY_INPUT_DIR / path.name
        if not input_path.is_file():
            raise FileNotFoundError(
                f"Reference is not staged in ComfyUI input/: {input_path}"
            )
        normalized.append(path.name)
    return normalized


def _wait_for_result(client, prompt_id, interval, timeout):
    started = time.monotonic()
    while True:
        if time.monotonic() - started > timeout:
            raise TimeoutError(
                f"Timed out waiting for ComfyUI prompt {prompt_id}."
            )
        history = client.get_history(prompt_id)
        if history is not None:
            status = history.get("status", {})
            status_string = status.get("status_str")
            if status_string in {"error", "failed"}:
                raise RuntimeError(
                    f"ComfyUI execution failed: "
                    f"{status.get('messages', status)}"
                )
            if status.get("completed") or status_string == "success":
                return history
        time.sleep(interval)


def main():
    args = _build_parser().parse_args()
    references = _validate_references(args.references)
    loader = MiniMaxH3R2VRef2VTurboExperimentalLoader
    workflow = loader.load(
        prompt=args.prompt,
        references=references,
        seed=args.seed,
    )

    client = ComfyUIClient()
    submitted_at = _timestamp()
    started = time.monotonic()
    prompt_id = client.queue_prompt(workflow)
    print(f"prompt_id={prompt_id}")
    print(f"submitted_at={submitted_at}")

    result = _wait_for_result(
        client,
        prompt_id,
        interval=args.poll_interval,
        timeout=args.timeout,
    )
    ended_at = _timestamp()
    elapsed = time.monotonic() - started
    output = ComfyUIProvider.find_video_output(result)
    if output is None:
        raise RuntimeError("ComfyUI completed without a video output.")

    output_root = Path("/workspace/ComfyUI/output").resolve()
    output_path = (
        output_root
        / output.get("subfolder", "")
        / output["filename"]
    ).resolve()
    if output_root not in output_path.parents:
        raise RuntimeError(f"ComfyUI output escaped output directory: {output_path}")

    print(f"ended_at={ended_at}")
    print(f"execution_seconds={elapsed:.3f}")
    print(f"output_filename={output['filename']}")
    print(f"output_subfolder={output.get('subfolder', '')}")
    print(f"output_path={output_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
