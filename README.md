# LoCoMotive: Comparing Behaviour Cloning and Reinforcement Learning for Real-World Robot Navigation

**IFT6163 — Robot Learning | Final Project**  
Byungsuk Min · Jad Bikarbass Azmi · Yanis Chikhar

---

## Overview

LoCoMotive is a comparative study of two learning-based navigation approaches deployed on a real mobile robot (LoCoBot WX250s, `ford-pinto`):

- **Behaviour Cloning (BC):** Fine-tuning the pretrained ViNT foundation model on locally collected demonstrations for topological map navigation. See [BC/BC_README.md](BC/BC_README.md) for more detail.
- **Reinforcement Learning (RL):** SAC-based navigation training on the physical robot using robo-gym. See [RL/README.md](RL/README.md) for more detail.

---

## Repository Structure

```
LoCoMotive/
├── README.md                   ← this file
├── BC/                         ← Behaviour Cloning pipeline (ViNT-based)
├── RL/                         ← Reinforcement Learning pipeline (SAC + robo-gym)
└── docs/
    └── RobotLearningProjectProposal.pdf
```

---

## Hardware & Setup

| Component     | Details                                |
| ------------- | -------------------------------------- |
| Robot         | LoCoBot WX250s (`ford-pinto`)          |
| Base          | iRobot Create3                         |
| Camera        | Intel RealSense D435                   |
| OS            | Ubuntu 22.04                           |
| ROS           | ROS2 Humble                            |
| ROS_DOMAIN_ID | 20                                     |
| Training (BC) | Google Colab, Mac (Apple Silicon, MPS) |
| Training (RL) | White PC (Docker, robo-gym)            |
