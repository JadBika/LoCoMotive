#!/usr/bin/env python3
import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32MultiArray

from .topic_config import WAYPOINT_TOPIC, CMD_VEL_TOPIC


class PdControllerNode(Node):
    def __init__(self) -> None:
        super().__init__("pd_controller_node")
        self.declare_parameter("k_v", 7.0)
        self.declare_parameter("k_w", 2.0)
        self.declare_parameter("max_v", 0.46)
        self.declare_parameter("max_w", 1.0)
        self.declare_parameter("waypoint_topic", WAYPOINT_TOPIC)
        self.declare_parameter("cmd_vel_topic", CMD_VEL_TOPIC)

        self.k_v = self.get_parameter("k_v").get_parameter_value().double_value
        self.k_w = self.get_parameter("k_w").get_parameter_value().double_value
        self.max_v = self.get_parameter("max_v").get_parameter_value().double_value
        self.max_w = self.get_parameter("max_w").get_parameter_value().double_value
        self.waypoint_topic = (
            self.get_parameter("waypoint_topic").get_parameter_value().string_value
        )
        self.cmd_vel_topic = self.get_parameter("cmd_vel_topic").get_parameter_value().string_value

        self.cmd_pub = self.create_publisher(Twist, self.cmd_vel_topic, 10)
        self.create_subscription(Float32MultiArray, self.waypoint_topic, self._waypoint_cb, 10)
        self._last_cmd = Twist()  # cached command, re-sent at 20 Hz
        self.create_timer(1.0 / 50.0, self._publish_last_cmd)

        self.get_logger().info(
            f"Started pd_controller_node out={self.cmd_vel_topic} waypoint={self.waypoint_topic} "
            f"k_v={self.k_v} k_w={self.k_w}"
        )

    def _clamp(self, val: float, lim: float) -> float:
        return max(-lim, min(lim, val))

    def _waypoint_cb(self, msg: Float32MultiArray) -> None:
        if len(msg.data) < 2:
            self.get_logger().warning("Waypoint must contain at least 2 values [x, y]")
            return

        x = float(msg.data[0])
        y = float(msg.data[1])

        heading = math.atan2(y, max(1e-6, x))

        v = self._clamp(self.k_v * x, self.max_v)
        w = self._clamp(self.k_w * heading, self.max_w)

        self._last_cmd.linear.x = v
        self._last_cmd.angular.z = w

    def _publish_last_cmd(self) -> None:
        self.cmd_pub.publish(self._last_cmd)


def main() -> None:
    rclpy.init()
    node = PdControllerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node._last_cmd = Twist()  # zero velocity on shutdown
        node.cmd_pub.publish(node._last_cmd)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
