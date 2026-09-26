from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import torch
from PIL import Image, UnidentifiedImageError
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


@dataclass(frozen=True)
class Sample:
    path: Path
    label: int


@dataclass(frozen=True)
class DatasetSplits:
    train: list[Sample]
    val: list[Sample]
    test: list[Sample]
    classes: list[str]

    def summary(self) -> dict[str, object]:
        def counts(samples: Sequence[Sample]) -> dict[str, int]:
            result = {name: 0 for name in self.classes}
            for sample in samples:
                result[self.classes[sample.label]] += 1
            return result

        return {
            "classes": self.classes,
            "train": {"total": len(self.train), "per_class": counts(self.train)},
            "val": {"total": len(self.val), "per_class": counts(self.val)},
            "test": {"total": len(self.test), "per_class": counts(self.test)},
        }


class GarbageDataset(Dataset[tuple[torch.Tensor, int]]):
    def __init__(self, samples: Sequence[Sample], transform: transforms.Compose) -> None:
        self.samples = list(samples)
        self.transform = transform

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, int]:
        sample = self.samples[index]
        with Image.open(sample.path) as image:
            tensor = self.transform(image.convert("RGB"))
        return tensor, sample.label


def discover_and_split(
    data_dir: Path,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    seed: int = 42,
    max_images_per_class: int = 0,
) -> DatasetSplits:
    data_dir = data_dir.resolve()
    if not data_dir.is_dir():
        raise FileNotFoundError(f"Dataset directory does not exist: {data_dir}")
    if train_ratio <= 0 or val_ratio <= 0 or train_ratio + val_ratio >= 1:
        raise ValueError("Ratios must be positive and train_ratio + val_ratio must be < 1")

    class_dirs = sorted(path for path in data_dir.iterdir() if path.is_dir())
    if len(class_dirs) < 2:
        raise ValueError(f"Expected at least two class folders in {data_dir}")

    classes = [path.name for path in class_dirs]
    split_samples: dict[str, list[Sample]] = {"train": [], "val": [], "test": []}

    for label, class_dir in enumerate(class_dirs):
        image_paths = sorted(
            path for path in class_dir.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
        )
        if max_images_per_class > 0:
            image_paths = image_paths[:max_images_per_class]
        if len(image_paths) < 3:
            raise ValueError(f"Class '{class_dir.name}' needs at least 3 images")

        random.Random(seed + label).shuffle(image_paths)
        train_end = max(1, int(len(image_paths) * train_ratio))
        val_count = max(1, int(len(image_paths) * val_ratio))
        val_end = min(len(image_paths) - 1, train_end + val_count)

        split_samples["train"].extend(Sample(path, label) for path in image_paths[:train_end])
        split_samples["val"].extend(Sample(path, label) for path in image_paths[train_end:val_end])
        split_samples["test"].extend(Sample(path, label) for path in image_paths[val_end:])

    for offset, name in enumerate(("train", "val", "test")):
        random.Random(seed + 10_000 + offset).shuffle(split_samples[name])

    return DatasetSplits(
        train=split_samples["train"],
        val=split_samples["val"],
        test=split_samples["test"],
        classes=classes,
    )


def get_train_transform(image_size: int = 224, strong: bool = False) -> transforms.Compose:
    if strong:
        # Aggressive enough to break the dataset's studio look: harsh crops,
        # TrivialAugmentWide for colour/geometry, occasional greyscale and blur,
        # then random erasing so no single region can carry the prediction.
        return transforms.Compose([
            transforms.RandomResizedCrop(image_size, scale=(0.30, 1.0), ratio=(0.6, 1.7)),
            transforms.RandomHorizontalFlip(),
            transforms.TrivialAugmentWide(),
            transforms.RandomGrayscale(p=0.10),
            transforms.RandomApply([transforms.GaussianBlur(5, sigma=(0.1, 2.0))], p=0.20),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
            transforms.RandomErasing(p=0.25, scale=(0.02, 0.20)),
        ])
    return transforms.Compose([
        transforms.RandomResizedCrop(image_size, scale=(0.75, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(12),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.15),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])


def get_eval_transform(image_size: int = 224) -> transforms.Compose:
    resize_size = int(image_size / 0.875)
    return transforms.Compose([
        transforms.Resize(resize_size),
        transforms.CenterCrop(image_size),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])


def build_dataloaders(
    splits: DatasetSplits,
    batch_size: int,
    num_workers: int,
    device: torch.device,
    image_size: int = 224,
    seed: int = 42,
    strong_augment: bool = False,
) -> dict[str, DataLoader]:
    datasets = {
        "train": GarbageDataset(splits.train, get_train_transform(image_size, strong_augment)),
        "val": GarbageDataset(splits.val, get_eval_transform(image_size)),
        "test": GarbageDataset(splits.test, get_eval_transform(image_size)),
    }
    generator = torch.Generator().manual_seed(seed)
    common = {
        "batch_size": batch_size,
        "num_workers": num_workers,
        "pin_memory": device.type == "cuda",
        "persistent_workers": num_workers > 0,
    }
    return {
        "train": DataLoader(datasets["train"], shuffle=True, generator=generator, **common),
        "val": DataLoader(datasets["val"], shuffle=False, **common),
        "test": DataLoader(datasets["test"], shuffle=False, **common),
    }


def validate_images(splits: DatasetSplits) -> list[str]:
    errors: list[str] = []
    samples = splits.train + splits.val + splits.test
    for sample in samples:
        try:
            with Image.open(sample.path) as image:
                image.verify()
        except (OSError, UnidentifiedImageError) as error:
            errors.append(f"{sample.path}: {error}")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect and validate the garbage dataset")
    parser.add_argument("--data-dir", type=Path, default=Path("../dataset_sach_zip"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-images-per-class", type=int, default=0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    splits = discover_and_split(
        args.data_dir,
        seed=args.seed,
        max_images_per_class=args.max_images_per_class,
    )
    print(json.dumps(splits.summary(), ensure_ascii=False, indent=2))
    errors = validate_images(splits)
    if errors:
        print("\nInvalid images:")
        print("\n".join(errors))
        raise SystemExit(1)
    print(f"\nValidated {len(splits.train) + len(splits.val) + len(splits.test)} images successfully.")


if __name__ == "__main__":
    main()
