from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn
from torch.utils.data import DataLoader


@dataclass(frozen=True)
class EvaluationResult:
    loss: float
    accuracy: float
    confusion_matrix: list[list[int]]
    per_class_accuracy: dict[str, float]

    def to_dict(self) -> dict[str, object]:
        return {
            "loss": self.loss,
            "accuracy": self.accuracy,
            "confusion_matrix": self.confusion_matrix,
            "per_class_accuracy": self.per_class_accuracy,
        }


def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    scaler: torch.amp.GradScaler,
    device: torch.device,
) -> tuple[float, float]:
    model.train()
    total_loss = 0.0
    total_correct = 0
    total_samples = 0
    amp_enabled = device.type == "cuda"

    for inputs, labels in loader:
        inputs = inputs.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)
        optimizer.zero_grad(set_to_none=True)

        with torch.autocast(device_type=device.type, enabled=amp_enabled):
            logits = model(inputs)
            loss = criterion(logits, labels)

        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()

        batch_size = labels.size(0)
        total_loss += loss.item() * batch_size
        total_correct += (logits.argmax(dim=1) == labels).sum().item()
        total_samples += batch_size

    return total_loss / total_samples, total_correct / total_samples


@torch.inference_mode()
def evaluate_model(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
    classes: list[str],
) -> EvaluationResult:
    model.eval()
    total_loss = 0.0
    total_correct = 0
    total_samples = 0
    confusion = torch.zeros((len(classes), len(classes)), dtype=torch.int64)
    amp_enabled = device.type == "cuda"

    for inputs, labels in loader:
        inputs = inputs.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)
        with torch.autocast(device_type=device.type, enabled=amp_enabled):
            logits = model(inputs)
            loss = criterion(logits, labels)

        predictions = logits.argmax(dim=1)
        batch_size = labels.size(0)
        total_loss += loss.item() * batch_size
        total_correct += (predictions == labels).sum().item()
        total_samples += batch_size
        for true_label, predicted_label in zip(labels.cpu(), predictions.cpu(), strict=True):
            confusion[true_label.item(), predicted_label.item()] += 1

    per_class_accuracy: dict[str, float] = {}
    for index, class_name in enumerate(classes):
        class_total = confusion[index].sum().item()
        class_correct = confusion[index, index].item()
        per_class_accuracy[class_name] = class_correct / class_total if class_total else 0.0

    return EvaluationResult(
        loss=total_loss / total_samples,
        accuracy=total_correct / total_samples,
        confusion_matrix=confusion.tolist(),
        per_class_accuracy=per_class_accuracy,
    )
