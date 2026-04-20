import os
from pathlib import Path


DATA_ROOT = Path(os.getenv("HAWK_DATA_ROOT", "data")).expanduser().resolve()
WORKFLOWS_DIR = DATA_ROOT / "workflows"
PROFILES_DIR = DATA_ROOT / "profiles"
RUNS_DIR = DATA_ROOT / "runs"
SETTINGS_DIR = DATA_ROOT / "settings"
TEMPLATES_DIR = DATA_ROOT / "templates"
