# BC README

## Repository
- `visualnav-transformer`: `BC/visualnav-transformer`

## Goal
- Behavior Cloning pipeline for LoCoBot navigation.

## Plan
1. Verify robot connection and topics.
2. Run pretrained checkpoint baseline.
3. Collect navigation demonstrations.
4. Process bags and create train/val splits.
5. Fine-tune and evaluate on real robot.

## Notes
- Robot: `ford-pinto` (`locobot_wx250s`)
- Expected key topics: `/usb_cam/image_raw`, `/odom`, `/locobot/mobile_base/cmd_vel`

## ROS2 Adapter (ford-pinto)
0. Run preflight checks:
   - `./scripts/00_preflight_ros2.sh`
1. Run robot connectivity check:
   - `./scripts/01_robot_check.sh`
2. Build + launch ROS2 adapter nodes:
   - `./scripts/02_run_pretrained_ros2.sh`

### Topic Overrides
- You can override topic names without editing code:
  - `CAMERA_TOPIC=/your/camera ODOM_TOPIC=/your/odom CMD_VEL_TOPIC=/your/cmd_vel ./scripts/00_preflight_ros2.sh`
  - `CAMERA_TOPIC=/your/camera ODOM_TOPIC=/your/odom CMD_VEL_TOPIC=/your/cmd_vel ./scripts/02_run_pretrained_ros2.sh`

### Files
- `ros2_adapter/ros2_adapter/vint_infer_node.py`: camera/odom subscriber and waypoint publisher (stub inference).
- `ros2_adapter/ros2_adapter/pd_controller_node.py`: waypoint to `/locobot/mobile_base/cmd_vel`.
- `ros2_adapter/launch/vint_nav.launch.py`: starts both nodes.
