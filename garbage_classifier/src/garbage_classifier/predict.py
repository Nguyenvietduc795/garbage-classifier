from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from PIL import Image

from .data import get_eval_transform
from .model import load_checkpoint
from .utils import resolve_device


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Predict the garbage class of one image")
    parser.add_argument("image", type=Path)
    parser.add_argument("--checkpoint", type=Path, default=Path("artifacts/best_model.pt"))
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.image.is_file():
        raise FileNotFoundError(f"Image does not exist: {args.image}")
    device = resolve_device(args.device)
    model, checkpoint = load_checkpoint(args.checkpoint.resolve(), device)
    classes: list[str] = checkpoint["classes"]
    image_size = int(checkpoint.get("config", {}).get("image_size", 224))

    with Image.open(args.image) as image:
        input_tensor = get_eval_transform(image_size)(image.convert("RGB")).unsqueeze(0).to(device)
    with torch.inference_mode():
        probabilities = torch.softmax(model(input_tensor), dim=1)[0]

    top_k = min(max(1, args.top_k), len(classes))
    values, indices = probabilities.topk(top_k)
    predictions = [
        {"class": classes[index], "probability": round(float(value), 6)}
        for value, index in zip(values.cpu(), indices.cpu(), strict=True)
    ]
    print(json.dumps({"image": str(args.image.resolve()), "predictions": predictions}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
