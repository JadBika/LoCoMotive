from nav_env import LocobotNavEnv
import numpy as np

env = LocobotNavEnv()
obs, _ = env.reset()
print("Initial obs:", obs)
print("Distance to goal:", np.linalg.norm(obs[:2]))

# Take a few random steps
for i in range(5):
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    print(f"Step {i+1}: reward={reward:.3f}, dist={np.linalg.norm(obs[:2]):.3f}")

env.close()
print("Environment test passed!")