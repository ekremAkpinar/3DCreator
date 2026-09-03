from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

BROKEN_IMPORT = "from .trellis2_profiler import NODE_CLASS_MAPPINGS as _P_MAP, NODE_DISPLAY_NAME_MAPPINGS as _P_DMAP"
BROKEN_UPDATE = "NODE_CLASS_MAPPINGS.update(_P_MAP); NODE_DISPLAY_NAME_MAPPINGS.update(_P_DMAP)"
PATCH_COMMENT = "# 3DCreator compatibility patch: upstream AMD nodes.py references missing trellis2_profiler.py."
UPSTREAM_COMMIT_WITH_BUG = "3aa728ad71b6f892a4c3074e5a38c17dd9f0eec5"
UPSTREAM_PARENT = "98da6e7da2325549ff4e7adbf822098d566a571f"


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: patch_trellis_upstream.py <ComfyUI-Trellis2-AMD-dir>")
        return 2

    custom = Path(sys.argv[1]).resolve()
    nodes = custom / "nodes.py"
    profiler = custom / "trellis2_profiler.py"
    manifest = custom / ".3dcreator_patch.json"

    if not nodes.exists():
        print(f"[FEHLER] nodes.py fehlt: {nodes}")
        return 1

    text = nodes.read_text(encoding="utf-8")

    if profiler.exists():
        print("[OK] trellis2_profiler.py ist vorhanden; kein 3DCreator-Patch notwendig.")
        return 0

    has_import = BROKEN_IMPORT in text
    has_update = BROKEN_UPDATE in text
    if not has_import and not has_update:
        print("[OK] Kein kaputter trellis2_profiler-Verweis gefunden; kein Patch notwendig.")
        return 0

    backup = custom / "nodes.py.3dcreator-upstream.bak"
    if not backup.exists():
        shutil.copy2(nodes, backup)

    lines = text.splitlines()
    patched: list[str] = []
    removed = 0
    for line in lines:
        stripped = line.strip()
        if stripped == BROKEN_IMPORT or stripped == BROKEN_UPDATE:
            removed += 1
            continue
        patched.append(line)

    # Defensive cleanup for partially patched files or unusual line endings/spacing.
    joined = "\n".join(patched)
    joined = joined.replace(BROKEN_IMPORT, "")
    joined = joined.replace(BROKEN_UPDATE, "")
    patched = [line for line in joined.splitlines() if line.strip()]

    if PATCH_COMMENT not in patched:
        patched.append("")
        patched.append(PATCH_COMMENT)

    nodes.write_text("\n".join(patched).rstrip() + "\n", encoding="utf-8")

    remaining = nodes.read_text(encoding="utf-8")
    if "trellis2_profiler" in remaining or "_P_MAP" in remaining or "_P_DMAP" in remaining:
        print("[FEHLER] Profiler-Verweis ist nach dem Patch noch vorhanden.")
        return 1

    manifest.write_text(
        json.dumps(
            {
                "patch": "remove_missing_trellis2_profiler_import",
                "applied_at": datetime.now(timezone.utc).isoformat(),
                "reason": "Upstream AMD nodes.py imports trellis2_profiler.py, but that file is absent from the repository.",
                "removed_lines": removed,
                "recovered_partial_patch": bool(has_import) != bool(has_update),
                "backup": backup.name,
                "upstream_commit_with_bug": UPSTREAM_COMMIT_WITH_BUG,
                "known_parent_without_import": UPSTREAM_PARENT,
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    print(f"[PATCH] Kaputte Profiler-Verweise entfernt ({removed} direkte Zeilen).")
    print(f"[PATCH] Backup: {backup}")
    print(f"[PATCH] Manifest: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
