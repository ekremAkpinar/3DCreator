from __future__ import annotations

import importlib.metadata
import importlib.util
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMFY = ROOT / "runtime" / "ComfyUI"
PLUGIN = COMFY / "custom_nodes" / "ComfyUI-Trellis2-AMD"
EXPECTED_NODES = {
    "Trellis2LoadImageWithTransparency",
    "Trellis2LoadModel",
    "Trellis2ShapeGenerator",
    "Trellis2ShapeMultiViewGenerator",
    "Trellis2SelectImagesForMultiView",
    "Trellis2DecodeLatents",
    "Trellis2ExportMesh",
}
PACKAGES_TO_REPORT = [
    "torch",
    "torchvision",
    "triton-windows",
    "aule-attention",
    "meshlib",
    "pymeshlab",
    "open3d",
    "opencv-python",
    "opencv-python-headless",
]


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "FEHLT"
    except Exception as exc:
        return f"FEHLER: {exc}"


def main() -> int:
    print("=== 3DCreator TRELLIS Plugin Importcheck ===")
    print("ComfyUI:", COMFY)
    print("Plugin:", PLUGIN)

    if not (COMFY / "folder_paths.py").exists():
        print("[FEHLER] ComfyUI ist nicht vollstaendig vorhanden.")
        return 2
    if not (PLUGIN / "__init__.py").exists():
        print("[FEHLER] ComfyUI-Trellis2-AMD ist nicht im custom_nodes-Ordner vorhanden.")
        return 3

    print("\nInstallierte Kernpakete:")
    for package in PACKAGES_TO_REPORT:
        print(f"  {package}: {package_version(package)}")

    # The custom node imports ComfyUI modules such as folder_paths. Put the
    # local ComfyUI checkout on sys.path, then import the plugin as a package.
    sys.path.insert(0, str(COMFY))
    module_name = "threedcreator_trellis2_amd_check"
    init_file = PLUGIN / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        module_name,
        init_file,
        submodule_search_locations=[str(PLUGIN)],
    )
    if spec is None or spec.loader is None:
        print("[FEHLER] Python konnte keinen Import-Spec fuer das TRELLIS-Plugin erstellen.")
        return 4

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        print("\n[FEHLER] TRELLIS-Custom-Node kann nicht importiert werden.")
        print("Das ist der eigentliche Grund fuer 'missing_node_type'.")
        print("\n--- Python Traceback ---")
        traceback.print_exc()
        print("--- Ende Traceback ---")
        return 5

    mappings = getattr(module, "NODE_CLASS_MAPPINGS", {})
    if not isinstance(mappings, dict):
        print("[FEHLER] Plugin wurde importiert, liefert aber keine NODE_CLASS_MAPPINGS.")
        return 6

    missing = sorted(EXPECTED_NODES - set(mappings))
    if missing:
        print("[FEHLER] Plugin importiert, aber erwartete Nodes fehlen:")
        for node in missing:
            print("  -", node)
        return 7

    print("\n[OK] TRELLIS-Plugin importiert erfolgreich.")
    print(f"Registrierte TRELLIS-Nodes: {len([k for k in mappings if str(k).startswith('Trellis2')])}")
    for node in sorted(EXPECTED_NODES):
        print("  [OK]", node)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
