"""API phan loai rac - model Teachable Machine 4 nhom (Keras), trien khai tren Render.

4 nhom: rac huu co, rac nguy hai, rac tai che, rac khong the tai che.
Model va labels.txt xuat tu Teachable Machine (converted_keras.zip).

Chay local:
    python app.py
Chay production (Render dung lenh nay):
    gunicorn app:app --workers 1 --threads 2 --timeout 120 --bind 0.0.0.0:$PORT
"""
from __future__ import annotations

import io
import os
from pathlib import Path

# Tat log INFO cua TensorFlow. TF 2.15 di kem Keras 2 nen doc duoc file .h5 cua
# Teachable Machine - dung nang len TF 2.16+ (Keras 3 khong doc duoc).
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np
import tensorflow as tf
from flask import Flask, jsonify, request
from flask_cors import CORS
from PIL import Image, ImageOps, UnidentifiedImageError

# Render goi mien phi chi co 512 MB RAM. Moi request chi chay 1 anh nen
# gioi han 1 thread khong mat gi ve toc do ma bot ton bo nho.
tf.config.threading.set_inter_op_parallelism_threads(1)
tf.config.threading.set_intra_op_parallelism_threads(1)

THU_MUC = Path(__file__).parent
MODEL_PATH = THU_MUC / "keras_model.h5"
LABELS_PATH = THU_MUC / "labels.txt"
IMAGE_SIZE = 224
NGUONG_TIN_CAY = 0.60
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB

# Nhan trong labels.txt -> (ten nhom, vi du vat the, huong dan xu ly, muc hien thi)
NHOM_RAC = {
    "organic waste": (
        "Rác hữu cơ", "Thức ăn thừa, rau củ quả, vỏ trái cây",
        "Bỏ vào thùng rác hữu cơ hoặc ủ làm phân compost.", "huu-co"),
    "hazardous waste": (
        "Rác nguy hại", "Pin, ắc quy",
        "Tuyệt đối không bỏ vào rác thường — pin rò rỉ gây ô nhiễm đất và nước. "
        "Mang tới điểm thu gom pin cũ, rác nguy hại.", "nguy-hiem"),
    "recyclable waste": (
        "Rác tái chế", "Carton, thủy tinh, chai nhựa, giấy, kim loại",
        "Rửa sạch, để khô, gấp gọn rồi bỏ vào thùng tái chế. Lon, giấy, carton bán ve chai được.",
        "tai-che"),
    "non-recyclable waste": (
        "Rác không thể tái chế", "Quần áo, dép, khẩu trang",
        "Bỏ vào thùng rác còn lại. Quần áo còn mặc được thì nên quyên góp.", "khong-tai-che"),
}


class PatchedDepthwiseConv2D(tf.keras.layers.DepthwiseConv2D):
    """Teachable Machine luu them tham so `groups` ma DepthwiseConv2D khong nhan."""

    def __init__(self, **kwargs):
        kwargs.pop("groups", None)
        super().__init__(**kwargs)


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES

# Frontend nam tren domain khac (Vercel) nen trinh duyet bat buoc phai co CORS.
# Dat ALLOWED_ORIGINS tren Render de gioi han lai dung domain cua ban.
CORS(app, resources={r"/predict": {"origins": os.environ.get("ALLOWED_ORIGINS", "*")}})

model = tf.keras.models.load_model(
    MODEL_PATH, custom_objects={"DepthwiseConv2D": PatchedDepthwiseConv2D}, compile=False)

# labels.txt co dang "0 organic waste", "1 hazardous waste", ...
classes: list[str] = [
    line.strip().split(" ", 1)[1]
    for line in LABELS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()
]

print(f"Da nap model: {len(classes)} nhom - {', '.join(classes)}")


def tien_xu_ly(image: Image.Image) -> np.ndarray:
    """Giong Teachable Machine: cat vuong o giua, resize 224, chuan hoa ve [-1, 1]."""
    image = ImageOps.fit(image.convert("RGB"), (IMAGE_SIZE, IMAGE_SIZE), Image.Resampling.LANCZOS)
    arr = np.asarray(image, dtype=np.float32) / 127.5 - 1
    return arr[np.newaxis]


@app.route("/health", methods=["GET"])
def health():
    """Render dung endpoint nay de kiem tra service con song."""
    return jsonify({"status": "ok", "classes": classes})


@app.route("/predict", methods=["POST"])
def predict():
    if "image" not in request.files:
        return jsonify({"error": "Vui lòng gửi file ảnh với key 'image'"}), 400

    try:
        batch = tien_xu_ly(Image.open(io.BytesIO(request.files["image"].read())))
    except (UnidentifiedImageError, OSError):
        return jsonify({"error": "Không đọc được file ảnh"}), 400

    probabilities = model(batch, training=False).numpy()[0]

    top_index = int(probabilities.argmax())
    confidence = float(probabilities[top_index])
    ten, vi_du, huong_dan, muc = NHOM_RAC.get(classes[top_index], (classes[top_index], "", "", "tai-che"))
    chac_chan = confidence >= NGUONG_TIN_CAY

    return jsonify({
        "class": classes[top_index],
        "ten": ten,
        "vi_du": vi_du,
        "confidence": round(confidence * 100, 2),
        "chac_chan": chac_chan,
        "muc": muc if chac_chan else "canh-bao",
        "goi_y_xu_ly": huong_dan if chac_chan else "Độ tin cậy thấp — chưa đưa gợi ý.",
        "all_scores": {
            NHOM_RAC.get(name, (name,))[0]: round(float(score) * 100, 2)
            for name, score in zip(classes, probabilities)
        },
    })


@app.route("/", methods=["GET"])
def home():
    return jsonify({"service": "API phân loại rác", "endpoint": "POST /predict", "classes": classes})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
