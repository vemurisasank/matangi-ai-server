from pathlib import Path


TELUGU_T3_MODEL = "t3_mtl_te.safetensors"
TELUGU_T3_VOCAB_SIZE = 2521
TELUGU_TOKEN = "[te]"
TELUGU_TOKEN_ID = 2520
REQUIRED_MODEL_FILES = (
    TELUGU_T3_MODEL,
    "s3gen.pt",
    "ve.pt",
    "grapheme_mtl_merged_expanded_v1.json",
)


def _load_torch_state(torch, path, map_location):
    try:
        return torch.load(
            path,
            map_location=map_location,
            weights_only=True,
        )
    except TypeError:
        return torch.load(path, map_location=map_location)


def _load_dependencies():
    import torch
    import chatterbox.mtl_tts as mtl_tts
    from chatterbox.models.s3gen import S3Gen
    from chatterbox.models.t3 import T3
    from chatterbox.models.t3.modules.t3_config import T3Config
    from chatterbox.models.tokenizers import MTLTokenizer
    from chatterbox.models.voice_encoder import VoiceEncoder
    from safetensors.torch import load_file as load_safetensors

    return (
        torch,
        mtl_tts,
        S3Gen,
        T3,
        T3Config,
        MTLTokenizer,
        VoiceEncoder,
        load_safetensors,
    )


def _validate_model_files(model_path):
    if not model_path.is_dir():
        raise RuntimeError("Chatterbox Telugu model directory is unavailable.")
    missing = [
        filename
        for filename in REQUIRED_MODEL_FILES
        if not (model_path / filename).is_file()
    ]
    if missing:
        raise RuntimeError(
            "Chatterbox Telugu model files are missing: " + ", ".join(missing)
        )


def _unwrap_checkpoint_state(state):
    if "model" not in state:
        return state
    wrapped = state["model"]
    if isinstance(wrapped, (list, tuple)):
        if len(wrapped) != 1:
            raise RuntimeError("Telugu T3 checkpoint has an invalid model wrapper.")
        return wrapped[0]
    return wrapped


def load_telugu_model(model_path, device, checkpoint_name=TELUGU_T3_MODEL):
    model_path = Path(model_path)
    if checkpoint_name != TELUGU_T3_MODEL:
        raise RuntimeError(
            f"Unsupported Chatterbox Telugu checkpoint: {checkpoint_name}"
        )
    _validate_model_files(model_path)

    (
        torch,
        mtl_tts,
        S3Gen,
        T3,
        T3Config,
        MTLTokenizer,
        VoiceEncoder,
        load_safetensors,
    ) = _load_dependencies()
    map_location = torch.device("cpu") if device in {"cpu", "mps"} else None

    voice_encoder = VoiceEncoder()
    voice_encoder.load_state_dict(
        _load_torch_state(torch, model_path / "ve.pt", map_location)
    )
    voice_encoder.to(device).eval()

    t3 = T3(T3Config(text_tokens_dict_size=TELUGU_T3_VOCAB_SIZE))
    t3_state = load_safetensors(model_path / checkpoint_name)
    t3.load_state_dict(_unwrap_checkpoint_state(t3_state))
    t3.to(device).eval()

    s3gen = S3Gen()
    s3gen.load_state_dict(
        _load_torch_state(torch, model_path / "s3gen.pt", map_location)
    )
    s3gen.to(device).eval()

    tokenizer = MTLTokenizer(
        str(model_path / "grapheme_mtl_merged_expanded_v1.json")
    )
    vocabulary = tokenizer.tokenizer.get_vocab()
    if vocabulary.get(TELUGU_TOKEN) != TELUGU_TOKEN_ID:
        raise RuntimeError(
            "Chatterbox Telugu tokenizer must map [te] to token ID 2520."
        )

    conds = None
    builtin_voice = model_path / "conds.pt"
    if builtin_voice.is_file():
        conds = mtl_tts.Conditionals.load(
            builtin_voice,
            map_location=map_location,
        ).to(device)

    return mtl_tts.ChatterboxMultilingualTTS(
        t3,
        s3gen,
        voice_encoder,
        tokenizer,
        device,
        conds=conds,
    )
