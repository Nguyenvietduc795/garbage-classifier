"""Dung dataset_8lop_v6: v5 + 2 lop moi `shoes`, `trash` (10 lop).

- Tach tu v5: clothes/shoes_* -> shoes; plastic/bdw_Chips_packet*, paper/bdw_Coffee_cup* -> trash.
- Them vao trash: RealWaste Miscellaneous Trash, MTA (s-litter, m-composite; train + valid,
  khong lay test vi do la realworld_mta_test), VN Trash Foam_box (chi anh chup that),
  sumn2u trash, TACO (xop, giay an, vo snack, ong hut, coc giay, gang tay; khong lay
  "Plastic film" vi phan lon la tui/mang nilon), UGV Cocksheet (xop).
  Tach tu v5: 38 crop MTA plastic-film la vo snack (mta_film_vo_snack.txt) -> trash.
  Them vao shoes: TACO Shoe, UGV-NBWASTE Plastic Sandal (UGV chi dung khi da tai tay).
- Loc trung dHash 64 bit (Hamming <= --nguong): anh moi trung voi anh v5, voi cac bo
  realworld_* hoac voi anh moi da them truoc do thi bo.

Chay tu thu muc goc repo:
    uv run --project garbage_classifier python garbage_classifier/scripts/build_dataset_v6.py
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, ImageOps

IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def list_images(d: Path) -> list[Path]:
    return sorted(p for p in d.rglob("*") if p.suffix.lower() in IMG_EXT)


def dhash(path: Path) -> int:
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im).convert("L").resize((9, 8), Image.Resampling.LANCZOS)
        px = im.tobytes()
    h = 0
    for r in range(8):
        for c in range(8):
            h = (h << 1) | (px[r * 9 + c] > px[r * 9 + c + 1])
    return h


class HashIndex:
    """Tim hash gan (Hamming <= k) bang cach chia 64 bit thanh k+1 doan (nguyen ly Dirichlet)."""

    def __init__(self, k: int):
        self.k = k
        self.n = k + 1
        bounds = [round(i * 64 / self.n) for i in range(self.n + 1)]
        self.segs = list(zip(bounds[:-1], bounds[1:]))
        self.buckets = [defaultdict(list) for _ in self.segs]

    def _keys(self, h: int):
        for i, (a, b) in enumerate(self.segs):
            yield i, (h >> a) & ((1 << (b - a)) - 1)

    def add(self, h: int, tag: str) -> None:
        for i, key in self._keys(h):
            self.buckets[i][key].append((h, tag))

    def find(self, h: int) -> str | None:
        for i, key in self._keys(h):
            for h2, tag in self.buckets[i][key]:
                if bin(h ^ h2).count("1") <= self.k:
                    return tag
        return None


def crop_save(img_path: Path, box: tuple[float, float, float, float], out: Path,
              exif: bool = False, pad: float = 0.1) -> None:
    with Image.open(img_path) as im:
        if exif:
            im = ImageOps.exif_transpose(im)
        im = im.convert("RGB")
        x, y, w, h = box
        px, py = w * pad, h * pad
        l, t = max(0, x - px), max(0, y - py)
        r, b = min(im.width, x + w + px), min(im.height, y + h + py)
        im.crop((int(l), int(t), int(r), int(b))).save(out, quality=95)


MAX_RATIO = 3.0  # crop dai qua (ong hut, que xien) bi meo khi resize ve 224x224


def box_ok(w: float, h: float, min_side: int) -> bool:
    return min(w, h) >= min_side and max(w, h) / min(w, h) <= MAX_RATIO


def coco_crops(ann_file: Path, img_dir: Path, wanted: dict[str, str], min_side: int):
    """Sinh (anh, bbox, lop dich, ten loai goc, id, (w, h)) tu file COCO."""
    d = json.loads(ann_file.read_text(encoding="utf-8"))
    cats = {c["id"]: c["name"] for c in d["categories"]}
    imgs = {i["id"]: i for i in d["images"]}
    for a in d["annotations"]:
        name = cats[a["category_id"]]
        if name not in wanted or not box_ok(*a["bbox"][2:], min_side):
            continue
        info = imgs[a["image_id"]]
        p = img_dir / info["file_name"]
        if p.exists():
            yield p, a["bbox"], wanted[name], name, a["id"], (info["width"], info["height"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="dataset_8lop_v5")
    ap.add_argument("--out", default="dataset_8lop_v6")
    ap.add_argument("--downloads", default="downloads")
    ap.add_argument("--nguong", type=int, default=4, help="Hamming toi da de coi la trung")
    ap.add_argument("--min-side", type=int, default=64, help="Bo crop co canh ngan hon (px)")
    ap.add_argument("--khong-vo-snack", action="store_true",
                    help="Dung ban v6 dau tien: khong them vo snack/coc giay/ong hut chup that")
    args = ap.parse_args()

    base, out, dl = Path(args.base), Path(args.out), Path(args.downloads)
    if out.exists():
        shutil.rmtree(out)

    # 1. Copy v5 (hard link), tach anh sang lop moi
    # Crop MTA plastic-film trong v5 da xem tay: vo snack, giay goi do an, ong hut -> trash
    # (con lai la tui nilon, mang trong nen giu o plastic)
    vo_snack = set() if args.khong_vo_snack else set(
        (Path(__file__).parent / "mta_film_vo_snack.txt").read_text().split())

    def lop_tu_v5(cls: str, name: str) -> str:
        if cls == "clothes" and name.startswith("shoes_"):
            return "shoes"
        if cls == "plastic" and (name.startswith("bdw_Chips_packet") or name in vo_snack):
            return "trash"
        if cls == "paper" and name.startswith("bdw_Coffee_cup"):
            return "trash"
        return cls

    base_files: list[Path] = []
    moved = Counter()
    for p in list_images(base):
        cls = lop_tu_v5(p.parent.name, p.name)
        dst = out / cls / p.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        os.link(p, dst)
        base_files.append(dst)
        if cls != p.parent.name:
            moved[f"{p.parent.name} -> {cls}"] += 1
    (out / "trash").mkdir(exist_ok=True)

    # 2. Anh moi: (duong dan dich, nguon)
    new: list[tuple[Path, str]] = []

    def them_file(src: Path, cls: str, name: str, nguon: str) -> None:
        dst = out / cls / name
        shutil.copy2(src, dst)
        new.append((dst, nguon))

    def them_crop(src, box, cls, name, nguon, exif=False):
        dst = out / cls / name
        crop_save(src, box, dst, exif=exif)
        new.append((dst, nguon))

    # Anh nhom tu chup, da gan nhan theo thu muc con (anh_tu_chup/<lop>/)
    for p in list_images(Path("anh_tu_chup")):
        them_file(p, p.parent.name, p.name, "Nhom tu chup")

    rw = dl / "realwaste/realwaste-main/RealWaste/Miscellaneous Trash"
    for p in list_images(rw):
        them_file(p, "trash", f"rw_{p.name}", "RealWaste Misc Trash")

    mta_want = {"s-litter": "trash", "m-composite": "trash"}
    for split in ("train", "valid"):
        d = dl / "mta" / split
        for p, box, cls, cat, aid, _ in coco_crops(d / "_annotations.coco.json", d, mta_want, args.min_side):
            them_crop(p, box, cls, f"mta7_{split[0]}{aid}.jpg", f"MTA {cat}")

    # Chi giu anh chup that: hop_xop_* (frame video) va IMG* (dien thoai). Phan con lai la
    # anh stock/quang cao, co ca hop nhua, hop nhom bi gan nham la hop xop.
    for p in list_images(dl / "vntrash/VN_trash_classification"):
        if p.parent.name == "Foam_box" and p.name.lower().startswith(("hop_xop", "img")):
            them_file(p, "trash", f"vnt_{p.parent.parent.name[:2].lower()}_{p.name}", "VN Trash Foam_box")

    # Ban mirror HF (19.762 anh, lop trash 947) cua sumn2u Garbage Classification v2
    for p in list_images(dl / "sumn2u_hf/trash"):
        them_file(p, "trash", p.name, "sumn2u trash")

    taco_want = {"Styrofoam piece": "trash", "Foam cup": "trash", "Foam food container": "trash",
                 "Tissues": "trash", "Crisp packet": "trash", "Other plastic wrapper": "trash",
                 "Paper cup": "trash", "Plastic straw": "trash", "Plastic glooves": "trash",
                 "Shoe": "shoes"}
    if args.khong_vo_snack:
        for k in ("Other plastic wrapper", "Paper cup", "Plastic straw", "Plastic glooves"):
            del taco_want[k]
    taco = dl / "taco"
    for p, box, cls, cat, aid, wh in coco_crops(taco / "annotations.json", taco / "img", taco_want, 80):
        with Image.open(p) as im:
            exif = im.size != wh  # bbox TACO tinh tren anh da xoay theo EXIF
        them_crop(p, box, cls, f"taco_{aid}.jpg", f"TACO {cat}", exif=exif)

    # UGV-NBWASTE (tai tay "Download All" tren Mendeley, giai nen vao downloads/ugv_yolo):
    # YOLO-OBB, moi dong nhan: lop x1 y1 ... x4 y4 (chuan hoa 0..1) -> lay hop bao thang.
    ugv_want = {"plastic sandal": "shoes", "cocksheet": "trash"}
    ugv = dl / "ugv_yolo"
    yaml = next(ugv.rglob("data.yaml"), None) if ugv.exists() else None
    if yaml:
        m = re.search(r"names:\s*\[(.*?)\]", yaml.read_text(encoding="utf-8"), re.S)
        names = [n.strip().strip("'\"").lower() for n in m.group(1).split(",")] if m else []
        for lbl in sorted(ugv.rglob("labels/*.txt")):
            img = next((q for q in lbl.parent.parent.joinpath("images").glob(lbl.stem + ".*")), None)
            if img is None:
                continue
            with Image.open(img) as im:
                W, H = im.size
            for k, line in enumerate(lbl.read_text().split("\n")):
                v = line.split()
                if len(v) != 9 or int(v[0]) >= len(names) or names[int(v[0])] not in ugv_want:
                    continue
                xs = [float(t) * W for t in v[1::2]]
                ys = [float(t) * H for t in v[2::2]]
                x, y = min(xs), min(ys)
                w, h = max(xs) - x, max(ys) - y
                if box_ok(w, h, args.min_side):
                    cat = names[int(v[0])]
                    them_crop(img, (x, y, w, h), ugv_want[cat],
                              f"ugv_{lbl.parent.parent.name[:2]}_{lbl.stem[:40]}_{k}.jpg", f"UGV {cat}")

    # 3. Loc trung dHash
    idx = HashIndex(args.nguong)
    for d in sorted(Path(".").glob("realworld_*")):
        for p in list_images(d):
            idx.add(dhash(p), f"test:{d.name}")
    for p in base_files:
        idx.add(dhash(p), f"v5:{p.parent.name}")

    kept, dropped = Counter(), Counter()
    reasons = Counter()
    for p, nguon in new:
        try:
            h = dhash(p)
        except Exception:
            p.unlink(); dropped[nguon] += 1; reasons["loi doc anh"] += 1
            continue
        tag = idx.find(h)
        if tag:
            p.unlink(); dropped[nguon] += 1; reasons[tag.split(":")[0] + ":" + tag.split(":")[1]] += 1
            continue
        idx.add(h, f"new:{p.parent.name}")
        kept[(p.parent.name, nguon)] += 1

    counts = {c.name: len(list_images(c)) for c in sorted(out.iterdir()) if c.is_dir()}
    report = {
        "base": str(base), "nguong_hamming": args.nguong, "min_side": args.min_side,
        "tach_tu_v5": dict(moved),
        "them_moi": {f"{c} <- {n}": v for (c, n), v in sorted(kept.items())},
        "bo_vi_trung": dict(dropped), "ly_do_bo": dict(reasons),
        "so_anh_moi_lop": counts, "tong": sum(counts.values()),
    }
    (out.parent / f"{out.name}_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
