from __future__ import annotations

import argparse
import gc
import time
from pathlib import Path

import torch
from torch import nn

from .data import build_dataloaders, discover_and_split
from .engine import evaluate_model, train_one_epoch
from .model import create_model, load_checkpoint, save_checkpoint, set_backbone_trainable
from .utils import resolve_device, seed_everything, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a seven-class garbage classifier")
    parser.add_argument("--data-dir", type=Path, default=Path("../dataset_sach_zip"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--backbone-learning-rate", type=float, default=3e-5)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--label-smoothing", type=float, default=0.1)
    parser.add_argument("--freeze-epochs", type=int, default=2)
    parser.add_argument("--patience", type=int, default=5)
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--no-pretrained", action="store_true")
    parser.add_argument(
        "--strong-augment",
        action="store_true",
        help="Heavier augmentation; helps on images that do not look like the training set",
    )
    parser.add_argument(
        "--max-images-per-class",
        type=int,
        default=0,
        help="Limit each class for a smoke test; 0 uses every image",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if args.epochs < 1 or args.batch_size < 1:
        raise ValueError("epochs and batch-size must be positive")
    if args.freeze_epochs < 0 or args.freeze_epochs >= args.epochs:
        raise ValueError("freeze-epochs must be >= 0 and smaller than epochs")
    if args.patience < 1:
        raise ValueError("patience must be positive")


def main() -> None:
    args = parse_args()
    validate_args(args)
    seed_everything(args.seed)
    device = resolve_device(args.device)
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    splits = discover_and_split(
        args.data_dir,
        seed=args.seed,
        max_images_per_class=args.max_images_per_class,
    )
    loaders = build_dataloaders(
        splits,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
        device=device,
        image_size=args.image_size,
        seed=args.seed,
        strong_augment=args.strong_augment,
    )
    write_json(output_dir / "dataset_split.json", splits.summary())

    model = create_model(len(splits.classes), pretrained=not args.no_pretrained).to(device)
    if args.freeze_epochs > 0:
        set_backbone_trainable(model, False)

    backbone_parameters = [parameter for name, parameter in model.named_parameters() if not name.startswith("fc.")]
    head_parameters = list(model.fc.parameters())
    optimizer = torch.optim.AdamW(
        [
            {"params": backbone_parameters, "lr": args.backbone_learning_rate},
            {"params": head_parameters, "lr": args.learning_rate},
        ],
        weight_decay=args.weight_decay,
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
    criterion = nn.CrossEntropyLoss(label_smoothing=args.label_smoothing)
    scaler = torch.amp.GradScaler("cuda", enabled=device.type == "cuda")

    print(f"Device: {device}")
    if device.type == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(device)}")
    print(f"Classes: {', '.join(splits.classes)}")
    print(f"Samples: train={len(splits.train)}, val={len(splits.val)}, test={len(splits.test)}")

    config = vars(args).copy()
    config["data_dir"] = str(args.data_dir.resolve())
    config["output_dir"] = str(output_dir)
    history: list[dict[str, float | int]] = []
    best_val_accuracy = -1.0
    epochs_without_improvement = 0
    training_started = time.perf_counter()

    for epoch_index in range(args.epochs):
        epoch = epoch_index + 1
        if epoch_index == args.freeze_epochs and args.freeze_epochs > 0:
            set_backbone_trainable(model, True)
            print("Backbone unfrozen; fine-tuning the full network.")

        epoch_started = time.perf_counter()
        train_loss, train_accuracy = train_one_epoch(
            model, loaders["train"], criterion, optimizer, scaler, device
        )
        val_result = evaluate_model(model, loaders["val"], criterion, device, splits.classes)
        scheduler.step()
        epoch_seconds = time.perf_counter() - epoch_started
        record = {
            "epoch": epoch,
            "train_loss": train_loss,
            "train_accuracy": train_accuracy,
            "val_loss": val_result.loss,
            "val_accuracy": val_result.accuracy,
            "seconds": epoch_seconds,
        }
        history.append(record)
        write_json(output_dir / "history.json", history)

        improved = val_result.accuracy > best_val_accuracy
        if improved:
            best_val_accuracy = val_result.accuracy
            epochs_without_improvement = 0
            save_checkpoint(
                output_dir / "best_model.pt",
                model,
                splits.classes,
                epoch,
                best_val_accuracy,
                config,
                history,
            )
        else:
            epochs_without_improvement += 1

        save_checkpoint(
            output_dir / "last_model.pt",
            model,
            splits.classes,
            epoch,
            best_val_accuracy,
            config,
            history,
        )
        print(
            f"Epoch {epoch:02d}/{args.epochs} | "
            f"train loss={train_loss:.4f} acc={train_accuracy:.2%} | "
            f"val loss={val_result.loss:.4f} acc={val_result.accuracy:.2%} | "
            f"{epoch_seconds:.1f}s{' | best' if improved else ''}"
        )
        if epochs_without_improvement >= args.patience:
            print(f"Early stopping after {args.patience} epochs without improvement.")
            break

    # Persistent dataloader workers stay alive for the whole run and each one
    # holds prefetched batches in RAM. On a large dataset with many workers that
    # is enough to run the machine out of memory during the final test pass, so
    # drop the train/val loaders before loading a second copy of the model.
    # The optimizer also keeps two momentum buffers per parameter, so release the
    # training model and optimizer rather than holding them alongside the reloaded
    # best checkpoint.
    del loaders["train"], loaders["val"], model, optimizer, scaler
    gc.collect()
    if device.type == "cuda":
        torch.cuda.empty_cache()

    best_model, checkpoint = load_checkpoint(output_dir / "best_model.pt", device)
    test_result = evaluate_model(best_model, loaders["test"], criterion, device, splits.classes)
    total_seconds = time.perf_counter() - training_started
    final_metrics = {
        "best_epoch": checkpoint["epoch"],
        "best_val_accuracy": checkpoint["best_val_accuracy"],
        "test": test_result.to_dict(),
        "training_seconds": total_seconds,
        "classes": splits.classes,
    }
    write_json(output_dir / "metrics.json", final_metrics)
    print(f"Best epoch: {checkpoint['epoch']}")
    print(f"Test accuracy: {test_result.accuracy:.2%}")
    print(f"Artifacts saved to: {output_dir}")


if __name__ == "__main__":
    main()
