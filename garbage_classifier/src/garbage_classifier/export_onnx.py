"""Xuat checkpoint sang ONNX de chuyen tiep sang TensorFlow.js (chay trong trinh duyet).

    uv run garbage-export-onnx --checkpoint artifacts/mnv3_8lop/best_model.pt --output model.onnx

Dau vao cua file ONNX: anh NCHW 1x3x224x224 da chuan hoa ImageNet (giong luc train).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from .model import load_checkpoint


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a checkpoint to ONNX")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--image-size", type=int, default=224)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model, checkpoint = load_checkpoint(args.checkpoint.resolve(), torch.device("cpu"))
    dummy = torch.zeros(1, 3, args.image_size, args.image_size)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    torch.onnx.export(
        model,
        dummy,
        args.output,
        input_names=["input"],
        output_names=["logits"],
        opset_version=17,
        dynamo=False,
    )
    # Danh sach lop di kem, cung thu tu voi dau ra cua model
    meta = {"arch": checkpoint["model_name"], "classes": checkpoint["classes"], "imageSize": args.image_size}
    args.output.with_suffix(".json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {args.output} ({checkpoint['model_name']}, {len(checkpoint['classes'])} classes)")


if __name__ == "__main__":
    main()
