from stable_baselines3 import SAC
from stable_baselines3.common.callbacks import CheckpointCallback
from nav_env import LocobotNavEnv
import torch

print("GPU available:", torch.cuda.is_available())

env = LocobotNavEnv()

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
    learning_starts=200,
    tensorboard_log="./tb_logs/",
    device = "cpu"
)

print("Starting training...")
model.learn(
    total_timesteps=50_000,
    callback=checkpoint_cb
)
model.save("locobot_nav_final")
print("Training complete!")