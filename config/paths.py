from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

PROJECTS = ROOT / "projects"

WORKFLOWS = ROOT / "workflows"

OUTPUTS = ROOT / "outputs"

MODELS = ROOT / "models"

LOGS = ROOT / "logs"

VOICE_REFERENCES = OUTPUTS / "voice_references"

VOICE_AUDIO = OUTPUTS / "audio"

CHATTERBOX_MODEL_DIR = MODELS / "chatterbox-telugu"