#!/usr/bin/env python3
import json

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

        self.last_image = None
        self.last_odom = None

        self.create_subscription(Image, CAMERA_TOPIC, self._image_cb, 10)
        self.create_subscription(Odometry, ODOM_TOPIC, self._odom_cb, 10)
        self.waypoint_pub = self.create_publisher(Float32MultiArray, WAYPOINT_TOPIC, 10)
        self.timer = self.create_timer(0.25, self._tick)  # 4 Hz

        model_name = self.get_parameter("model_name").get_parameter_value().string_value
        ckpt = self.get_parameter("checkpoint_path").get_parameter_value().string_value
        self.get_logger().info(
            f"Started vint_infer_node model={model_name} checkpoint={ckpt or '[not set]'}"
        )

    def _image_cb(self, msg: Image) -> None:
        self.last_image = msg

    def _odom_cb(self, msg: Odometry) -> None:
        self.last_odom = msg

    def _tick(self) -> None:
        if self.last_image is None or self.last_odom is None:
            return

        # TODO: Replace stub with real ViNT inference.
        waypoint = Float32MultiArray()
        waypoint.data = [0.6, 0.0]  # [forward_m, lateral_m]
        self.waypoint_pub.publish(waypoint)

        self.get_logger().debug(json.dumps({"waypoint": waypoint.data}))


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
