"""Danh gia tap test noi bo cua tung phien ban, dung dung discover_and_split/build_dataloaders/evaluate_model
nhu evaluate.py (seed lay tu config checkpoint), them confusion 4 nhom (argmax 8 lop -> nhom) va 4 nhom theo luat pin.
Chay (tu C:/AL-PLR/garbage_classifier):
  PYTHONPATH=src .venv/Scripts/python.exe ../audit/scripts/eval_test_split.py v2_r18 v4_r18 ...
Ghi: ../audit/eval_test/<run>.json"""
import json, sys
from pathlib import Path
import torch
from torch import nn
from garbage_classifier.data import build_dataloaders, discover_and_split
from garbage_classifier.engine import evaluate_model
from garbage_classifier.model import load_checkpoint

GROUP = {"organic": "huu-co", "battery": "nguy-hiem", "cardboard": "tai-che", "glass": "tai-che", "metal": "tai-che",
         "paper": "tai-che", "plastic": "tai-che", "clothes": "khong-tai-che"}
GROUPS = ["huu-co", "nguy-hiem", "tai-che", "khong-tai-che"]
ROOT = Path(__file__).resolve().parents[2]
out_dir = ROOT / "audit/eval_test"; out_dir.mkdir(parents=True, exist_ok=True)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

for run in sys.argv[1:]:
    ck = ROOT / "garbage_classifier/artifacts" / run / "best_model.pt"
    model, c = load_checkpoint(ck, device)
    cfg = c["config"]
    data_dir = ROOT / Path(cfg["data_dir"]).name
    splits = discover_and_split(data_dir, seed=int(cfg.get("seed", 42)), max_images_per_class=int(cfg.get("max_images_per_class", 0)))
    assert splits.classes == c["classes"]
    loaders = build_dataloaders(splits, batch_size=32, num_workers=0, device=device, image_size=int(cfg.get("image_size", 224)), seed=int(cfg.get("seed", 42)))
    crit = nn.CrossEntropyLoss(label_smoothing=float(cfg.get("label_smoothing", 0.0)))
    r = evaluate_model(model, loaders["test"], crit, device, splits.classes)
    # second pass for probabilities (same autocast as engine)
    probs, labels = [], []
    with torch.inference_mode():
        for x, y in loaders["test"]:
            with torch.autocast(device_type=device.type, enabled=device.type == "cuda"):
                lg = model(x.to(device))
            probs.append(torch.softmax(lg.float(), 1).cpu()); labels.append(y)
    P = torch.cat(probs); Y = torch.cat(labels)
    cls = splits.classes; ib = cls.index("battery")
    def group_conf(th):
        m = [[0] * 4 for _ in range(4)]
        for p, y in zip(P, Y):
            if th is None: g = GROUP[cls[int(p.argmax())]]
            else:
                q = p.clone(); q[ib] = -1
                g = "nguy-hiem" if p[ib] >= th else GROUP[cls[int(q.argmax())]]
            m[GROUPS.index(GROUP[cls[int(y)]])][GROUPS.index(g)] += 1
        return m
    cm = r.confusion_matrix
    res = {"run": run, "checkpoint": str(ck), "data_dir": str(data_dir), "seed": int(cfg.get("seed", 42)),
           "classes": cls, "n_test": len(splits.test), "dung": sum(cm[i][i] for i in range(len(cls))),
           "accuracy": r.accuracy, "loss": r.loss, "confusion_matrix": cm,
           "per_class": {k: {"dung": cm[i][i], "tong": sum(cm[i])} for i, k in enumerate(cls)},
           "groups": GROUPS, "group_confusion_argmax": group_conf(None),
           "group_confusion_pin0.5": group_conf(0.5), "group_confusion_pin0.3": group_conf(0.3),
           "argmax_pass2_dung": int((P.argmax(1) == Y).sum())}
    (out_dir / f"{run}.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(run, res["dung"], "/", res["n_test"], f"{r.accuracy:.4f}", "pass2", res["argmax_pass2_dung"])
