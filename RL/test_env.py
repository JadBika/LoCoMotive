import gymnasium as gym
import robo_gym

env = gym.make(
    'EmptyEnvironmentInterbotixRRob-v0',
    rs_address='127.0.0.1:50051',
    gui=True,
    robot_model='locobot_wx250s',
    with_camera=True
)

obs, _ = env.reset()
print("State shape:", obs['state'].shape)
print("Camera shape:", obs['camera'].shape)