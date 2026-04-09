#!/usr/bin/env bash
set -euo pipefail

: "${ROS_DOMAIN_ID:=20}"
export ROS_DOMAIN_ID

echo "[INFO] ROS_DOMAIN_ID=$ROS_DOMAIN_ID"
echo "[INFO] Checking key topics..."
ros2 topic list | rg -e "/locobot/mobile_base/cmd_vel|/odom|/usb_cam/image_raw" || true

echo "[INFO] Odom rate (3s)..."
timeout 3 ros2 topic hz /odom || true

echo "[INFO] Sending tiny forward command..."
ros2 topic pub --once /locobot/mobile_base/cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.05, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"

sleep 1

echo "[INFO] Sending stop command..."
ros2 topic pub --once /locobot/mobile_base/cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"

echo "[OK] Basic robot connectivity check completed."
