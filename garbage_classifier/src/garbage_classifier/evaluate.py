from __future__ import annotations

import argparse
from pathlib import Path

from torch import nn

from .data import build_dataloaders, discover_and_split
from .engine import evaluate_model
from .model import load_checkpoint
from .utils import resolve_device, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a trained checkpoint on the test split")
    parser.add_argument("--checkpoint", type=Path, default=Path("artifacts/best_model.pt"))
    parser.add_argument("--data-dir", type=Path, default=Path("../dataset_sach_zip"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/evaluation.json"))
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    device = resolve_device(args.device)
    model, checkpoint = load_checkpoint(args.checkpoint.resolve(), device)
    config = checkpoint.get("config", {})
    splits = discover_and_split(
        args.data_dir,
        seed=int(config.get("seed", 42)),
        max_images_per_class=int(config.get("max_images_per_class", 0)),
    )
    if splits.classes != checkpoint["classes"]:
        raise ValueError("Dataset classes do not match checkpoint classes")
    loaders = build_dataloaders(
        splits,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
        device=device,
        image_size=int(config.get("image_size", 224)),
        seed=int(config.get("seed", 42)),
    )
    criterion = nn.CrossEntropyLoss(label_smoothing=float(config.get("label_smoothing", 0.0)))
    result = evaluate_model(model, loaders["test"], criterion, device, splits.classes)
    payload = {"checkpoint": str(args.checkpoint.resolve()), "classes": splits.classes, **result.to_dict()}
    write_json(args.output.resolve(), payload)

    print(f"Test accuracy: {result.accuracy:.2%}")
    for class_name, accuracy in result.per_class_accuracy.items():
        print(f"  {class_name:<12} {accuracy:.2%}")
    print(f"Evaluation saved to: {args.output.resolve()}")


if __name__ == "__main__":
    main()
