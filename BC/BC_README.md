# BC README

## Repository
- `visualnav-transformer`: `BC/visualnav-transformer`

## Goal
- Behavior Cloning pipeline for LoCoBot navigation.

## Plan
1. Verify robot connection and topics.
2. Run pretrained checkpoint baseline.
3. Collect navigation demonstrations.
4. Process bags and create train/val splits.
5. Fine-tune and evaluate on real robot.

## Notes
- Robot: `ford-pinto` (`locobot_wx250s`)
- Expected key topics: `/usb_cam/image_raw`, `/odom`, `/locobot/mobile_base/cmd_vel`
