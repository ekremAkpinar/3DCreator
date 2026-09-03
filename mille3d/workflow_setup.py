from __future__ import annotations

import copy
import json
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from .config import WORKFLOWS_DIR, ensure_dirs

SOURCE_REPOSITORY = "visualbruno/3DGenStudio"
SOURCE_COMMIT = "6b385dff7f32fd12436b9dcc6f4a6751f89ff103"
SOURCE_LICENSE = "https://github.com/visualbruno/3DGenStudio/blob/6b385dff7f32fd12436b9dcc6f4a6751f89ff103/LICENSE"
SOURCE_SINGLE_PATH = "setup/Gen Mesh Only with Trellis2.json"
SOURCE_MULTI_PATH = "setup/Gen MultiView Mesh Only with Trellis2.json"


def _raw_url(path: str) -> str:
    quoted = "/".join(urllib.parse.quote(part) for part in path.split("/"))
    return f"https://raw.githubusercontent.com/visualbruno/3DGenStudio/{SOURCE_COMMIT}/{quoted}"


def _download_json(path: str) -> dict[str, Any]:
    request = urllib.request.Request(
        _raw_url(path),
        headers={"User-Agent": "Mille3D-local-workflow-setup/0.2.1"},
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Ungueltiger Workflow von {path}")
    return payload


def _find_nodes(workflow: dict[str, Any], class_type: str) -> list[tuple[str, dict[str, Any]]]:
    return [
        (str(node_id), node)
        for node_id, node in workflow.items()
        if isinstance(node, dict) and node.get("class_type") == class_type
    ]


def _one(workflow: dict[str, Any], class_type: str) -> tuple[str, dict[str, Any]]:
    nodes = _find_nodes(workflow, class_type)
    if not nodes:
        raise RuntimeError(f"Workflow enthaelt keinen {class_type}-Knoten")
    return nodes[0]


def _patch_amd(workflow: dict[str, Any], filename_prefix: str) -> None:
    for _, node in _find_nodes(workflow, "Trellis2LoadModel"):
        inputs = node.setdefault("inputs", {})
        inputs["modelname"] = "microsoft/TRELLIS.2-4B"
        inputs["backend"] = "aule"
        inputs["device"] = "cuda"
        inputs["low_vram"] = True
        inputs["keep_models_loaded"] = False
        inputs["conv_backend"] = "flex_gemm"
        inputs["sparse_backend"] = "aule"
        inputs["use_reconviagen"] = False

    for _, node in _find_nodes(workflow, "Trellis2ExportMesh"):
        inputs = node.setdefault("inputs", {})
        inputs["filename_prefix"] = filename_prefix
        inputs["file_format"] = "glb"


def _make_single_512(workflow: dict[str, Any]) -> None:
    shape_id, _ = _one(workflow, "Trellis2ShapeGenerator")
    _, decode = _one(workflow, "Trellis2DecodeLatents")
    decode_inputs = decode.setdefault("inputs", {})
    decode_inputs["resolution"] = [shape_id, 1]
    decode_inputs["pipeline"] = [shape_id, 2]
    decode_inputs["shape_slat"] = [shape_id, 0]

    for _, reconstruct in _find_nodes(workflow, "Trellis2ReconstructMeshWithQuad"):
        reconstruct.setdefault("inputs", {})["resolution"] = 512


def _make_multiview_512(workflow: dict[str, Any]) -> None:
    shape_id, _ = _one(workflow, "Trellis2ShapeMultiViewGenerator")
    _, decode = _one(workflow, "Trellis2DecodeLatents")
    decode_inputs = decode.setdefault("inputs", {})
    decode_inputs["resolution"] = [shape_id, 1]
    decode_inputs["pipeline"] = [shape_id, 3]
    decode_inputs["shape_slat"] = [shape_id, 0]

    for _, reconstruct in _find_nodes(workflow, "Trellis2ReconstructMeshWithQuad"):
        reconstruct.setdefault("inputs", {})["resolution"] = 512


def _validate(workflow: dict[str, Any], multiview: bool) -> None:
    _one(workflow, "Trellis2LoadModel")
    _one(workflow, "Trellis2ExportMesh")
    _one(workflow, "Trellis2DecodeLatents")
    if multiview:
        _one(workflow, "Trellis2SelectImagesForMultiView")
        _one(workflow, "Trellis2ShapeMultiViewGenerator")
    else:
        _one(workflow, "Trellis2LoadImageWithTransparency")
        _one(workflow, "Trellis2ShapeGenerator")


def _write(path: Path, workflow: dict[str, Any], force: bool) -> str:
    if path.exists() and not force:
        return "vorhanden"
    path.write_text(json.dumps(workflow, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return "erstellt"


def setup_workflows(force: bool = False) -> dict[str, Any]:
    ensure_dirs()
    targets = {
        "single_512": WORKFLOWS_DIR / "mesh_only_512_api.json",
        "single_1024": WORKFLOWS_DIR / "mesh_only_1024_api.json",
        "multiview_512": WORKFLOWS_DIR / "mesh_multiview_512_api.json",
        "multiview_1024": WORKFLOWS_DIR / "mesh_multiview_1024_api.json",
    }

    if not force and all(path.exists() for path in targets.values()):
        return {
            "ok": True,
            "downloaded": False,
            "source": SOURCE_REPOSITORY,
            "license": SOURCE_LICENSE,
            "files": {key: {"path": str(path), "status": "vorhanden"} for key, path in targets.items()},
        }

    single_source = _download_json(SOURCE_SINGLE_PATH)
    multi_source = _download_json(SOURCE_MULTI_PATH)
    _validate(single_source, multiview=False)
    _validate(multi_source, multiview=True)

    single_512 = copy.deepcopy(single_source)
    _patch_amd(single_512, "Mille3D_single_512")
    _make_single_512(single_512)

    single_1024 = copy.deepcopy(single_source)
    _patch_amd(single_1024, "Mille3D_single_1024")

    multiview_512 = copy.deepcopy(multi_source)
    _patch_amd(multiview_512, "Mille3D_multiview_512")
    _make_multiview_512(multiview_512)

    multiview_1024 = copy.deepcopy(multi_source)
    _patch_amd(multiview_1024, "Mille3D_multiview_1024")

    generated = {
        "single_512": single_512,
        "single_1024": single_1024,
        "multiview_512": multiview_512,
        "multiview_1024": multiview_1024,
    }
    states = {
        key: {"path": str(targets[key]), "status": _write(targets[key], workflow, force)}
        for key, workflow in generated.items()
    }

    source_note = WORKFLOWS_DIR / "UPSTREAM_SOURCE.txt"
    source_note.write_text(
        "Mille 3D generated these local workflow profiles from upstream files downloaded directly on this machine.\n"
        f"Repository: https://github.com/{SOURCE_REPOSITORY}\n"
        f"Pinned commit: {SOURCE_COMMIT}\n"
        f"Single source: {SOURCE_SINGLE_PATH}\n"
        f"MultiView source: {SOURCE_MULTI_PATH}\n"
        f"Upstream license: {SOURCE_LICENSE}\n"
        "The downloaded upstream workflow files are not bundled in the Mille GitHub repository.\n",
        encoding="utf-8",
    )

    return {
        "ok": True,
        "downloaded": True,
        "source": SOURCE_REPOSITORY,
        "source_commit": SOURCE_COMMIT,
        "license": SOURCE_LICENSE,
        "files": states,
    }
