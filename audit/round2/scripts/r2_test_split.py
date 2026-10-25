"""Vong 2 - accuracy 8 lop tren tap test noi bo, tai hien split bang chinh ham
garbage_classifier.data.discover_and_split (seed, max_images_per_class doc tu checkpoint config),
tien xu ly get_eval_transform nhu evaluate.py. Ghi audit/round2/test_split.json.
Chay: garbage_classifier/.venv/Scripts/python.exe audit/round2/scripts/r2_test_split.py v2_r18 v5_r18
"""
import json
import sys
from pathlib import Path

import torch
from PIL import Image
from torch import nn
from torchvision.models import resnet18

ROOT = Path(r"C:\AL-PLR")
sys.path.insert(0, str(ROOT / "garbage_classifier" / "src"))
from garbage_classifier.data import discover_and_split, get_eval_transform  # noqa: E402


def main():
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    res = {}
    for run in sys.argv[1:]:
        ad = ROOT / "garbage_classifier" / "artifacts" / run
        ck = torch.load(ad / "best_model.pt", map_location="cpu", weights_only=False)
        cfg = ck["config"]
        sp = discover_and_split(Path(cfg["data_dir"]), seed=int(cfg.get("seed", 42)),
                                max_images_per_class=int(cfg.get("max_images_per_class", 0)))
        assert sp.classes == ck["classes"]
        m = resnet18(weights=None)
        m.fc = nn.Linear(512, len(sp.classes))
        m.load_state_dict(ck["model_state_dict"])
        m.eval().to(dev)
        tf = get_eval_transform(int(cfg.get("image_size", 224)))
        ok = 0
        per = {c: [0, 0] for c in sp.classes}
        batch, labels = [], []

        def flush():
            nonlocal ok
            with torch.no_grad():
                pr = m(torch.stack(batch).to(dev)).argmax(1).cpu().tolist()
            for p, y in zip(pr, labels):
                ok += p == y
                per[sp.classes[y]][0] += p == y
                per[sp.classes[y]][1] += 1
            batch.clear(); labels.clear()

        for s in sp.test:
            with Image.open(s.path) as im:
                batch.append(tf(im.convert("RGB")))
            labels.append(s.label)
            if len(batch) == 64:
                flush()
        if batch:
            flush()
        split_json = json.loads((ad / "dataset_split.json").read_text(encoding="utf-8")) if (ad / "dataset_split.json").exists() else None
        res[run] = {"data_dir": cfg["data_dir"], "seed": cfg.get("seed"), "dung": ok, "tong": len(sp.test),
                    "train": len(sp.train), "val": len(sp.val), "per_class": per,
                    "test_total_trong_dataset_split_json": split_json["test"]["total"] if split_json else None,
                    "khop_dataset_split_json": (split_json == json.loads(json.dumps(sp.summary()))) if split_json else None}
        print(run, ok, len(sp.test), flush=True)
    (ROOT / "audit" / "round2" / "test_split.json").write_text(json.dumps(res, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
