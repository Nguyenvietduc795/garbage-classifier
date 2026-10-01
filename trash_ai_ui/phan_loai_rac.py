"""
PHAN LOAI RAC - model Teachable Machine 4 nhom (Keras).

4 nhom: rac huu co, rac nguy hai, rac tai che, rac khong the tai che.
Model (keras_model.h5) va labels.txt xuat tu Teachable Machine.

Ban ResNet-18 7 loai truoc do van con trong lich su git neu can quay lai.

Cai thu vien (TensorFlow 2.15 chi chay tren Python 3.9 - 3.11):
    pip install -r requirements.txt
"""

import os
import sys

# Ten nhom co dau (Rác hữu cơ...): console Windows mac dinh cp1252 se bao
# UnicodeEncodeError khi print - ep stdout sang UTF-8.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Tat log INFO cua TensorFlow. TF 2.15 di kem Keras 2 nen doc duoc file .h5 cua
# Teachable Machine - dung nang len TF 2.16+ (Keras 3 khong doc duoc).
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import cv2
import numpy as np
import tensorflow as tf
from PIL import Image, ImageOps

# ======================================================================
# CAU HINH
# ======================================================================

# Tep model va nhan (xuat tu Teachable Machine - dinh dang Keras)
MODEL_PATH = "keras_model.h5"
LABELS_PATH = "labels.txt"

# Kich thuoc anh dau vao ma Teachable Machine dung de train
IMAGE_SIZE = 224

# Nhan trong labels.txt -> thong tin nhom hien cho nguoi dung.
#   ten:          ten co dau, dung cho giao dien PyQt / API
#   ten_khong_dau: cv2.putText khong ve duoc chu co dau
#   muc:          dung de to mau theo nhom
NHOM_RAC = {
    "organic waste": {
        "ten": "Rác hữu cơ", "ten_khong_dau": "Rac huu co", "muc": "huu-co",
        "vi_du": "Thức ăn thừa, rau củ quả, vỏ trái cây",
        "huong_dan": "Bỏ vào thùng rác hữu cơ hoặc ủ làm phân compost.",
    },
    "hazardous waste": {
        "ten": "Rác nguy hại", "ten_khong_dau": "Rac nguy hai", "muc": "nguy-hiem",
        "vi_du": "Pin, ắc quy",
        "huong_dan": "Tuyệt đối không bỏ vào rác thường — pin rò rỉ gây ô nhiễm đất và nước. "
                     "Mang tới điểm thu gom pin cũ, rác nguy hại.",
    },
    "recyclable waste": {
        "ten": "Rác tái chế", "ten_khong_dau": "Rac tai che", "muc": "tai-che",
        "vi_du": "Carton, thủy tinh, chai nhựa, giấy, kim loại",
        "huong_dan": "Rửa sạch, để khô, gấp gọn rồi bỏ vào thùng tái chế. "
                     "Lon, giấy, carton bán ve chai được.",
    },
    "non-recyclable waste": {
        "ten": "Rác không thể tái chế", "ten_khong_dau": "Rac khong the tai che",
        "muc": "khong-tai-che",
        "vi_du": "Quần áo, dép, khẩu trang",
        "huong_dan": "Bỏ vào thùng rác còn lại. Quần áo còn mặc được thì nên quyên góp.",
    },
}

# Giu ten cu cho code nao con dung: nhan -> huong dan xu ly
GOI_Y_XU_LY = {nhan: nhom["huong_dan"] for nhan, nhom in NHOM_RAC.items()}


def thong_tin_nhom(label):
    """Tra ve dict thong tin nhom cho 1 nhan; nhan la thi tra ve ban toi thieu."""
    return NHOM_RAC.get(label, {
        "ten": label, "ten_khong_dau": label, "muc": "tai-che", "vi_du": "", "huong_dan": "",
    })


# ======================================================================
# LOP DepthwiseConv2D VA LOI TUONG THICH
# (Teachable Machine luu them tham so 'groups' ma DepthwiseConv2D khong nhan)
# ======================================================================
class PatchedDepthwiseConv2D(tf.keras.layers.DepthwiseConv2D):
    def __init__(self, **kwargs):
        kwargs.pop("groups", None)
        super().__init__(**kwargs)


# ======================================================================
# NAP MODEL VA NHAN
# ======================================================================
def load_model_and_labels(model_path=MODEL_PATH, labels_path=LABELS_PATH):
    """
    Nap model phan loai rac (Keras/TensorFlow) va danh sach nhan.
    Tra ve: (model, class_names)
    """
    model = tf.keras.models.load_model(
        model_path,
        custom_objects={"DepthwiseConv2D": PatchedDepthwiseConv2D},
        compile=False,
    )

    with open(labels_path, "r", encoding="utf-8") as f:
        # labels.txt co dang: "0 organic waste", "1 hazardous waste", ...
        class_names = [line.strip().split(" ", 1)[1] for line in f if line.strip()]

    print(f"Da nap model thanh cong! Cac nhom rac: {class_names}")
    return model, class_names


# ======================================================================
# TIEN XU LY ANH
# ======================================================================
def preprocess_pil(image):
    """
    Chuyen 1 anh PIL thanh mang dau vao cho model, giong het Teachable Machine:
    cat vuong o giua -> resize 224x224 -> chuan hoa pixel ve [-1, 1].
    Dung chung cho giao dien PyQt lan API Flask, de hai ben khong lech ket qua.
    """
    image = ImageOps.fit(image.convert("RGB"), (IMAGE_SIZE, IMAGE_SIZE), Image.Resampling.LANCZOS)
    arr = np.asarray(image, dtype=np.float32) / 127.5 - 1
    return arr[np.newaxis]


def preprocess_frame(frame):
    """
    Chuyen 1 khung hinh BGR (OpenCV) thanh mang dau vao cho model.
    """
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return preprocess_pil(Image.fromarray(img_rgb))


# ======================================================================
# DU DOAN NHOM RAC
# ======================================================================
def predict_trash(frame, model, class_names):
    """
    Du doan nhom rac tu 1 khung hinh.
    Tra ve: (nhan_du_doan, do_tin_cay, mang_xac_suat_tat_ca_class)
    Mang xac suat cung thu tu voi `class_names` de giao dien zip duoc.
    """
    # Goi model truc tiep thay vi model.predict(): nhanh hon nhieu khi chi co
    # 1 anh, quan trong voi webcam chay ~30 khung/giay.
    predictions = model(preprocess_frame(frame), training=False).numpy()[0]

    max_idx = int(predictions.argmax())
    return class_names[max_idx], float(predictions[max_idx]), predictions


# ======================================================================
# VE KET QUA LEN ANH
# ======================================================================
def draw_result(frame, label, confidence, threshold=0.6):
    """
    Ve ten nhom + % tin cay len khung hinh de hien thi.
    """
    ten = thong_tin_nhom(label)["ten_khong_dau"]
    if confidence >= threshold:
        text = f"{ten}: {confidence * 100:.1f}%"
        color = (0, 255, 0)  # xanh la - tu tin
    else:
        text = f"Khong chac chan ({ten}: {confidence * 100:.1f}%)"
        color = (0, 165, 255)  # cam - chua chac

    cv2.putText(frame, text, (15, 35), cv2.FONT_HERSHEY_SIMPLEX,
                0.85, color, 2, cv2.LINE_AA)
    return frame


# ======================================================================
# XU LY 1 ANH TINH
# ======================================================================
def process_image(image_path, model, class_names, threshold=0.6):
    """
    Doc 1 file anh, du doan nhom rac, hien thi ket qua + goi y xu ly.
    """
    frame = cv2.imread(image_path)
    if frame is None:
        print(f"Loi: Khong tim thay anh tai '{image_path}'")
        return

    label, confidence, all_preds = predict_trash(frame, model, class_names)

    print(f"\nKet qua du doan: {thong_tin_nhom(label)['ten']} ({confidence * 100:.1f}%)")
    print("Chi tiet tung nhom:")
    for name, score in zip(class_names, all_preds):
        print(f"  - {thong_tin_nhom(name)['ten']}: {score * 100:.1f}%")

    if confidence >= threshold:
        print(f"\nGoi y xu ly: {thong_tin_nhom(label)['huong_dan']}")
    else:
        print("\nDo tin cay thap - khong dua ra goi y.")

    frame_display = draw_result(frame.copy(), label, confidence, threshold)

    cv2.imshow("Phan loai rac - 4 nhom", frame_display)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


# ======================================================================
# XU LY TRUC TIEP QUA WEBCAM
# ======================================================================
def process_webcam(model, class_names, threshold=0.6, camera_index=0):
    """
    Mo webcam, phan loai rac theo thoi gian thuc.
    Nhan phim 'q' de thoat.
    """
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("Loi: Khong mo duoc webcam.")
        return

    print("Dang chay webcam... Nhan 'q' de thoat.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Loi: Khong doc duoc khung hinh tu webcam.")
            break

        label, confidence, _ = predict_trash(frame, model, class_names)
        frame_display = draw_result(frame.copy(), label, confidence, threshold)

        cv2.imshow("Phan loai rac - Webcam", frame_display)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


# ======================================================================
# HAM CHINH
# ======================================================================
def main():
    model, class_names = load_model_and_labels()

    # Chon 1 trong 2 cach chay ben duoi:

    # Cach 1: Phan loai tren 1 anh co san
    # process_image("test.jpg", model, class_names)

    # Cach 2: Phan loai truc tiep qua webcam
    process_webcam(model, class_names)


if __name__ == "__main__":
    main()
