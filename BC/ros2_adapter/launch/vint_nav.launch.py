from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description() -> LaunchDescription:
    camera_topic = LaunchConfiguration("camera_topic")
    odom_topic = LaunchConfiguration("odom_topic")
    waypoint_topic = LaunchConfiguration("waypoint_topic")
    cmd_vel_topic = LaunchConfiguration("cmd_vel_topic")
    vint_repo_root = LaunchConfiguration("vint_repo_root")
    topomap_images_dir = LaunchConfiguration("topomap_images_dir")
    model_name = LaunchConfiguration("model_name")
    checkpoint_path = LaunchConfiguration("checkpoint_path")
    max_v = LaunchConfiguration("max_v")
    max_w = LaunchConfiguration("max_w")
    k_v = LaunchConfiguration("k_v")
    k_w = LaunchConfiguration("k_w")

    return LaunchDescription(
        [
            DeclareLaunchArgument("camera_topic", default_value="/camera/camera/color/image_raw"),
            DeclareLaunchArgument("odom_topic", default_value="/locobot/mobile_base/odom"),
            DeclareLaunchArgument("waypoint_topic", default_value="/waypoint"),
            DeclareLaunchArgument("cmd_vel_topic", default_value="/locobot/mobile_base/cmd_vel"),
            DeclareLaunchArgument("vint_repo_root", default_value=""),
            DeclareLaunchArgument("topomap_images_dir", default_value=""),
            DeclareLaunchArgument("model_name", default_value="vint"),
            DeclareLaunchArgument("checkpoint_path", default_value=""),
            DeclareLaunchArgument("max_v", default_value="0.46"),
            DeclareLaunchArgument("max_w", default_value="1.0"),
            DeclareLaunchArgument("k_v", default_value="7.0"),
            DeclareLaunchArgument("k_w", default_value="2.0"),
            Node(
                package="ros2_adapter",
                executable="vint_infer_node",
                name="vint_infer_node",
                output="screen",
                parameters=[
                    {
                        "model_name": model_name,
                        "vint_repo_root": vint_repo_root,
                        "topomap_images_dir": topomap_images_dir,
                        "checkpoint_path": checkpoint_path,
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
                        "k_v": ParameterValue(k_v, value_type=float),
                        "k_w": ParameterValue(k_w, value_type=float),
                        "max_v": ParameterValue(max_v, value_type=float),
                        "max_w": ParameterValue(max_w, value_type=float),
                        "waypoint_topic": waypoint_topic,
                        "cmd_vel_topic": cmd_vel_topic,
                    }
                ],
            ),
        ]
    )
