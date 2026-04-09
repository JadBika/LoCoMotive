from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            Node(
                package="ros2_adapter",
                executable="vint_infer_node",
                name="vint_infer_node",
                output="screen",
                parameters=[
                    {
                        "model_name": "vint",
                        "checkpoint_path": "",
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
                    }
                ],
            ),
        ]
    )
