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

```bash
conda deactivate   # run this if conda is active
```

---

## Step 1 — Launch Robot Stack

```bash
# Terminal 1
source /opt/ros/humble/setup.bash && export ROS_DOMAIN_ID=20
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
source /opt/ros/humble/setup.bash && export ROS_DOMAIN_ID=20
ros2 launch interbotix_xslocobot_joy xslocobot_joy.launch.py \
  robot_model:=locobot_wx250s \
  launch_driver:=false
```

## Step 3 — Launch RealSense Camera

```bash
# Terminal 3
source /opt/ros/humble/setup.bash && export ROS_DOMAIN_ID=20
ros2 launch realsense2_camera rs_launch.py
```

Verify the camera is publishing:

```bash
ros2 topic hz /camera/camera/color/image_raw
# Expected: ~30 Hz
```

---

## Topomap Collection

Topomaps are the goal-image sequences used during navigation. Record one topomap per route by driving the robot along the route.

```bash
# Terminal 4 — run from BC/ directory
source /opt/ros/humble/setup.bash && export ROS_DOMAIN_ID=20
cd ~/LoCoMotive/BC
python3 scripts/create_topomap_ros2.py \
  --dir <topomap_name> \
  --dt 1.0 \
  --camera-topic /camera/camera/color/image_raw
```

- `--dir`: name of the topomap (e.g. `eval_route_01`) — **must be unique per route**
- `--dt`: seconds between saved images (1.0 = one image per second at walking speed)
- Drive the robot through the desired route while the script is running
- Press **Ctrl+C** to stop recording

> **Common mistake:** Forgetting `--camera-topic /camera/camera/color/image_raw` causes empty topomaps (default topic is `/usb_cam/image_raw` which is not used).

Images are saved to:
```
~/LoCoMotive/BC/data/topomaps/<topomap_name>/0.png, 1.png, ...
```

### Verify after recording

```bash
ls ~/LoCoMotive/BC/data/topomaps/<topomap_name>/ | wc -l
# Should be > 0 (typically 10–40 nodes for a lab route)
```

---

## Demo Bag Collection (for fine-tuning)

Record demonstrations by driving the robot manually along a route while recording all sensor data.

```bash
# Terminal 4
source /opt/ros/humble/setup.bash && export ROS_DOMAIN_ID=20
cd ~/LoCoMotive/BC/data/raw/rosbags
ros2 bag record \
  /camera/camera/color/image_raw \
  /locobot/mobile_base/odom \
  -o demo_route_01
```

- Name convention: `demo_route_<NN>` for training demos, `eval_route_<NN>` for evaluation bags
- Record 5+ demos per route for fine-tuning
- Press **Ctrl+C** to stop

---

## Transfer Data to Mac (for fine-tuning)

From Mac (white or personal laptop):

```bash
# Transfer all rosbags
scp -r locobot@192.168.50.194:~/LoCoMotive/BC/data/raw/rosbags/ \
    "BC/data/raw/"

# Transfer topomaps
scp -r locobot@192.168.50.194:~/LoCoMotive/BC/data/topomaps/ \
    "BC/data/"
```

---

## Collected Topomaps

| Name            | Nodes | Date       | Purpose      |
|-----------------|-------|------------|--------------|
| `lab_route_01`  | 22    | 2026-04-15 | Training nav test |
| `lab_route_02`  | ?     | 2026-04-15 | Training nav test |
| `lab_route_03`  | ?     | 2026-04-15 | Training nav test |
| `lab_route_04`  | ?     | 2026-04-15 | Training nav test |
| `eval_route_01` | ?     | 2026-04-21 | Evaluation   |
| `eval_route_02` | ?     | 2026-04-21 | Evaluation   |
| `eval_route_03` | ?     | 2026-04-21 | Evaluation   |
| `eval_route_04` | ?     | 2026-04-21 | Evaluation   |

---

## Active Topic Names (ford-pinto)

| Topic          | Value                            |
|----------------|----------------------------------|
| Camera (color) | `/camera/camera/color/image_raw` |
| Odometry       | `/locobot/mobile_base/odom`      |
| Cmd vel        | `/locobot/mobile_base/cmd_vel`   |
