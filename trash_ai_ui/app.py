"""
API PHAN LOAI RAC - model ResNet-18 8 loai (PyTorch), gop thanh 4 nhom
----------------------------------------------------------------
Dung chung model va tien xu ly voi giao dien PyQt (phan_loai_rac.py),
nen API va desktop luon tra ve cung mot ket qua cho cung mot anh.

Cai thu vien truoc khi chay:
    pip install -r requirements.txt

Chay server:
    python app.py

Server se chay tai: http://127.0.0.1:5000
Endpoint du doan:   POST http://127.0.0.1:5000/predict  (gui kem 1 anh)
"""

import io

from flask import Flask, jsonify, request
from PIL import Image, UnidentifiedImageError

from phan_loai_rac import load_model_and_labels, preprocess_pil, thong_tin_nhom

# Nguong tin cay: duoi muc nay thi khong dua ra goi y xu ly,
# giong het giao dien PyQt va trang web.
NGUONG_TIN_CAY = 0.5

app = Flask(__name__)

# Nap model 1 lan khi server khoi dong (khong nap lai moi request)
model, class_names = load_model_and_labels()


@app.route("/predict", methods=["POST"])
def predict():
    if "image" not in request.files:
        return jsonify({"error": "Vui long gui file anh voi key 'image'"}), 400

    try:
        image = Image.open(io.BytesIO(request.files["image"].read()))
        tensor = preprocess_pil(image)
    except (UnidentifiedImageError, OSError):
        return jsonify({"error": "Khong doc duoc file anh"}), 400

    label, theo_nhom = model.du_doan(tensor)
    confidence = float(theo_nhom[class_names.index(label)])
    nhom = thong_tin_nhom(label)
    chac_chan = confidence >= NGUONG_TIN_CAY

    return jsonify({
        "class": label,
        "ten": nhom["ten"],
        "vi_du": nhom["vi_du"],
        "confidence": round(confidence * 100, 2),
        "chac_chan": chac_chan,
        "goi_y_xu_ly": nhom["huong_dan"] if chac_chan else "Do tin cay thap - khong dua ra goi y.",
        "all_scores": {
            thong_tin_nhom(name)["ten"]: round(float(score) * 100, 2)
            for name, score in zip(class_names, theo_nhom)
        },
    })


@app.route("/", methods=["GET"])
def home():
    return f"API phan loai rac dang chay ({len(class_names)} nhom). Gui POST anh toi /predict"


if __name__ == "__main__":
    # debug=False: che do debug mo mot shell thuc thi code tu xa khi co loi,
    # khong duoc bat khi may co the truy cap tu ngoai.
    app.run(debug=False, port=5000)
