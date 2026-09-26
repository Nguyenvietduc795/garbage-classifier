"""Gradio demo for the seven-class garbage classifier.

Runs the same way locally and on Hugging Face Spaces. Locally it loads the
checkpoint from `artifacts/`; on Spaces, set HF_MODEL_REPO and the weights are
pulled from the Hub instead.
"""
from __future__ import annotations

import os
from pathlib import Path

import gradio as gr
import torch

from garbage_classifier.data import get_eval_transform
from garbage_classifier.model import load_checkpoint
from garbage_classifier.utils import resolve_device

APP_DIR = Path(__file__).resolve().parent
DEFAULT_CHECKPOINT = APP_DIR / "artifacts" / "aug" / "best_model.pt"
LOW_CONFIDENCE = 0.60


def locate_checkpoint() -> Path:
    override = os.environ.get("MODEL_PATH")
    if override:
        return Path(override)
    if DEFAULT_CHECKPOINT.is_file():
        return DEFAULT_CHECKPOINT
    repo = os.environ.get("HF_MODEL_REPO")
    if not repo:
        raise FileNotFoundError(
            f"No checkpoint at {DEFAULT_CHECKPOINT}. Train one first, or set "
            "MODEL_PATH, or set HF_MODEL_REPO to download from the Hub."
        )
    from huggingface_hub import hf_hub_download

    return Path(hf_hub_download(repo_id=repo, filename=os.environ.get("HF_MODEL_FILE", "best_model.pt")))


device = resolve_device(os.environ.get("DEVICE", "auto"))
checkpoint_path = locate_checkpoint()
model, checkpoint = load_checkpoint(checkpoint_path, device)
classes: list[str] = checkpoint["classes"]
image_size = int(checkpoint.get("config", {}).get("image_size", 224))
transform = get_eval_transform(image_size)

print(f"Loaded {checkpoint_path} on {device}")
print(f"Classes: {', '.join(classes)}")


def predict(image):
    if image is None:
        return {}, "Chưa có ảnh."
    tensor = transform(image.convert("RGB")).unsqueeze(0).to(device)
    with torch.inference_mode():
        probabilities = torch.softmax(model(tensor), dim=1)[0]
    scores = {name: float(probabilities[index]) for index, name in enumerate(classes)}
    top_name, top_score = max(scores.items(), key=lambda item: item[1])
    if top_score < LOW_CONFIDENCE:
        note = (
            f"⚠️ Độ tự tin thấp ({top_score:.0%}). Model đoán **{top_name}** nhưng không chắc — "
            "khi sai nó thường rơi vào khoảng này."
        )
    else:
        note = f"Model đoán **{top_name}** với độ tự tin {top_score:.0%}."
    return scores, note


DESCRIPTION = """
Phân loại ảnh rác thành 7 nhóm: Battery, Cardboard, Clothes, Glass, Metal, Paper, Plastic.

**Model biết gì và không biết gì** — ResNet-18 fine-tune trên 2.890 ảnh:

| Đo trên | Accuracy |
|---|---|
| Ảnh cùng nguồn dataset (626 ảnh) | 96,0% |
| Ảnh từ nguồn khác, Wikimedia (49 ảnh) | 44,9% |

Con số thứ hai mới là con số thật khi bạn đưa ảnh của mình vào. Dataset huấn luyện gần
như toàn ảnh chụp studio nền trắng, nên ảnh đời thường model làm kém hẳn. Nếu kết quả
kèm cảnh báo độ tự tin thấp thì đừng tin nó.
"""

demo = gr.Interface(
    fn=predict,
    inputs=gr.Image(type="pil", label="Ảnh rác"),
    outputs=[
        gr.Label(num_top_classes=3, label="Kết quả"),
        gr.Markdown(label="Ghi chú"),
    ],
    title="Phân loại rác — 7 lớp",
    description=DESCRIPTION,
    flagging_mode="never",
)

if __name__ == "__main__":
    demo.launch()
