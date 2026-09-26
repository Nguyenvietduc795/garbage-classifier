from __future__ import annotations

from pathlib import Path
from typing import Any

import torch
from torch import nn
from torchvision.models import ResNet18_Weights, resnet18

MODEL_NAME = "resnet18"


def create_model(num_classes: int, pretrained: bool = True) -> nn.Module:
    weights = ResNet18_Weights.DEFAULT if pretrained else None
    model = resnet18(weights=weights)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    return model


def set_backbone_trainable(model: nn.Module, trainable: bool) -> None:
    for parameter in model.parameters():
        parameter.requires_grad = trainable
    for parameter in model.fc.parameters():
        parameter.requires_grad = True


def save_checkpoint(
    path: Path,
    model: nn.Module,
    classes: list[str],
    epoch: int,
    best_val_accuracy: float,
    config: dict[str, Any],
    history: list[dict[str, float | int]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_name": MODEL_NAME,
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
    if checkpoint.get("model_name") != MODEL_NAME:
        raise ValueError(f"Unsupported model: {checkpoint.get('model_name')}")
    classes = checkpoint.get("classes")
    if not isinstance(classes, list) or not classes:
        raise ValueError("Checkpoint is missing its class list")
    model = create_model(len(classes), pretrained=False)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()
    return model, checkpoint
