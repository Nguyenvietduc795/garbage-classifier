"""So sanh backend/model.pt va TFJS (frontend/models/*) voi tung best_model.pt / last_model.pt.
Chay: garbage_classifier/.venv/Scripts/python.exe audit/scripts/identify_models.py  (tu C:/AL-PLR)"""
import hashlib, json, sys
from pathlib import Path
import numpy as np, torch

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "garbage_classifier" / "artifacts"
out = {"checkpoints": {}, "backend": {}, "tfjs": {}}

def md5(p): return hashlib.md5(p.read_bytes()).hexdigest()

ckpts = {}
for p in sorted(ART.glob("*/*.pt")):
    c = torch.load(p, map_location="cpu", weights_only=False)
    sd = c["model_state_dict"]
    key = f"{p.parent.name}/{p.name}"
    ckpts[key] = sd
    cfg = c.get("config", {})
    out["checkpoints"][key] = {"md5": md5(p), "arch": c.get("model_name"), "classes": c.get("classes"),
        "epoch": c.get("epoch"), "best_val_accuracy": c.get("best_val_accuracy"),
        "data_dir": cfg.get("data_dir"), "seed": cfg.get("seed"), "max_images_per_class": cfg.get("max_images_per_class"),
        "image_size": cfg.get("image_size"), "label_smoothing": cfg.get("label_smoothing"),
        "balance_classes": cfg.get("balance_classes"), "oversample": cfg.get("oversample"), "strong_augment": cfg.get("strong_augment")}

def compare(sd_a, sd_b):
    if set(sd_a) != set(sd_b): return None
    m = 0.0
    for k in sd_a:
        a, b = sd_a[k], sd_b[k]
        if a.shape != b.shape: return None
        if a.is_floating_point(): m = max(m, float((a.float() - b.float()).abs().max()))
        elif not torch.equal(a, b): m = max(m, float((a.float()-b.float()).abs().max()))
    return m

for extra in [ROOT / "backend" / "model.pt", ROOT / "trash_ai_ui" / "garbage_resnet18.pt"]:
    if not extra.exists(): continue
    c = torch.load(extra, map_location="cpu", weights_only=False)
    sd = c["model_state_dict"] if "model_state_dict" in c else c
    res = {}
    for k, s in ckpts.items():
        d = compare(sd, s)
        if d is not None: res[k] = d
    best = min(res, key=res.get) if res else None
    out["backend"][str(extra.relative_to(ROOT))] = {"md5": md5(extra), "keys_in_file": [k for k in c.keys()] if isinstance(c, dict) else None,
        "classes": c.get("classes") if isinstance(c, dict) else None, "epoch": c.get("epoch"),
        "best_val_accuracy": c.get("best_val_accuracy"),
        "config_data_dir": (c.get("config") or {}).get("data_dir"),
        "max_abs_diff_by_ckpt": dict(sorted(res.items(), key=lambda x: x[1])[:6]), "closest": best}

# TFJS: dequantize the final dense kernel (8 x 512 or 512 x 8) and compare with fc.weight
for mdir in sorted((ROOT / "frontend" / "models").iterdir()):
    mj = json.loads((mdir / "model.json").read_text())
    buf = b"".join((mdir / p).read_bytes() for g in mj["weightsManifest"] for p in g["paths"])
    specs = [w for g in mj["weightsManifest"] for w in g["weights"]]
    off = 0; tensors = {}
    for w in specs:
        n = int(np.prod(w["shape"])) if w["shape"] else 1
        q = w.get("quantization")
        if q:
            dt = {"uint8": np.uint8, "uint16": np.uint16, "float16": np.float16}[q["dtype"]]
            raw = np.frombuffer(buf, dtype=dt, count=n, offset=off); off += n * raw.itemsize
            val = raw.astype(np.float32) * q["scale"] + q["min"] if "scale" in q else raw.astype(np.float32)
        else:
            dt = {"float32": np.float32, "int32": np.int32}[w["dtype"]]
            val = np.frombuffer(buf, dtype=dt, count=n, offset=off).astype(np.float32); off += n * 4
        tensors[w["name"]] = val.reshape(w["shape"])
    cands = {k: v for k, v in tensors.items() if sorted(v.shape) == [8, 512]}
    res = {}
    for name, t in cands.items():
        tt = t if t.shape == (8, 512) else t.T
        for k, sd in ckpts.items():
            fw = sd.get("fc.weight")
            if fw is None or tuple(fw.shape) != (8, 512): continue
            res[k] = float(np.abs(fw.numpy() - tt).max())
    srt = sorted(res.items(), key=lambda x: x[1])
    out["tfjs"][mdir.name] = {"fc_tensor_names": list(cands), "fc_max_abs_diff_top5": dict(srt[:5]),
        "closest": srt[0][0] if srt else None}
print(json.dumps(out, indent=1, ensure_ascii=False))
