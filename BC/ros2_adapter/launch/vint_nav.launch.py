from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    camera_topic = LaunchConfiguration("camera_topic")
    odom_topic = LaunchConfiguration("odom_topic")
    waypoint_topic = LaunchConfiguration("waypoint_topic")
    cmd_vel_topic = LaunchConfiguration("cmd_vel_topic")

    return LaunchDescription(
        [
            DeclareLaunchArgument("camera_topic", default_value="/usb_cam/image_raw"),
            DeclareLaunchArgument("odom_topic", default_value="/odom"),
            DeclareLaunchArgument("waypoint_topic", default_value="/waypoint"),
            DeclareLaunchArgument("cmd_vel_topic", default_value="/locobot/mobile_base/cmd_vel"),
            Node(
                package="ros2_adapter",
                executable="vint_infer_node",
                name="vint_infer_node",
                output="screen",
                parameters=[
                    {
                        "model_name": "vint",
                        "checkpoint_path": "",
                        "camera_topic": camera_topic,
                        "odom_topic": odom_topic,
                        "waypoint_topic": waypoint_topic,
                    }
                ],
            ),
            Node(
                package="ros2_adapter",
                executable="pd_controller_node",
                name="pd_controller_node",
                output="screen",
                parameters=[
                    {
                        "k_v": 0.6,
                        "k_w": 1.2,
                        "max_v": 0.15,
                        "max_w": 0.6,
                        "waypoint_topic": waypoint_topic,
                        "cmd_vel_topic": cmd_vel_topic,
                    }
                ],
            ),
        ]
    )
