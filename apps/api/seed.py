from __future__ import annotations

import json
from pathlib import Path

from apps.api.storage import FileStore


SEED_ROOT = Path(__file__).resolve().parent / "seeds"
SEED_PROFILES_DIR = SEED_ROOT / "profiles"
SEED_WORKFLOWS_DIR = SEED_ROOT / "workflows"


def ensure_seed_data(store: FileStore) -> None:
    store.ensure_dirs()

    for seed_path in sorted(SEED_PROFILES_DIR.glob("*.toml")):
        target_path = store.profiles_dir / seed_path.name
        if not target_path.exists():
            target_path.write_text(seed_path.read_text(encoding="utf-8"), encoding="utf-8")

    for seed_path in sorted(SEED_WORKFLOWS_DIR.glob("*.json")):
        target_path = store.workflows_dir / seed_path.name
        if not target_path.exists():
            payload = json.loads(seed_path.read_text(encoding="utf-8"))
            target_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
