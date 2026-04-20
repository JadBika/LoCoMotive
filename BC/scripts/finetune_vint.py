#!/usr/bin/env python3
"""
finetune_vint.py — Fine-tune pretrained ViNT on collected locobot data.

Usage (from repo root, with vint_train conda env active):
    cd BC/visualnav-transformer/train
    python ../../scripts/finetune_vint.py

Optional args:
    --epochs 30
    --lr 1e-4
    --batch-size 16
    --use-wandb
"""
import sys
import os
import argparse
import pickle
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
from tqdm import tqdm

# --- path setup so vint_train is importable ---------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT   = SCRIPT_DIR.parent                              # BC/
TRAIN_DIR   = REPO_ROOT / "visualnav-transformer" / "train"
sys.path.insert(0, str(TRAIN_DIR))

from vint_train.data.vint_dataset import ViNT_Dataset        # noqa: E402
from vint_train.models.vint.vint import ViNT                  # noqa: E402

# ---------------------------------------------------------------------------
DATA_DIR    = REPO_ROOT / "data" / "processed" / "locobot"
SPLITS_DIR  = REPO_ROOT / "data" / "splits"   / "locobot"
CKPT_IN     = REPO_ROOT / "visualnav-transformer" / "deployment" / "model_weights" / "vint.pth"
CKPT_OUT    = REPO_ROOT / "checkpoints" / "finetuned"

# ViNT model hyper-params (must match pretrained checkpoint)
MODEL_KWARGS = dict(
    context_size=5,
    len_traj_pred=5,
    learn_angle=True,
    obs_encoder="efficientnet-b0",
    obs_encoding_size=512,
    mha_num_attention_heads=4,
    mha_num_attention_layers=4,
    mha_ff_dim_factor=4,
    late_fusion=False,
)

# Dataset hyper-params (match upstream vint.yaml)
DATASET_KWARGS = dict(
    dataset_name="locobot",
    image_size=(85, 64),
    waypoint_spacing=1,
    min_dist_cat=0,
    max_dist_cat=10,
    min_action_distance=0,
    max_action_distance=10,
    negative_mining=True,
    len_traj_pred=5,
    learn_angle=True,
    context_size=5,
    context_type="temporal",
    end_slack=0,
    goals_per_obs=1,
    normalize=True,
)

ALPHA = 0.5   # dist_loss weight  (same as upstream)


def _pick_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def _load_model(ckpt_path: Path, device: torch.device) -> ViNT:
    obj = torch.load(str(ckpt_path), map_location="cpu", weights_only=False)
    model = ViNT(**MODEL_KWARGS)
    # Unwrap: checkpoint is {"model": <ViNT object>, "epoch": ..., ...}
    raw = obj["model"] if (isinstance(obj, dict) and "model" in obj) else obj
    # raw may be a full model object or already a state_dict
    state = raw.state_dict() if hasattr(raw, "state_dict") else raw
    model.load_state_dict(state, strict=False)
    return model.to(device)


def _compute_loss(batch, model, device, learn_angle: bool):
    # ViNT_Dataset returns a 7-tuple:
    # obs_image, goal_image, action, distance, goal_pos, dataset_index, action_mask
    obs_img, goal_img, action_label, dist_label, _, _, action_mask = batch
    obs_img      = obs_img.to(device)
    goal_img     = goal_img.to(device)
    dist_label   = dist_label.to(device).float()
    action_label = action_label.to(device).float()
    action_mask  = action_mask.to(device).float()

    dist_pred, action_pred = model(obs_img, goal_img)

    dist_loss = F.mse_loss(dist_pred.squeeze(-1), dist_label)

    def masked_mse(pred, label, mask):
        loss = F.mse_loss(pred, label, reduction="none")
        while loss.dim() > 1:
            loss = loss.mean(dim=-1)
        return (loss * mask).mean() / (mask.mean() + 1e-2)

    action_loss = masked_mse(action_pred, action_label, action_mask)
    total = ALPHA * 1e-2 * dist_loss + (1 - ALPHA) * action_loss
    return total, dist_loss.item(), action_loss.item()


def train_one_epoch(model, loader, optimizer, device, learn_angle):
    model.train()
    total, d_acc, a_acc, n = 0.0, 0.0, 0.0, 0
    for batch in tqdm(loader, desc="  train", leave=False):
        optimizer.zero_grad()
        loss, d, a = _compute_loss(batch, model, device, learn_angle)
        loss.backward()
        optimizer.step()
        total += loss.item(); d_acc += d; a_acc += a; n += 1
    return total / n, d_acc / n, a_acc / n


@torch.no_grad()
def val_one_epoch(model, loader, device, learn_angle):
    model.eval()
    total, d_acc, a_acc, n = 0.0, 0.0, 0.0, 0
    for batch in loader:
        loss, d, a = _compute_loss(batch, model, device, learn_angle)
        total += loss.item(); d_acc += d; a_acc += a; n += 1
    return total / n, d_acc / n, a_acc / n


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs",     type=int,   default=30)
    parser.add_argument("--lr",         type=float, default=1e-4)
    parser.add_argument("--batch-size", type=int,   default=16)
    parser.add_argument("--num-workers",type=int,   default=0)
    parser.add_argument("--use-wandb",  action="store_true")
    parser.add_argument("--ckpt-in",    default=str(CKPT_IN))
    parser.add_argument("--ckpt-out",   default=str(CKPT_OUT))
    args = parser.parse_args()

    device = _pick_device()
    print(f"Device: {device}")

    ckpt_out = Path(args.ckpt_out)
    ckpt_out.mkdir(parents=True, exist_ok=True)

    # datasets
    train_ds = ViNT_Dataset(
        data_folder=str(DATA_DIR),
        data_split_folder=str(SPLITS_DIR / "train"),
        **DATASET_KWARGS,
    )
    val_ds = ViNT_Dataset(
        data_folder=str(DATA_DIR),
        data_split_folder=str(SPLITS_DIR / "val"),
        **DATASET_KWARGS,
    )
    print(f"Train: {len(train_ds)} samples   Val: {len(val_ds)} samples")

    train_loader = DataLoader(train_ds, batch_size=args.batch_size,
                              shuffle=True,  num_workers=args.num_workers, drop_last=True)
    val_loader   = DataLoader(val_ds,   batch_size=args.batch_size,
                              shuffle=False, num_workers=args.num_workers)

    model = _load_model(Path(args.ckpt_in), device)
    print(f"Loaded pretrained checkpoint: {args.ckpt_in}")

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    if args.use_wandb:
        import wandb
        wandb.init(project="locomotive-vint-finetune", config=vars(args))

    best_val = float("inf")
    for epoch in range(1, args.epochs + 1):
        t_loss, t_d, t_a = train_one_epoch(model, train_loader, optimizer, device, MODEL_KWARGS["learn_angle"])
        v_loss, v_d, v_a = val_one_epoch(model, val_loader, device, MODEL_KWARGS["learn_angle"])
        scheduler.step()
        print(f"Epoch {epoch:3d}/{args.epochs}  "
              f"train {t_loss:.4f} (d={t_d:.4f} a={t_a:.4f})  "
              f"val {v_loss:.4f} (d={v_d:.4f} a={v_a:.4f})")

        if args.use_wandb:
            import wandb
            wandb.log({"train/loss": t_loss, "train/dist_loss": t_d, "train/action_loss": t_a,
                       "val/loss": v_loss, "val/dist_loss": v_d, "val/action_loss": v_a,
                       "epoch": epoch})

        # save latest
        torch.save(model.state_dict(), ckpt_out / "vint_finetuned_latest.pth")

        # save best
        if v_loss < best_val:
            best_val = v_loss
            torch.save(model.state_dict(), ckpt_out / "vint_finetuned_best.pth")
            print(f"  ✓ New best val loss: {best_val:.4f}")

    print(f"\nDone. Best checkpoint: {ckpt_out}/vint_finetuned_best.pth")
    if args.use_wandb:
        import wandb
        wandb.finish()


if __name__ == "__main__":
    main()
