# Data Collection Procedure

## Robot Setup

**Robot:** `ford-pinto` (`locobot_wx250s`)  
**Camera:** Intel RealSense D435  
**ROS:** ROS2 Humble (Ubuntu 22.04)  
**ROS_DOMAIN_ID:** 20

---

## Terminal Setup (every session)

Every terminal on the robot must have:

```bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=20
```

**Important:** Do NOT activate conda when running ROS2 scripts.
Conda uses Python 3.13 which is incompatible with ROS2 Humble (Python 3.10).

```bash
conda deactivate   # run this if conda is active
```

---

## Step 1 — Launch Robot Stack

```bash
# Terminal 1
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=20
ros2 launch interbotix_xslocobot_control xslocobot_control.launch.py \
  robot_model:=locobot_wx250s \
  use_base:=true \
  use_camera:=false \
  use_lidar:=true \
  lidar_type:=rplidar_a2m8 \
  use_usb_cam:=true
```

## Step 2 — Launch Teleop (Joystick)

```bash
# Terminal 2
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=20
ros2 launch interbotix_xslocobot_joy xslocobot_joy.launch.py \
  robot_model:=locobot_wx250s \
  launch_driver:=false
```

## Step 3 — Launch RealSense Camera

```bash
# Terminal 3
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=20
ros2 launch realsense2_camera rs_launch.py
```

Verify the camera is publishing:

```bash
ros2 topic hz /camera/camera/color/image_raw
# Expected: ~30 Hz
```

## Step 4 — Record Topomap

```bash
# Terminal 4
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=20
cd ~/LoCoMotive/BC/scripts
python3 create_topomap_ros2.py \
  --dir <topomap_name> \
  --dt 1.0 \
  --camera-topic /camera/camera/color/image_raw
```

- `--dir`: name of the topomap (e.g. `lab_route_01`)
- `--dt`: seconds between saved images (1.0 = one image per second)
- Drive the robot through the desired route while the script is running
- Press **Ctrl+C** to stop recording

Images are saved to:

```
~/LoCoMotive/BC/data/topomaps/<topomap_name>/
```

### Collecting Multiple Topomaps

**Each route must use a different `--dir` name.** Using the same name will delete the previous topomap.

```bash
# First route (e.g. hallway A → B)
python3 create_topomap_ros2.py --dir lab_route_01 --dt 1.0 \
  --camera-topic /camera/camera/color/image_raw

# Second route (e.g. hallway B → C)
python3 create_topomap_ros2.py --dir lab_route_02 --dt 1.0 \
  --camera-topic /camera/camera/color/image_raw

# Third route (e.g. loop around lab)
python3 create_topomap_ros2.py --dir lab_route_03 --dt 1.0 \
  --camera-topic /camera/camera/color/image_raw
```

This creates separate folders:
```
topomaps/images/lab_route_01/   ← 0.png, 1.png, ...
topomaps/images/lab_route_02/   ← 0.png, 1.png, ...
topomaps/images/lab_route_03/   ← 0.png, 1.png, ...
```

---

## Verify Collected Data

```bash
# Count nodes
ls ~/LoCoMotive/BC/data/topomaps/<topomap_name>/ | wc -l

# Copy to lab desktop for visual inspection
# On white:
scp -r locobot@192.168.50.194:~/LoCoMotive/BC/visualnav-transformer/deployment/topomaps/images/<topomap_name> \
  ~/<topomap_name>
eog ~/<topomap_name>/
```

What to check:

- Images numbered `0.png, 1.png, 2.png ...` sequentially
- Visually continuous — no black frames or large jumps
- ~10–30 nodes for a short corridor route

---

## Active Topic Names (ford-pinto)

| Topic          | Value                            |
| -------------- | -------------------------------- |
| Camera (color) | `/camera/camera/color/image_raw` |
| Odometry       | `/locobot/mobile_base/odom`      |
| Cmd vel        | `/locobot/mobile_base/cmd_vel`   |

---

## Collected Topomaps

| Name           | Nodes | Date       | Notes            |
| -------------- | ----- | ---------- | ---------------- |
| `lab_route_01` | 22    | 2026-04-15 | First test route |
| `lab_route_02` | ?     | 2026-04-15 |                  |
| `lab_route_03` | ?     | 2026-04-15 |                  |
| `lab_route_04` | ?     | 2026-04-15 |                  |
| `lab_route_05` | ?     | 2026-04-15 |                  |
