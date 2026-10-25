"""Tinh xac suat tung anh cua cac bo realworld_* theo DUNG quy trinh realworld.py
(bo trung MD5 trong tung bo theo thu tu lop/ten file, Resize256+CenterCrop224, tang sang anh toi, fp32, batch 1),
va them ban KHONG tang sang (giong backend/app.py). Luu probs de tinh nguong 0.5 / 0.3 va nguong tin cay.
Chay (tu C:/AL-PLR/garbage_classifier):
  PYTHONPATH=src .venv/Scripts/python.exe ../audit/scripts/eval_realworld_probs.py v5_r18 ...
Ghi: ../audit/eval_realworld/<run>_probs.json"""
import hashlib, json, sys
from pathlib import Path
import torch
from PIL import Image
from torchvision import transforms
from garbage_classifier.data import IMAGENET_MEAN, IMAGENET_STD, SUPPORTED_EXTENSIONS
from garbage_classifier.model import load_checkpoint
from garbage_classifier.realworld import LOAI_VAO_NHOM, can_bang_sang

ROOT = Path(__file__).resolve().parents[2]
SETS = ["realworld_test", "realworld_test2", "realworld_clothes_test", "realworld_pin_test", "realworld_mta_test",
        "realworld_bdw_test", "realworld_bower_test", "realworld_rw5_test", "realworld_curated",
        "realworld_loai_bo/realworld_test", "realworld_loai_bo/realworld_test2"]
out_dir = ROOT / "audit/eval_realworld"; out_dir.mkdir(parents=True, exist_ok=True)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
to_tensor = transforms.Compose([transforms.Resize(256), transforms.CenterCrop(224), transforms.ToTensor()])
norm = transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)
for run in sys.argv[1:]:
    model, c = load_checkpoint(ROOT / "garbage_classifier/artifacts" / run / "best_model.pt", device)
    model.eval()
    res = {"run": run, "classes": c["classes"], "sets": {}}
    for s in SETS:
        recs = []; seen = set(); raw = 0
        for ld in sorted(p for p in (ROOT / s).iterdir() if p.is_dir()):
            loai = ld.name.lower()
            if loai not in LOAI_VAO_NHOM: continue
            for f in sorted(ld.iterdir()):
                if f.suffix.lower() not in SUPPORTED_EXTENSIONS: continue
                raw += 1
                h = hashlib.md5(f.read_bytes()).hexdigest()
                if h in seen: continue
                seen.add(h)
                with Image.open(f) as im:
                    t = to_tensor(im.convert("RGB"))
                tb = can_bang_sang(t)
                with torch.no_grad():
                    pb = torch.softmax(model(norm(tb).unsqueeze(0).to(device)), 1)[0].cpu().tolist()
                    pn = torch.softmax(model(norm(t).unsqueeze(0).to(device)), 1)[0].cpu().tolist()
                recs.append({"file": f"{ld.name}/{f.name}", "loai": loai, "tang_sang": not torch.equal(t, tb),
                             "p_web": pb, "p_backend": pn})
        res["sets"][s] = {"raw": raw, "records": recs}
        print(run, s, raw, len(recs))
    (out_dir / f"{run}_probs.json").write_text(json.dumps(res), encoding="utf-8")
