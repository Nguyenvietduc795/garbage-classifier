"""Vong 2 - suy luan doc lap: xac suat softmax 8 lop cho MOI anh trong cac bo anh that,
cho 6 model, theo 2 che do tien xu ly:
  - "web": Resize(256)+CenterCrop(224)+ToTensor, anh toi (do sang<0,30) nang gamma toi 0,45, roi Normalize
  - "raw": giong backend/app.py (Resize(256)+CenterCrop(224)+Normalize, khong tang sang)
Ghi ra audit/round2/probs_realworld.json: {model: {mode: {relpath: [8 xac suat]}}}, kem md5 tung anh.
Chay: garbage_classifier/.venv/Scripts/python.exe audit/round2/scripts/r2_infer_realworld.py
"""
import hashlib
import json
import math
from pathlib import Path

import torch
from PIL import Image
from torch import nn
from torchvision import transforms
from torchvision.models import resnet18

ROOT = Path(r"C:\AL-PLR")
ART = ROOT / "garbage_classifier" / "artifacts"
MODELS = ["v2_r18", "v3_r18", "v4_r18", "v5_r18", "v5_r18_s1", "v5_r18_s2"]
SETS = ["realworld_test", "realworld_test2", "realworld_curated", "realworld_clothes_test",
        "realworld_pin_test", "realworld_mta_test", "realworld_bdw_test", "realworld_bower_test",
        "realworld_rw5_test", "realworld_loai_bo/realworld_test", "realworld_loai_bo/realworld_test2"]
EXT = {".jpg", ".jpeg", ".png", ".webp"}
MEAN, STD = (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)


def brighten(x):
    s = float((x * torch.tensor([0.299, 0.587, 0.114]).view(3, 1, 1)).sum(0).mean())
    if s >= 0.30 or s <= 0.01:
        return x, s, False
    g = max(0.35, math.log(0.45) / math.log(s))
    return x.clamp_min(1e-6).pow(g), s, True


def load(run, dev):
    ck = torch.load(ART / run / "best_model.pt", map_location="cpu", weights_only=False)
    assert ck.get("model_name", "resnet18") == "resnet18"
    m = resnet18(weights=None)
    m.fc = nn.Linear(m.fc.in_features, len(ck["classes"]))
    m.load_state_dict(ck["model_state_dict"])
    return m.eval().to(dev), ck["classes"]


def main():
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    models = {r: load(r, dev) for r in MODELS}
    classes = models["v5_r18"][1]
    assert all(c == classes for _, c in models.values())
    tt = transforms.Compose([transforms.Resize(256), transforms.CenterCrop(224), transforms.ToTensor()])
    norm = transforms.Normalize(MEAN, STD)
    out = {"classes": classes, "images": {}, "probs": {r: {"web": {}, "raw": {}} for r in MODELS}}
    for s in SETS:
        for f in sorted((ROOT / s).rglob("*")):
            if not f.is_file() or f.suffix.lower() not in EXT:
                continue
            rel = f.relative_to(ROOT).as_posix()
            with Image.open(f) as im:
                x = tt(im.convert("RGB"))
            xb, sang, bright = brighten(x)
            batch = torch.stack([norm(x), norm(xb)]).to(dev)
            out["images"][rel] = {"md5": hashlib.md5(f.read_bytes()).hexdigest(), "do_sang": sang, "tang_sang": bright}
            with torch.no_grad():
                for r, (m, _) in models.items():
                    p = torch.softmax(m(batch), 1).cpu()
                    out["probs"][r]["raw"][rel] = [round(float(v), 7) for v in p[0]]
                    out["probs"][r]["web"][rel] = [round(float(v), 7) for v in p[1]]
        print(s, "xong", flush=True)
    (ROOT / "audit" / "round2" / "probs_realworld.json").write_text(json.dumps(out), encoding="utf-8")
    print("anh:", len(out["images"]))


if __name__ == "__main__":
    main()
