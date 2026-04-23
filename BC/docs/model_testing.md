# Model Testing Procedure

Compare pretrained vs fine-tuned ViNT on the same topomap route.

---

## One-Time Setup

### 1 — Transfer project to robot (from Mac)

```bash
scp -r ~/LoCoMotive/BC locobot@192.168.50.194:~/LoCoMotive/
```

Or update individual files only:
```bash
scp BC/ros2_adapter/ros2_adapter/vint_infer_node.py \
    BC/ros2_adapter/ros2_adapter/pd_controller_node.py \
    locobot@192.168.50.194:~/LoCoMotive/BC/ros2_adapter/ros2_adapter/
```

### 2 — Install Python dependencies on robot

SSH into robot, install with **system pip3** (not conda):

```bash
ssh locobot@192.168.50.194
conda deactivate

pip3 install --user torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip3 install --user efficientnet-pytorch Pillow
pip3 install --user git+https://github.com/ildoonet/pytorch-gradual-warmup-lr.git
```

> Installs into `~/.local/lib/python3.10/` — picked up by system Python automatically.

### 3 — Build ros2_adapter (on robot, once per session after reboot)

```bash
conda deactivate
source /opt/ros/humble/setup.bash && export ROS_DOMAIN_ID=20

cd ~/LoCoMotive/BC/ros2_adapter
colcon build --packages-select ros2_adapter
source install/setup.bash
```

### 4 — Transfer fine-tuned checkpoint to robot (from Mac)

```bash
ssh locobot@192.168.50.194 "mkdir -p ~/LoCoMotive/BC/checkpoints/finetuned"

scp "BC/checkpoints/finetuned/vint_finetuned_best.pth" \
    locobot@192.168.50.194:~/LoCoMotive/BC/checkpoints/finetuned/
```

---

## Every Session

### Terminal 1 — Robot stack

```bash
source /opt/ros/humble/setup.bash && export ROS_DOMAIN_ID=20
ros2 launch interbotix_xslocobot_control xslocobot_control.launch.py \
  robot_model:=locobot_wx250s use_base:=true use_camera:=false \
  use_lidar:=true lidar_type:=rplidar_a2m8 use_usb_cam:=true
```

### Terminal 2 — Joystick (safety override)

```bash
source /opt/ros/humble/setup.bash && export ROS_DOMAIN_ID=20
ros2 launch interbotix_xslocobot_joy xslocobot_joy.launch.py \
  robot_model:=locobot_wx250s launch_driver:=false
```

### Terminal 3 — RealSense camera

```bash
source /opt/ros/humble/setup.bash && export ROS_DOMAIN_ID=20
ros2 launch realsense2_camera rs_launch.py
```

Verify: `ros2 topic hz /camera/camera/color/image_raw` → ~30 Hz

### Terminal 4 — ViNT inference

Source the adapter first (required every session):
```bash
conda deactivate
source /opt/ros/humble/setup.bash && export ROS_DOMAIN_ID=20
cd ~/LoCoMotive/BC/ros2_adapter && source install/setup.bash
```

---

## Launch Commands

### Pretrained model (baseline)

```bash
ros2 launch ros2_adapter vint_nav.launch.py \
  vint_repo_root:=~/LoCoMotive/BC/visualnav-transformer \
  topomap_images_dir:=~/LoCoMotive/BC/data/topomaps/eval_route_01
```

### Fine-tuned model

```bash
ros2 launch ros2_adapter vint_nav.launch.py \
  vint_repo_root:=~/LoCoMotive/BC/visualnav-transformer \
  topomap_images_dir:=~/LoCoMotive/BC/data/topomaps/eval_route_01 \
  checkpoint_path:=~/LoCoMotive/BC/checkpoints/finetuned/vint_finetuned_best.pth
```

Change `eval_route_01` to `eval_route_02`, `03`, `04` for other routes.

### Speed tuning (if needed)

```bash
# Slower (default is max_v=0.46, k_v=7.0)
  max_v:=0.2 k_v:=3.0
```

---

## Diagnostics

```bash
# Check waypoint predictions (x ≈ 0.06–0.15 going straight, y ≠ 0 when turning)
ros2 topic echo /waypoint

# Check velocity commands sent to base
ros2 topic echo /locobot/mobile_base/cmd_vel

# Check publish rates
ros2 topic hz /waypoint                        # expected ~4 Hz
ros2 topic hz /locobot/mobile_base/cmd_vel    # expected ~50 Hz
```

### Symptoms and fixes

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Robot goes straight on all routes | `/waypoint` y ≈ 0 always | Check robot start position matches topomap start; verify topomap has turns |
| Robot doesn't move | `/waypoint` not publishing | Check inference node started correctly; check camera topic |
| Package not found error | ros2_adapter not sourced | Run `cd ~/LoCoMotive/BC/ros2_adapter && source install/setup.bash` |
| Empty topomap | Wrong camera topic used | Re-record with `--camera-topic /camera/camera/color/image_raw` |
| Robot too fast / too slow | PD gains | Adjust `max_v` and `k_v` in launch command |

---

## Result Logging

For each trial, record in `BC/results/metrics/`:

| Field | Value |
|-------|-------|
| `model` | `pretrained` or `finetuned` |
| `topomap` | e.g. `eval_route_01` |
| `success` | 1 / 0 |
| `collision` | 1 / 0 |
| `time_sec` | seconds to complete route |
| `notes` | observations |
