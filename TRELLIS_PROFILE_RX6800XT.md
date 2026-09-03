# Mille TRELLIS Profil - RX 6800 XT 16 GB

Dieses Profil ist der Startpunkt fuer deine Karte.

## Loader

- Model: `microsoft/TRELLIS.2-4B`
- Attention backend: `aule`
- Device: `cuda`
- Low VRAM: `true`
- Keep models loaded: `false`
- Convolution backend: `flex_gemm`
- Sparse attention backend: `aule`
- ReconViaGen: `false`

`cuda` ist hier kein NVIDIA-Zwang: PyTorch ROCm bildet die GPU-Funktionen weiterhin unter `torch.cuda` ab.

## Qualitaetsstrategie

1. Zuerst 512/konservatives Profil stabil bekommen.
2. Danach 1024 testen.
3. Erst nach stabiler 1024-Generation Face Count und Nachbearbeitung erhoehen.
4. Fuer FDM ist ein sauberes, geschlossenes Mesh wichtiger als maximale Polygonzahl.

## Lernregel

Mille darf ein Ergebnis nur dann als positives Lernbeispiel markieren, wenn du es mit 4 oder 5 Sternen bewertest **und** explizit `Fuer Lernen freigeben` aktivierst.

1-2 Sterne bleiben als Negativbeispiele erhalten. 3 Sterne werden gespeichert, aber nicht automatisch als positives Trainingsmaterial verwendet.
