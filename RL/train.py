from stable_baselines3 import SAC
from stable_baselines3.common.callbacks import CheckpointCallback
from locobot_nav_env import LocobotNavEnv

GOAL = [1.5, 0.0]  # 1.5 meters ahead

env = LocobotNavEnv(goal_pos=GOAL)

checkpoint_cb = CheckpointCallback(
    save_freq=1000,
    save_path='./checkpoints/',
    name_prefix='locobot_nav'
)

model = SAC(
    "MlpPolicy",
    env,
    verbose=1,
    learning_rate=3e-4,
    buffer_size=50_000,
    batch_size=256,
    learning_starts=500,
    tensorboard_log="./tb_logs/"
)

model.learn(
    total_timesteps=50_000,
    callback=checkpoint_cb
)
model.save("locobot_nav_final")