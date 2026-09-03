from __future__ import annotations

import sys

print("3DCreator AMD Check")
print("Python:", sys.version.replace("\n", " "))
try:
    import torch
    print("Torch:", torch.__version__)
    print("HIP/ROCm:", torch.version.hip)
    print("GPU API verfuegbar:", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("GPU:", torch.cuda.get_device_name(0))
        props = torch.cuda.get_device_properties(0)
        print("VRAM GiB:", round(props.total_memory / 1024**3, 2))
        if "6800 XT" in torch.cuda.get_device_name(0):
            print("OK: RX 6800 XT erkannt (gfx1030-Familie).")
    else:
        print("FEHLER: Torch sieht keine GPU. ROCm/Torch-Installation pruefen.")
except Exception as exc:
    print("FEHLER:", repr(exc))
