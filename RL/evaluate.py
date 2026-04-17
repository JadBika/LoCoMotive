from stable_baselines3 import SAC
from locobot_nav_env import LocobotNavEnv

env = LocobotNavEnv(goal_pos=[1.5, 0.0])
model = SAC.load("locobot_nav_final", env=env)

obs, _ = env.reset()
for _ in range(500):
    action, _ = model.predict(obs, deterministic=True)
    obs, reward, done, truncated, info = env.step(action)
    if done:
        print("Goal reached!")
        break