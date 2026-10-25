"""Vong 2 - dem anh dataset theo lop va theo nguon; dem bo anh that (truoc/sau bo trung MD5, pin);
trung MD5 giua curated/test/test2. Ghi audit/round2/datasets.json.

Cach nhan dien nguon (tien to ten file, phan truoc dau '_' dau tien):
  - mta_, rw_, bower_, bdw_, cm_, oi_, gam_, ar_, new_ : nguon theo dung tien to do
  - tien to la ten lop (battery_, cardboard_, clothes_, glass_, metal_, paper_, plastic_) hoac shoes_
    -> nguon "goc" (anh goc khong co tien to nguon)
  - con lai -> "khac"
Chi dem file co duoi .jpg/.jpeg/.png/.webp (giong data.py).
Chay: python audit/round2/scripts/r2_datasets.py
"""
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(r"C:\AL-PLR")
EXT = {".jpg", ".jpeg", ".png", ".webp"}
DS = ["dataset_8lop", "dataset_8lop_v2", "dataset_8lop_v3", "dataset_8lop_v4", "dataset_8lop_v5"]
NAMED = {"mta", "rw", "bower", "bdw", "cm", "oi", "gam", "ar", "new"}
GOC = {"battery", "cardboard", "clothes", "glass", "metal", "paper", "plastic", "shoes", "organic"}
RW = ["realworld_test", "realworld_test2", "realworld_curated", "realworld_clothes_test", "realworld_pin_test",
      "realworld_mta_test", "realworld_bdw_test", "realworld_bower_test", "realworld_rw5_test",
      "realworld_loai_bo/realworld_test", "realworld_loai_bo/realworld_test2"]
GROUP = {"organic": "huu-co", "battery": "nguy-hiem", "clothes": "khong-tai-che"}


def source(name):
    p = name.split("_")[0].lower()
    if p in NAMED:
        return p
    if p in GOC:
        return "goc"
    return "khac"


def md5(f):
    return hashlib.md5(f.read_bytes()).hexdigest()


def main():
    out = {"datasets": {}, "realworld": {}}
    for d in DS:
        per_class, per_src, per_cls_src = {}, Counter(), defaultdict(Counter)
        for c in sorted(p for p in (ROOT / d).iterdir() if p.is_dir()):
            files = [f for f in c.iterdir() if f.is_file() and f.suffix.lower() in EXT]
            per_class[c.name] = len(files)
            for f in files:
                s = source(f.name)
                per_src[s] += 1
                per_cls_src[c.name][s] += 1
        out["datasets"][d] = {"per_class": per_class, "total": sum(per_class.values()),
                              "per_source": dict(per_src),
                              "per_class_source": {k: dict(v) for k, v in per_cls_src.items()}}
    # bo anh that: dedup giong realworld.py (thu muc lop sorted, file sorted, giu lan dau)
    hashes = {}
    for s in RW:
        seen, n_all, n_uniq, pin_all, pin_uniq, per = set(), 0, 0, 0, 0, Counter()
        hs = []
        for c in sorted(p for p in (ROOT / s).iterdir() if p.is_dir()):
            for f in sorted(c.iterdir()):
                if f.suffix.lower() not in EXT:
                    continue
                h = md5(f)
                n_all += 1
                pin_all += c.name.lower() == "battery"
                hs.append((h, c.name.lower()))
                if h in seen:
                    continue
                seen.add(h)
                n_uniq += 1
                pin_uniq += c.name.lower() == "battery"
                per[c.name.lower()] += 1
        hashes[s] = hs
        out["realworld"][s] = {"truoc_bo_trung": n_all, "sau_bo_trung": n_uniq, "pin_truoc": pin_all,
                               "pin_sau": pin_uniq, "theo_lop_sau_bo_trung": dict(per)}
    # trung giua curated / test / test2
    sets = {k: {h for h, _ in hashes[k]} for k in ["realworld_curated", "realworld_test", "realworld_test2"]}
    lab = {}
    for k in sets:
        for h, c in hashes[k]:
            lab.setdefault(h, set()).add(c)
    cur, t1, t2 = sets["realworld_curated"], sets["realworld_test"], sets["realworld_test2"]
    union = cur | t1 | t2
    pin_union = {h for h in union if "battery" in lab[h]}
    out["trung_md5"] = {
        "curated_va_test": len(cur & t1), "curated_va_test2": len(cur & t2), "test_va_test2": len(t1 & t2),
        "curated_va_test_hoac_test2": len(cur & (t1 | t2)), "ca_ba": len(cur & t1 & t2),
        "anh_khac_nhau_3_bo": len(union), "pin_khac_nhau_3_bo": len(pin_union),
        "curated_chi_rieng": len(cur - t1 - t2),
        "nhan_mau_thuan": sum(1 for h in union if len(lab[h]) > 1),
    }
    # 102 anh cu (test + test2 + loai_bo) co trung nhau khong
    old = [h for k in ["realworld_test", "realworld_test2", "realworld_loai_bo/realworld_test",
                       "realworld_loai_bo/realworld_test2"] for h, _ in hashes[k]]
    out["trung_md5"]["anh_102_cu_tong_file"] = len(old)
    out["trung_md5"]["anh_102_cu_khac_nhau"] = len(set(old))
    # trung giua bo anh that va dataset v5 (ro ri)
    v5 = {}
    for f in (ROOT / "dataset_8lop_v5").rglob("*"):
        if f.is_file() and f.suffix.lower() in EXT:
            v5[md5(f)] = f.parent.name
    out["trung_voi_dataset_v5"] = {s: sum(1 for h in {h for h, _ in hashes[s]} if h in v5) for s in RW}
    (ROOT / "audit" / "round2" / "datasets.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
