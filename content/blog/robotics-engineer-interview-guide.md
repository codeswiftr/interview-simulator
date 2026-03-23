---
title: "Robotics Engineer Interview Guide"
description: "Technical interview preparation for robotics engineering roles: ROS/ROS2, perception pipelines, motion planning, control systems, and what companies like Boston Dynamics, Waymo, Tesla Bot, Amazon Robotics, and robotics startups expect."
date: "2026-03-19"
category: "Specialty Engineering Roles"
---

Robotics engineering sits at one of the more demanding intersections in software: real-time systems, probabilistic reasoning, hardware constraints, and safety requirements all in one role. If you're a software engineer pivoting into robotics, or a generalist targeting a specific company, this guide covers what the interview will actually test.

## The Landscape You're Entering

Robotics hiring is spread across distinct verticals, each with its own technical culture.

**Autonomous vehicles** — Waymo, Cruise, Motional — are mature software organizations with deep perception and planning stacks. They hire like large tech companies: strong algorithms, system design, and distributed systems experience.

**Humanoid and mobile robots** — Boston Dynamics, Figure, 1X, Agility Robotics — move fast and have hard real-time requirements. Expect questions about control theory, embedded constraints, and hardware/software co-design.

**Industrial and warehouse robotics** — Amazon Robotics, Symbotic, Locus Robotics — prioritize reliability, throughput, and fleet coordination. Systems integration and operational robustness matter more than cutting-edge algorithms.

**Manipulation and specialized robotics** — Covariant (AI-driven pick-and-place), Machina Labs (robotic metalworking) — mix deep learning with classical robotics. Expect computer vision and force control.

**Drone and aerial** — Shield AI, Skydio — emphasize state estimation, GPS-denied navigation, and low-latency control.

Know which segment you're targeting. The interview focus shifts significantly between them.

## Engineering Disciplines You'll Be Tested On

Robotics roles cluster around five areas:

**Perception** — turning sensor data into a world model. Sensor fusion (IMU + LiDAR + camera), localization, object detection, and tracking.

**Planning** — deciding what to do. Motion planning for collision-free trajectories, task planning for multi-step objectives.

**Control** — executing decisions reliably. Real-time control loops, PID, model predictive control, feedback stability.

**Simulation** — testing in software before touching hardware. Gazebo, Isaac Sim, MuJoCo. Being able to reproduce hardware behavior in sim is increasingly important.

**Systems integration** — the glue. Hardware drivers, real-time OS configuration, latency budgets, communication buses (CAN, EtherCAT).

Most roles emphasize two or three of these. Senior roles expect fluency across all of them.

## ROS and ROS2

If you don't know ROS (Robot Operating System), you need to. It's the de facto middleware for robotics development — not a full OS, but a framework providing communication infrastructure, tooling, and a vast ecosystem of libraries.

**Core ROS2 concepts to know cold:**

- **Nodes** — independent processes that do computation
- **Topics** — pub/sub channels for streaming data (sensor readings, pose estimates)
- **Services** — synchronous request/response calls
- **Actions** — long-running tasks with feedback and cancellation (move to waypoint, execute grasp)
- **TF2** — coordinate transform library; tracks relationships between reference frames over time
- **URDF** — Unified Robot Description Format; XML description of robot kinematics and geometry

**ROS2 vs ROS1:** ROS2 replaced the custom master-based discovery with DDS (Data Distribution Service) middleware, enabling real-time support, security (SROS2), and lifecycle-managed nodes. If someone asks why ROS2 was needed, the answer is production reliability — ROS1 was a research tool, ROS2 is deployable.

**When to avoid ROS2:** Hard real-time control loops (sub-millisecond cycle times) don't belong in ROS2. The DDS overhead and Python/C++ abstraction layers introduce jitter. For tight control loops, you talk directly to the hardware interface — often via EtherCAT, CAN bus, or a dedicated microcontroller — and use ROS2 only for higher-level coordination.

## Technical Interview Areas

### Perception and State Estimation

The standard question: "How would you fuse IMU and LiDAR to estimate robot pose?" Walk through an Extended Kalman Filter (EKF). Know the prediction step (propagate state using motion model), the update step (correct with sensor measurement), and why you use the Jacobian for nonlinear systems. Understand when to use a particle filter instead — high nonlinearity, multi-modal distributions.

For point cloud processing, know PCL (Point Cloud Library) or Open3D. Common tasks: downsampling (voxel grid), normal estimation, ICP (Iterative Closest Point) for scan matching.

SLAM (Simultaneous Localization and Mapping) is a common topic at AV and mobile robotics companies. Know the graph SLAM formulation — poses as nodes, constraints as edges, optimize with g2o or GTSAM. For smaller problems, particle filters (FastSLAM). Be able to explain the data association problem: how do you know that two sensor observations correspond to the same landmark?

### Motion Planning

Know the difference between configuration space (C-space, all joint angles) and workspace (Cartesian space). Most planning algorithms operate in C-space.

**Sampling-based planners:** RRT (Rapidly-exploring Random Trees) grows a tree by sampling random configurations and extending toward them. RRT* adds rewiring to converge toward optimal paths. PRM (Probabilistic Roadmap) pre-builds a graph for repeated queries in static environments.

**Graph search:** A* on a discretized grid map. Know the heuristic requirements (admissible, consistent). Dijkstra as the baseline. D* Lite for dynamic replanning.

**Trajectory optimization:** TrajOpt and CHOMP optimize trajectory smoothness and collision avoidance simultaneously. Understand the difference between planning (finding a feasible path) and trajectory optimization (refining it for dynamics and smoothness).

### Control Theory

Every robotics engineer should be able to implement a PID controller and explain its tuning:

- **Proportional** — acts on current error; too high causes oscillation
- **Integral** — eliminates steady-state error; too high causes windup
- **Derivative** — damps oscillations; sensitive to noise

Know integral windup and how to prevent it (clamping, anti-windup reset). Know discrete-time implementation — you're coding this on a real-time system with a fixed timestep.

For more advanced roles: **LQR** (Linear Quadratic Regulator) minimizes a cost function over state and control effort. **MPC** (Model Predictive Control) optimizes over a receding horizon, handles constraints explicitly — used in high-performance motion control and autonomous driving.

### Real-Time Constraints

Control loops typically run at 1 kHz (1ms cycle) for robots, up to 10 kHz for high-bandwidth haptics or precision manipulation. Know the difference between hard and soft real-time:

- **Hard real-time:** missing a deadline causes system failure (industrial robot, safety-critical control)
- **Soft real-time:** missing a deadline degrades performance but doesn't break the system

PREEMPT-RT patches the Linux kernel for near-hard real-time performance. For truly hard real-time, bare-metal microcontrollers (STM32, Teensy) or dedicated RTOSes (FreeRTOS, VxWorks) are common.

## Coding in Robotics Interviews

**C++** dominates for performance-critical code. You'll use `Eigen` for linear algebra (matrices, quaternions). Know move semantics, memory layout, and why cache efficiency matters for control loops.

**Python** is standard for ROS scripting, tooling, and prototyping. Most perception pipelines mix Python (for ML models) with C++ nodes.

**Rust** is emerging, especially in safety-critical and drone applications. Mention it if relevant, but don't lead with it.

Expect coding questions on: Kalman filter implementation, quaternion interpolation, A* on a grid, basic PID, and sometimes matrix decompositions (SVD for least-squares fitting of point clouds).

## How to Prepare

1. **Build a ROS2 project.** Set up a simulated robot in Gazebo. Implement subscriber/publisher nodes, a transform tree, and a basic controller. This alone will teach you more than reading documentation.

2. **Implement a Kalman filter from scratch.** Do it in Python, then in C++ with Eigen. Use a simulated sensor with added Gaussian noise.

3. **Read "Probabilistic Robotics" by Thrun, Burgard, and Fox.** Chapters on Kalman filters, particle filters, and SLAM are the canonical reference. You don't need to read the whole book — focus on the chapters matching your target role.

4. **Get hardware time.** A TurtleBot, a Raspberry Pi with motors, or even an RC car with a microcontroller teaches you things simulation doesn't. Hardware surprises — sensor noise, timing jitter, mechanical slop — are central to robotics engineering.

5. **Contribute to ROS community.** Fix a bug in a ROS2 package, write a driver, or post on ROS Discourse. It signals genuine engagement, not just interview prep.

Robotics interviews reward engineers who understand the whole stack — from sensor driver to task planner. The companies doing the most interesting work want people who can operate across that range and know where to apply rigor versus pragmatism.
