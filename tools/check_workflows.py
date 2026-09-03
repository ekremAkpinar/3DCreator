from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mille3d.config import workflow_for


def node_by_type(workflow: dict, class_type: str):
    for node_id, node in workflow.items():
        if isinstance(node, dict) and node.get("class_type") == class_type:
            return str(node_id), node
    return None, None


def check(mode: str, quality: str) -> list[str]:
    errors=[]; path=workflow_for(mode,quality)
    if not path.exists(): return [f"fehlt: {path}"]
    try: workflow=json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc: return [f"ungueltiges JSON: {exc}"]
    _,model=node_by_type(workflow,"Trellis2LoadModel")
    if model is None: errors.append("Trellis2LoadModel fehlt")
    else:
        inputs=model.get("inputs",{}); expected={"backend":"aule","sparse_backend":"aule","conv_backend":"flex_gemm","low_vram":True,"keep_models_loaded":False}
        for key,value in expected.items():
            if inputs.get(key)!=value: errors.append(f"{key}={inputs.get(key)!r}, erwartet {value!r}")
    _,decode=node_by_type(workflow,"Trellis2DecodeLatents")
    if decode is None: errors.append("Trellis2DecodeLatents fehlt")
    if mode=="multiview":
        _,selector=node_by_type(workflow,"Trellis2SelectImagesForMultiView")
        if selector is None: errors.append("Trellis2SelectImagesForMultiView fehlt")
        shape_type="Trellis2ShapeMultiViewGenerator"
    else:
        _,image=node_by_type(workflow,"Trellis2LoadImageWithTransparency")
        if image is None: errors.append("Trellis2LoadImageWithTransparency fehlt")
        shape_type="Trellis2ShapeGenerator"
    shape_id,_=node_by_type(workflow,shape_type)
    if shape_id is None: errors.append(f"{shape_type} fehlt")
    elif quality=="512" and decode is not None:
        pipeline_ref=decode.get("inputs",{}).get("pipeline")
        if not isinstance(pipeline_ref,list) or not pipeline_ref or str(pipeline_ref[0])!=shape_id: errors.append("512-Profil nutzt noch den 1024-Cascade")
    return errors


def main() -> int:
    print("=== 3DCreator Workflowcheck ==="); failed=False
    for mode in ("single","multiview"):
        for quality in ("512","1024"):
            errors=check(mode,quality); label=f"{mode}/{quality}"
            if errors:
                failed=True; print(f"[FEHLER] {label}")
                for error in errors: print(f"  - {error}")
            else: print(f"[OK] {label}")
    if failed:
        print("Tipp: setup-workflows.ps1 ausfuehren oder in 3DCreator Workflows automatisch einrichten."); return 1
    print("Alle lokalen TRELLIS-AMD-Workflows sind bereit."); return 0

if __name__ == "__main__": raise SystemExit(main())
