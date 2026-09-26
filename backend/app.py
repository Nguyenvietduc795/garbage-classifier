"""API phan loai rac - ResNet-18 (PyTorch), trien khai tren Render.

Chay local:
    python app.py
Chay production (Render dung lenh nay):
    gunicorn app:app --workers 1 --threads 2 --timeout 120 --bind 0.0.0.0:$PORT
"""
from __future__ import annotations

import gc
import io
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
NGUONG_TIN_CAY = 0.60
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

VAT_LIEU = {
    "battery":   ("Pin", "Tuyệt đối không bỏ vào rác thường — pin rò rỉ gây ô nhiễm đất và nước. "
                         "Mang tới điểm thu gom pin cũ.", "nguy-hiem"),
    "cardboard": ("Bìa carton", "Gấp phẳng cho gọn, bỏ vào thùng tái chế giấy hoặc carton.", "thuong"),
    "clothes":   ("Quần áo, vải", "Còn dùng được thì quyên góp. Nếu không, bỏ vào thùng thu gom vải.", "thuong"),
    "glass":     ("Thủy tinh", "Rửa sạch, bỏ vào thùng tái chế. Nếu vỡ thì bọc giấy lại trước khi bỏ.", "thuong"),
    "metal":     ("Kim loại", "Rửa sạch rồi bỏ vào thùng tái chế. Lon nhôm và vỏ hộp bán ve chai được.", "thuong"),
    "paper":     ("Giấy", "Giữ khô ráo, không dính dầu mỡ. Gấp gọn rồi bỏ vào thùng tái chế giấy.", "thuong"),
    "plastic":   ("Nhựa", "Rửa sạch rồi bỏ vào thùng tái chế.", "thuong"),
}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES

# Frontend nam tren domain khac (Vercel) nen trinh duyet bat buoc phai co CORS.
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

transform = transforms.Compose([
    transforms.Resize(int(IMAGE_SIZE / 0.875)),
    transforms.CenterCrop(IMAGE_SIZE),
    transforms.ToTensor(),
    transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
])

print(f"Da nap model: {len(classes)} lop - {', '.join(classes)}")


@app.route("/health", methods=["GET"])
def health():
    """Render dung endpoint nay de kiem tra service con song."""
    return jsonify({"status": "ok", "classes": classes})


@app.route("/predict", methods=["POST"])
def predict():
    if "image" not in request.files:
        return jsonify({"error": "Vui lòng gửi file ảnh với key 'image'"}), 400

    try:
        image = Image.open(io.BytesIO(request.files["image"].read()))
        tensor = transform(image.convert("RGB")).unsqueeze(0)
    except (UnidentifiedImageError, OSError):
        return jsonify({"error": "Không đọc được file ảnh"}), 400

    with torch.inference_mode():
        probabilities = torch.softmax(model(tensor), dim=1)[0]

    top_index = int(probabilities.argmax())
    confidence = float(probabilities[top_index])
    ten, huong_dan, muc = VAT_LIEU.get(classes[top_index], (classes[top_index], "", "thuong"))
    chac_chan = confidence >= NGUONG_TIN_CAY

    return jsonify({
        "class": classes[top_index],
        "ten": ten,
        "confidence": round(confidence * 100, 2),
        "chac_chan": chac_chan,
        "muc": muc if chac_chan else "canh-bao",
        "goi_y_xu_ly": huong_dan if chac_chan else "Độ tin cậy thấp — chưa đưa gợi ý.",
        "all_scores": {
            VAT_LIEU.get(name, (name,))[0]: round(float(score) * 100, 2)
            for name, score in zip(classes, probabilities)
        },
    })


@app.route("/", methods=["GET"])
def home():
    return jsonify({"service": "API phân loại rác", "endpoint": "POST /predict", "classes": classes})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
