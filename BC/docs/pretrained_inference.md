# Running Pretrained ViNT on ford-pinto

End-to-end procedure for running the pretrained `vint.pth` checkpoint with topological map navigation on the real robot.

---

## Requirements

### Robot (ford-pinto)
- Ubuntu 22.04, ROS2 Humble, Python 3.10 (system)
- **Do NOT use conda** — ROS2 is compiled for system Python 3.10

### Desktop (white)
- Used only to transfer files via `scp`
- GPU not needed for this step (inference runs on robot CPU)

---

## One-Time Setup

### 1 — Transfer project to robot

On white, copy the project to the robot:

```bash
scp -r ~/LoCoMotive/BC locobot@192.168.50.194:~/LoCoMotive/
```

Or if updating individual files:

```bash
scp BC/ros2_adapter/ros2_adapter/vint_infer_node.py \
    BC/ros2_adapter/ros2_adapter/pd_controller_node.py \
    locobot@192.168.50.194:~/LoCoMotive/BC/ros2_adapter/ros2_adapter/
```

### 2 — Install Python dependencies on robot

SSH into robot, then install with **system pip3** (not conda):

```bash
ssh locobot@192.168.50.194
conda deactivate   # if conda is active

pip3 install --user torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip3 install --user efficientnet-pytorch Pillow
pip3 install --user git+https://github.com/ildoonet/pytorch-gradual-warmup-lr.git
```

> These install into `~/.local/lib/python3.10/` and are picked up by system Python automatically.

### 3 — Download model checkpoints

On white (has internet access), download from Google Drive:

```bash
cd ~/LoCoMotive/BC/visualnav-transformer/deployment
mkdir -p model_weights
# Download vint, gnm, nomad checkpoints
gdown --folder <gdrive_folder_id> -O /tmp/checkpoints
mv /tmp/checkpoints/*.pth model_weights/
```

Then transfer to robot:

```bash
scp -r model_weights/ locobot@192.168.50.194:~/LoCoMotive/BC/visualnav-transformer/deployment/
```

Verify:

```bash
ls ~/LoCoMotive/BC/visualnav-transformer/deployment/model_weights/
# Expected: vint.pth  gnm.pth  nomad.pth
```

### 4 — Build ROS2 adapter (on robot)

```bash
ssh locobot@192.168.50.194
conda deactivate
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=20

cd ~/LoCoMotive/BC/ros2_adapter
colcon build --packages-select ros2_adapter
source install/setup.bash
```

---

## Every Session

### Terminal 1 — Robot stack

```bash
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

### Terminal 2 — Joystick (optional, for safety override)

```bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=20
ros2 launch interbotix_xslocobot_joy xslocobot_joy.launch.py \
  robot_model:=locobot_wx250s \
  launch_driver:=false
```

### Terminal 3 — RealSense camera

```bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=20
ros2 launch realsense2_camera rs_launch.py
```

Verify:

```bash
ros2 topic hz /camera/camera/color/image_raw
# Expected: ~30 Hz
```

### Terminal 4 — ViNT inference + PD controller

```bash
conda deactivate
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=20

cd ~/LoCoMotive/BC/ros2_adapter
source install/setup.bash

ros2 launch ros2_adapter vint_nav.launch.py \
  vint_repo_root:=/home/locobot/LoCoMotive/BC/visualnav-transformer \
  topomap_images_dir:=/home/locobot/LoCoMotive/BC/data/topomaps/lab_route_01
```

Expected log output:

```
[vint_infer_node] Model loaded: vint  context_size=5  device=cpu
[vint_infer_node] Topomap loaded: 22 nodes from .../lab_route_01
[vint_infer_node] vint_infer_node started  model=vint  ...  nodes=22  ready=True
[pd_controller_node] Started pd_controller_node out=/locobot/mobile_base/cmd_vel ...
```

Place the robot at the **start position of the recorded topomap** before the node accumulates context (~1.5 s).

---

## Switching Topomap

Pass a different `topomap_images_dir`:

```bash
ros2 launch ros2_adapter vint_nav.launch.py \
  vint_repo_root:=/home/locobot/LoCoMotive/BC/visualnav-transformer \
  topomap_images_dir:=/home/locobot/LoCoMotive/BC/data/topomaps/lab_route_02
```

Available topomaps:

| Name | Nodes | Date |
|------|-------|------|
| `lab_route_01` | 22 | 2026-04-15 |
| `lab_route_02` | ? | 2026-04-15 |
| `lab_route_03` | ? | 2026-04-15 |
| `lab_route_04` | ? | 2026-04-15 |
| `lab_route_05` | ? | 2026-04-15 |

---

## Diagnostics

```bash
# Check waypoint values (x ≈ 0.06–0.15 when going straight)
ros2 topic echo /waypoint

# Check actual velocity commands sent to base
ros2 topic echo /locobot/mobile_base/cmd_vel

# Check inference + publish rates
ros2 topic hz /waypoint
ros2 topic hz /locobot/mobile_base/cmd_vel  # expected ~50 Hz
```

---

## Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `model_name` | `vint` | `vint` or `gnm` |
| `checkpoint_path` | auto (model_weights/vint.pth) | Override checkpoint |
| `topomap_images_dir` | — | **Required**: path to topomap folder |
| `vint_repo_root` | auto | Path to `visualnav-transformer/` |
| `waypoint_index` | `2` | Which step of predicted trajectory to follow |
| `close_threshold` | `3` | Distance to consider a node reached |
| `radius` | `2` | Topomap search window around closest node |
| `device` | `cpu` | `cpu` or `cuda` |

PD controller (`pd_controller_node`):

| Parameter | Value | Description |
|-----------|-------|-------------|
| `k_v` | 7.0 | Forward gain |
| `k_w` | 2.0 | Angular gain |
| `max_v` | 0.46 | Max linear speed (Create3 limit, m/s) |
| `max_w` | 1.0 | Max angular speed (rad/s) |

---

## Active Topics (ford-pinto)

| Topic | Value |
|-------|-------|
| Camera | `/camera/camera/color/image_raw` |
| Odometry | `/locobot/mobile_base/odom` |
| Cmd vel | `/locobot/mobile_base/cmd_vel` |
| Waypoint (internal) | `/waypoint` |

---

## Common Errors

| Error | Fix |
|-------|-----|
| `No module named 'torch'` | `conda deactivate` then use system Python; reinstall with `pip3 install --user` |
| `No module named 'efficientnet_pytorch'` | `pip3 install --user efficientnet-pytorch` |
| `No module named 'warmup_scheduler'` | `pip3 install --user git+https://github.com/ildoonet/pytorch-gradual-warmup-lr.git` |
| `Checkpoint not found` | Verify `model_weights/vint.pth` exists; check `vint_repo_root` parameter |
| `Topomap directory not found` | Check `topomap_images_dir` path; images must be named `0.png, 1.png, ...` |
| Camera not publishing | Launch realsense with `export ROS_DOMAIN_ID=20` explicitly in the same terminal |
| QoS mismatch on odom | Already fixed: odom subscriber uses `BEST_EFFORT` QoS |
| `weights_only` error on torch.load | Already fixed: `weights_only=False` in `_load_model` |
