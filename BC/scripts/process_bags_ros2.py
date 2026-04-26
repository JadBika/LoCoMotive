#!/usr/bin/env python3
"""
process_bags_ros2.py — Convert ROS2 bags to ViNT training format.

Output per trajectory:
    BC/data/processed/locobot/<traj_name>/
        0.jpg, 1.jpg, ...
        traj_data.pkl  →  {"position": np.array([[x,y],...]), "yaw": np.array([...])}

Also writes train/val split files to BC/data/splits/locobot/.

Usage:
    python3 scripts/process_bags_ros2.py
"""
import os
import pickle
import argparse
from pathlib import Path
from typing import List, Tuple

import numpy as np
from PIL import Image as PILImage
from tqdm import tqdm

REPO_ROOT = Path(__file__).resolve().parents[1]
BAGS_DIR = REPO_ROOT / "data" / "raw" / "rosbags"
OUT_DIR = REPO_ROOT / "data" / "processed" / "locobot"
SPLITS_DIR = REPO_ROOT / "data" / "splits" / "locobot"

IMAGE_TOPIC = "/camera/camera/color/image_raw"
ODOM_TOPIC = "/locobot/mobile_base/odom"
SAMPLE_HZ = 4.0  # match ViNT training rate


def quat_to_yaw(x: float, y: float, z: float, w: float) -> float:
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    return float(np.arctan2(siny_cosp, cosy_cosp))


def process_bag(bag_path: Path, out_dir: Path) -> bool:
    try:
        from rosbags.rosbag2 import Reader
        from rosbags.typesys import get_typestore, Stores
    except ImportError:
        raise RuntimeError("pip install rosbags>=0.10")

    typestore = get_typestore(Stores.ROS2_HUMBLE)
    out_dir.mkdir(parents=True, exist_ok=True)

    images: List[Tuple[int, PILImage.Image]] = []
    odoms: List[Tuple[int, np.ndarray, float]] = []

    with Reader(str(bag_path)) as reader:
        img_conns = [c for c in reader.connections if c.topic == IMAGE_TOPIC]
        odom_conns = [c for c in reader.connections if c.topic == ODOM_TOPIC]

        if not img_conns or not odom_conns:
            print(f"  Missing topics in {bag_path.name}, skipping.")
            return False

        for conn, ts, raw in reader.messages(connections=img_conns):
            msg = typestore.deserialize_cdr(raw, conn.msgtype)
            img_np = np.frombuffer(msg.data, dtype=np.uint8).reshape(
                msg.height, msg.width, -1
            )
            if msg.encoding.lower() in ("bgr8", "bgr"):
                img_np = img_np[:, :, ::-1].copy()
            images.append((ts, PILImage.fromarray(img_np).convert("RGB")))

        for conn, ts, raw in reader.messages(connections=odom_conns):
            msg = typestore.deserialize_cdr(raw, conn.msgtype)
            px = msg.pose.pose.position.x
            py = msg.pose.pose.position.y
            q = msg.pose.pose.orientation
            yaw = quat_to_yaw(q.x, q.y, q.z, q.w)
            odoms.append((ts, np.array([px, py]), yaw))

    if not images or not odoms:
        print(f"  Empty data in {bag_path.name}, skipping.")
        return False

    # sample images at SAMPLE_HZ
    dt_ns = int(1e9 / SAMPLE_HZ)
    sampled_images = []
    last_ts = -dt_ns
    for ts, img in sorted(images):
        if ts - last_ts >= dt_ns:
            sampled_images.append((ts, img))
            last_ts = ts

    if len(sampled_images) < 5:
        print(f"  Too few frames in {bag_path.name}, skipping.")
        return False

    # for each sampled image, find closest odom by timestamp
    odom_ts = np.array([o[0] for o in odoms])
    positions = []
    yaws = []
    final_images = []

    for ts, img in sampled_images:
        idx = int(np.argmin(np.abs(odom_ts - ts)))
        dt_ms = abs(odom_ts[idx] - ts) / 1e6
        if dt_ms > 200:  # skip if odom is >200ms away
            continue
        positions.append(odoms[idx][1])
        yaws.append(odoms[idx][2])
        final_images.append(img)

    if len(final_images) < 5:
        print(f"  Too few synchronized frames in {bag_path.name}, skipping.")
        return False

    # save images
    for i, img in enumerate(final_images):
        img.save(out_dir / f"{i}.jpg")

    # save traj_data.pkl
    traj_data = {
        "position": np.array(positions),
        "yaw": np.array(yaws),
    }
    with open(out_dir / "traj_data.pkl", "wb") as f:
        pickle.dump(traj_data, f)

    return True


def write_splits(train_names: List[str], val_names: List[str]) -> None:
    for split, names in [("train", train_names), ("val", val_names)]:
        split_dir = SPLITS_DIR / split
        split_dir.mkdir(parents=True, exist_ok=True)
        with open(split_dir / "traj_names.txt", "w") as f:
            f.write("\n".join(names))
    print(f"\nSplits written: {len(train_names)} train, {len(val_names)} val")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--val-ratio", type=float, default=0.2,
                        help="Fraction of demo bags to use for validation (default 0.2)")
    parser.add_argument("--bags-dir", default=str(BAGS_DIR))
    parser.add_argument("--out-dir", default=str(OUT_DIR))
    args = parser.parse_args()

    bags_dir = Path(args.bags_dir)
    out_dir = Path(args.out_dir)

    demo_bags = sorted([p for p in bags_dir.iterdir()
                        if p.is_dir() and p.name.startswith("demo_")])
    eval_bags = sorted([p for p in bags_dir.iterdir()
                        if p.is_dir() and p.name.startswith("eval_")])

    print(f"Found {len(demo_bags)} demo bags, {len(eval_bags)} eval bags")

    # process demo bags
    train_names, val_names = [], []
    n_val = max(1, int(len(demo_bags) * args.val_ratio))

    for i, bag_path in enumerate(tqdm(demo_bags, desc="Processing demo bags")):
        traj_out = out_dir / bag_path.name
        ok = process_bag(bag_path, traj_out)
        if ok:
            if i < len(demo_bags) - n_val:
                train_names.append(bag_path.name)
            else:
                val_names.append(bag_path.name)
            print(f"  ✓ {bag_path.name} → {len(list(traj_out.glob('*.jpg')))} frames")

    # process eval bags (listed separately, not used in train/val split)
    eval_names = []
    for bag_path in tqdm(eval_bags, desc="Processing eval bags"):
        traj_out = out_dir / bag_path.name
        ok = process_bag(bag_path, traj_out)
        if ok:
            eval_names.append(bag_path.name)
            print(f"  ✓ {bag_path.name} → {len(list(traj_out.glob('*.jpg')))} frames")

    # write eval split
    eval_split_dir = SPLITS_DIR / "eval"
    eval_split_dir.mkdir(parents=True, exist_ok=True)
    with open(eval_split_dir / "traj_names.txt", "w") as f:
        f.write("\n".join(eval_names))

    write_splits(train_names, val_names)
    print(f"\nDone. Processed data in: {out_dir}")


if __name__ == "__main__":
    main()
