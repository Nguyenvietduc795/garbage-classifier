"""
API PHAN LOAI RAC - dung model ResNet-18 (PyTorch)
----------------------------------------------------------------
Dung chung model va tien xu ly voi giao dien PyQt (phan_loai_rac.py),
nen API va desktop luon tra ve cung mot ket qua cho cung mot anh.

Ban goc dung Teachable Machine giu o `app_TEACHABLEMACHINE_goc.py.bak`.

Cai thu vien truoc khi chay:
    pip install torch torchvision flask pillow numpy opencv-python

Chay server:
    python app.py

Server se chay tai: http://127.0.0.1:5000
Endpoint du doan:   POST http://127.0.0.1:5000/predict  (gui kem 1 anh)
"""

import io

import torch
from flask import Flask, jsonify, request
from PIL import Image, UnidentifiedImageError

from phan_loai_rac import GOI_Y_XU_LY, load_model_and_labels, preprocess_pil

# Nguong tin cay: duoi muc nay thi khong dua ra goi y xu ly,
# giong het cach giao dien PyQt lam.
NGUONG_TIN_CAY = 0.6

app = Flask(__name__)

# Nap model 1 lan khi server khoi dong (khong nap lai moi request)
model, class_names = load_model_and_labels()


@app.route("/predict", methods=["POST"])
def predict():
    if "image" not in request.files:
        return jsonify({"error": "Vui long gui file anh voi key 'image'"}), 400

    try:
        image = Image.open(io.BytesIO(request.files["image"].read()))
    except (UnidentifiedImageError, OSError):
        return jsonify({"error": "Khong doc duoc file anh"}), 400

    with torch.inference_mode():
        probabilities = torch.softmax(model(preprocess_pil(image)), dim=1)[0]

    predictions = probabilities.numpy()
    top_index = int(predictions.argmax())
    confidence = float(predictions[top_index])
    label = class_names[top_index]

    return jsonify({
        "class": label,
        "confidence": round(confidence * 100, 2),
        "chac_chan": confidence >= NGUONG_TIN_CAY,
        "goi_y_xu_ly": (
            GOI_Y_XU_LY.get(label, "Chua co goi y cho loai nay.")
            if confidence >= NGUONG_TIN_CAY
            else "Do tin cay thap - khong dua ra goi y."
        ),
        "all_scores": {
            name: round(float(score) * 100, 2)
            for name, score in zip(class_names, predictions)
        },
    })


@app.route("/", methods=["GET"])
def home():
    return f"API phan loai rac dang chay ({len(class_names)} loai). Gui POST anh toi /predict"


if __name__ == "__main__":
    # debug=False: che do debug mo mot shell thuc thi code tu xa khi co loi,
    # khong duoc bat khi may co the truy cap tu ngoai.
    app.run(debug=False, port=5000)
