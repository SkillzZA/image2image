"""Utility functions for the model."""

from pathlib import Path

import torch
from torch import nn, optim
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
from torchvision.utils import make_grid, save_image

from img2img import cfg


def remove_normalization(x: torch.Tensor) -> torch.Tensor:
    """Removes normalization from the image."""
    return x * cfg.NORM_STD + cfg.NORM_MEAN


# TODO: remove Magic numbers from this module
@torch.inference_mode()
def save_some_examples(
    gen: nn.Module,
    val_loader: DataLoader[tuple[torch.Tensor, torch.Tensor]],
    epoch: int,
    folder: Path,
    writer: SummaryWriter,
) -> None:
    """Saves a grid of generated images. Also saves ground truth if epoch is 0.

    Args:
        gen (nn.Module): Generator model.
        val_loader (DataLoader): Dataloader for train/val set.
        epoch (int): Current epoch.
        folder (Path): Folder to save the images in.
        writer (SummaryWriter): Tensorboard writer.
    """
    # TODO: refactor this function for single responsibility and improving readability
    gen.eval()

    x, y = next(iter(val_loader))
    x, y = x.to(cfg.DEVICE), y.to(cfg.DEVICE)
    if epoch == 0:
        writer.add_graph(gen, x)
        save_image(
            remove_normalization(y), folder / f"label_{epoch}.png", nrow=4, padding=0
        )

    y_fake = gen(x)
    y_fake = remove_normalization(y_fake)
    x = remove_normalization(x)
    x_concat = torch.cat([x, y_fake], dim=3)  # stack images side by side
    save_image(x_concat, folder / f"sample_{epoch}.png", nrow=4, padding=0)
    img_grid = make_grid(x_concat, nrow=4, padding=0)
    writer.add_image(f"test_image {epoch=}", img_grid)
    gen.train()


@torch.inference_mode()
def evaluate_val_set(
    gen: nn.Module,
    val_loader: DataLoader[tuple[torch.Tensor, torch.Tensor]],
    folder: Path,
) -> None:
    """Runs inference on all images in the val_loader and saves them in the folder.

    Args:
        gen (nn.Module): Generator model.
        val_loader (DataLoader): Dataloader for val set.
        folder (Path): Path for saving the images.
    """

    gen.eval()
    for idx, (x, y) in enumerate(val_loader):
        x, y = x.to(cfg.DEVICE), y.to(cfg.DEVICE)
        y_fake = gen(x)
        y_fake = remove_normalization(y_fake)
        x = remove_normalization(x)
        y_concat = torch.cat([y, y_fake], dim=3)
        print(f"Saving {idx} image")
        save_image(y_concat, folder / f"val_{idx}.png", nrow=4, padding=0)
    gen.train()


def save_checkpoint(
    model: nn.Module, optimizer: optim.Optimizer, filename: Path
) -> None:
    """Saves checkpoint for the model and optimizer in the folder filename.

    Args:
        model (nn.Module): torch Model.
        optimizer (optim.Optimizer): Optimizer.
        filename (Path): new File name/path.
    """
    print("=> Saving checkpoint")
    checkpoint = {
        "state_dict": model.state_dict(),
        "optimizer": optimizer.state_dict(),
    }
    torch.save(checkpoint, filename)


def load_checkpoint(
    checkpoint_file: Path, model: nn.Module, optimizer: optim.Optimizer, lr: float
) -> None:
    """Loads checkpoint for the model and optimizer from the checkpoint_file.
    With the new learning rate.

    Args:
        checkpoint_file (Path): Saved model name/path.
        model (nn.Module): Model object to restore its state.
        optimizer (optim.Optimizer): Optimizer object to restore its state.
        lr (float): Learning rate.
    """
    print("=> Loading checkpoint")
    checkpoint = torch.load(checkpoint_file, map_location=cfg.DEVICE)
    model.load_state_dict(checkpoint["state_dict"])
    optimizer.load_state_dict(checkpoint["optimizer"])

    # if we don't do this then it will just have learning rate of old checkpoint
    # and it will lead to many hours of debugging \:
    for param_group in optimizer.param_groups:
        param_group["lr"] = lr
