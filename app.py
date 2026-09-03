from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from mille3d import __version__
from mille3d.blender_bridge import blender_status, repair_mesh
from mille3d.comfy_client import ComfyClient, ComfyError
from mille3d.config import COMFY_URL, PROJECTS_DIR, ROOT, ensure_dirs, workflow_for
from mille3d.db import connect, init_db, rows, utcnow
from mille3d.workflow_setup import setup_workflows

ensure_dirs()
init_db()
app = FastAPI(title="Mille 3D", version=__version__)
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
client = ComfyClient(COMFY_URL)

VIEW_ORDER = ("front", "right", "back", "left")
VIEW_LABELS = {
    "front": "Front",
    "right": "Rechte Seite",
    "back": "Rueckseite",
    "left": "Linke Seite",
}
VALID_QUALITIES = {"512", "1024"}
VALID_MODES = {"single", "multiview"}


class FeedbackIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    note: str = ""
    issues: list[str] = Field(default_factory=list)
    approved_for_learning: bool = False


def _generation(generation_id: str) -> dict:
    result = rows("SELECT * FROM generations WHERE id=?", (generation_id,))
    if not result:
        raise HTTPException(404, "Generation nicht gefunden")
    return result[0]


def _best_file(g: dict, variant: str = "best") -> Path:
    if variant not in {"best", "raw", "repaired"}:
        raise HTTPException(400, "variant muss best, raw oder repaired sein")
    if variant == "raw":
        value = g.get("output_file")
    elif variant == "repaired":
        value = g.get("repaired_file")
    else:
        value = g.get("repaired_file") or g.get("output_file")
    if not value:
        raise HTTPException(404, "Keine passende 3D-Datei vorhanden")
    path = Path(value)
    if not path.exists():
        raise HTTPException(404, "3D-Datei fehlt auf dem Datentraeger")
    return path


def _save_upload(upload: UploadFile, target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("wb") as handle:
        shutil.copyfileobj(upload.file, handle)
    return target


def _run_repair(generation_id: str, raw_path: Path, output_dir: Path) -> dict:
    target = output_dir / "repaired.glb"
    with connect() as conn:
        conn.execute(
            "UPDATE generations SET repair_status='running', repair_log='' WHERE id=?",
            (generation_id,),
        )
    ok, log = repair_mesh(raw_path, target)
    with connect() as conn:
        if ok:
            conn.execute(
                "UPDATE generations SET repaired_file=?, repair_status='done', repair_log=? WHERE id=?",
                (str(target), log, generation_id),
            )
        else:
            conn.execute(
                "UPDATE generations SET repair_status='error', repair_log=? WHERE id=?",
                (log, generation_id),
            )
    return {"ok": ok, "target": str(target) if ok else None, "log": log}


def _ensure_workflow(mode: str, quality: str) -> Path:
    path = workflow_for(mode, quality)
    if path.exists():
        return path
    try:
        setup_workflows(force=False)
    except Exception as exc:
        raise HTTPException(
            503,
            "TRELLIS-Workflow fehlt und die automatische Einrichtung ist fehlgeschlagen: "
            f"{exc}",
        ) from exc
    path = workflow_for(mode, quality)
    if not path.exists():
        raise HTTPException(503, f"Workflow konnte nicht erzeugt werden: {path}")
    return path


@app.get("/")
def index() -> FileResponse:
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/api/status")
def status() -> dict:
    comfy = client.status()
    workflows = {
        f"{mode}_{quality}": {
            "path": str(workflow_for(mode, quality)),
            "exists": workflow_for(mode, quality).exists(),
        }
        for mode in VALID_MODES
        for quality in VALID_QUALITIES
    }
    return {
        "version": __version__,
        "comfy_url": COMFY_URL,
        "comfy": comfy,
        "blender": blender_status(),
        "workflows": workflows,
        "workflow_setup_ready": True,
    }


@app.post("/api/setup/workflows")
def setup_workflows_api(force: bool = False) -> dict:
    try:
        return setup_workflows(force=force)
    except Exception as exc:
        raise HTTPException(500, f"Workflow-Einrichtung fehlgeschlagen: {exc}") from exc


@app.get("/api/projects")
def projects() -> list[dict]:
    return rows("SELECT * FROM projects ORDER BY created_at DESC")


@app.get("/api/generations")
def generations() -> list[dict]:
    items = rows(
        """
        SELECT g.*, p.name AS project_name, p.prompt,
               (SELECT rating FROM feedback f WHERE f.generation_id=g.id ORDER BY f.id DESC LIMIT 1) AS rating,
               (SELECT approved_for_learning FROM feedback f WHERE f.generation_id=g.id ORDER BY f.id DESC LIMIT 1) AS approved_for_learning,
               (SELECT note FROM feedback f WHERE f.generation_id=g.id ORDER BY f.id DESC LIMIT 1) AS feedback_note,
               (SELECT issues_json FROM feedback f WHERE f.generation_id=g.id ORDER BY f.id DESC LIMIT 1) AS issues_json
        FROM generations g
        JOIN projects p ON p.id=g.project_id
        ORDER BY g.created_at DESC LIMIT 100
        """
    )
    for item in items:
        try:
            item["source_images"] = json.loads(item.get("source_images_json") or "[]")
        except json.JSONDecodeError:
            item["source_images"] = []
        try:
            item["issues"] = json.loads(item.get("issues_json") or "[]")
        except json.JSONDecodeError:
            item["issues"] = []
        item["has_raw"] = bool(item.get("output_file"))
        item["has_repaired"] = bool(item.get("repaired_file"))
    return items


@app.get("/api/learning/stats")
def learning_stats() -> dict:
    total = rows("SELECT COUNT(*) AS n FROM feedback")[0]["n"]
    approved = rows("SELECT COUNT(*) AS n FROM feedback WHERE approved_for_learning=1")[0]["n"]
    positive = rows("SELECT COUNT(*) AS n FROM feedback WHERE rating>=4")[0]["n"]
    negative = rows("SELECT COUNT(*) AS n FROM feedback WHERE rating<=2")[0]["n"]
    return {"feedback": total, "approved": approved, "positive": positive, "negative": negative}


@app.post("/api/generate")
def generate(
    name: str = Form(...),
    prompt: str = Form(""),
    quality: str = Form("512"),
    mode: str = Form("single"),
    auto_repair: bool = Form(False),
    front: UploadFile = File(...),
    right: UploadFile | None = File(None),
    back: UploadFile | None = File(None),
    left: UploadFile | None = File(None),
) -> dict:
    if quality not in VALID_QUALITIES:
        raise HTTPException(400, "quality muss 512 oder 1024 sein")
    if mode not in VALID_MODES:
        raise HTTPException(400, "mode muss single oder multiview sein")
    if front is None or not front.filename:
        raise HTTPException(400, "Eine Frontansicht ist erforderlich.")
    if not client.status().get("online"):
        raise HTTPException(503, "ComfyUI ist nicht erreichbar. Backend zuerst starten.")

    uploads = {"front": front, "right": right, "back": back, "left": left}
    selected = [(key, uploads[key]) for key in VIEW_ORDER if uploads[key] and uploads[key].filename]
    if mode == "single":
        selected = [("front", front)]
    elif len(selected) < 2:
        raise HTTPException(400, "MultiView benoetigt Frontansicht plus mindestens eine weitere Ansicht.")

    workflow_path = _ensure_workflow(mode, quality)

    project_id = uuid.uuid4().hex
    generation_id = uuid.uuid4().hex
    project_dir = PROJECTS_DIR / project_id
    input_dir = project_dir / "input"
    output_dir = project_dir / "output"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    sources: list[dict[str, str]] = []
    for view, upload in selected:
        suffix = Path(upload.filename or f"{view}.png").suffix.lower() or ".png"
        source = _save_upload(upload, input_dir / f"{view}{suffix}")
        sources.append({"view": view, "label": VIEW_LABELS[view], "path": str(source)})

    with connect() as conn:
        conn.execute(
            "INSERT INTO projects(id,name,prompt,created_at) VALUES(?,?,?,?)",
            (project_id, name.strip(), prompt.strip(), utcnow()),
        )
        conn.execute(
            """
            INSERT INTO generations(
                id,project_id,status,quality,mode,source_image,source_images_json,
                repair_status,created_at
            ) VALUES(?,?,?,?,?,?,?,?,?)
            """,
            (
                generation_id,
                project_id,
                "queued",
                quality,
                mode,
                sources[0]["path"],
                json.dumps(sources, ensure_ascii=False),
                "pending" if auto_repair else "skipped",
                utcnow(),
            ),
        )

    try:
        uploaded_by_view = {
            item["view"]: client.upload_image(Path(item["path"]))
            for item in sources
        }
        workflow = client.load_workflow(workflow_path)
        client.inject_views(workflow, uploaded_by_view)
        prompt_id = client.queue(workflow)
        with connect() as conn:
            conn.execute(
                "UPDATE generations SET status='running', comfy_prompt_id=? WHERE id=?",
                (prompt_id, generation_id),
            )

        history = client.wait_history(prompt_id)
        outputs = client.find_3d_files(history)
        if not outputs:
            raise ComfyError("Workflow beendet, aber keine GLB/OBJ/PLY/STL-Ausgabe gefunden.")

        ref = outputs[0]
        raw_suffix = Path(ref["filename"]).suffix.lower() or ".glb"
        raw_path = output_dir / f"raw{raw_suffix}"
        client.download_output(ref, raw_path)
        with connect() as conn:
            conn.execute(
                "UPDATE generations SET status='done', output_file=? WHERE id=?",
                (str(raw_path), generation_id),
            )

        repair_result = None
        if auto_repair:
            repair_result = _run_repair(generation_id, raw_path, output_dir)

        return {
            "project_id": project_id,
            "generation_id": generation_id,
            "mode": mode,
            "views": [item["view"] for item in sources],
            "workflow": str(workflow_path),
            "model_url": f"/api/generations/{generation_id}/model",
            "download_url": f"/api/generations/{generation_id}/file",
            "repair": repair_result,
        }
    except Exception as exc:
        with connect() as conn:
            conn.execute(
                "UPDATE generations SET status='error', error=? WHERE id=?",
                (str(exc), generation_id),
            )
        raise HTTPException(500, str(exc)) from exc


@app.get("/api/generations/{generation_id}/model")
def generation_model(generation_id: str, variant: str = "best") -> FileResponse:
    path = _best_file(_generation(generation_id), variant)
    media = {
        ".glb": "model/gltf-binary",
        ".gltf": "model/gltf+json",
        ".stl": "model/stl",
        ".obj": "text/plain",
        ".ply": "application/octet-stream",
    }.get(path.suffix.lower(), "application/octet-stream")
    return FileResponse(path, media_type=media)


@app.get("/api/generations/{generation_id}/file")
def generation_file(generation_id: str, variant: str = "best") -> FileResponse:
    path = _best_file(_generation(generation_id), variant)
    return FileResponse(path, filename=path.name)


@app.post("/api/generations/{generation_id}/repair")
def repair_generation(generation_id: str) -> dict:
    g = _generation(generation_id)
    raw_path = _best_file(g, "raw")
    output_dir = raw_path.parent
    result = _run_repair(generation_id, raw_path, output_dir)
    if not result["ok"]:
        raise HTTPException(500, result["log"] or "Blender-Reparatur fehlgeschlagen.")
    return {
        **result,
        "model_url": f"/api/generations/{generation_id}/model?variant=repaired",
        "download_url": f"/api/generations/{generation_id}/file?variant=repaired",
    }


@app.post("/api/generations/{generation_id}/feedback")
def feedback(generation_id: str, body: FeedbackIn) -> dict:
    _generation(generation_id)
    approved = int(body.approved_for_learning and body.rating >= 4)
    issues = sorted({issue.strip() for issue in body.issues if issue.strip()})
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO feedback(
                generation_id,rating,note,issues_json,approved_for_learning,created_at
            ) VALUES(?,?,?,?,?,?)
            """,
            (
                generation_id,
                body.rating,
                body.note.strip(),
                json.dumps(issues, ensure_ascii=False),
                approved,
                utcnow(),
            ),
        )
    return {
        "saved": True,
        "approved_for_learning": bool(approved),
        "issues": issues,
    }
