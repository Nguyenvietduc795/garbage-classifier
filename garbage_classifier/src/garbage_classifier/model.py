from __future__ import annotations

from pathlib import Path
from typing import Any

import torch
from torch import nn
from torchvision.models import (
    MobileNet_V3_Large_Weights,
    ResNet18_Weights,
    mobilenet_v3_large,
    resnet18,
)

# resnet18: chinh xac, nang (~45 MB). mobilenet_v3_large: nhe (~17 MB), du
# nhanh de chay trong trinh duyet tren dien thoai.
ARCHITECTURES = ("resnet18", "mobilenet_v3_large")
DEFAULT_ARCH = "resnet18"

# Tien to ten tham so cua phan dau phan loai - phan nay luon duoc train va
# dung learning rate lon hon phan backbone.
_HEAD_PREFIX = {"resnet18": "fc.", "mobilenet_v3_large": "classifier."}


def create_model(num_classes: int, pretrained: bool = True, arch: str = DEFAULT_ARCH) -> nn.Module:
    if arch == "resnet18":
        model = resnet18(weights=ResNet18_Weights.DEFAULT if pretrained else None)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
    elif arch == "mobilenet_v3_large":
        model = mobilenet_v3_large(weights=MobileNet_V3_Large_Weights.DEFAULT if pretrained else None)
        last = model.classifier[-1]
        model.classifier[-1] = nn.Linear(last.in_features, num_classes)
    else:
        raise ValueError(f"Unsupported architecture: {arch}")
    return model


def split_parameters(model: nn.Module, arch: str) -> tuple[list[nn.Parameter], list[nn.Parameter]]:
    """Tra ve (tham so backbone, tham so dau phan loai)."""
    prefix = _HEAD_PREFIX[arch]
    backbone, head = [], []
    for name, parameter in model.named_parameters():
        (head if name.startswith(prefix) else backbone).append(parameter)
    return backbone, head


def set_backbone_trainable(model: nn.Module, trainable: bool, arch: str = DEFAULT_ARCH) -> None:
    backbone, head = split_parameters(model, arch)
    for parameter in backbone:
        parameter.requires_grad = trainable
    for parameter in head:
        parameter.requires_grad = True


def save_checkpoint(
    path: Path,
    model: nn.Module,
    classes: list[str],
    epoch: int,
    best_val_accuracy: float,
    config: dict[str, Any],
    history: list[dict[str, float | int]],
    arch: str = DEFAULT_ARCH,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_name": arch,
            "model_state_dict": model.state_dict(),
            "classes": classes,
            "epoch": epoch,
            "best_val_accuracy": best_val_accuracy,
            "config": config,
            "history": history,
        },
        path,
    )


def load_checkpoint(path: Path, device: torch.device) -> tuple[nn.Module, dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"Checkpoint does not exist: {path}")
    checkpoint = torch.load(path, map_location=device, weights_only=False)
    arch = checkpoint.get("model_name")
    if arch not in ARCHITECTURES:
        raise ValueError(f"Unsupported model: {arch}")
    classes = checkpoint.get("classes")
    if not isinstance(classes, list) or not classes:
        raise ValueError("Checkpoint is missing its class list")
    model = create_model(len(classes), pretrained=False, arch=arch)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()
    return model, checkpoint
