# BC — Behaviour Cloning Navigation with ViNT

This module implements **topological map navigation** on a real LoCoBot (`ford-pinto`, locobot_wx250s) using the pretrained [ViNT](https://general-navigation-models.github.io) model, with fine-tuning on locally collected demonstration data.

The full pipeline covers:

1. Deploying the pretrained ViNT model on the robot via a custom ROS2 adapter
2. Collecting topomaps and demonstration bags in the lab
3. Processing bags and fine-tuning the model on a local Mac (Apple Silicon)
4. Evaluating pretrained vs fine-tuned navigation performance

---

## Note on Data

The `data/` folder (raw rosbags, processed trajectories, topomaps) is **not tracked in this repository** due to its large size.

---

## Folder Structure

```
BC/
├── BC_README.md                        ← this file
│
├── checkpoints/
│   ├── finetuned/
│   │   ├── vint_finetuned_best.pth     ← best checkpoint from 50-epoch fine-tuning
│   │   └── vint_finetuned_latest.pth   ← last epoch checkpoint
│   └── pretrained/                     ← (empty; pretrained weights in visualnav-transformer/)
│
├── data/
│   ├── metadata/                       ← run logs and trial records (CSV)
│   ├── processed/
│   │   └── locobot/
│   │       └── <traj_name>/
│   │           ├── 0.jpg, 1.jpg, ...   ← images sampled at 4 Hz
│   │           └── traj_data.pkl       ← {"position": np.array, "yaw": np.array}
│   ├── raw/
│   │   └── rosbags/
│   │       ├── demo_route_*/           ← ROS2 bags for fine-tuning (20 demos, 4 routes)
│   │       └── eval_route_*/           ← ROS2 bags for evaluation (8 bags, 4 routes)
│   ├── splits/
│   │   └── locobot/
│   │       ├── train/traj_names.txt    ← 16 training trajectories
│   │       ├── val/traj_names.txt      ← 4 validation trajectories
│   │       └── eval/traj_names.txt     ← 8 evaluation trajectories
│   └── topomaps/
│       ├── lab_route_01/ ... 04/       ← topomaps used during navigation testing
│       └── eval_route_01/ ... 04/      ← topomaps used for evaluation runs
│
├── docs/
│   ├── data_collection.md              ← how to record topomaps and demo bags on the robot
│   ├── lab_run_checklist.md            ← pre-run checklist for lab sessions
│   └── model_testing.md               ← how to deploy and compare pretrained vs fine-tuned
│
├── results/
│   ├── metrics/                        ← CSV trial logs (success, collision, time)
│   └── plots/
│       ├── loss_curves.png             ← train/val loss over 50 fine-tuning epochs
│       └── trajectory_map.png          ← top-down view of all collected demo trajectories
│
├── ros2_adapter/                       ← custom ROS2 package for ViNT deployment
│   ├── launch/
│   │   └── vint_nav.launch.py          ← launches vint_infer_node + pd_controller_node
│   ├── ros2_adapter/
│   │   ├── vint_infer_node.py          ← loads ViNT, samples context at 4 Hz, runs async inference, publishes /waypoint
│   │   ├── pd_controller_node.py       ← converts /waypoint to cmd_vel at 50 Hz
│   │   └── topic_config.py             ← topic name constants for ford-pinto
│   ├── package.xml
│   ├── setup.cfg
│   └── setup.py
│
├── scripts/
│   ├── create_topomap_ros2.py          ← record a topomap by driving the robot manually
│   ├── process_bags_ros2.py            ← convert ROS2 bags to ViNT training format
│   ├── finetune_vint.py                ← fine-tune pretrained ViNT on local demo data
│   └── plot_results.py                 ← generate loss curves and trajectory map plots
│
└── visualnav-transformer/              ← upstream ViNT repository (not modified)
    ├── deployment/
    │   └── model_weights/
    │       ├── vint.pth                ← pretrained ViNT checkpoint (430 MB)
    │       ├── gnm.pth
    │       └── nomad.pth
    └── train/
        ├── config/vint.yaml            ← upstream training config (reference for hyperparams)
        └── vint_train/                 ← training library used by finetune_vint.py
            ├── data/
            │   ├── vint_dataset.py     ← ViNT_Dataset class with LMDB image cache
            │   ├── data_utils.py       ← image loading, coordinate transforms
            │   └── data_config.yaml    ← dataset-specific params (added locobot entry)
            ├── models/vint/vint.py     ← ViNT model (EfficientNet + Transformer)
            └── training/train_utils.py ← loss functions (_compute_losses)
```

---

## Quick Start

### Deploy pretrained model on robot

```bash
# On robot — build adapter (once per session)
cd ~/LoCoMotive/BC/ros2_adapter
colcon build --packages-select ros2_adapter && source install/setup.bash

# Launch
ros2 launch ros2_adapter vint_nav.launch.py \
  vint_repo_root:=~/LoCoMotive/BC/visualnav-transformer \
  topomap_images_dir:=~/LoCoMotive/BC/data/topomaps/eval_route_01
```

### Deploy fine-tuned model on robot

```bash
ros2 launch ros2_adapter vint_nav.launch.py \
  vint_repo_root:=~/LoCoMotive/BC/visualnav-transformer \
  topomap_images_dir:=~/LoCoMotive/BC/data/topomaps/eval_route_01 \
  checkpoint_path:=~/LoCoMotive/BC/checkpoints/finetuned/vint_finetuned_best.pth
```

### Install Python dependencies

```bash
conda activate vint_train
pip install -r BC/requirements.txt

# Warmup LR scheduler (not on PyPI)
pip install git+https://github.com/ildoonet/pytorch-gradual-warmup-lr.git
```

### Fine-tune on new data

```bash
conda activate vint_train
cd BC/visualnav-transformer/train
python ../../scripts/finetune_vint.py --epochs 50 --lr 1e-4 --batch-size 16
```

See [docs/model_testing.md](docs/model_testing.md) and [docs/data_collection.md](docs/data_collection.md) for full procedures.

---

## References

### Papers

- **ViNT: A Foundation Model for Visual Navigation**  
  Shah et al., _CoRL 2023_  
  https://arxiv.org/abs/2306.14846

- **GNM: A General Navigation Model to Drive Any Robot**  
  Shah et al., _ICRA 2023_  
  https://arxiv.org/abs/2210.03370

- **ViNG: Learning Open-World Navigation with Visual Goals**  
  Shah et al., _ICRA 2021_ — negative mining strategy used in ViNT_Dataset  
  https://arxiv.org/abs/2012.09812

### Repositories

- **visualnav-transformer** (upstream ViNT codebase)  
  https://github.com/robodhruv/visualnav-transformer

- **Interbotix ROS2 LoCoBot**  
  https://github.com/Interbotix/interbotix_ros_rovers

- **rosbags** (ROS2 bag reading without ROS installation)  
  https://github.com/rpng/rosbags

### Hardware

- **LoCoBot WX250s** — Interbotix, Create3 mobile base  
  https://www.trossenrobotics.com/locobot-wx250s

- **Intel RealSense D435** — RGB-D camera  
  https://www.intelrealsense.com/depth-camera-d435/
