"""
PHAN LOAI RAC - dung model ResNet-18 (PyTorch) thay cho Teachable Machine.

Ban goc dung Teachable Machine (keras_model.h5) van duoc giu nguyen o file
`phan_loai_rac_TEACHABLEMACHINE_goc.py.bak` neu can quay lai.

Giao dien `giao_dien_pyqt.py` KHONG can sua gi: ba thu no dung
(`load_model_and_labels`, `predict_trash`, `GOI_Y_XU_LY`) van y nguyen.

Cai thu vien:
    pip install torch torchvision opencv-python numpy pillow
"""

import cv2
import torch
from PIL import Image
from torch import nn
from torchvision import transforms
from torchvision.models import resnet18

# ======================================================================
# CAU HINH
# ======================================================================

# Checkpoint ResNet-18 (sinh ra tu pipeline garbage_classifier)
MODEL_PATH = "garbage_resnet18.pt"

# Kich thuoc anh dau vao
IMAGE_SIZE = 224

# Chuan hoa theo ImageNet - PHAI khop voi luc train. Khac han Teachable
# Machine: TM dung khoang [-1, 1], model nay dung mean/std cua ImageNet.
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

# Goi y xu ly cho tung loai rac - chinh sua noi dung theo y nhom ban.
GOI_Y_XU_LY = {
    "Clothes": "Quan ao cu: quyen gop neu con dung duoc, hoac bo vao thung tai che vai.",
    "Glass": "Thuy tinh: rua sach, bo vao thung tai che mau xanh.",
    "Metal": "Kim loai: rua sach, co the ban ve chai hoac bo vao thung tai che.",
    "Paper": "Giay: giu kho rao, khong dinh dau mo, bo vao thung tai che giay.",
    "Plastic": "Nhua: rua sach truoc khi bo vao thung tai che.",
    "Cardboard": "Bia carton: gap phang, bo vao thung tai che giay/carton.",
    "Battery": "CANH BAO: khong bo vao rac thuong. Mang den diem thu gom pin cu chuyen dung.",
}
# Them ban viet thuong de tra cuu khong bi truot neu doi nhan sau nay.
GOI_Y_XU_LY.update({key.lower(): value for key, value in list(GOI_Y_XU_LY.items())})


# ======================================================================
# NAP MODEL VA NHAN
# ======================================================================
def load_model_and_labels(model_path=MODEL_PATH, labels_path=None):
    """
    Nap model phan loai rac (ResNet-18 / PyTorch) va danh sach nhan.

    Khac ban Teachable Machine: danh sach nhan nam san trong checkpoint nen
    khong can doc `labels.txt`. Tham so `labels_path` giu lai cho tuong thich
    nguoc voi code cu, khong dung toi.

    Tra ve: (model, class_names)
    """
    checkpoint = torch.load(model_path, map_location="cpu", weights_only=False)

    class_names = checkpoint["classes"]
    model = resnet18(weights=None)
    model.fc = nn.Linear(model.fc.in_features, len(class_names))
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    accuracy = checkpoint.get("best_val_accuracy")
    ghi_chu = f" (val accuracy {accuracy:.1%})" if accuracy else ""
    print(f"Da nap model ResNet-18{ghi_chu}! Cac loai rac: {class_names}")
    return model, class_names


# ======================================================================
# TIEN XU LY ANH
# ======================================================================
def _build_transform(image_size=IMAGE_SIZE):
    resize_size = int(image_size / 0.875)
    return transforms.Compose([
        transforms.Resize(resize_size),
        transforms.CenterCrop(image_size),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])


_TRANSFORM = _build_transform()


def preprocess_pil(image):
    """
    Chuyen 1 anh PIL thanh tensor cho model.
    Resize canh ngan ve 256 -> cat giua 224 -> chuan hoa ImageNet.
    Dung chung cho ca giao dien PyQt lan API Flask, de hai ben khong bao gio
    lech ket qua vi tien xu ly khac nhau.
    """
    return _TRANSFORM(image.convert("RGB")).unsqueeze(0)


def preprocess_frame(frame):
    """
    Chuyen 1 khung hinh BGR (OpenCV) thanh tensor cho model.
    """
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return preprocess_pil(Image.fromarray(img_rgb))


# ======================================================================
# DU DOAN LOAI RAC
# ======================================================================
def predict_trash(frame, model, class_names):
    """
    Du doan loai rac tu 1 khung hinh.
    Tra ve: (nhan_du_doan, do_tin_cay, mang_xac_suat_tat_ca_class)
    Mang xac suat cung thu tu voi `class_names` de giao dien zip duoc.
    """
    input_tensor = preprocess_frame(frame)
    with torch.inference_mode():
        probabilities = torch.softmax(model(input_tensor), dim=1)[0]

    predictions = probabilities.numpy()
    max_idx = int(predictions.argmax())
    return class_names[max_idx], float(predictions[max_idx]), predictions


# ======================================================================
# VE KET QUA LEN ANH
# ======================================================================
def draw_result(frame, label, confidence, threshold=0.6):
    """
    Ve nhan du doan + % tin cay len khung hinh de hien thi.
    """
    if confidence >= threshold:
        text = f"{label}: {confidence * 100:.1f}%"
        color = (0, 255, 0)  # xanh la - tu tin
    else:
        text = f"Khong chac chan ({label}: {confidence * 100:.1f}%)"
        color = (0, 165, 255)  # cam - chua chac

    cv2.putText(frame, text, (15, 35), cv2.FONT_HERSHEY_SIMPLEX,
                0.85, color, 2, cv2.LINE_AA)
    return frame


# ======================================================================
# XU LY 1 ANH TINH
# ======================================================================
def process_image(image_path, model, class_names, threshold=0.6):
    """
    Doc 1 file anh, du doan loai rac, hien thi ket qua + goi y xu ly.
    """
    frame = cv2.imread(image_path)
    if frame is None:
        print(f"Loi: Khong tim thay anh tai '{image_path}'")
        return

    label, confidence, all_preds = predict_trash(frame, model, class_names)

    print(f"\nKet qua du doan: {label} ({confidence * 100:.1f}%)")
    print("Chi tiet tung loai:")
    for name, score in zip(class_names, all_preds):
        print(f"  - {name}: {score * 100:.1f}%")

    if confidence >= threshold:
        goi_y = GOI_Y_XU_LY.get(label, "Chua co goi y cho loai nay.")
        print(f"\nGoi y xu ly: {goi_y}")
    else:
        print("\nDo tin cay thap - khong dua ra goi y.")

    frame_display = draw_result(frame.copy(), label, confidence, threshold)

    cv2.imshow("Phan loai rac - ResNet-18", frame_display)
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

        if confidence >= threshold:
            goi_y = GOI_Y_XU_LY.get(label, "")
            cv2.putText(frame_display, goi_y[:60], (15, 65),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

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
