# Lab Run Checklist (ford-pinto, ROS2)

## Before Leaving for Lab
- Laptop charged, SSH key/password ready.
- Team roles assigned: driver, observer/logger, safety watcher.
- Baseline CSV templates ready in `BC/results/metrics/` and `BC/data/metadata/`.

## In Lab: Pre-Run
1. Connect to the same Wi-Fi as the robot.
2. Verify robot domain:
   - `ford-pinto -> ROS_DOMAIN_ID=20`
3. Export env:
   - `export ROS_DOMAIN_ID=20`
4. Confirm topics:
   - `ros2 topic list`

## Connectivity Test
1. Run:
   - `cd BC`
   - `./scripts/01_robot_check.sh`
2. Confirm robot moves slightly and then stops.

## Adapter Run
1. Run:
   - `cd BC`
   - `./scripts/02_run_pretrained_ros2.sh`
2. Confirm no launch/build errors.

## Trial Logging (each run)
- Fill `BC/results/metrics/pretrained_baseline.csv`:
  - `trial_id,success,collision,time_sec,notes`
- Fill `BC/data/metadata/run_log.csv`:
  - run context (date, map, start/goal, lighting, operator).

## End of Session
- Stop nodes safely.
- Save logs and bag names in notes.
- Push commits the same day.
