"""Gradio Space: phan loai anh rac thanh 7 nhom bang ResNet-18.

Ban standalone - khong phu thuoc package `garbage_classifier`, chi can
torch/torchvision/gradio/pillow nen chay thang tren Hugging Face Spaces.
"""
from __future__ import annotations

from pathlib import Path

import gradio as gr
import torch
from torch import nn
from torchvision import transforms
from torchvision.models import resnet18

MODEL_PATH = Path(__file__).parent / "model.pt"
IMAGE_SIZE = 224
LOW_CONFIDENCE = 0.60
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

# Ten hien thi + huong dan vut. Muc "nguy-hiem" chi danh cho pin.
VAT_LIEU = {
    "battery":   ("Pin", "Tuyệt đối không bỏ vào rác thường — pin rò rỉ gây ô nhiễm đất và nước. "
                         "Mang tới điểm thu gom pin cũ.", True),
    "cardboard": ("Bìa carton", "Gấp phẳng cho gọn, bỏ vào thùng tái chế giấy hoặc carton.", False),
    "clothes":   ("Quần áo, vải", "Còn dùng được thì quyên góp. Nếu không, bỏ vào thùng thu gom vải.", False),
    "glass":     ("Thủy tinh", "Rửa sạch, bỏ vào thùng tái chế. Nếu vỡ thì bọc giấy lại trước khi bỏ.", False),
    "metal":     ("Kim loại", "Rửa sạch rồi bỏ vào thùng tái chế. Lon nhôm và vỏ hộp bán ve chai được.", False),
    "paper":     ("Giấy", "Giữ khô ráo, không dính dầu mỡ. Gấp gọn rồi bỏ vào thùng tái chế giấy.", False),
    "plastic":   ("Nhựa", "Rửa sạch rồi bỏ vào thùng tái chế.", False),
}

checkpoint = torch.load(MODEL_PATH, map_location="cpu", weights_only=False)
classes: list[str] = checkpoint["classes"]

model = resnet18(weights=None)
model.fc = nn.Linear(model.fc.in_features, len(classes))
model.load_state_dict(checkpoint["model_state_dict"])
model.eval()

transform = transforms.Compose([
    transforms.Resize(int(IMAGE_SIZE / 0.875)),
    transforms.CenterCrop(IMAGE_SIZE),
    transforms.ToTensor(),
    transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
])


def predict(image):
    if image is None:
        return {}, "Chưa có ảnh."

    tensor = transform(image.convert("RGB")).unsqueeze(0)
    with torch.inference_mode():
        probabilities = torch.softmax(model(tensor), dim=1)[0]

    ten_hien_thi = {VAT_LIEU.get(c, (c,))[0]: float(probabilities[i]) for i, c in enumerate(classes)}
    top_index = int(probabilities.argmax())
    top_score = float(probabilities[top_index])
    ten, huong_dan, nguy_hiem = VAT_LIEU.get(classes[top_index], (classes[top_index], "", False))

    if top_score < LOW_CONFIDENCE:
        note = (f"### ⚠️ Chưa chắc — cao nhất chỉ {top_score:.0%}\n\n"
                f"Máy nghiêng về **{ten}** nhưng không đủ chắc để khuyên bạn. "
                "Thử ảnh rõ hơn, đủ sáng, mỗi lần một vật.")
    elif nguy_hiem:
        note = f"### 🔴 {ten} — {top_score:.0%}\n\n{huong_dan}"
    else:
        note = f"### ♻️ {ten} — {top_score:.0%}\n\n{huong_dan}"
    return ten_hien_thi, note


DESCRIPTION = """
Đưa ảnh vào để biết nên vứt vào thùng nào. ResNet-18 fine-tune trên 7.772 ảnh.

**Độ chính xác thật sự — cả hai con số:**

| Đo trên | Accuracy |
|---|---|
| Ảnh cùng nguồn dataset (1.672 ảnh) | 94,4% |
| **Ảnh đời thực từ Wikimedia (49 ảnh)** | **57,1%** |

Con số thứ hai mới đúng với ảnh bạn tự chụp. Dữ liệu huấn luyện phần lớn là ảnh
một vật trên nền sạch, nên ảnh đời thường nhiều vật/nền lộn xộn model làm kém hẳn.
Khi kết quả kèm cảnh báo *"Chưa chắc"* thì đừng tin nó.
"""

demo = gr.Interface(
    fn=predict,
    inputs=gr.Image(type="pil", label="Ảnh rác"),
    outputs=[
        gr.Label(num_top_classes=3, label="Các khả năng"),
        gr.Markdown(label="Kết luận"),
    ],
    title="♻️ Bỏ vào thùng nào?",
    description=DESCRIPTION,
    flagging_mode="never",
)

if __name__ == "__main__":
    demo.launch()
