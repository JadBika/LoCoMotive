from stable_baselines3 import SAC
from nav_env import LocobotNavEnv
import numpy as np

env = LocobotNavEnv()
model = SAC.load("checkpoints/locobot_nav_4000_steps", env=env, device="cpu")

obs, _ = env.reset()
total_reward = 0

for _ in range(20):
    action, _ = model.predict(obs, deterministic=True)
    obs, reward, terminated, truncated, info = env.step(action)
    total_reward += reward
    if terminated or truncated:
        break

print(f"Total reward: {total_reward:.2f}")
print("Goal reached!" if terminated else "Did not reach goal")
env.close()