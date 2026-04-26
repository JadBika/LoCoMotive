#!/usr/bin/env bash
set -euo pipefail

: "${ROS_DOMAIN_ID:=20}"
export ROS_DOMAIN_ID
: "${RMW_IMPLEMENTATION:=rmw_fastrtps_cpp}"
export RMW_IMPLEMENTATION

: "${CMD_VEL_TOPIC:=/locobot/mobile_base/cmd_vel}"
: "${ODOM_TOPIC:=/odom}"
: "${CAMERA_TOPIC:=/usb_cam/image_raw}"

echo "[INFO] ROS_DOMAIN_ID=$ROS_DOMAIN_ID"
echo "[INFO] Checking key topics..."
ros2 topic list | grep -E "cmd_vel|odom|image_raw|camera|mobile_base" || true

echo "[INFO] Odom rate (3s)..."
timeout 3 ros2 topic hz "$ODOM_TOPIC" || true

echo "[INFO] Sending tiny forward command..."
timeout 5 ros2 topic pub --once "$CMD_VEL_TOPIC" geometry_msgs/msg/Twist \
"{linear: {x: 0.05, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"

sleep 1

echo "[INFO] Sending stop command..."
timeout 5 ros2 topic pub --once "$CMD_VEL_TOPIC" geometry_msgs/msg/Twist \
"{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"

echo "[OK] Basic robot connectivity check completed."
