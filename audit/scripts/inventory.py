"""Kiem ke anh: dataset_* x lop, nguon (theo tien to ten file + doi chieu MD5), trung MD5,
chenh lech giua phien ban, split train/val/test tai hien bang discover_and_split, cac bo realworld_*.
Chay (tu C:/AL-PLR):
  PYTHONPATH=garbage_classifier/src garbage_classifier/.venv/Scripts/python.exe audit/scripts/inventory.py
Ghi: audit/inventory.json, audit/md5_index.json"""
import hashlib, json, os, re, zipfile
from collections import Counter, defaultdict
from pathlib import Path
from garbage_classifier.data import SUPPORTED_EXTENSIONS, discover_and_split

ROOT = Path(__file__).resolve().parents[2]
CLASSES = ["battery", "cardboard", "clothes", "glass", "metal", "organic", "paper", "plastic"]
DATASETS = ["dataset_8lop", "dataset_8lop_v2", "dataset_8lop_v3", "dataset_8lop_v4", "dataset_8lop_v5",
            "dataset_8lop_v6a", "dataset_8lop_v6b", "dataset_merged"]
REALWORLD = ["realworld_test", "realworld_test2", "realworld_clothes_test", "realworld_pin_test", "realworld_mta_test",
             "realworld_bdw_test", "realworld_bower_test", "realworld_rw5_test", "realworld_curated",
             "realworld_loai_bo/realworld_test", "realworld_loai_bo/realworld_test2"]
# run -> dataset (tu config trong checkpoint, xem model_identity.json)
RUNS = {"v2_r18": "dataset_8lop_v2", "v3_r18": "dataset_8lop_v3", "v4_r18": "dataset_8lop_v4",
        "v5_r18": "dataset_8lop_v5", "v5_r18_s1": "dataset_8lop_v5", "v5_r18_s2": "dataset_8lop_v5",
        "v6a_r18": "dataset_8lop_v6a", "v6b_r18": "dataset_8lop_v6b"}
RUN_SEED = {"v5_r18_s1": 1, "v5_r18_s2": 2}

_cache = {}
def md5(p):
    p = str(p)
    if p not in _cache:
        h = hashlib.md5()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        _cache[p] = h.hexdigest()
    return _cache[p]

def is_img(p):
    return p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS

PREFIX_RULES = [  # (regex tren ten file, nhan nguon)
    (r"^bdw_", "BDWaste (bdw_)"), (r"^bower_", "Bower (bower_)"), (r"^rw_", "RealWaste (rw_)"),
    (r"^mta_", "Malaysian Trash Annotation/Roboflow (mta_)"), (r"^oi_", "Open Images (oi_)"),
    (r"^cm_", "Wikimedia Commons (cm_)"), (r"^rise_", "RISE (rise_)"), (r"^npcg_", "NPCG (npcg_)"),
    (r"^gam_", "gam_ (khong ro bo goc)"), (r"^ar_", "archive/Garbage_Classification (ar_)"),
    (r"^new_", "bo new11k (new_<lop>_N)"), (r"^shoes_", "bo new11k (shoes_N)"),
    (r"^(battery|cardboard|clothes|glass|metal|paper|plastic|trash|biological)_?\d+", "bo new11k (<lop>_N)"),
]
def prefix_source(name):
    for rx, lab in PREFIX_RULES:
        if re.match(rx, name, re.I):
            return lab
    return "khac/khong nhan dien (" + re.sub(r"\d+", "N", Path(name).stem)[:20] + ")"

# ---- MD5 pools of local raw sources (to cross-check prefix rule) ----
POOLS = {
    "new11k (C:/Users/admin/Documents/dataset/dataset)": Path("C:/Users/admin/Documents/dataset/dataset"),
    "archive/Data/Garbage_Classification": ROOT / "archive/Data/Garbage_Classification",
    "dataset_sach_zip": ROOT / "dataset_sach_zip",
    "downloads/commons_pin": ROOT / "downloads/commons_pin", "downloads/commons_clothes": ROOT / "downloads/commons_clothes",
    "downloads/oi": ROOT / "downloads/oi", "downloads/realwaste": ROOT / "downloads/realwaste",
    "downloads/rw5": ROOT / "downloads/rw5", "downloads/mta": ROOT / "downloads/mta", "downloads/rise": ROOT / "downloads/rise",
    "downloads/npcg": ROOT / "downloads/npcg", "downloads/trashbusters": ROOT / "downloads/trashbusters",
}
pool_md5 = defaultdict(set)
for name, d in POOLS.items():
    if not d.exists():
        continue
    for p in d.rglob("*"):
        if is_img(p):
            pool_md5[md5(p)].add(name)
tz = ROOT / "trashnet/data/dataset-resized.zip"
if tz.exists():
    with zipfile.ZipFile(tz) as z:
        for n in z.namelist():
            if Path(n).suffix.lower() in SUPPORTED_EXTENSIONS and not n.startswith("__MACOSX"):
                pool_md5[hashlib.md5(z.read(n)).hexdigest()].add("TrashNet (trashnet/data/dataset-resized.zip)")

inv = {"datasets": {}, "diffs": {}, "splits": {}, "realworld": {}, "realworld_cross": {}}
md5_index = {}

def scan_class_dirs(base):
    res = {}
    for cd in sorted(p for p in base.iterdir() if p.is_dir()):
        files = sorted(p for p in cd.iterdir() if p.is_file())
        res[cd.name] = ([p for p in files if is_img(p)], [p for p in files if not is_img(p)])
    return res

for ds in DATASETS:
    base = ROOT / ds
    per = {}; all_md5 = Counter(); idx = {}
    for cls, (imgs, others) in scan_class_dirs(base).items():
        hs = [md5(p) for p in imgs]
        c = Counter(hs)
        dup_extra = sum(v - 1 for v in c.values() if v > 1)
        src = Counter(prefix_source(p.name) for p in imgs)
        pool = Counter()
        for h in hs:
            pool[" + ".join(sorted(pool_md5[h])) if h in pool_md5 else "(khong khop pool cuc bo nao)"] += 1
        per[cls] = {"so_anh": len(imgs), "so_file_khong_phai_anh": len(others),
                    "ext_khong_phai_anh": dict(Counter(p.suffix.lower() for p in others)),
                    "so_md5_duy_nhat": len(c), "so_file_trung_md5_thua": dup_extra,
                    "nguon_theo_tien_to": dict(src.most_common()), "nguon_theo_md5_pool": dict(pool.most_common())}
        all_md5.update(hs)
        for p, h in zip(imgs, hs):
            idx[f"{cls}/{p.name}"] = h
    tot = sum(v["so_anh"] for v in per.values())
    h2cls = defaultdict(set)
    for k, v in idx.items():
        h2cls[v].add(k.split("/")[0])
    inv["datasets"][ds] = {"per_class": per, "tong_anh": tot, "so_md5_duy_nhat_toan_bo": len(all_md5),
        "so_file_trung_md5_thua_toan_bo": tot - len(all_md5),
        "md5_xuat_hien_o_nhieu_lop": sum(1 for s in h2cls.values() if len(s) > 1),
        "tong_theo_nguon_tien_to": dict(sum((Counter(v["nguon_theo_tien_to"]) for v in per.values()), Counter()).most_common()),
        "mtime_moi_nhat": max(os.path.getmtime(ROOT / ds / k) for k in idx)}
    md5_index[ds] = idx
    print("dataset", ds, tot, flush=True)

order = ["dataset_8lop", "dataset_8lop_v2", "dataset_8lop_v3", "dataset_8lop_v4", "dataset_8lop_v5", "dataset_8lop_v6a", "dataset_8lop_v6b"]
pairs = list(zip(order, order[1:])) + [("dataset_8lop_v5", "dataset_8lop_v6b")]
for a, b in pairs:
    d = {}
    for cls in CLASSES:
        A = inv["datasets"][a]["per_class"].get(cls, {"so_anh": 0}); B = inv["datasets"][b]["per_class"].get(cls, {"so_anh": 0})
        ha = {v for k, v in md5_index[a].items() if k.startswith(cls + "/")}
        hb = {v for k, v in md5_index[b].items() if k.startswith(cls + "/")}
        added = [k for k, v in md5_index[b].items() if k.startswith(cls + "/") and v not in ha]
        d[cls] = {"truoc": A["so_anh"], "sau": B["so_anh"], "chenh": B["so_anh"] - A["so_anh"],
                  "md5_moi": len(hb - ha), "md5_bi_bo": len(ha - hb),
                  "nguon_anh_moi": dict(Counter(prefix_source(k.split('/', 1)[1]) for k in added).most_common())}
    inv["diffs"][f"{a}->{b}"] = {"per_class": d, "tong_truoc": inv["datasets"][a]["tong_anh"], "tong_sau": inv["datasets"][b]["tong_anh"],
                                 "chenh_tong": inv["datasets"][b]["tong_anh"] - inv["datasets"][a]["tong_anh"]}

# ---- splits ----
split_md5 = {}
for run, ds in RUNS.items():
    seed = RUN_SEED.get(run, 42)
    s = discover_and_split(ROOT / ds, seed=seed)
    summ = s.summary()
    saved_p = ROOT / "garbage_classifier/artifacts" / run / "dataset_split.json"
    saved = json.loads(saved_p.read_text()) if saved_p.exists() else None
    match = saved is not None and all(saved[k] == summ[k] for k in ("train", "val", "test")) and saved["classes"] == summ["classes"]
    ck = ROOT / "garbage_classifier/artifacts" / run / "best_model.pt"
    inv["splits"][run] = {"dataset": ds, "seed": seed, "train_ratio": 0.70, "val_ratio": 0.15, "summary": summ,
        "khop_dataset_split_json_da_luu": match,
        "dataset_mtime_moi_nhat_truoc_best_model": inv["datasets"][ds]["mtime_moi_nhat"] < os.path.getmtime(ck)}
    split_md5[run] = {k: {md5(x.path): s.classes[x.label] for x in getattr(s, k)} for k in ("train", "val", "test")}
    tr = set(split_md5[run]["train"])
    inv["splits"][run]["test_trung_md5_voi_train"] = sum(1 for x in s.test if md5(x.path) in tr)
    inv["splits"][run]["val_trung_md5_voi_train"] = sum(1 for x in s.val if md5(x.path) in tr)
    inv["splits"][run]["test_trung_md5_voi_train_theo_lop"] = dict(Counter(s.classes[x.label] for x in s.test if md5(x.path) in tr))
    print("split", run, flush=True)

# ---- realworld ----
rw_md5 = {}
for rw in REALWORLD:
    base = ROOT / rw
    per = {}; seen = set(); hs_all = []
    for cd in sorted(p for p in base.iterdir() if p.is_dir()):
        imgs = sorted(p for p in cd.iterdir() if is_img(p))
        hs = [md5(p) for p in imgs]
        uniq_in_class = 0
        for h in hs:
            if h not in seen:
                seen.add(h); uniq_in_class += 1
        per[cd.name.lower()] = {"so_anh_tho": len(imgs), "so_anh_sau_bo_trung_md5_thu_tu_realworld_py": uniq_in_class}
        hs_all += [(cd.name.lower(), h, p.name) for h, p in zip(hs, imgs)]
    rw_md5[rw] = hs_all
    inv["realworld"][rw] = {"per_class": per, "tong_tho": len(hs_all), "tong_sau_bo_trung": len(seen),
                            "so_file_trung_thua": len(hs_all) - len(seen),
                            "co_manifest": (base / "manifest.json").exists()}
    ov = {}
    for ds in DATASETS:
        dsh = set(md5_index[ds].values())
        ov[ds] = len({h for _, h, _ in hs_all if h in dsh})
    inv["realworld"][rw]["md5_duy_nhat_trung_voi_dataset"] = ov
    inv["realworld"][rw]["md5_duy_nhat_trung_voi_split"] = {
        run: {k: len({h for _, h, _ in hs_all if h in split_md5[run][k]}) for k in ("train", "val", "test")} for run in RUNS}
for i, a in enumerate(REALWORLD):
    for b in REALWORLD[i + 1:]:
        n = len({h for _, h, _ in rw_md5[a]} & {h for _, h, _ in rw_md5[b]})
        if n:
            inv["realworld_cross"][f"{a}&{b}"] = n
ha = {h: (c, f) for c, h, f in rw_md5["realworld_test"]}
inv["realworld_test_vs_test2_chi_tiet"] = [[ha[h], [c, f]] for c, h, f in rw_md5["realworld_test2"] if h in ha]

(ROOT / "audit/inventory.json").write_text(json.dumps(inv, ensure_ascii=False, indent=1), encoding="utf-8")
(ROOT / "audit/md5_index.json").write_text(json.dumps(md5_index), encoding="utf-8")
print("ok")
