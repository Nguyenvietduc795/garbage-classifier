"""Do model tren cac bo anh that theo dung luat cua trang web (frontend/index.html).

- Resize(256) + CenterCrop(224) nhu luc train.
- Anh toi (do sang < 0,30) nang gamma toi do sang 0,45.
- P(pin) >= nguong thi bao nguy hai; duoi nguong chon loai cao nhat trong 7 loai con lai.
- Tinh dung theo 4 nhom; bo anh trung MD5 trong tung bo.

Chay: uv run python -m garbage_classifier.realworld --checkpoint artifacts/v5_r18/best_model.pt ../realworld_test ../realworld_clothes_test
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import torch
from PIL import Image
from torchvision import transforms

from .data import IMAGENET_MEAN, IMAGENET_STD, SUPPORTED_EXTENSIONS
from .model import load_checkpoint
from .utils import resolve_device

LOAI_VAO_NHOM = {
    "organic": "huu-co",
    "battery": "nguy-hiem",
    "cardboard": "tai-che", "glass": "tai-che", "metal": "tai-che", "paper": "tai-che", "plastic": "tai-che",
    "clothes": "khong-tai-che", "shoes": "khong-tai-che", "trash": "khong-tai-che",
}
NGUONG_TOI = 0.30
DO_SANG_DICH = 0.45


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Do model tren bo anh that (thu muc con = ten loai)")
    parser.add_argument("dirs", type=Path, nargs="+")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--nguong-pin", type=float, default=0.5)
    parser.add_argument("--chi-tiet", default="", help="In du doan tung anh cua loai nay, vd clothes")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    return parser.parse_args()


def can_bang_sang(x: torch.Tensor) -> torch.Tensor:
    sang = float((x * torch.tensor([0.299, 0.587, 0.114]).view(3, 1, 1)).sum(0).mean())
    if sang >= NGUONG_TOI or sang <= 0.01:
        return x
    gamma = max(0.35, math.log(DO_SANG_DICH) / math.log(sang))
    return x.clamp_min(1e-6).pow(gamma)


def main() -> None:
    args = parse_args()
    device = resolve_device(args.device)
    model, checkpoint = load_checkpoint(args.checkpoint.resolve(), device)
    model.eval()
    classes: list[str] = checkpoint["classes"]
    i_pin = classes.index("battery")
    to_tensor = transforms.Compose([transforms.Resize(256), transforms.CenterCrop(224), transforms.ToTensor()])
    normalize = transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)

    ket_qua = {}
    for thu_muc in args.dirs:
        dung = tong = bao_nham_pin = bao_nham_vai = 0
        theo_loai: dict[str, list[int]] = {}
        da_thay: set[str] = set()
        for lop_dir in sorted(p for p in thu_muc.iterdir() if p.is_dir()):
            loai = lop_dir.name.lower()
            if loai not in LOAI_VAO_NHOM:
                continue
            for f in sorted(lop_dir.iterdir()):
                if f.suffix.lower() not in SUPPORTED_EXTENSIONS:
                    continue
                md5 = hashlib.md5(f.read_bytes()).hexdigest()
                if md5 in da_thay:
                    continue
                da_thay.add(md5)
                with Image.open(f) as im:
                    x = normalize(can_bang_sang(to_tensor(im.convert("RGB"))))
                with torch.no_grad():
                    p = torch.softmax(model(x.unsqueeze(0).to(device)), 1)[0].cpu()
                khac_pin = p.clone()
                khac_pin[i_pin] = -1
                top = int(khac_pin.argmax())
                nhom = "nguy-hiem" if p[i_pin] >= args.nguong_pin else LOAI_VAO_NHOM[classes[top]]
                ok = nhom == LOAI_VAO_NHOM[loai]
                dung += ok
                tong += 1
                bao_nham_pin += nhom == "nguy-hiem" and loai != "battery"
                bao_nham_vai += nhom == "khong-tai-che" and LOAI_VAO_NHOM[loai] != "khong-tai-che"
                d = theo_loai.setdefault(loai, [0, 0])
                d[0] += ok
                d[1] += 1
                if loai == args.chi_tiet:
                    top3 = ", ".join(f"{classes[int(i)]} {float(p[i]):.0%}" for i in p.argsort(descending=True)[:3])
                    print(f"  {'DUNG' if ok else 'sai '} {f.name:<40} -> {nhom:<14} ({top3})")
        ket_qua[thu_muc.name] = {"dung": dung, "tong": tong, "bao_nham_pin": bao_nham_pin,
                                 "bao_nham_quan_ao": bao_nham_vai, "theo_loai": theo_loai}
        loai_str = " ".join(f"{k} {v[0]}/{v[1]}" for k, v in theo_loai.items())
        print(f"{thu_muc.name}: {dung}/{tong} ({dung / max(tong, 1):.0%}) dung nhom, "
              f"bao nham pin {bao_nham_pin}, bao nham quan ao {bao_nham_vai} | {loai_str}")
    if args.output:
        args.output.write_text(json.dumps(ket_qua, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
