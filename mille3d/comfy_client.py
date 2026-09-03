from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import requests


class ComfyError(RuntimeError):
    pass


class ComfyClient:
    IMAGE_NODE_TYPES = {"LoadImage", "Trellis2LoadImageWithTransparency"}
    MULTIVIEW_SELECTOR = "Trellis2SelectImagesForMultiView"
    MULTIVIEW_KEYS = ("front", "back", "left", "right")
    REQUIRED_TRELLIS_NODES = (
        "Trellis2LoadImageWithTransparency",
        "Trellis2LoadModel",
        "Trellis2ShapeGenerator",
        "Trellis2ShapeMultiViewGenerator",
        "Trellis2SelectImagesForMultiView",
        "Trellis2DecodeLatents",
        "Trellis2ExportMesh",
    )

    def __init__(self, base_url: str, timeout: int = 20):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def trellis_node_status(self) -> dict[str, Any]:
        missing: list[str] = []
        errors: dict[str, str] = {}
        for node in self.REQUIRED_TRELLIS_NODES:
            try:
                response = requests.get(f"{self.base_url}/object_info/{node}", timeout=4)
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict) or node not in payload:
                    missing.append(node)
            except Exception as exc:
                missing.append(node)
                errors[node] = str(exc)
        return {
            "ready": not missing,
            "missing": missing,
            "errors": errors,
        }

    def status(self) -> dict[str, Any]:
        try:
            response = requests.get(f"{self.base_url}/system_stats", timeout=3)
            response.raise_for_status()
            nodes = self.trellis_node_status()
            return {
                "online": True,
                "trellis_ready": nodes["ready"],
                "missing_nodes": nodes["missing"],
                "node_errors": nodes["errors"],
                "data": response.json(),
            }
        except Exception as exc:
            return {
                "online": False,
                "trellis_ready": False,
                "missing_nodes": list(self.REQUIRED_TRELLIS_NODES),
                "error": str(exc),
            }

    def upload_image(self, image_path: Path) -> str:
        with image_path.open("rb") as handle:
            response = requests.post(
                f"{self.base_url}/upload/image",
                files={"image": (image_path.name, handle, "application/octet-stream")},
                data={"overwrite": "true"},
                timeout=120,
            )
        response.raise_for_status()
        payload = response.json()
        return payload.get("name", image_path.name)

    @staticmethod
    def load_workflow(path: Path) -> dict[str, Any]:
        if not path.exists():
            raise ComfyError(f"API-Workflow fehlt: {path}.")
        with path.open("r", encoding="utf-8") as handle:
            workflow = json.load(handle)
        if not isinstance(workflow, dict):
            raise ComfyError("Workflow muss ein ComfyUI API-JSON-Objekt sein.")
        return workflow

    @classmethod
    def image_nodes(cls, workflow: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
        nodes = [
            (str(key), node)
            for key, node in workflow.items()
            if isinstance(node, dict) and node.get("class_type") in cls.IMAGE_NODE_TYPES
        ]

        def sort_key(item: tuple[str, dict[str, Any]]):
            key = item[0]
            return (0, int(key)) if key.isdigit() else (1, key)

        nodes.sort(key=sort_key)
        return nodes

    @classmethod
    def multiview_selectors(cls, workflow: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            node
            for node in workflow.values()
            if isinstance(node, dict) and node.get("class_type") == cls.MULTIVIEW_SELECTOR
        ]

    @classmethod
    def image_capacity(cls, workflow: dict[str, Any]) -> int:
        selectors = cls.multiview_selectors(workflow)
        if selectors:
            return len(cls.MULTIVIEW_KEYS)
        return len(cls.image_nodes(workflow))

    @classmethod
    def inject_views(cls, workflow: dict[str, Any], views: dict[str, str]) -> None:
        selectors = cls.multiview_selectors(workflow)
        if selectors:
            selector_inputs = selectors[0].setdefault("inputs", {})
            for key in cls.MULTIVIEW_KEYS:
                selector_inputs[key] = views.get(key, "")
            if not selector_inputs.get("front"):
                raise ComfyError("Der MultiView-Workflow benoetigt eine Frontansicht.")
            return

        ordered = [views[key] for key in ("front", "right", "back", "left") if views.get(key)]
        cls.inject_images(workflow, ordered)

    @classmethod
    def inject_images(cls, workflow: dict[str, Any], image_names: list[str]) -> None:
        load_nodes = cls.image_nodes(workflow)
        if not load_nodes:
            supported = ", ".join(sorted(cls.IMAGE_NODE_TYPES))
            raise ComfyError(f"Kein unterstuetzter Bildknoten im API-Workflow gefunden ({supported}).")
        if len(image_names) > len(load_nodes):
            raise ComfyError(
                f"Workflow hat {len(load_nodes)} Bildknoten, aber {len(image_names)} Ansichten wurden uebergeben."
            )
        for (_, node), image_name in zip(load_nodes, image_names):
            node.setdefault("inputs", {})["image"] = image_name

    @classmethod
    def inject_image(cls, workflow: dict[str, Any], image_name: str) -> None:
        cls.inject_images(workflow, [image_name])

    def queue(self, workflow: dict[str, Any]) -> str:
        nodes = self.trellis_node_status()
        if not nodes["ready"]:
            missing = ", ".join(nodes["missing"][:4])
            if len(nodes["missing"]) > 4:
                missing += f" (+{len(nodes['missing']) - 4} weitere)"
            raise ComfyError(
                "ComfyUI laeuft, aber das TRELLIS-AMD-Plugin ist nicht vollstaendig registriert. "
                f"Fehlende Nodes: {missing}. Schliesse das Backend-Fenster und fuehre "
                "repair-amd-backend.ps1 aus."
            )

        response = requests.post(f"{self.base_url}/prompt", json={"prompt": workflow}, timeout=self.timeout)
        if not response.ok:
            raise ComfyError(f"ComfyUI /prompt: {response.status_code} {response.text[:1000]}")
        payload = response.json()
        prompt_id = payload.get("prompt_id")
        if not prompt_id:
            raise ComfyError(f"ComfyUI lieferte keine prompt_id: {payload}")
        return prompt_id

    def wait_history(self, prompt_id: str, timeout_s: int = 1800) -> dict[str, Any]:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            response = requests.get(f"{self.base_url}/history/{prompt_id}", timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            if prompt_id in data:
                return data[prompt_id]
            time.sleep(2)
        raise ComfyError(f"Timeout nach {timeout_s}s fuer Prompt {prompt_id}")

    @staticmethod
    def find_3d_files(history: dict[str, Any]) -> list[dict[str, str]]:
        found: list[dict[str, str]] = []
        valid = (".glb", ".gltf", ".obj", ".ply", ".stl")

        def walk(value: Any) -> None:
            if isinstance(value, dict):
                filename = value.get("filename")
                if isinstance(filename, str) and filename.lower().endswith(valid):
                    found.append(
                        {
                            "filename": filename,
                            "subfolder": str(value.get("subfolder", "")),
                            "type": str(value.get("type", "output")),
                        }
                    )
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(history.get("outputs", history))
        unique = {(x["filename"], x["subfolder"], x["type"]): x for x in found}
        return list(unique.values())

    def download_output(self, ref: dict[str, str], destination: Path) -> Path:
        response = requests.get(f"{self.base_url}/view", params=ref, timeout=300)
        response.raise_for_status()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(response.content)
        return destination
