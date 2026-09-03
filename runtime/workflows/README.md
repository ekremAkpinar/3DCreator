# 3DCreator API-Workflows

Ab v0.2.1 werden die vier TRELLIS-Workflows normalerweise automatisch lokal erzeugt.

Beim Ausfuehren von `setup-app.ps1` werden gepinnte API-Workflowvorlagen vom Upstream-Projekt geladen und lokal angepasst:

- `mesh_only_512_api.json`
- `mesh_only_1024_api.json`
- `mesh_multiview_512_api.json`
- `mesh_multiview_1024_api.json`

Manuell neu erzeugen:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup-workflows.ps1
```

RX-6800-XT-Profil:

- model: `microsoft/TRELLIS.2-4B`
- device: `cuda` ueber PyTorch/ROCm
- backend: `aule`
- sparse_backend: `aule`
- conv_backend: `flex_gemm`
- low_vram: `true`
- keep_models_loaded: `false`

Das 512-Profil ist der empfohlene Startpunkt. 1024 ist experimentell und benoetigt mehr VRAM.
