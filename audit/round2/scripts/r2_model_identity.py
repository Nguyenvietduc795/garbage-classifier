"""Vong 2 - backend/model.pt trung trong so voi artifact nao (so toan bo state_dict, torch.equal),
va frontend/models/r18-8lop-v5 (TF.js, nen uint8) khop artifact nao: giai nen lop fc (unknown_43 [512,8],
unknown_45 [8]) tu file .bin va so voi fc.weight.T / fc.bias moi artifact (sai so toi da so voi scale/2).
Ghi audit/round2/model_identity.json.
"""
import json
from pathlib import Path

import numpy as np
import torch

ROOT = Path(r"C:\AL-PLR")
ART = ROOT / "garbage_classifier" / "artifacts"


def tfjs_weights(d):
    m = json.loads((d / "model.json").read_text(encoding="utf-8"))
    out = {}
    for g in m["weightsManifest"]:
        buf = b"".join((d / p).read_bytes() for p in g["paths"])
        off = 0
        for w in g["weights"]:
            n = int(np.prod(w["shape"])) if w["shape"] else 1
            q = w.get("quantization")
            if q:
                size = {"uint8": 1, "uint16": 2, "float16": 2}[q["dtype"]] * n
                raw = np.frombuffer(buf, dtype=q["dtype"], count=n, offset=off)
                arr = raw.astype(np.float64) * q["scale"] + q["min"] if q["dtype"] != "float16" else raw.astype(np.float64)
                out[w["name"]] = (arr.reshape(w["shape"]), q.get("scale", 0))
            else:
                size = 4 * n
                out[w["name"]] = (np.frombuffer(buf, dtype=w["dtype"], count=n, offset=off).reshape(w["shape"]), 0)
            off += size
    return out


def main():
    runs = sorted(p.name for p in ART.iterdir() if (p / "best_model.pt").exists())
    sds = {}
    for r in runs:
        ck = torch.load(ART / r / "best_model.pt", map_location="cpu", weights_only=False)
        sds[r] = ck["model_state_dict"]
    be = torch.load(ROOT / "backend" / "model.pt", map_location="cpu", weights_only=False)
    bsd = be["model_state_dict"]
    res = {"backend": {}, "frontend_v5": {}}
    for r, sd in sds.items():
        same = set(sd) == set(bsd) and all(sd[k].shape == bsd[k].shape and torch.equal(sd[k], bsd[k]) for k in sd)
        res["backend"][r] = same
    res["backend_config"] = {k: str(v) for k, v in be.get("config", {}).items() if k in ("data_dir", "seed", "output_dir")}
    res["backend_epoch"] = be.get("epoch")
    tw = tfjs_weights(ROOT / "frontend" / "models" / "r18-8lop-v5")
    W, sw = tw["unknown_43"]
    B, sb = tw["unknown_45"]
    for r, sd in sds.items():
        if "fc.weight" not in sd or tuple(sd["fc.weight"].shape) != (8, 512):
            continue
        dw = float(np.abs(sd["fc.weight"].numpy().T - W).max())
        db = float(np.abs(sd["fc.bias"].numpy() - B).max())
        res["frontend_v5"][r] = {"max_sai_fc_w": dw, "max_sai_fc_b": db, "nua_scale_w": sw / 2, "nua_scale_b": sb / 2,
                                 "khop": dw <= sw / 2 + 1e-6 and db <= sb / 2 + 1e-6}
    (ROOT / "audit" / "round2" / "model_identity.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
