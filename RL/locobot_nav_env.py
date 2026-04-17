import gymnasium as gym
import robo_gym
import numpy as np

class LocobotNavEnv(gym.Env):
    def __init__(self, goal_pos, rs_address='127.0.0.1:50051'):
        self.base_env = gym.make(
            'EmptyEnvironmentInterbotixRRob-v0',
            rs_address=rs_address,
            gui=True,
            robot_model='locobot_wx250s',
            with_camera=False
        )

        self.goal = np.array(goal_pos[:2])
        self.goal_threshold = 0.15

        # Only control base: [linear_x, angular_z]
        self.action_space = gym.spaces.Box(
            low=np.array([-0.3, -1.0]),
            high=np.array([0.5,  1.0]),
            dtype=np.float32
        )

        # [dx_to_goal, dy_to_goal, heading, linear_vel, angular_vel]
        self.observation_space = gym.spaces.Box(
            low=-np.inf, high=np.inf, shape=(5,), dtype=np.float32
        )

    def _parse_state(self, raw_obs):
        state = raw_obs['state']
        odom = state[-7:]
        x, y = odom[0], odom[1]
        qz, qw = odom[5], odom[6]
        heading = 2 * np.arctan2(qz, qw)
        wheel_vel = state[16:18]
        linear_vel = np.mean(wheel_vel)
        angular_vel = wheel_vel[1] - wheel_vel[0]
        dx = self.goal[0] - x
        dy = self.goal[1] - y
        return np.array([dx, dy, heading, linear_vel, angular_vel], dtype=np.float32)

    def _compute_reward(self, obs, prev_dist):
        dist = np.sqrt(obs[0]**2 + obs[1]**2)
        reward = prev_dist - dist
        if dist < self.goal_threshold:
            reward += 10.0
        return reward, dist

    def reset(self, **kwargs):
        raw_obs, info = self.base_env.reset(
            options={"joint_positions": [0, 0, 0, 0, 0, 0]}
        )
        obs = self._parse_state(raw_obs)
        self.prev_dist = np.linalg.norm(obs[:2])
        return obs, info

    def step(self, action):
        # Pad arm joints with zeros
        full_action = np.array([0, 0, 0, 0, 0, 0, action[0], action[1]])
        raw_obs, _, terminated, truncated, info = self.base_env.step(full_action)
        obs = self._parse_state(raw_obs)
        reward, dist = self._compute_reward(obs, self.prev_dist)
        self.prev_dist = dist
        if dist < self.goal_threshold:
            terminated = True
        return obs, reward, terminated, truncated, info

    def close(self):
        self.base_env.close()