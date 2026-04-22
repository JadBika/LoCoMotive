import gymnasium as gym
import robo_gym
import numpy as np

class LocobotNavEnv(gym.Env):
    metadata = {'render_modes': []}

    HOME_ARM = [0.0, -1.1642915, 1.57079637, 0.00460194, 0.50928164, 0.13805827]

    def __init__(self, rs_address='192.168.50.194:50051'):
        super().__init__()
        
        self.base_env = gym.make(
            'EmptyEnvironmentInterbotixRRob-v0',
            rs_address=rs_address,
            gui=True,
            robot_model='locobot_wx250s',
            with_camera=True
        ).unwrapped

        self.goal = np.array([1.5, 0.0])
        self.goal_threshold = 0.15
        self.max_steps = 100
        self.current_step = 0

        self.action_space = gym.spaces.Box(
            low=np.array([-0.3, -1.0], dtype=np.float32),
            high=np.array([0.5, 1.0], dtype=np.float32),
            dtype=np.float32
        )

        self.observation_space = gym.spaces.Dict({
            'image': gym.spaces.Box(
                low=0, high=255, shape=(120, 160, 3), dtype=np.uint8
            ),
            'state': gym.spaces.Box(
                low=-np.inf, high=np.inf, shape=(5,), dtype=np.float32
            )
        })

    def _parse_state(self, raw_obs):
        state = raw_obs['state']
        camera = raw_obs['camera']

        odom = state[16:23]
        x, y = odom[0], odom[1]
        qz, qw = odom[5], odom[6]
        heading = 2 * np.arctan2(qz, qw)
        wheel_vel = state[14:16]
        linear_vel = np.mean(wheel_vel)
        angular_vel = wheel_vel[1] - wheel_vel[0]
        dx = self.goal[0] - x
        dy = self.goal[1] - y

        nav_state = np.array([dx, dy, heading, linear_vel, angular_vel], dtype=np.float32)
        image = camera.astype(np.uint8)

        return {'image': image, 'state': nav_state}

    def _compute_reward(self, obs, prev_dist):
        dist = np.sqrt(obs['state'][0]**2 + obs['state'][1]**2)
        reward = (prev_dist - dist) * 10
        if dist < self.goal_threshold:
            reward += 100.0
        reward -= 0.01
        too_far = dist > 3.0
        return reward, dist, too_far

    def reset(self, **kwargs):
        self.current_step = 0
        raw_obs, _ = self.base_env.reset(
            options={"joint_positions": self.HOME_ARM}
        )
        # Set goal relative to starting position
        odom = raw_obs[16:23]
        self.start_x = odom[0]
        self.start_y = odom[1]
        self.goal = np.array([self.start_x + 1.5, self.start_y])

        obs = self._parse_state(raw_obs)
        self.prev_dist = np.linalg.norm(obs['state'][:2])
        return obs, {}

    def _parse_state(self, raw_obs):
        state = raw_obs['state']
        camera = raw_obs['camera']

        odom = state[16:23]
        x, y = odom[0], odom[1]
        qz, qw = odom[5], odom[6]
        heading = 2 * np.arctan2(qz, qw)
        wheel_vel = state[14:16]
        linear_vel = np.mean(wheel_vel)
        angular_vel = wheel_vel[1] - wheel_vel[0]
        dx = self.goal[0] - x
        dy = self.goal[1] - y

        nav_state = np.array([dx, dy, heading, linear_vel, angular_vel], dtype=np.float32)
        image = camera.astype(np.uint8)

        return {'image': image, 'state': nav_state}

    def step(self, action):
        self.current_step += 1
        full_action = np.array(self.HOME_ARM + [action[0], action[1]])
        raw_obs, _, terminated, truncated, _ = self.base_env.step(full_action)

        obs = self._parse_state(raw_obs)
        reward, dist, too_far = self._compute_reward(obs, self.prev_dist)
        self.prev_dist = dist

        if dist < self.goal_threshold:
            terminated = True
            print("Goal reached!")

        if too_far:
            truncated = True
            reward -= 10.0
            print("Too far, resetting...")

        if self.current_step >= self.max_steps:
            truncated = True

        return obs, reward, terminated, truncated, {}

    def close(self):
        self.base_env.close()