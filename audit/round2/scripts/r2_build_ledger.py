"""Vong 2 - tinh moi chi so tu probs_realworld.json, datasets.json, test_split.json, model_identity.json
va ghi audit/round2/numbers_ledger.json.

Luat:
  web(t):   anh tang sang (che do "web"); P(battery) >= t -> nguy-hai, nguoc lai nhom cua lop cao nhat trong 7 lop con lai.
  backend:  che do "raw" (khong tang sang), argmax 8 lop, khong luat pin.
  do chac (muc 7): tong xac suat cac lop trong nhom duoc chon (luat web, t=0,5); do chac < nguong -> "chua chac".
Moi bo bo trung MD5 trong bo (giu lan dau theo thu tu thu muc lop roi ten file da sap xep), giong realworld.py.
"""
import json
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

ROOT = Path(r"C:\AL-PLR")
A = ROOT / "audit" / "round2"
G = {"organic": "huu-co", "battery": "nguy-hiem", "cardboard": "tai-che", "glass": "tai-che", "metal": "tai-che",
     "paper": "tai-che", "plastic": "tai-che", "clothes": "khong-tai-che"}
PY = "garbage_classifier/.venv/Scripts/python.exe"
CMD_INF = f"{PY} audit/round2/scripts/r2_infer_realworld.py && {PY} audit/round2/scripts/r2_build_ledger.py"
CMD_DS = f"{PY} audit/round2/scripts/r2_datasets.py"
CMD_TS = f"{PY} audit/round2/scripts/r2_test_split.py v2_r18 v5_r18"
CMD_ID = f"{PY} audit/round2/scripts/r2_model_identity.py"

P = json.loads((A / "probs_realworld.json").read_text(encoding="utf-8"))
D = json.loads((A / "datasets.json").read_text(encoding="utf-8"))
T = json.loads((A / "test_split.json").read_text(encoding="utf-8"))
I = json.loads((A / "model_identity.json").read_text(encoding="utf-8"))
C = P["classes"]
IB = C.index("battery")

ledger = []


def pct(a, b):
    if not b:
        return None
    return float((Decimal(a) * 100 / Decimal(b)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def add(ten, ver, tu, mau=None, cmd=CMD_INF, src="audit/round2/probs_realworld.json"):
    v = f"{tu}/{mau} = {pct(tu, mau)}%" if mau is not None else tu
    ledger.append({"ten_chi_so": ten, "phien_ban": ver, "gia_tri": v, "tu_so": tu, "mau_so": mau,
                   "lenh_tao_ra": cmd, "file_nguon": src})


def images(setname):
    """Danh sach (relpath, lop) sau bo trung MD5 trong bo."""
    rels = sorted(r for r in P["images"] if r.startswith(setname + "/") and r.count("/") == setname.count("/") + 2)
    seen, out = set(), []
    for r in rels:
        h = P["images"][r]["md5"]
        if h in seen:
            continue
        seen.add(h)
        out.append((r, r.split("/")[-2].lower()))
    return out


def predict(p, rule, t):
    if rule == "backend":
        return G[C[max(range(8), key=p.__getitem__)]]
    if p[IB] >= t:
        return "nguy-hiem"
    return G[C[max((i for i in range(8) if i != IB), key=p.__getitem__)]]


def evaluate(model, setnames, rule="web", t=0.5):
    mode = "raw" if rule == "backend" else "web"
    r = {"dung": 0, "tong": 0, "pin_dung": 0, "pin": 0, "bao_nham_pin": 0, "huu_co_dung": 0, "huu_co": 0}
    for s in setnames:
        for rel, lop in images(s):
            p = P["probs"][model][mode][rel]
            g = predict(p, rule, t)
            r["tong"] += 1
            r["dung"] += g == G[lop]
            if lop == "battery":
                r["pin"] += 1
                r["pin_dung"] += g == "nguy-hiem"
            elif g == "nguy-hiem":
                r["bao_nham_pin"] += 1
            if lop == "organic":
                r["huu_co"] += 1
                r["huu_co_dung"] += g == "huu-co"
    return r


OLD = ["realworld_test", "realworld_test2", "realworld_loai_bo/realworld_test", "realworld_loai_bo/realworld_test2"]
SETS = {"rw5": ["realworld_rw5_test"], "mta": ["realworld_mta_test"], "bower": ["realworld_bower_test"],
        "bdw": ["realworld_bdw_test"], "curated": ["realworld_curated"], "test": ["realworld_test"],
        "test2": ["realworld_test2"], "clothes": ["realworld_clothes_test"], "pin_test": ["realworld_pin_test"],
        "102_anh_cu": OLD}
EIGHT = ["realworld_rw5_test", "realworld_mta_test", "realworld_bower_test", "realworld_bdw_test",
         "realworld_curated", "realworld_test", "realworld_test2", "realworld_clothes_test"]
EIGHT_NO_CUR = [s for s in EIGHT if s != "realworld_curated"]

# ---------- muc 1: dataset ----------
for d, v in D["datasets"].items():
    for c, n in v["per_class"].items():
        add(f"so anh lop {c}", d, n, cmd=CMD_DS, src=f"{d}/ (dem file anh); audit/round2/datasets.json")
    add("tong so anh", d, v["total"], cmd=CMD_DS, src=f"{d}/; audit/round2/datasets.json")
    for s, n in v["per_source"].items():
        add(f"so anh nguon '{s}' (tien to ten file; 'goc' = tien to la ten lop/shoes)", d, n, cmd=CMD_DS,
            src=f"{d}/; audit/round2/datasets.json")
for a, b in [("dataset_8lop_v3", "dataset_8lop_v4"), ("dataset_8lop_v4", "dataset_8lop_v5")]:
    va, vb = D["datasets"][a], D["datasets"][b]
    for c in vb["per_class"]:
        add(f"chenh lech so anh lop {c} ({a}->{b})", f"{a}->{b}", vb["per_class"][c] - va["per_class"].get(c, 0), cmd=CMD_DS,
            src="audit/round2/datasets.json")
    for s in sorted(set(va["per_source"]) | set(vb["per_source"])):
        add(f"chenh lech so anh nguon '{s}' ({a}->{b})", f"{a}->{b}", vb["per_source"].get(s, 0) - va["per_source"].get(s, 0),
            cmd=CMD_DS, src="audit/round2/datasets.json")
    add(f"chenh lech tong ({a}->{b})", f"{a}->{b}", vb["total"] - va["total"], cmd=CMD_DS, src="audit/round2/datasets.json")
    for c, srcs in vb["per_class_source"].items():
        for s, n in srcs.items():
            delta = n - va["per_class_source"].get(c, {}).get(s, 0)
            if delta:
                add(f"chenh lech lop {c} nguon '{s}' ({a}->{b})", f"{a}->{b}", delta, cmd=CMD_DS, src="audit/round2/datasets.json")

# ---------- muc 2: bo anh that ----------
for s, v in D["realworld"].items():
    add("so anh truoc bo trung MD5", s, v["truoc_bo_trung"], cmd=CMD_DS, src=f"{s}/")
    add("so anh sau bo trung MD5 (trong bo)", s, v["sau_bo_trung"], cmd=CMD_DS, src=f"{s}/")
    add("so anh pin (sau bo trung)", s, v["pin_sau"], cmd=CMD_DS, src=f"{s}/")
for k, v in D["trung_md5"].items():
    add(f"trung MD5: {k}", "curated/test/test2", v, cmd=CMD_DS, src="realworld_curated/, realworld_test/, realworld_test2/")
for k, v in D["trung_voi_dataset_v5"].items():
    add("so anh trung MD5 voi dataset_8lop_v5", k, v, cmd=CMD_DS, src=f"{k}/, dataset_8lop_v5/")

# ---------- muc 3: test noi bo ----------
for run, v in T.items():
    add("accuracy 8 lop tap test noi bo (tai hien split data.py)", run, v["dung"], v["tong"], cmd=CMD_TS,
        src=f"{v['data_dir']}; garbage_classifier/artifacts/{run}/best_model.pt; audit/round2/test_split.json")
    add("split test tai hien khop dataset_split.json", run, v["khop_dataset_split_json"], cmd=CMD_TS,
        src=f"garbage_classifier/artifacts/{run}/dataset_split.json")

# ---------- muc 4, 5: luat web ----------
CONFIGS = [("v5_r18", 0.5), ("v5_r18", 0.7), ("v2_r18", 0.3), ("v5_r18_s1", 0.5), ("v5_r18_s2", 0.5), ("v2_r18", 0.5)]
summary = {}
for m, t in CONFIGS:
    ver = f"{m} luat web t={t}"
    res = {k: evaluate(m, v, "web", t) for k, v in SETS.items()}
    res["tong_8_bo"] = evaluate(m, EIGHT, "web", t)
    res["tong_8_bo_bo_curated"] = evaluate(m, EIGHT_NO_CUR, "web", t)
    res["166_pin"] = evaluate(m, OLD + ["realworld_pin_test", "realworld_bower_test"], "web", t)
    res["102cu_rw5_bower_mta"] = evaluate(m, OLD + ["realworld_rw5_test", "realworld_bower_test", "realworld_mta_test"], "web", t)
    summary[ver] = res
    for k, r in res.items():
        if k == "166_pin":
            add("pin nhan dung tren 166 anh pin (102 cu + pin_test + bower)", ver, r["pin_dung"], r["pin"])
            continue
        if k == "102cu_rw5_bower_mta":
            add("bao nham pin tren 102 cu + rw5 + bower + mta", ver, r["bao_nham_pin"], r["tong"] - r["pin"])
            continue
        add(f"dung nhom [{k}]", ver, r["dung"], r["tong"])
        if r["pin"]:
            add(f"pin dung [{k}]", ver, r["pin_dung"], r["pin"])
        add(f"anh khong phai pin bi bao nham pin [{k}]", ver, r["bao_nham_pin"], r["tong"] - r["pin"])
        if k == "rw5":
            add("huu co dung [rw5]", ver, r["huu_co_dung"], r["huu_co"])

# ---------- muc 6: luat backend ----------
for m in ["v2_r18", "v3_r18", "v4_r18", "v5_r18"]:
    ver = f"{m} luat backend (argmax 8 lop, khong tang sang)"
    for k in ["102_anh_cu", "rw5", "bower", "mta"]:
        r = evaluate(m, SETS[k], "backend")
        summary.setdefault(ver, {})[k] = r
        add(f"dung nhom [{k}]", ver, r["dung"], r["tong"])
        if r["pin"]:
            add(f"pin dung [{k}]", ver, r["pin_dung"], r["pin"])
        add(f"bao nham pin [{k}]", ver, r["bao_nham_pin"], r["tong"] - r["pin"])
        if k == "rw5":
            add("huu co dung [rw5]", ver, r["huu_co_dung"], r["huu_co"])


# ---------- muc 7: nguong tin cay ----------
def confidence_table(model, setnames, thr, t=0.5):
    d = s_ = u = 0
    for sn in setnames:
        for rel, lop in images(sn):
            p = P["probs"][model]["web"][rel]
            g = predict(p, "web", t)
            conf = sum(p[i] for i in range(8) if G[C[i]] == g)
            if conf < thr:
                u += 1
            elif g == G[lop]:
                d += 1
            else:
                s_ += 1
    return d, s_, u


for k, sn in [("102_anh_cu", OLD), ("curated", ["realworld_curated"])]:
    for thr in (0.4, 0.5, 0.6):
        d, s_, u = confidence_table("v5_r18", sn, thr)
        n = d + s_ + u
        ver = f"v5_r18 luat web t=0.5, nguong tin cay {thr}"
        summary.setdefault("tin_cay", {})[f"{k} {thr}"] = (d, s_, u, n)
        add(f"dung (du tin cay) [{k}]", ver, d, n)
        add(f"sai (du tin cay) [{k}]", ver, s_, n)
        add(f"chua chac [{k}]", ver, u, n)


def top_vs_group(model, mode, setnames):
    a = b = n = 0
    for sn in setnames:
        for rel, lop in images(sn):
            p = P["probs"][model][mode][rel]
            g1 = G[C[max(range(8), key=p.__getitem__)]]
            sums = {}
            for i in range(8):
                sums[G[C[i]]] = sums.get(G[C[i]], 0) + p[i]
            g2 = max(sums, key=sums.get)
            a += g1 == G[lop]
            b += g2 == G[lop]
            n += 1
    return a, b, n


for m in ["v5_r18", "v2_r18"]:
    for mode, desc in [("raw", "khong tang sang"), ("web", "co tang sang")]:
        a, b, n = top_vs_group(m, mode, ["realworld_curated"])
        summary.setdefault("top_vs_group", {})[f"{m} {mode}"] = (a, b, n)
        add("curated: chon nhom theo lop cao nhat (8 lop, khong luat pin) - dung nhom", f"{m} ({desc})", a, n)
        add("curated: chon nhom theo tong xac suat nhom - dung nhom", f"{m} ({desc})", b, n)

# ---------- muc 8 ----------
match_be = [r for r, v in I["backend"].items() if v]
add("backend/model.pt trung state_dict voi artifact", "backend", ", ".join(match_be) or "khong co", cmd=CMD_ID,
    src="backend/model.pt; garbage_classifier/artifacts/*/best_model.pt")
match_fe = [r for r, v in I["frontend_v5"].items() if v["khop"]]
add("frontend/models/r18-8lop-v5 khop artifact (lop fc giai nen uint8, sai so <= scale/2)", "frontend", ", ".join(match_fe) or "khong co",
    cmd=CMD_ID, src="frontend/models/r18-8lop-v5/model.json + *.bin; garbage_classifier/artifacts/*/best_model.pt")

(A / "numbers_ledger.json").write_text(json.dumps(ledger, ensure_ascii=False, indent=1), encoding="utf-8")
(A / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
print("so muc:", len(ledger))
