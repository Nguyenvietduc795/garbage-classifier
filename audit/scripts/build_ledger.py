"""Gom ket qua thanh audit/numbers_ledger.json.
Dau vao: audit/inventory.json, audit/model_identity.json, audit/eval_test/*.json,
         audit/eval_realworld/*_probs.json, audit/eval_realworld/official/*.json
Chay (tu C:/AL-PLR): python audit/scripts/build_ledger.py"""
import json
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "audit"
PY = "garbage_classifier/.venv/Scripts/python.exe"
CMD_INV = f"PYTHONPATH=garbage_classifier/src {PY} audit/scripts/inventory.py  (cwd C:/AL-PLR)"
CMD_ID = f"{PY} audit/scripts/identify_models.py > audit/model_identity.json  (cwd C:/AL-PLR)"
CMD_TEST = "PYTHONPATH=src .venv/Scripts/python.exe ../audit/scripts/eval_test_split.py v2_r18 v3_r18 v4_r18 v5_r18 v5_r18_s1 v5_r18_s2 v6a_r18 v6b_r18  (cwd C:/AL-PLR/garbage_classifier)"
CMD_RW = "PYTHONPATH=src .venv/Scripts/python.exe ../audit/scripts/eval_realworld_probs.py v2_r18 v3_r18 v4_r18 v5_r18 v5_r18_s1 v5_r18_s2 v6a_r18 v6b_r18  (cwd C:/AL-PLR/garbage_classifier); tong hop: python audit/scripts/build_ledger.py"
CMD_OFF = "bash audit/scripts/run_realworld_official.sh  (goi garbage_classifier.realworld --nguong-pin {th} --output ...)"

GROUP = {"organic": "huu-co", "battery": "nguy-hiem", "cardboard": "tai-che", "glass": "tai-che", "metal": "tai-che",
         "paper": "tai-che", "plastic": "tai-che", "clothes": "khong-tai-che"}
GROUPS = ["huu-co", "nguy-hiem", "tai-che", "khong-tai-che"]
L = []

def pct(t, m):
    if not m:
        return None
    f = Fraction(100 * t, m)  # chinh xac, roi lam tron half-up 1 chu so
    return float((Decimal(f.numerator) / Decimal(f.denominator)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))

def add(name, ver, val, tu, mau, cmd, src):
    L.append({"ten_chi_so": name, "phien_ban": ver, "gia_tri": val, "tu_so": tu, "mau_so": mau,
              "lenh_tao_ra": cmd, "file_nguon": src})

def addp(name, ver, tu, mau, cmd, src):
    add(name, ver, pct(tu, mau), tu, mau, cmd, src)

# ---------- model identity ----------
mid = json.loads((A / "model_identity.json").read_text(encoding="utf-8"))
for f, d in mid["backend"].items():
    add(f"{f.replace(chr(92), '/')}.trong_so_trung_voi", d["closest"].split("/")[0], d["closest"], None, None, CMD_ID,
        "audit/model_identity.json")
    add(f"{f.replace(chr(92), '/')}.max_abs_diff_state_dict", d["closest"].split("/")[0], d["max_abs_diff_by_ckpt"][d["closest"]],
        None, None, CMD_ID, "audit/model_identity.json")
for m, d in mid["tfjs"].items():
    add(f"frontend/models/{m}.fc_trung_voi", d["closest"].split("/")[0], d["closest"], None, None, CMD_ID, "audit/model_identity.json")
    add(f"frontend/models/{m}.fc_max_abs_diff", d["closest"].split("/")[0], d["fc_max_abs_diff_top5"][d["closest"]], None, None, CMD_ID,
        "audit/model_identity.json")

# ---------- inventory ----------
inv = json.loads((A / "inventory.json").read_text(encoding="utf-8"))
SRC_INV = "audit/inventory.json"
for ds, d in inv["datasets"].items():
    add(f"{ds}.tong.so_anh", ds, d["tong_anh"], d["tong_anh"], None, CMD_INV, SRC_INV)
    add(f"{ds}.tong.so_md5_duy_nhat", ds, d["so_md5_duy_nhat_toan_bo"], d["so_md5_duy_nhat_toan_bo"], None, CMD_INV, SRC_INV)
    add(f"{ds}.tong.so_file_trung_md5_thua", ds, d["so_file_trung_md5_thua_toan_bo"], d["so_file_trung_md5_thua_toan_bo"], None, CMD_INV, SRC_INV)
    add(f"{ds}.tong.md5_xuat_hien_o_nhieu_lop", ds, d["md5_xuat_hien_o_nhieu_lop"], d["md5_xuat_hien_o_nhieu_lop"], None, CMD_INV, SRC_INV)
    for src, n in d["tong_theo_nguon_tien_to"].items():
        add(f"{ds}.tong.nguon[{src}].so_anh", ds, n, n, None, CMD_INV, SRC_INV)
    for cls, c in d["per_class"].items():
        add(f"{ds}.{cls}.so_anh", ds, c["so_anh"], c["so_anh"], None, CMD_INV, SRC_INV)
        add(f"{ds}.{cls}.so_file_trung_md5_thua", ds, c["so_file_trung_md5_thua"], c["so_file_trung_md5_thua"], None, CMD_INV, SRC_INV)
        if c["so_file_khong_phai_anh"]:
            add(f"{ds}.{cls}.so_file_khong_phai_anh", ds, c["so_file_khong_phai_anh"], c["so_file_khong_phai_anh"], None, CMD_INV, SRC_INV)
        for src, n in c["nguon_theo_tien_to"].items():
            add(f"{ds}.{cls}.nguon[{src}].so_anh", ds, n, n, None, CMD_INV, SRC_INV)
        for src, n in c["nguon_theo_md5_pool"].items():
            add(f"{ds}.{cls}.md5_khop_pool[{src}].so_anh", ds, n, n, None, CMD_INV, SRC_INV)
for pair, d in inv["diffs"].items():
    add(f"chenh_lech.{pair}.tong", pair, d["chenh_tong"], d["tong_sau"], d["tong_truoc"], CMD_INV, SRC_INV)
    for cls, c in d["per_class"].items():
        add(f"chenh_lech.{pair}.{cls}.so_anh", pair, c["chenh"], c["sau"], c["truoc"], CMD_INV, SRC_INV)
        add(f"chenh_lech.{pair}.{cls}.md5_moi", pair, c["md5_moi"], c["md5_moi"], None, CMD_INV, SRC_INV)
        add(f"chenh_lech.{pair}.{cls}.md5_bi_bo", pair, c["md5_bi_bo"], c["md5_bi_bo"], None, CMD_INV, SRC_INV)
        for src, n in c["nguon_anh_moi"].items():
            add(f"chenh_lech.{pair}.{cls}.anh_moi_nguon[{src}]", pair, n, n, None, CMD_INV, SRC_INV)
for run, s in inv["splits"].items():
    for part in ("train", "val", "test"):
        add(f"{run}.split.{part}.tong", run, s["summary"][part]["total"], s["summary"][part]["total"], None, CMD_INV, SRC_INV)
        for cls, n in s["summary"][part]["per_class"].items():
            add(f"{run}.split.{part}.{cls}", run, n, n, None, CMD_INV, SRC_INV)
    add(f"{run}.split.khop_dataset_split_json_da_luu", run, s["khop_dataset_split_json_da_luu"], None, None, CMD_INV, SRC_INV)
    add(f"{run}.split.dataset_khong_doi_sau_khi_train(mtime)", run, s["dataset_mtime_moi_nhat_truoc_best_model"], None, None, CMD_INV, SRC_INV)
    addp(f"{run}.split.test_trung_md5_voi_train", run, s["test_trung_md5_voi_train"], s["summary"]["test"]["total"], CMD_INV, SRC_INV)
    addp(f"{run}.split.val_trung_md5_voi_train", run, s["val_trung_md5_voi_train"], s["summary"]["val"]["total"], CMD_INV, SRC_INV)
for rw, d in inv["realworld"].items():
    add(f"{rw}.tong_tho", "du_lieu", d["tong_tho"], d["tong_tho"], None, CMD_INV, SRC_INV)
    add(f"{rw}.tong_sau_bo_trung_md5", "du_lieu", d["tong_sau_bo_trung"], d["tong_sau_bo_trung"], None, CMD_INV, SRC_INV)
    add(f"{rw}.so_file_trung_md5_thua", "du_lieu", d["so_file_trung_thua"], d["so_file_trung_thua"], None, CMD_INV, SRC_INV)
    for cls, c in d["per_class"].items():
        add(f"{rw}.{cls}.so_anh_tho", "du_lieu", c["so_anh_tho"], c["so_anh_tho"], None, CMD_INV, SRC_INV)
        add(f"{rw}.{cls}.so_anh_sau_bo_trung", "du_lieu", c["so_anh_sau_bo_trung_md5_thu_tu_realworld_py"],
            c["so_anh_sau_bo_trung_md5_thu_tu_realworld_py"], None, CMD_INV, SRC_INV)
    for ds, n in d["md5_duy_nhat_trung_voi_dataset"].items():
        if n:
            addp(f"{rw}.anh_trung_md5_voi[{ds}]", ds, n, d["tong_sau_bo_trung"], CMD_INV, SRC_INV)
    for run, parts in d["md5_duy_nhat_trung_voi_split"].items():
        for part, n in parts.items():
            if n:
                addp(f"{rw}.anh_trung_md5_voi[{run}.{part}]", run, n, d["tong_sau_bo_trung"], CMD_INV, SRC_INV)
for pair, n in inv["realworld_cross"].items():
    add(f"realworld_trung_md5_giua_bo[{pair}]", "du_lieu", n, n, None, CMD_INV, SRC_INV)

# ---------- internal test ----------
for f in sorted((A / "eval_test").glob("*.json")):
    r = json.loads(f.read_text(encoding="utf-8"))
    run = r["run"]; src = f"audit/eval_test/{f.name}"
    addp(f"{run}.test_noi_bo.accuracy", run, r["dung"], r["n_test"], CMD_TEST, src)
    for cls, c in r["per_class"].items():
        addp(f"{run}.test_noi_bo.{cls}.accuracy", run, c["dung"], c["tong"], CMD_TEST, src)
    add(f"{run}.test_noi_bo.confusion_8lop(hang=that,cot=du_doan,thu_tu={','.join(r['classes'])})", run, r["confusion_matrix"], None, None, CMD_TEST, src)
    for key, lab in (("group_confusion_argmax", "argmax"), ("group_confusion_pin0.5", "luat_pin0.5"), ("group_confusion_pin0.3", "luat_pin0.3")):
        m = r[key]
        addp(f"{run}.test_noi_bo.4nhom_{lab}.accuracy", run, sum(m[i][i] for i in range(4)), sum(map(sum, m)), CMD_TEST, src)
        add(f"{run}.test_noi_bo.4nhom_{lab}.confusion(hang=that,cot=du_doan,thu_tu={','.join(GROUPS)})", run, m, None, None, CMD_TEST, src)
        addp(f"{run}.test_noi_bo.4nhom_{lab}.pin_dung", run, m[1][1], sum(m[1]), CMD_TEST, src)
        fp = sum(m[i][1] for i in range(4) if i != 1)
        addp(f"{run}.test_noi_bo.4nhom_{lab}.bao_nham_pin", run, fp, sum(sum(m[i]) for i in range(4) if i != 1), CMD_TEST, src)

# ---------- realworld ----------
def decide(p, classes, th):
    ib = classes.index("battery")
    if p[ib] >= th:
        return "nguy-hiem"
    q = list(p); q[ib] = -1
    return GROUP[classes[max(range(len(q)), key=q.__getitem__)]]

for f in sorted((A / "eval_realworld").glob("*_probs.json")):
    r = json.loads(f.read_text(encoding="utf-8"))
    run = r["run"]; classes = r["classes"]; src = f"audit/eval_realworld/{f.name}"
    for s, d in r["sets"].items():
        recs = d["records"]; n = len(recs)
        add(f"{s}.{run}.so_anh_truoc_bo_trung", run, d["raw"], d["raw"], None, CMD_RW, src)
        add(f"{s}.{run}.so_anh_sau_bo_trung", run, n, n, None, CMD_RW, src)
        add(f"{s}.{run}.so_anh_duoc_tang_sang", run, sum(x["tang_sang"] for x in recs), sum(x["tang_sang"] for x in recs), n, CMD_RW, src)
        for th in (0.5, 0.3):
            tag = f"{s}.{run}.nguong{th}"
            m = [[0] * 4 for _ in range(4)]; per = {}
            for x in recs:
                g = decide(x["p_web"], classes, th); t = GROUP[x["loai"]]
                m[GROUPS.index(t)][GROUPS.index(g)] += 1
                pc = per.setdefault(x["loai"], [0, 0]); pc[0] += g == t; pc[1] += 1
            dung = sum(m[i][i] for i in range(4))
            addp(f"{tag}.dung_4nhom", run, dung, n, CMD_RW, src)
            add(f"{tag}.confusion_4nhom(hang=that,cot=du_doan,thu_tu={','.join(GROUPS)})", run, m, None, None, CMD_RW, src)
            for cls, (a, b) in per.items():
                addp(f"{tag}.{cls}.dung_4nhom", run, a, b, CMD_RW, src)
            nb = sum(m[1]); nonb = n - nb
            if nb:
                addp(f"{tag}.pin_dung", run, m[1][1], nb, CMD_RW, src)
            if nonb:
                addp(f"{tag}.khong_phai_pin_bi_bao_pin", run, sum(m[i][1] for i in range(4) if i != 1), nonb, CMD_RW, src)
        # backend rule (app.py): no brightening, argmax 8 lop -> nhom, confidence = tong xac suat nhom, NGUONG_TIN_CAY 0.50
        m = [[0] * 4 for _ in range(4)]; low = 0
        for x in recs:
            p = x["p_backend"]; top = max(range(len(p)), key=p.__getitem__); g = GROUP[classes[top]]
            conf = sum(pp for c, pp in zip(classes, p) if GROUP[c] == g)
            low += conf < 0.50
            m[GROUPS.index(GROUP[x["loai"]])][GROUPS.index(g)] += 1
        addp(f"{s}.{run}.luat_backend.dung_4nhom", run, sum(m[i][i] for i in range(4)), n, CMD_RW, src)
        addp(f"{s}.{run}.luat_backend.duoi_nguong_tin_cay_0.50", run, low, n, CMD_RW, src)
        nb = sum(m[1])
        if nb:
            addp(f"{s}.{run}.luat_backend.pin_dung", run, m[1][1], nb, CMD_RW, src)

# official realworld.py cross-check
for f in sorted((A / "eval_realworld/official").glob("*.json")):
    run, th = f.stem.split("_pin")
    r = json.loads(f.read_text(encoding="utf-8"))
    for s, d in r.items():
        if s in ("realworld_test", "realworld_test2"):
            continue  # realworld.py luu theo ten thu muc: realworld_loai_bo/realworld_test ghi de -> lay tu stdout ben duoi
        addp(f"doi_chieu_realworld_py.{s}.{run}.nguong{th}.dung_4nhom", run, d["dung"], d["tong"], CMD_OFF.format(th=th),
             f"audit/eval_realworld/official/{f.name}")

import re
stdout = A / "eval_realworld/official/stdout.txt"
if stdout.exists():
    run = th = None; seen = set()
    for line in stdout.read_text(encoding="utf-8").splitlines():
        m = re.match(r"### (\S+) nguong (\S+)", line)
        if m:
            run, th = m.groups(); seen = set(); continue
        m = re.match(r"(realworld_test2?): (\d+)/(\d+)", line)
        if m and m.group(1) not in seen:  # lan in dau = bo goc; lan sau = realworld_loai_bo/...
            seen.add(m.group(1))
            addp(f"doi_chieu_realworld_py.{m.group(1)}.{run}.nguong{th}.dung_4nhom", run, int(m.group(2)), int(m.group(3)),
                 CMD_OFF.format(th=th) + " (lay tu stdout)", "audit/eval_realworld/official/stdout.txt")

(A / "numbers_ledger.json").write_text(json.dumps(L, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(L), "muc")
