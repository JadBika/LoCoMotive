#!/usr/bin/env python3
"""
vint_infer_node.py — ROS2 node that runs ViNT/GNM inference and publishes waypoints.

Ports the core inference logic from visualnav-transformer/deployment/src/navigate.py
to ROS2. Intentionally avoids importing upstream utils.py because it pulls in
diffusion_policy (NoMaD-only dep) at the top level.
"""
import json
import os
import sys
from collections import deque
from pathlib import Path
from typing import List, Optional

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image
from nav_msgs.msg import Odometry
from std_msgs.msg import Float32MultiArray

from .topic_config import CAMERA_TOPIC, ODOM_TOPIC, WAYPOINT_TOPIC

# robot.yaml values (kept here to avoid a runtime file dependency)
_MAX_V = 0.2   # m/s
_RATE = 4.0    # Hz


class VintInferNode(Node):
    def __init__(self) -> None:
        super().__init__("vint_infer_node")

        self.declare_parameter("model_name", "vint")
        self.declare_parameter("checkpoint_path", "")
        self.declare_parameter("vint_repo_root", "")
        self.declare_parameter("device", "cpu")
        self.declare_parameter("camera_topic", CAMERA_TOPIC)
        self.declare_parameter("odom_topic", ODOM_TOPIC)
        self.declare_parameter("waypoint_topic", WAYPOINT_TOPIC)
        self.declare_parameter("topomap_images_dir", "")
        self.declare_parameter("waypoint_index", 2)
        self.declare_parameter("close_threshold", 3)
        self.declare_parameter("radius", 4)

        self.model_name = self.get_parameter("model_name").get_parameter_value().string_value
        self.device_str = self.get_parameter("device").get_parameter_value().string_value
        self.camera_topic = self.get_parameter("camera_topic").get_parameter_value().string_value
        self.odom_topic = self.get_parameter("odom_topic").get_parameter_value().string_value
        self.waypoint_topic = self.get_parameter("waypoint_topic").get_parameter_value().string_value
        self.waypoint_index = self.get_parameter("waypoint_index").get_parameter_value().integer_value
        self.close_threshold = self.get_parameter("close_threshold").get_parameter_value().integer_value
        self.radius = self.get_parameter("radius").get_parameter_value().integer_value

        ckpt = self.get_parameter("checkpoint_path").get_parameter_value().string_value.strip()
        repo_root = self.get_parameter("vint_repo_root").get_parameter_value().string_value.strip()
        topomap_dir = self.get_parameter("topomap_images_dir").get_parameter_value().string_value.strip()

        self.vint_repo_root = self._resolve_repo_root(repo_root)
        self.checkpoint_path = self._resolve_path(ckpt) if ckpt else self._default_checkpoint()
        self.topomap_dir = self._resolve_path(topomap_dir) if topomap_dir else None

        # inference state
        self.context_queue: deque = deque()
        self.context_size: Optional[int] = None
        self.model = None
        self.model_params: Optional[dict] = None
        self.device = None
        self.topomap: List = []
        self.closest_node = 0
        self.goal_node = -1
        self.reached_goal = False
        self.warned_stub = False

        best_effort_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )
        self.create_subscription(Image, self.camera_topic, self._image_cb, 10)
        self.create_subscription(Odometry, self.odom_topic, self._odom_cb, best_effort_qos)
        self.waypoint_pub = self.create_publisher(Float32MultiArray, self.waypoint_topic, 10)
        self.timer = self.create_timer(1.0 / _RATE, self._tick)

        self._add_to_pythonpath()
        self.model_ready = self._load_model()
        if self.model_ready:
            self._load_topomap()

        self.get_logger().info(
            f"vint_infer_node started  model={self.model_name} "
            f"ckpt={self.checkpoint_path or '[not set]'}  "
            f"topomap={self.topomap_dir or '[not set]'}  "
            f"nodes={len(self.topomap)}  ready={self.model_ready}"
        )

    # ── ROS callbacks ──────────────────────────────────────────────────────────

    def _image_cb(self, msg: Image) -> None:
        try:
            pil_img = self._msg_to_pil(msg)
            if self.context_size is not None:
                if len(self.context_queue) >= self.context_size + 1:
                    self.context_queue.popleft()
                self.context_queue.append(pil_img)
        except Exception as exc:
            self.get_logger().warning(f"Image conversion failed: {exc}")

    def _odom_cb(self, msg: Odometry) -> None:
        pass  # ViNT inference is vision-only

    # ── Timer tick ─────────────────────────────────────────────────────────────

    def _tick(self) -> None:
        if not self.model_ready or len(self.topomap) == 0:
            if not self.warned_stub:
                self.get_logger().warning(
                    "Model or topomap not ready — publishing stub waypoint. "
                    "Provide checkpoint_path and topomap_images_dir."
                )
                self.warned_stub = True
            self._publish_waypoint([0.6, 0.0, 0.0, 0.0])
            return

        if len(self.context_queue) <= self.context_size:
            return  # accumulating context

        chosen_wp = self._run_inference()
        if chosen_wp is not None:
            self._publish_waypoint(chosen_wp.tolist())
            self.get_logger().debug(
                json.dumps({"waypoint": chosen_wp.tolist(),
                            "closest_node": self.closest_node})
            )

    def _publish_waypoint(self, data: list) -> None:
        msg = Float32MultiArray()
        msg.data = [float(x) for x in data]
        self.waypoint_pub.publish(msg)

    # ── ViNT inference ─────────────────────────────────────────────────────────

    def _run_inference(self) -> Optional[np.ndarray]:
        import torch

        params = self.model_params
        image_size = params["image_size"]
        goal_node = len(self.topomap) - 1 if self.goal_node == -1 else self.goal_node

        start = max(self.closest_node - self.radius, 0)
        end = min(self.closest_node + self.radius + 1, goal_node)

        context_list = list(self.context_queue)

        distances = []
        waypoints = []
        try:
            with torch.no_grad():
                for sg_img in self.topomap[start:end + 1]:
                    obs_tensor = self._transform_images(context_list, image_size).to(self.device)
                    goal_tensor = self._transform_images([sg_img], image_size).to(self.device)
                    dist, wp = self.model(obs_tensor, goal_tensor)
                    distances.append(dist.item())
                    waypoints.append(wp.squeeze(0).cpu().numpy())
        except Exception as exc:
            self.get_logger().error(f"Inference failed: {exc}")
            return None

        distances = np.array(distances)
        min_idx = int(np.argmin(distances))

        if distances[min_idx] > self.close_threshold:
            chosen_wp = waypoints[min_idx][self.waypoint_index]
            self.closest_node = start + min_idx
        else:
            chosen_wp = waypoints[min(min_idx + 1, len(waypoints) - 1)][self.waypoint_index]
            self.closest_node = min(start + min_idx + 1, goal_node)

        self.reached_goal = (self.closest_node == goal_node)
        if self.reached_goal:
            self.get_logger().info("Reached goal node.")

        if params.get("normalize", False):
            chosen_wp = chosen_wp.copy()
            chosen_wp[:2] *= (_MAX_V / _RATE)

        return chosen_wp

    # ── Image helpers ──────────────────────────────────────────────────────────

    def _msg_to_pil(self, msg: Image):
        from PIL import Image as PILImage
        raw = bytes(msg.data)
        img_np = np.frombuffer(raw, dtype=np.uint8).reshape(msg.height, msg.width, -1)
        if msg.encoding.lower() in ("bgr8", "bgr"):
            img_np = img_np[:, :, ::-1].copy()
        return PILImage.fromarray(img_np)

    def _transform_images(self, pil_imgs, image_size) -> "torch.Tensor":
        """Minimal re-implementation of deployment/src/utils.py:transform_images."""
        import torch
        from torchvision import transforms
        transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225]),
        ])
        if not isinstance(pil_imgs, list):
            pil_imgs = [pil_imgs]
        tensors = []
        for img in pil_imgs:
            img = img.resize(image_size)
            tensors.append(transform(img).unsqueeze(0))
        return torch.cat(tensors, dim=1)

    # ── Model loading ──────────────────────────────────────────────────────────

    def _load_model(self) -> bool:
        if not self.checkpoint_path or not Path(self.checkpoint_path).exists():
            self.get_logger().warning(f"Checkpoint not found: {self.checkpoint_path}")
            return False
        if not self.vint_repo_root:
            self.get_logger().warning("vint_repo_root could not be resolved.")
            return False
        try:
            import torch
            import yaml

            models_yaml = Path(self.vint_repo_root) / "deployment" / "config" / "models.yaml"
            with open(models_yaml) as f:
                model_paths = yaml.safe_load(f)

            cfg_rel = model_paths[self.model_name]["config_path"]
            cfg_abs = Path(self.vint_repo_root) / cfg_rel
            with open(cfg_abs) as f:
                self.model_params = yaml.safe_load(f)

            self.context_size = self.model_params["context_size"]
            self.device = torch.device(self.device_str)

            model = self._build_vint_model(self.model_params)
            checkpoint = torch.load(self.checkpoint_path, map_location=self.device)
            loaded = checkpoint["model"]
            try:
                state_dict = loaded.module.state_dict()
            except AttributeError:
                state_dict = loaded.state_dict()
            model.load_state_dict(state_dict, strict=False)
            model.to(self.device)
            model.eval()
            self.model = model
            self.get_logger().info(
                f"Model loaded: {self.model_name}  "
                f"context_size={self.context_size}  device={self.device}"
            )
            return True
        except Exception as exc:
            self.get_logger().error(f"Model load failed: {exc}")
            return False

    def _build_vint_model(self, cfg: dict):
        """Instantiate ViNT or GNM without importing NoMaD/diffusion_policy."""
        from vint_train.models.vint.vint import ViNT
        from vint_train.models.gnm.gnm import GNM

        mtype = cfg["model_type"]
        if mtype == "vint":
            return ViNT(
                context_size=cfg["context_size"],
                len_traj_pred=cfg["len_traj_pred"],
                learn_angle=cfg["learn_angle"],
                obs_encoder=cfg["obs_encoder"],
                obs_encoding_size=cfg["obs_encoding_size"],
                late_fusion=cfg["late_fusion"],
                mha_num_attention_heads=cfg["mha_num_attention_heads"],
                mha_num_attention_layers=cfg["mha_num_attention_layers"],
                mha_ff_dim_factor=cfg["mha_ff_dim_factor"],
            )
        if mtype == "gnm":
            return GNM(
                cfg["context_size"],
                cfg["len_traj_pred"],
                cfg["learn_angle"],
                cfg["obs_encoding_size"],
                cfg["goal_encoding_size"],
            )
        raise ValueError(f"Unsupported model_type '{mtype}'. Use 'vint' or 'gnm'.")

    # ── Topomap loading ────────────────────────────────────────────────────────

    def _load_topomap(self) -> None:
        if not self.topomap_dir or not Path(self.topomap_dir).exists():
            self.get_logger().warning(
                f"Topomap directory not found: {self.topomap_dir}. "
                "Record a topomap first, then set topomap_images_dir."
            )
            return
        from PIL import Image as PILImage
        filenames = sorted(
            [f for f in os.listdir(self.topomap_dir)
             if f.lower().endswith((".jpg", ".jpeg", ".png"))],
            key=lambda x: int(Path(x).stem)
        )
        if not filenames:
            self.get_logger().warning(f"No images found in topomap dir: {self.topomap_dir}")
            return
        self.topomap = [
            PILImage.open(os.path.join(self.topomap_dir, f)).convert("RGB")
            for f in filenames
        ]
        self.goal_node = len(self.topomap) - 1
        self.get_logger().info(
            f"Topomap loaded: {len(self.topomap)} nodes from {self.topomap_dir}"
        )

    # ── Path helpers ───────────────────────────────────────────────────────────

    def _add_to_pythonpath(self) -> None:
        if not self.vint_repo_root:
            return
        for subdir in ("train",):
            p = os.path.join(self.vint_repo_root, subdir)
            if p not in sys.path:
                sys.path.insert(0, p)

    def _default_checkpoint(self) -> Optional[str]:
        if not self.vint_repo_root:
            return None
        p = Path(self.vint_repo_root) / "deployment" / "model_weights" / f"{self.model_name}.pth"
        return str(p) if p.exists() else None

    def _resolve_path(self, p: str) -> str:
        return str(Path(os.path.expanduser(p)).resolve())

    def _resolve_repo_root(self, repo_root: str) -> Optional[str]:
        if repo_root:
            return str(Path(os.path.expanduser(repo_root)).resolve())
        default = Path(__file__).resolve().parents[2] / "visualnav-transformer"
        return str(default) if default.exists() else None


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
