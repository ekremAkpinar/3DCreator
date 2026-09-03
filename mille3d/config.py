from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime"
DATA_DIR = RUNTIME / "data"
PROJECTS_DIR = RUNTIME / "projects"
WORKFLOWS_DIR = RUNTIME / "workflows"
DB_PATH = DATA_DIR / "mille3d.sqlite3"

COMFY_URL = os.getenv("MILLE_COMFY_URL", "http://127.0.0.1:8188").rstrip("/")
WORKFLOW_PATH = Path(os.getenv("MILLE_WORKFLOW", str(WORKFLOWS_DIR / "mesh_only_api.json")))
BLENDER_PATH = os.getenv("MILLE_BLENDER", "").strip()


def ensure_dirs() -> None:
    for path in (DATA_DIR, PROJECTS_DIR, WORKFLOWS_DIR):
        path.mkdir(parents=True, exist_ok=True)


def workflow_for(mode: str, quality: str) -> Path:
    if mode == "multiview":
        candidates = [
            WORKFLOWS_DIR / f"mesh_multiview_{quality}_api.json",
            WORKFLOWS_DIR / "mesh_multiview_api.json",
        ]
    else:
        candidates = [
            WORKFLOWS_DIR / f"mesh_only_{quality}_api.json",
            WORKFLOW_PATH,
        ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def workflow_for_quality(quality: str, multiview: bool = False) -> Path:
    return workflow_for("multiview" if multiview else "single", quality)
