#!/usr/bin/env bash
set -euo pipefail

: "${ROS_DOMAIN_ID:=20}"
export ROS_DOMAIN_ID
: "${RMW_IMPLEMENTATION:=rmw_fastrtps_cpp}"
export RMW_IMPLEMENTATION

WS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PKG_DIR="$WS_DIR/ros2_adapter"
: "${CAMERA_TOPIC:=/usb_cam/image_raw}"
: "${ODOM_TOPIC:=/odom}"
: "${WAYPOINT_TOPIC:=/waypoint}"
: "${CMD_VEL_TOPIC:=/locobot/mobile_base/cmd_vel}"

echo "[INFO] ROS_DOMAIN_ID=$ROS_DOMAIN_ID"
cd "$WS_DIR"

if command -v colcon >/dev/null 2>&1; then
  echo "[INFO] Building ros2_adapter package with colcon..."
  mkdir -p build install log
  colcon build --base-paths "$PKG_DIR"
  source "$WS_DIR/install/setup.bash"

  echo "[INFO] Launching ViNT ROS2 adapter stack..."
  ros2 launch ros2_adapter vint_nav.launch.py \
    camera_topic:="$CAMERA_TOPIC" \
    odom_topic:="$ODOM_TOPIC" \
    waypoint_topic:="$WAYPOINT_TOPIC" \
    cmd_vel_topic:="$CMD_VEL_TOPIC"
else
  echo "[WARN] colcon not found. Falling back to direct Python node launch."
  echo "[WARN] For production usage, install colcon and use ROS2 package launch."
  export PYTHONPATH="$PKG_DIR:$PYTHONPATH"

  python3 -m ros2_adapter.vint_infer_node \
    --ros-args \
    -p camera_topic:="$CAMERA_TOPIC" \
    -p odom_topic:="$ODOM_TOPIC" \
    -p waypoint_topic:="$WAYPOINT_TOPIC" &
  INFER_PID=$!

  cleanup() {
    kill "$INFER_PID" 2>/dev/null || true
  }
  trap cleanup EXIT INT TERM

  python3 -m ros2_adapter.pd_controller_node \
    --ros-args \
    -p waypoint_topic:="$WAYPOINT_TOPIC" \
    -p cmd_vel_topic:="$CMD_VEL_TOPIC"
fi
