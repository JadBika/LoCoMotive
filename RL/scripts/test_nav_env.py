from nav_env import LocobotNavEnv
import numpy as np

env = LocobotNavEnv()
obs, _ = env.reset()
print("State shape:", obs['state'].shape)
print("Image shape:", obs['image'].shape)
print("Initial state:", obs['state'])
print("Distance to goal:", np.linalg.norm(obs['state'][:2]))

for i in range(5):
    action = env.action_space.say()
    obs, reward, terminated, truncated, info = env.step(action)
    print(f"Step {i+1}: reward={reward:.3f}, dist={np.linalg.norm(obs['state'][:2]):.3f}")
    if terminated or truncated:
        print("Episode ended early")
        break

env.close()
print("Environment test passed!")