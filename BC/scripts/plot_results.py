#!/usr/bin/env python3
"""
plot_results.py — Generate plots for the LoCoMotive BC project.

Produces:
  BC/results/plots/loss_curves.png     — train/val loss over 50 epochs
  BC/results/plots/trajectory_map.png  — top-down map of all demo trajectories

Usage:
    python3 scripts/plot_results.py
"""
import pickle
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm

REPO_ROOT  = Path(__file__).resolve().parents[1]
DATA_DIR   = REPO_ROOT / "data" / "processed" / "locobot"
SPLITS_DIR = REPO_ROOT / "data" / "splits" / "locobot"
OUT_DIR    = REPO_ROOT / "results" / "plots"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. Loss curves (hardcoded from 50-epoch fine-tuning run)
# ---------------------------------------------------------------------------

EPOCHS = list(range(1, 51))

TRAIN_LOSS = [
    0.4566, 0.1092, 0.0898, 0.0855, 0.0811, 0.0737, 0.0698, 0.0668, 0.0658,
    0.0635, 0.0580, 0.0575, 0.0578, 0.0572, 0.0515, 0.0528, 0.0503, 0.0513,
    0.0497, 0.0497, 0.0485, 0.0470, 0.0487, 0.0470, 0.0477, 0.0452, 0.0463,
    0.0462, 0.0451, 0.0455, 0.0418, 0.0422, 0.0445, 0.0402, 0.0422, 0.0403,
    0.0385, 0.0402, 0.0400, 0.0416, 0.0399, 0.0390, 0.0401, 0.0379, 0.0383,
    0.0403, 0.0375, 0.0392, 0.0387, 0.0377,
]

VAL_LOSS = [
    0.2540, 0.2159, 0.2321, 0.2056, 0.1969, 0.1723, 0.1582, 0.1568, 0.1391,
    0.1528, 0.1518, 0.1424, 0.1471, 0.1320, 0.1545, 0.1388, 0.1403, 0.1299,
    0.1453, 0.1334, 0.1315, 0.1217, 0.1337, 0.1238, 0.1321, 0.1327, 0.1222,
    0.1246, 0.1306, 0.1308, 0.1286, 0.1336, 0.1417, 0.1233, 0.1328, 0.1166,
    0.1248, 0.1324, 0.1279, 0.1316, 0.1310, 0.1242, 0.1280, 0.1349, 0.1326,
    0.1210, 0.1245, 0.1392, 0.1271, 0.1185,
]

TRAIN_ACTION = [
    0.7318, 0.1442, 0.1187, 0.1144, 0.1100, 0.0937, 0.0907, 0.0850, 0.0842,
    0.0779, 0.0717, 0.0738, 0.0735, 0.0709, 0.0619, 0.0645, 0.0619, 0.0631,
    0.0601, 0.0614, 0.0598, 0.0559, 0.0577, 0.0553, 0.0575, 0.0541, 0.0549,
    0.0570, 0.0541, 0.0525, 0.0486, 0.0496, 0.0530, 0.0466, 0.0517, 0.0478,
    0.0444, 0.0459, 0.0461, 0.0460, 0.0459, 0.0440, 0.0471, 0.0442, 0.0452,
    0.0453, 0.0414, 0.0450, 0.0440, 0.0437,
]

VAL_ACTION = [
    0.4340, 0.3627, 0.3950, 0.3535, 0.3143, 0.2781, 0.2571, 0.2594, 0.2266,
    0.2401, 0.2553, 0.2319, 0.2473, 0.2096, 0.2560, 0.2143, 0.2302, 0.2164,
    0.2396, 0.2213, 0.2142, 0.2007, 0.2173, 0.2002, 0.2175, 0.2264, 0.1976,
    0.2013, 0.2119, 0.2164, 0.2074, 0.2179, 0.2350, 0.2060, 0.2144, 0.1936,
    0.2021, 0.2119, 0.2088, 0.2183, 0.2170, 0.2015, 0.2020, 0.2182, 0.2160,
    0.1941, 0.2056, 0.2264, 0.2027, 0.1969,
]

best_epoch = int(np.argmin(VAL_LOSS)) + 1
best_val   = min(VAL_LOSS)

fig, axes = plt.subplots(1, 2, figsize=(12, 4))

# Total loss
ax = axes[0]
ax.plot(EPOCHS, TRAIN_LOSS, label="Train", color="#2196F3", linewidth=1.5)
ax.plot(EPOCHS, VAL_LOSS,   label="Val",   color="#F44336", linewidth=1.5)
ax.axvline(best_epoch, color="gray", linestyle="--", linewidth=1, alpha=0.7)
ax.annotate(f"Best val={best_val:.4f}\n(epoch {best_epoch})",
            xy=(best_epoch, best_val),
            xytext=(best_epoch + 3, best_val + 0.02),
            fontsize=8, color="gray",
            arrowprops=dict(arrowstyle="->", color="gray", lw=0.8))
ax.set_xlabel("Epoch")
ax.set_ylabel("Total Loss")
ax.set_title("Fine-tuning Loss (50 epochs)")
ax.legend()
ax.grid(True, alpha=0.3)

# Action loss only
ax = axes[1]
ax.plot(EPOCHS, TRAIN_ACTION, label="Train action", color="#2196F3", linewidth=1.5)
ax.plot(EPOCHS, VAL_ACTION,   label="Val action",   color="#F44336", linewidth=1.5)
ax.set_xlabel("Epoch")
ax.set_ylabel("Action Loss (MSE)")
ax.set_title("Action Loss (50 epochs)")
ax.legend()
ax.grid(True, alpha=0.3)

fig.suptitle("ViNT Fine-tuning on LoCoBot Demo Data (20 demos, 4 routes)", fontsize=11)
fig.tight_layout()
out = OUT_DIR / "loss_curves.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {out}")


# ---------------------------------------------------------------------------
# 2. Trajectory map
# ---------------------------------------------------------------------------

def load_split(split: str):
    split_file = SPLITS_DIR / split / "traj_names.txt"
    if not split_file.exists():
        return []
    return [l for l in split_file.read_text().splitlines() if l]


train_names = load_split("train")
val_names   = load_split("val")
eval_names  = load_split("eval")

split_map = {n: "train" for n in train_names}
split_map.update({n: "val" for n in val_names})
split_map.update({n: "eval" for n in eval_names})

colors = {"train": "#2196F3", "val": "#FF9800", "eval": "#4CAF50"}
labels_added = set()

fig, ax = plt.subplots(figsize=(10, 8))

for pkl_path in sorted(DATA_DIR.glob("*/traj_data.pkl")):
    traj_name = pkl_path.parent.name
    split = split_map.get(traj_name, "train")
    color = colors[split]

    with open(pkl_path, "rb") as f:
        data = pickle.load(f)
    pos = np.array(data["position"])
    if pos.shape[0] < 2:
        continue

    label = split if split not in labels_added else None
    ax.plot(pos[:, 0], pos[:, 1], color=color, linewidth=1.2,
            alpha=0.7, label=label)
    ax.plot(pos[0, 0], pos[0, 1], "o", color=color, markersize=4)
    labels_added.add(split)

ax.set_xlabel("X (m)")
ax.set_ylabel("Y (m)")
ax.set_title("Collected Demo Trajectories (top-down view)")
ax.legend(title="Split")
ax.set_aspect("equal")
ax.grid(True, alpha=0.3)
fig.tight_layout()

out = OUT_DIR / "trajectory_map.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {out}")

print("\nAll plots saved to:", OUT_DIR)
