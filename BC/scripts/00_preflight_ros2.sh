#!/usr/bin/env bash
set -euo pipefail

: "${ROS_DOMAIN_ID:=20}"
export ROS_DOMAIN_ID
: "${RMW_IMPLEMENTATION:=rmw_fastrtps_cpp}"
export RMW_IMPLEMENTATION

: "${CAMERA_TOPIC:=/usb_cam/image_raw}"
: "${ODOM_TOPIC:=/odom}"
: "${CMD_VEL_TOPIC:=/locobot/mobile_base/cmd_vel}"

if [[ -n "${ROS_DISCOVERY_SERVER:-}" ]]; then
  echo "[INFO] ROS_DISCOVERY_SERVER=$ROS_DISCOVERY_SERVER"
fi

echo "[INFO] ROS_DOMAIN_ID=$ROS_DOMAIN_ID"
echo "[INFO] RMW_IMPLEMENTATION=$RMW_IMPLEMENTATION"

echo "[CHECK] ros2 CLI"
command -v ros2 >/dev/null && echo "[OK] ros2 found" || { echo "[FAIL] ros2 missing"; exit 1; }

echo "[CHECK] rclpy import"
if python3 -c "import rclpy" 2>/dev/null; then
  echo "[OK] rclpy import"
else
  echo "[FAIL] rclpy import failed"
  echo "[HINT] run: source /opt/ros/humble/setup.bash"
  exit 1
fi

echo "[CHECK] topic visibility"
ros2 topic list | grep -E "cmd_vel|odom|image_raw|camera|mobile_base" || true

for t in "$CAMERA_TOPIC" "$ODOM_TOPIC" "$CMD_VEL_TOPIC"; do
  if ros2 topic list | grep -Fx "$t" >/dev/null; then
    echo "[OK] topic exists: $t"
  else
    echo "[WARN] topic missing: $t"
  fi
done

echo "[CHECK] cmd_vel subscriber count"
if ros2 topic list | grep -Fx "$CMD_VEL_TOPIC" >/dev/null; then
  ros2 topic info "$CMD_VEL_TOPIC" || true
else
  echo "[WARN] Cannot query subscriber count because topic is missing: $CMD_VEL_TOPIC"
fi

echo "[DONE] Preflight complete."
