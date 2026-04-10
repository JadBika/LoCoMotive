#!/usr/bin/env python3
import json
import os
from pathlib import Path
from typing import List, Optional

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from nav_msgs.msg import Odometry
from std_msgs.msg import Float32MultiArray

from .topic_config import CAMERA_TOPIC, ODOM_TOPIC, WAYPOINT_TOPIC


class VintInferNode(Node):
    def __init__(self) -> None:
        super().__init__("vint_infer_node")
        self.declare_parameter("model_name", "vint")
        self.declare_parameter("checkpoint_path", "")
        self.declare_parameter("vint_repo_root", "")
        self.declare_parameter("device", "cpu")

        self.last_image = None
        self.last_odom = None
        self.warned_stub = False

        self.create_subscription(Image, CAMERA_TOPIC, self._image_cb, 10)
        self.create_subscription(Odometry, ODOM_TOPIC, self._odom_cb, 10)
        self.waypoint_pub = self.create_publisher(Float32MultiArray, WAYPOINT_TOPIC, 10)
        self.timer = self.create_timer(0.25, self._tick)  # 4 Hz

        self.model_name = self.get_parameter("model_name").get_parameter_value().string_value
        self.device = self.get_parameter("device").get_parameter_value().string_value
        ckpt = self.get_parameter("checkpoint_path").get_parameter_value().string_value.strip()
        repo_root = self.get_parameter("vint_repo_root").get_parameter_value().string_value.strip()

        self.checkpoint_path = self._resolve_checkpoint_path(ckpt)
        self.vint_repo_root = self._resolve_repo_root(repo_root)
        self.model_ready = self._try_load_checkpoint_only()

        self.get_logger().info(
            f"Started vint_infer_node model={self.model_name} "
            f"checkpoint={self.checkpoint_path or '[not set]'} "
            f"repo_root={self.vint_repo_root or '[not set]'} "
            f"ready={self.model_ready}"
        )

    def _image_cb(self, msg: Image) -> None:
        self.last_image = msg

    def _odom_cb(self, msg: Odometry) -> None:
        self.last_odom = msg

    def _tick(self) -> None:
        if self.last_image is None or self.last_odom is None:
            return

        # Current fallback: keep robot behavior deterministic while integration
        # with upstream ViNT forward pass is completed.
        if not self.model_ready and not self.warned_stub:
            self.get_logger().warning(
                "Model runtime is not ready; publishing stub waypoint. "
                "Set checkpoint_path and ensure torch + ViNT deps are installed."
            )
            self.warned_stub = True

        waypoint = Float32MultiArray()
        waypoint.data = self._predict_waypoint_stub()  # [forward_m, lateral_m]
        self.waypoint_pub.publish(waypoint)

        self.get_logger().debug(json.dumps({"waypoint": waypoint.data}))

    def _predict_waypoint_stub(self) -> List[float]:
        return [0.6, 0.0]

    def _resolve_checkpoint_path(self, ckpt: str) -> Optional[str]:
        if not ckpt:
            return None
        expanded = os.path.expanduser(ckpt)
        return str(Path(expanded).resolve())

    def _resolve_repo_root(self, repo_root: str) -> Optional[str]:
        if repo_root:
            return str(Path(os.path.expanduser(repo_root)).resolve())
        # Default expected layout:
        # BC/ros2_adapter/ros2_adapter/vint_infer_node.py -> BC/visualnav-transformer
        default = Path(__file__).resolve().parents[2] / "visualnav-transformer"
        return str(default) if default.exists() else None

    def _try_load_checkpoint_only(self) -> bool:
        """
        Offline-safe scaffold:
        - verifies checkpoint path exists
        - verifies torch can deserialize weights
        This does not yet construct the ViNT model graph.
        """
        if not self.checkpoint_path:
            self.get_logger().warning("checkpoint_path is empty.")
            return False
        if not Path(self.checkpoint_path).exists():
            self.get_logger().warning(f"checkpoint not found: {self.checkpoint_path}")
            return False

        try:
            import torch

            _ = torch.load(self.checkpoint_path, map_location=self.device)
            self.get_logger().info("Checkpoint deserialization succeeded.")
            return True
        except Exception as exc:
            self.get_logger().warning(f"Checkpoint load failed: {exc}")
            return False


def main() -> None:
    rclpy.init()
    node = VintInferNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
