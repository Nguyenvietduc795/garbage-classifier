"""API phan loai rac - ResNet-18 10 loai v6 (PyTorch), gop thanh 4 nhom, trien khai tren Render.

Cung model, tien xu ly (ca tang sang anh toi) va luat pin voi trang web (frontend/)
va giao dien desktop.
Trang web hien tu chay model trong trinh duyet; API nay danh cho ai can goi qua HTTP.

Chay local:
    python app.py
Chay production (Render dung lenh nay):
    gunicorn app:app --workers 1 --threads 2 --timeout 120 --bind 0.0.0.0:$PORT
"""
from __future__ import annotations

import gc
import io
import math
import os
from pathlib import Path

import torch
from flask import Flask, jsonify, request
from flask_cors import CORS
from PIL import Image, UnidentifiedImageError
from torch import nn
from torchvision import transforms
from torchvision.models import resnet18

# Render goi mien phi chi co 512 MB RAM. Gioi han torch o 1 thread giup giam
# dang ke bo nho va so thread nen sinh ra - dang nao moi request cung chi
# chay 1 anh nen khong mat gi ve toc do.
torch.set_num_threads(1)

MODEL_PATH = Path(__file__).parent / "model.pt"
IMAGE_SIZE = 224
# Giong trang web: model train co label smoothing nen xac suat hiem khi vuot 90%.
NGUONG_TIN_CAY = 0.50
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)
# Giong trang web: anh co do sang trung binh < NGUONG_TOI thi nang gamma cho
# do sang ve ~DO_SANG_DICH; anh du sang giu nguyen.
NGUONG_TOI = 0.30
DO_SANG_DICH = 0.45
# Giong trang web: P(pin) >= NGUONG_PIN thi bao rac nguy hai; duoi nguong thi
# chon loai cao nhat trong cac loai con lai.
NGUONG_PIN = 0.50

# Loai vat lieu (lop cua model) -> nhom rac
LOAI_VAO_NHOM = {
    "organic": "huu-co",
    "battery": "nguy-hiem",
    "cardboard": "tai-che", "glass": "tai-che", "metal": "tai-che",
    "paper": "tai-che", "plastic": "tai-che",
    "clothes": "khong-tai-che", "shoes": "khong-tai-che", "trash": "khong-tai-che",
}

# Nhom -> (ten, vi du vat the, huong dan xu ly). Khoa nhom cung la "muc" de to mau.
NHOM_RAC = {
    "huu-co": ("Rác hữu cơ", "Thức ăn thừa, rau củ quả, vỏ trái cây",
               "Bỏ vào thùng rác hữu cơ hoặc ủ làm phân compost."),
    "nguy-hiem": ("Rác nguy hại", "Pin AA/AAA, pin cúc áo, pin điện thoại",
                  "Tuyệt đối không bỏ vào rác thường — pin rò rỉ gây ô nhiễm đất và nước. "
                  "Mang tới điểm thu gom pin cũ, rác nguy hại."),
    "tai-che": ("Rác tái chế", "Carton, thủy tinh, chai nhựa, giấy, kim loại",
                "Rửa sạch, để khô, gấp gọn rồi bỏ vào thùng tái chế. Lon, giấy, carton bán ve chai được."),
    "khong-tai-che": ("Rác không thể tái chế", "Quần áo, giày dép, hộp xốp, vỏ bánh kẹo, giấy ăn, ống hút",
                      "Bỏ vào thùng rác còn lại. Quần áo còn mặc được thì nên quyên góp."),
}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES

# Goi tu domain khac (vd. trang Vercel) thi trinh duyet bat buoc phai co CORS.
# Dat ALLOWED_ORIGINS tren Render de gioi han lai dung domain cua ban.
CORS(app, resources={r"/predict": {"origins": os.environ.get("ALLOWED_ORIGINS", "*")}})

checkpoint = torch.load(MODEL_PATH, map_location="cpu", weights_only=False)
classes: list[str] = checkpoint["classes"]

model = resnet18(weights=None)
model.fc = nn.Linear(model.fc.in_features, len(classes))
model.load_state_dict(checkpoint["model_state_dict"])
model.eval()

# Checkpoint giu them 1 ban sao day du cua trong so cong voi lich su train.
# Khong giai phong thi no nam lai suot doi tien trinh - dang ke khi chi co
# 512 MB RAM. Danh sach lop da copy ra bien `classes` o tren roi.
del checkpoint
gc.collect()

cat_anh = transforms.Compose([
    transforms.Resize(int(IMAGE_SIZE / 0.875)),
    transforms.CenterCrop(IMAGE_SIZE),
    transforms.ToTensor(),
])
chuan_hoa = transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)
HE_SO_SANG = torch.tensor([0.299, 0.587, 0.114]).view(3, 1, 1)


def can_bang_sang(x: torch.Tensor) -> tuple[torch.Tensor, bool]:
    """x: anh [3, cao, rong] gia tri 0..1. Anh toi thi nang gamma, con lai giu nguyen."""
    sang = float((x * HE_SO_SANG).sum(0).mean())
    if sang >= NGUONG_TOI or sang <= 0.01:
        return x, False
    gamma = max(0.35, math.log(DO_SANG_DICH) / math.log(sang))
    return x.clamp(min=1e-6).pow(gamma), True

print(f"Da nap model: {len(classes)} loai - {', '.join(classes)}")


@app.route("/health", methods=["GET"])
def health():
    """Render dung endpoint nay de kiem tra service con song."""
    return jsonify({"status": "ok", "classes": classes, "groups": list(NHOM_RAC)})


@app.route("/predict", methods=["POST"])
def predict():
    if "image" not in request.files:
        return jsonify({"error": "Vui lòng gửi file ảnh với key 'image'"}), 400

    try:
        image = Image.open(io.BytesIO(request.files["image"].read()))
        x, da_tang_sang = can_bang_sang(cat_anh(image.convert("RGB")))
        tensor = chuan_hoa(x).unsqueeze(0)
    except (UnidentifiedImageError, OSError):
        return jsonify({"error": "Không đọc được file ảnh"}), 400

    with torch.inference_mode():
        probabilities = torch.softmax(model(tensor), dim=1)[0].tolist()

    theo_nhom = dict.fromkeys(NHOM_RAC, 0.0)
    for loai, p in zip(classes, probabilities):
        theo_nhom[LOAI_VAO_NHOM[loai]] += p

    # Pin dat nguong thi chon nguy hai; con lai chon nhom theo LOAI co xac suat
    # cao nhat (bo pin ra), khong theo tong xac suat nhom: nhom tai che gom 5
    # loai, cong lai de lan at pin (44 dung so voi 42 / 49 anh that).
    i_pin = classes.index("battery")
    top_index = max((i for i in range(len(classes)) if i != i_pin), key=probabilities.__getitem__)
    if probabilities[i_pin] >= NGUONG_PIN:
        top_index = i_pin
    nhom = LOAI_VAO_NHOM[classes[top_index]]
    confidence = theo_nhom[nhom]
    ten, vi_du, huong_dan = NHOM_RAC[nhom]
    chac_chan = confidence >= NGUONG_TIN_CAY

    return jsonify({
        "class": nhom,
        "loai": classes[top_index],
        "ten": ten,
        "vi_du": vi_du,
        "confidence": round(confidence * 100, 2),
        "chac_chan": chac_chan,
        "da_tang_sang": da_tang_sang,
        "muc": nhom if chac_chan else "canh-bao",
        "goi_y_xu_ly": huong_dan if chac_chan else "Độ tin cậy thấp — chưa đưa gợi ý.",
        "all_scores": {NHOM_RAC[k][0]: round(v * 100, 2) for k, v in theo_nhom.items()},
    })


@app.route("/", methods=["GET"])
def home():
    return jsonify({"service": "API phân loại rác", "endpoint": "POST /predict", "groups": list(NHOM_RAC)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
