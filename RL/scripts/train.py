import os
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

from stable_baselines3 import SAC
from stable_baselines3.common.callbacks import CheckpointCallback, BaseCallback
from nav_env import LocobotNavEnv
import torch
import wandb
from wandb.integration.sb3 import WandbCallback

class ResetCallback(BaseCallback):
    def __init__(self, verbose=0):
        super().__init__(verbose)
        self.episode_count = 0

    def _on_step(self) -> bool:
        dones = self.locals.get('dones', [False])
        if any(dones):
            self.episode_count += 1
            print(f"\n{'='*50}")
            print(f"Episode {self.episode_count} finished.")
            print(f"Place robot back at start position.")
            print(f"{'='*50}")
            input("Press Enter when ready to continue...")
        return True

print("GPU available:", torch.cuda.is_available())

run = wandb.init(
    project="locobot-navigation",
    resume="allow",
    config={
        "algorithm": "SAC",
        "total_timesteps": 50_000,
        "learning_rate": 3e-4,
        "batch_size": 256,
        "buffer_size": 50_000,
        "learning_starts": 200,
        "goal_distance": 1.5,
        "max_steps_per_episode": 100,
        "observation": "camera+odometry",
        "policy": "MultiInputPolicy"
    }
)

env = LocobotNavEnv()

checkpoint_cb = CheckpointCallback(
    save_freq=1000,
    save_path='./checkpoints/',
    name_prefix='locobot_nav'
)

wandb_cb = WandbCallback(
    gradient_save_freq=1000,
    model_save_path=f"models/{run.id}",
    verbose=2
)

reset_cb = ResetCallback()

# Load existing model if available
checkpoint_path = './checkpoints/'
existing_checkpoints = sorted([
    f for f in os.listdir(checkpoint_path)
    if f.startswith('locobot_nav')
]) if os.path.exists(checkpoint_path) else []

if existing_checkpoints:
    latest = os.path.join(checkpoint_path, existing_checkpoints[-1])
    print(f"Resuming from checkpoint: {latest}")
    model = SAC.load(latest, env=env, device="cpu")
else:
    print("Starting fresh training...")
    model = SAC(
        "MultiInputPolicy",
        env,
        verbose=1,
        learning_rate=3e-4,
        buffer_size=50_000,
        batch_size=256,
        learning_starts=200,
        device="cpu",
        tensorboard_log="./tb_logs/"
    )

print("Starting training...")
model.learn(
    total_timesteps=50_000,
    callback=[checkpoint_cb, wandb_cb, reset_cb],
    log_interval=1,
    reset_num_timesteps=False
)
model.save("locobot_nav_final")
run.finish()
print("Training complete!")