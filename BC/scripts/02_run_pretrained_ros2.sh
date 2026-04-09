#!/usr/bin/env bash
set -euo pipefail

: "${ROS_DOMAIN_ID:=20}"
export ROS_DOMAIN_ID

WS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PKG_DIR="$WS_DIR/ros2_adapter"

echo "[INFO] ROS_DOMAIN_ID=$ROS_DOMAIN_ID"
echo "[INFO] Building ros2_adapter package..."
cd "$WS_DIR"
mkdir -p build install log

# Build as a standalone package path
colcon build --base-paths "$PKG_DIR"

source "$WS_DIR/install/setup.bash"

echo "[INFO] Launching ViNT ROS2 adapter stack..."
ros2 launch ros2_adapter vint_nav.launch.py
