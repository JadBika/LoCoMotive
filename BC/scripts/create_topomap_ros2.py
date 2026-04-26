#!/usr/bin/env python3
"""
create_topomap_ros2.py — ROS2 port of create_topomap.py

Teleop the robot along the desired route while this script is running.
It saves one image every --dt seconds from the camera topic.

Usage:
    # source ROS2 first
    source /opt/ros/humble/setup.bash
    python3 create_topomap_ros2.py --dir lab_route_01 --dt 1.0
"""
import argparse
import os
import sys
import time
from pathlib import Path

import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image

TOPOMAP_IMAGES_DIR = str(Path(__file__).resolve().parents[1] / "data" / "topomaps")
DEFAULT_CAMERA_TOPIC = "/usb_cam/image_raw"


class TopoMapRecorder(Node):
    def __init__(self, topomap_dir: str, dt: float, camera_topic: str) -> None:
        super().__init__("create_topomap")

        self.topomap_dir = topomap_dir
        self.dt = dt
        self.idx = 0
        self.last_save_time = time.time()
        self.last_msg_time = time.time()
        self.running = True

        os.makedirs(self.topomap_dir, exist_ok=True)
        # Clear existing images
        for f in Path(self.topomap_dir).glob("*.png"):
            f.unlink()
        for f in Path(self.topomap_dir).glob("*.jpg"):
            f.unlink()

        self.create_subscription(Image, camera_topic, self._image_cb, 1)
        self.timer = self.create_timer(0.1, self._check_timeout)

        self.get_logger().info(
            f"Recording topomap to: {self.topomap_dir}\n"
            f"  camera_topic : {camera_topic}\n"
            f"  dt           : {self.dt}s\n"
            f"Teleop the robot now. Press Ctrl+C to stop."
        )

    def _image_cb(self, msg: Image) -> None:
        self.last_msg_time = time.time()
        now = time.time()
        if now - self.last_save_time < self.dt:
            return

        try:
            from PIL import Image as PILImage
            raw = bytes(msg.data)
            img_np = np.frombuffer(raw, dtype=np.uint8).reshape(msg.height, msg.width, -1)
            if msg.encoding.lower() in ("bgr8", "bgr"):
                img_np = img_np[:, :, ::-1].copy()
            pil_img = PILImage.fromarray(img_np)
            out_path = os.path.join(self.topomap_dir, f"{self.idx}.png")
            pil_img.save(out_path)
            self.get_logger().info(f"Saved node {self.idx}  →  {out_path}")
            self.idx += 1
            self.last_save_time = now
        except Exception as exc:
            self.get_logger().warning(f"Failed to save image: {exc}")

    def _check_timeout(self) -> None:
        if time.time() - self.last_msg_time > 5.0 and self.idx > 0:
            self.get_logger().warning("No images received for 5s. Check camera topic.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Record a topological map by teleoperating the robot."
    )
    parser.add_argument(
        "--dir", "-d", default="topomap", type=str,
        help="Name of the topomap (saved under deployment/topomaps/images/<dir>)"
    )
    parser.add_argument(
        "--dt", "-t", default=1.0, type=float,
        help="Seconds between saved images (default: 1.0)"
    )
    parser.add_argument(
        "--camera-topic", default=DEFAULT_CAMERA_TOPIC, type=str,
        help=f"Camera topic (default: {DEFAULT_CAMERA_TOPIC})"
    )

    # rclpy may consume its own args; split on '--'
    argv = sys.argv[1:]
    if "--ros-args" in argv:
        idx = argv.index("--ros-args")
        ros_argv = argv[idx:]
        argv = argv[:idx]
    else:
        ros_argv = []

    args = parser.parse_args(argv)
    assert args.dt > 0, "--dt must be positive"

    topomap_dir = os.path.join(TOPOMAP_IMAGES_DIR, args.dir)

    rclpy.init(args=ros_argv if ros_argv else None)
    node = TopoMapRecorder(topomap_dir, args.dt, args.camera_topic)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.get_logger().info(
            f"Topomap recording complete. {node.idx} nodes saved to {topomap_dir}"
        )
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
