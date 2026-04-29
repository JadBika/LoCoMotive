# LoCoBot Navigation - RL Component

SAC based navigation training on the physical LoCoBot WX-250s using robo-gym.

## Requirements

- Docker (with robogym container running)
- Access to the lab network (duckietown WiFi)
- LoCoBot WX-250s (`ford-pinto`)

## Running the Experiments

### Terminal 1 — Launch robot control (SSH into robot)
```bash
ssh locobot@ford-pinto.local
ros2 launch interbotix_xslocobot_control xslocobot_control.launch.py \
    robot_model:=locobot_wx250s \
    use_base:=true \
    use_camera:=true \
    use_lidar:=true \
    lidar_type:=rplidar_a2m8
```
Wait for: `InterbotixRobotXS is up!`

### Terminal 2 — Launch robot server (SSH into robot)
```bash
ssh locobot@ford-pinto.local
source ~/robogym_ws/install/setup.bash
ros2 launch interbotix_rover_robot_server interbotix_rover_robot_server.launch.py \
    real_robot:=true \
    action_cycle_rate:=20.0 \
    context_size:=1 \
    camera:=true \
    resize_image:=true \
    reference_frame:=base_link \
    robot_model:=locobot_wx250s
```

### Terminal 3 — Enter Docker container (White PC)
```bash
docker exec -it robogym bash
git clone https://github.com/JadBika/LoCoMotive.git
cd LoCoMotive/RL/scripts
```

### Terminal 4 — Launch TensorBoard (White PC)
```bash
docker exec -it robogym bash -c \
    "tensorboard --logdir /robogym_ws/src/robo-gym/LoCoMotive/RL/scripts/tb_logs/ \
    --host 0.0.0.0 --port 6006"
```
Then open `http://192.168.50.231:6006` in your browser.

## Training
Inside Terminal 3 (Docker container):
```bash
python3 train.py
```
The script automatically resumes from the latest checkpoint if one exists.
After each episode, place the robot back at the start position and press Enter.

## Evaluation
Inside Terminal 3 (Docker container):
```bash
python3 evaluate.py
```
Loads the latest checkpoint automatically and runs one evaluation episode.

## Testing the Environment
```bash
python3 test_nav_env.py
```

## Files
| File | Description |
|---|---|
| `nav_env.py` | Custom Gymnasium environment wrapping robo-gym |
| `train.py` | SAC training loop with checkpointing and TensorBoard logging |
| `evaluate.py` | Load checkpoint and run evaluation episode |
| `test_nav_env.py` | Sanity check for the environment |

## Resuming Training
Checkpoints are saved every 1,000 steps in `checkpoints/`.
To resume, simply run `python3 train.py`. The latest checkpoint is loaded automatically.
To extend training beyond the current `total_timesteps`, increase the value in `train.py` 
to the new cumulative total (e.g. if you trained 10,000 steps and want 10,000 more, set `total_timesteps=20000`).