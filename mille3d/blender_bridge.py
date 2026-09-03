from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .config import BLENDER_PATH, ROOT


def find_blender() -> Path | None:
    candidates: list[Path] = []
    if BLENDER_PATH:
        candidates.append(Path(BLENDER_PATH))

    on_path = shutil.which("blender")
    if on_path:
        candidates.append(Path(on_path))

    for root in [Path(r"C:\Program Files\Blender Foundation"), Path(r"C:\Program Files (x86)\Blender Foundation")]:
        if root.exists():
            candidates.extend(sorted(root.glob("Blender */blender.exe"), reverse=True))
            candidates.extend(root.glob("blender.exe"))

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def blender_status() -> dict:
    blender = find_blender()
    return {
        "available": blender is not None,
        "path": str(blender) if blender else None,
        "configured": bool(BLENDER_PATH),
    }


def repair_mesh(source: Path, target: Path) -> tuple[bool, str]:
    blender = find_blender()
    if blender is None:
        return False, "Blender wurde nicht gefunden. Installiere Blender oder setze MILLE_BLENDER auf den Pfad zu blender.exe."

    script = ROOT / "tools" / "blender_repair.py"
    if not script.exists():
        return False, f"Blender-Reparaturskript fehlt: {script}"

    cmd = [
        str(blender),
        "--background",
        "--factory-startup",
        "--python",
        str(script),
        "--",
        str(source),
        str(target),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1200, check=False)
    except subprocess.TimeoutExpired:
        return False, "Blender-Reparatur nach 20 Minuten abgebrochen."

    log = (result.stdout + "\n" + result.stderr).strip()[-8000:]
    if result.returncode != 0:
        return False, log or f"Blender endete mit Code {result.returncode}."
    return target.exists(), log
