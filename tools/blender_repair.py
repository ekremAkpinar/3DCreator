from __future__ import annotations

import sys
from pathlib import Path

import bpy
import bmesh


def args() -> tuple[Path, Path]:
    rest = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(rest) != 2:
        raise SystemExit("Usage: blender --background --python blender_repair.py -- input output")
    return Path(rest[0]), Path(rest[1])


def import_mesh(path: Path) -> None:
    suffix = path.suffix.lower()
    if suffix in {".glb", ".gltf"}:
        bpy.ops.import_scene.gltf(filepath=str(path))
    elif suffix == ".obj":
        bpy.ops.wm.obj_import(filepath=str(path))
    elif suffix == ".stl":
        bpy.ops.wm.stl_import(filepath=str(path))
    elif suffix == ".ply":
        bpy.ops.wm.ply_import(filepath=str(path))
    else:
        raise RuntimeError(f"Nicht unterstuetztes Eingabeformat: {suffix}")


def clean_object(obj) -> dict[str, int]:
    if obj.type != "MESH":
        return {"verts": 0, "faces": 0, "boundary_edges": 0, "filled": 0}
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    mesh = obj.data
    bm = bmesh.new(); bm.from_mesh(mesh); bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.00001)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=0.000001)
    boundary=[edge for edge in bm.edges if edge.is_boundary]; boundary_before=len(boundary); filled=0
    if boundary:
        try:
            result=bmesh.ops.holes_fill(bm, edges=boundary, sides=0); filled=len(result.get("faces", []))
        except Exception as exc:
            print(f"REPAIR_WARNING holes_fill: {exc}")
    if bm.faces: bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    stats={"verts":len(bm.verts),"faces":len(bm.faces),"boundary_edges":boundary_before,"filled":filled}
    bm.to_mesh(mesh); bm.free(); mesh.update(); obj.select_set(False); return stats


def export_mesh(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix=path.suffix.lower()
    if suffix==".stl": bpy.ops.wm.stl_export(filepath=str(path), export_selected_objects=False)
    elif suffix in {".glb", ".gltf"}: bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB" if suffix==".glb" else "GLTF_SEPARATE", export_apply=True)
    else: raise RuntimeError("Ziel muss .stl, .glb oder .gltf sein")

source,target=args(); bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False); import_mesh(source)
mesh_objects=[obj for obj in bpy.context.scene.objects if obj.type=="MESH"]
if not mesh_objects: raise RuntimeError("Die Eingabedatei enthaelt kein Mesh.")
total={"verts":0,"faces":0,"boundary_edges":0,"filled":0}
for obj in list(bpy.context.scene.objects):
    stats=clean_object(obj)
    for key,value in stats.items(): total[key]+=value
export_mesh(target)
print(f"REPAIR_OK objects={len(mesh_objects)} verts={total['verts']} faces={total['faces']} boundary_edges_before={total['boundary_edges']} filled_faces={total['filled']} target={target}")
