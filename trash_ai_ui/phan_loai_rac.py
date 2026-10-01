"""
PHAN LOAI RAC - model ResNet-18 8 loai (PyTorch), gop thanh 4 nhom.

Model phan 8 loai vat lieu (battery, cardboard, clothes, glass, metal, organic,
paper, plastic); giao dien chi hien 4 nhom: rac huu co, rac tai che, rac khong
the tai che, rac nguy hai. Cung model va cung cach gop nhom voi trang web
(frontend/), nen desktop, API va web luon cho cung ket qua.

Giao dien `giao_dien_pyqt.py` dung 3 thu: `load_model_and_labels`,
`predict_trash`, `thong_tin_nhom`.

Cai thu vien:
    pip install -r requirements.txt
"""

import sys

# Ten nhom co dau (Rác hữu cơ...): console Windows mac dinh cp1252 se bao
# UnicodeEncodeError khi print - ep stdout sang UTF-8.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import cv2
import numpy as np
import torch
from PIL import Image
from torch import nn
from torchvision import transforms
from torchvision.models import resnet18

# ======================================================================
# CAU HINH
# ======================================================================

# Checkpoint ResNet-18 8 loai (garbage_classifier/artifacts/v2_r18/best_model.pt)
MODEL_PATH = "garbage_resnet18.pt"

# Kich thuoc anh dau vao
IMAGE_SIZE = 224

# Chuan hoa theo ImageNet - PHAI khop voi luc train.
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

# Loai vat lieu (lop cua model) -> nhom rac hien cho nguoi dung
LOAI_VAO_NHOM = {
    "organic": "huu-co",
    "battery": "nguy-hiem",
    "cardboard": "tai-che", "glass": "tai-che", "metal": "tai-che",
    "paper": "tai-che", "plastic": "tai-che",
    "clothes": "khong-tai-che",
}

# Thong tin tung nhom. Khoa nhom cung la "muc" dung de to mau.
#   ten:           ten co dau, dung cho giao dien PyQt / API
#   ten_khong_dau: cv2.putText khong ve duoc chu co dau
NHOM_RAC = {
    "huu-co": {
        "ten": "Rác hữu cơ", "ten_khong_dau": "Rac huu co", "muc": "huu-co",
        "vi_du": "Thức ăn thừa, rau củ quả, vỏ trái cây",
        "huong_dan": "Bỏ vào thùng rác hữu cơ hoặc ủ làm phân compost.",
    },
    "nguy-hiem": {
        "ten": "Rác nguy hại", "ten_khong_dau": "Rac nguy hai", "muc": "nguy-hiem",
        "vi_du": "Pin, ắc quy",
        "huong_dan": "Tuyệt đối không bỏ vào rác thường — pin rò rỉ gây ô nhiễm đất và nước. "
                     "Mang tới điểm thu gom pin cũ, rác nguy hại.",
    },
    "tai-che": {
        "ten": "Rác tái chế", "ten_khong_dau": "Rac tai che", "muc": "tai-che",
        "vi_du": "Carton, thủy tinh, chai nhựa, giấy, kim loại",
        "huong_dan": "Rửa sạch, để khô, gấp gọn rồi bỏ vào thùng tái chế. "
                     "Lon, giấy, carton bán ve chai được.",
    },
    "khong-tai-che": {
        "ten": "Rác không thể tái chế", "ten_khong_dau": "Rac khong the tai che",
        "muc": "khong-tai-che",
        "vi_du": "Quần áo, dép, khẩu trang",
        "huong_dan": "Bỏ vào thùng rác còn lại. Quần áo còn mặc được thì nên quyên góp.",
    },
}
DANH_SACH_NHOM = list(NHOM_RAC)

# Giu ten cu cho code nao con dung: nhom -> huong dan xu ly
GOI_Y_XU_LY = {nhom: info["huong_dan"] for nhom, info in NHOM_RAC.items()}


def thong_tin_nhom(nhom):
    """Tra ve dict thong tin cua 1 nhom rac."""
    return NHOM_RAC[nhom]


# ======================================================================
# NAP MODEL
# ======================================================================
class ModelGopNhom:
    """Boc model 8 loai, dung chung cho desktop va API."""

    def __init__(self, net, classes):
        self.net = net
        self.classes = classes

    def du_doan(self, tensor):
        """
        Tra ve (nhom_duoc_chon, mang xac suat 4 nhom theo DANH_SACH_NHOM).
        Chon nhom theo LOAI co xac suat cao nhat, khong theo tong xac suat nhom:
        nhom tai che gom 5 loai, cong 5 xac suat nho lai de lan at pin
        (do tren 49 anh that: 44 dung so voi 42). Xac suat nhom = tong cac loai.
        """
        with torch.inference_mode():
            xac_suat = torch.softmax(self.net(tensor), dim=1)[0].numpy()
        theo_nhom = np.zeros(len(DANH_SACH_NHOM), dtype=np.float32)
        for loai, p in zip(self.classes, xac_suat):
            theo_nhom[DANH_SACH_NHOM.index(LOAI_VAO_NHOM[loai])] += p
        return LOAI_VAO_NHOM[self.classes[int(xac_suat.argmax())]], theo_nhom


def load_model_and_labels(model_path=MODEL_PATH, labels_path=None):
    """
    Nap model ResNet-18 8 loai.
    Tra ve: (model, danh_sach_nhom) - danh sach 4 nhom, cung thu tu voi mang
    xac suat ma predict_trash tra ve. `labels_path` giu lai cho tuong thich
    nguoc, khong dung toi (danh sach lop nam san trong checkpoint).
    """
    checkpoint = torch.load(model_path, map_location="cpu", weights_only=False)
    classes = checkpoint["classes"]
    net = resnet18(weights=None)
    net.fc = nn.Linear(net.fc.in_features, len(classes))
    net.load_state_dict(checkpoint["model_state_dict"])
    net.eval()

    print(f"Da nap model ResNet-18 - {len(classes)} loai: {classes}")
    return ModelGopNhom(net, classes), DANH_SACH_NHOM


# ======================================================================
# TIEN XU LY ANH
# ======================================================================
_TRANSFORM = transforms.Compose([
    transforms.Resize(int(IMAGE_SIZE / 0.875)),
    transforms.CenterCrop(IMAGE_SIZE),
    transforms.ToTensor(),
    transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
])


def preprocess_pil(image):
    """
    Chuyen 1 anh PIL thanh tensor cho model, giong luc train:
    canh ngan ve 256 -> cat giua 224 -> chuan hoa ImageNet.
    Dung chung cho giao dien PyQt lan API Flask.
    """
    return _TRANSFORM(image.convert("RGB")).unsqueeze(0)


def preprocess_frame(frame):
    """
    Chuyen 1 khung hinh BGR (OpenCV) thanh tensor cho model.
    """
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return preprocess_pil(Image.fromarray(img_rgb))


# ======================================================================
# DU DOAN NHOM RAC
# ======================================================================
def predict_trash(frame, model, class_names=None):
    """
    Du doan nhom rac tu 1 khung hinh.
    Tra ve: (nhom_du_doan, do_tin_cay, mang_xac_suat_4_nhom)
    Mang xac suat cung thu tu voi danh sach nhom ma load_model_and_labels tra ve.
    """
    nhom, theo_nhom = model.du_doan(preprocess_frame(frame))
    return nhom, float(theo_nhom[DANH_SACH_NHOM.index(nhom)]), theo_nhom


# ======================================================================
# VE KET QUA LEN ANH
# ======================================================================
def draw_result(frame, label, confidence, threshold=0.5):
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
def process_image(image_path, model, class_names, threshold=0.5):
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
def process_webcam(model, class_names, threshold=0.5, camera_index=0):
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
