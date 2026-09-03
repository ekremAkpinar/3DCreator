from __future__ import annotations

import sys

import requests

BASE_URL = "http://127.0.0.1:8188"
EXPECTED_NODES = (
    "Trellis2LoadImageWithTransparency",
    "Trellis2LoadModel",
    "Trellis2ShapeGenerator",
    "Trellis2ShapeMultiViewGenerator",
    "Trellis2SelectImagesForMultiView",
    "Trellis2DecodeLatents",
    "Trellis2ExportMesh",
)


def main() -> int:
    print("=== 3DCreator ComfyUI Nodecheck ===")
    try:
        system = requests.get(f"{BASE_URL}/system_stats", timeout=3)
        system.raise_for_status()
    except Exception as exc:
        print(f"[INFO] ComfyUI ist nicht gestartet: {exc}")
        print("Der Offline-Importcheck wird trotzdem von check-system.bat ausgefuehrt.")
        return 0

    print("[OK] ComfyUI ist online.")
    missing: list[str] = []
    for node in EXPECTED_NODES:
        try:
            response = requests.get(f"{BASE_URL}/object_info/{node}", timeout=5)
            response.raise_for_status()
            payload = response.json()
            if node in payload:
                print(f"  [OK] {node}")
            else:
                print(f"  [FEHLT] {node}")
                missing.append(node)
        except Exception as exc:
            print(f"  [FEHLER] {node}: {exc}")
            missing.append(node)

    if missing:
        print("\n[FEHLER] ComfyUI laeuft, aber TRELLIS ist nicht vollstaendig registriert.")
        print("Fuehre aus: powershell -ExecutionPolicy Bypass -File .\\repair-amd-backend.ps1")
        return 1

    print("\n[OK] Alle fuer 3DCreator benoetigten TRELLIS-Nodes sind in ComfyUI registriert.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
