---
title: "Autonomous Vehicles Engineer Interview Guide"
description: "Technical interview preparation for AV engineering roles: perception stacks, sensor fusion, motion planning, behavior prediction, and what Waymo, Cruise, Tesla Autopilot, and AV startups expect from software engineers."
date: "2026-03-19"
category: "Specialty Engineering Roles"
---

Autonomous vehicles are one of the most technically demanding corners of software engineering. The interview process reflects that. Companies like Waymo, Tesla, Zoox, and Aurora hire for a narrow, specific skill set — and a general software engineering background won't cut it without preparation.

This guide covers what you need to know to interview for AV engineering roles in 2026.

## The AV Landscape in 2026

The industry has matured and consolidated since the optimistic early 2020s projections.

**Waymo** (Alphabet) operates L4 robotaxi services in Phoenix, San Francisco, and Austin. It is the clearest proof-of-concept for fully driverless commercial deployment. Waymo's stack is sensor-rich: LiDAR, camera, and radar working in tight fusion. They are selective about where they deploy — geofenced cities with extensive prior mapping.

**Tesla FSD** takes a philosophically different approach: camera-only, relying on occupancy networks and end-to-end neural networks trained on fleet-scale data. Tesla argues that humans drive with eyes alone, so cameras should suffice. The debate between camera-only and sensor-rich approaches remains genuinely open among practitioners.

**Cruise** (GM) paused commercial operations in late 2023 following a pedestrian incident and has been restructuring since. The legal and reputational fallout shaped how the entire industry approaches safety communication and incident reporting.

**Zoox** (Amazon) is developing a purpose-built robotaxi with bidirectional travel and no traditional front/back orientation. **Motional** (Hyundai/Aptiv) focuses on robotaxi deployment partnerships. **Aurora** and **Plus** are attacking long-haul trucking, where the operational design domain is more constrained and the business case is clearer. **Mobileye**, **Continental**, and **Bosch** dominate the ADAS (Advanced Driver Assistance Systems) market — not full autonomy, but a large employer base for engineers with overlapping skills.

## The AV Engineering Stack

AV systems follow a pipeline: perception → prediction → planning → control, with simulation cutting across everything.

**Perception** is where raw sensor data becomes a structured understanding of the environment. The core outputs are 3D bounding boxes around other vehicles, pedestrians, and cyclists; lane geometry; drivable area segmentation; and occupancy grids that encode free vs. occupied space. Sensor fusion is the hard problem here — LiDAR gives accurate range measurements but no color or texture; cameras provide rich semantic information but require stereo or depth estimation techniques to recover 3D structure; radar handles all-weather conditions and measures Doppler velocity directly. Fusing these modalities, especially for tracking objects over time, requires Kalman filters or learned fusion architectures.

**Prediction** asks: given what I perceive now, what will the other agents do next? This is genuinely hard — pedestrian and driver behavior is context-dependent and often ambiguous. The field has moved toward learned trajectory forecasting (VectorNet, MTR) trained on large datasets like the Waymo Open Motion Dataset (WOMD). Social force models remain useful as baselines. The output is a distribution over future positions, not a single predicted path.

**Planning** has three layers. Route planning finds a path from A to B on the road graph (A* or Dijkstra over the lane graph). Behavior planning makes decisions like when to change lanes, how to handle an unprotected left turn, or when to yield to an ambulance. Motion planning generates a smooth, dynamically feasible trajectory that avoids obstacles and satisfies comfort constraints — typically framed as a constrained optimization problem.

**Control** tracks the planned trajectory. Model Predictive Control (MPC) is the industry standard for both lateral (steering) and longitudinal (throttle/brake) control because it handles constraints explicitly. PID controllers are simpler and often used for following well-defined reference signals.

**Simulation** is not optional — it is how AV teams test the long tail of rare scenarios that real-world miles can't cover in reasonable time. Waymo runs billions of simulated miles. CARLA is the main open-source simulator. Adversarial scenario generation (deliberately creating near-miss situations in sim) is an active research area.

## What Interviewers Actually Test

**Sensor physics and placement.** Know the failure modes of each modality. LiDAR struggles in heavy rain and fog. Cameras lose performance in glare and darkness. Radar has low angular resolution. Sensor placement is a systems engineering problem — coverage gaps and overlapping fields of view both matter.

**Kalman filter and EKF.** You should be able to derive the prediction and update steps from first principles. The prediction step propagates the state forward using a motion model; the update step corrects the estimate using a new measurement, weighted by relative uncertainty. The Extended Kalman Filter linearizes nonlinear systems via Jacobians. Know when EKF breaks down (highly nonlinear systems) and that particle filters exist as an alternative.

**3D object detection architectures.** Know PointPillars and CenterPoint for LiDAR-based detection. Understand anchor-free detection and why it simplified training. Camera-LiDAR fusion approaches (early fusion on point clouds, late fusion on detections, or learned joint representations) come up frequently.

**Coordinate transforms.** AV systems chain multiple coordinate frames: sensor frame → vehicle frame → world frame. You should be comfortable with homogeneous transformation matrices, rotation representations (quaternions vs. Euler angles and why quaternions avoid gimbal lock), and the pinhole camera model (intrinsic and extrinsic matrices, projection from 3D world to 2D image plane).

**Safety thinking.** ISO 26262 is the automotive functional safety standard. SOTIF (Safety Of The Intended Functionality, ISO 21448) addresses failures that occur because the system works as intended but the intended functionality is insufficient for some scenario. Interviewers at serious AV companies will probe whether you think about failure modes, not just happy paths. The disengagement rate metric (how often a human had to take over) is widely reported but insufficient on its own — it says nothing about severity of the situation that triggered disengagement.

## What Makes AV Interviews Different

The weighting is unusual compared to typical software engineering interviews:

- **C++ performance matters more than usual.** Perception and planning pipelines run in real time on embedded hardware. Memory allocation patterns, cache locality, and parallelism are practical constraints, not trivia.
- **Probability and statistics are core.** Sensor models, uncertainty propagation through Kalman filters, probabilistic occupancy grids — these are not optional background knowledge.
- **Systems failure mode reasoning.** Interviewers want to see that you think about what happens when a sensor fails, when predictions are wrong, or when the planner receives conflicting inputs.

## How to Prepare

**Implement a Kalman filter from scratch.** Track a simulated moving object through noisy measurements. Then extend it to an EKF for a nonlinear motion model. This hands-on exercise makes the theory stick.

**Install and run CARLA.** The open-source AV simulator has Python bindings and lets you spawn vehicles, control sensors, and pull data from a running simulation. Even a few hours of hands-on time gives you something concrete to discuss in interviews.

**Read the Waymo Open Dataset papers.** The WOMD challenges (motion prediction, occupancy prediction) are published with baselines. Reading the challenge papers exposes you to the current state of trajectory forecasting and the evaluation metrics the industry uses.

**Work through "Probabilistic Robotics" by Thrun, Burgard, and Fox.** The first half — covering Bayes filters, Kalman filters, and particle filters — is foundational to almost everything in the AV perception and estimation stack. It is dense but worth it.

**Study real incident reports.** The NHTSA publishes AV incident data. Reading incident reports trains you to think about how systems fail in practice, which is exactly the reasoning AV interviewers want to see.

AV engineering roles are hard to get without preparation, but the preparation is straightforward if you know what to target. The stack is deep but learnable — and most of the foundational mathematics has been stable for decades.
