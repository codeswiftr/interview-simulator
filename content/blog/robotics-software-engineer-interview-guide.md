---
title: "Robotics Software Engineer Interview Guide: ROS, Motion Planning & Autonomy"
description: "Land robotics engineering roles — ROS/ROS2 architecture, motion planning algorithms, sensor fusion, SLAM, state machines for autonomy, and real-time control systems."
date: "2026-03-20"
category: "Specialty Engineering Roles"
---

# Robotics Software Engineer Interview Guide: ROS, Motion Planning & Autonomy

Robotics software engineering sits at an uncomfortable intersection of embedded systems, applied mathematics, and distributed software. Interviewers assume you can write clean code — that is the floor, not the ceiling. What actually differentiates candidates is whether you understand why motion planning algorithms fail in practice, how sensor noise propagates through a state estimator, and what happens when a real-time control loop misses its deadline. This guide covers the technical depth those interviews demand.

## ROS and ROS2 Architecture

Most robotics roles assume ROS2 proficiency, and many teams are actively migrating legacy ROS1 systems. The architecture differences matter for interviews.

ROS2 replaced the single ROS Master with DDS (Data Distribution Service) for peer-to-peer discovery. This removes the single point of failure from ROS1 but introduces QoS (Quality of Service) policy complexity. Know the five QoS policies you will configure on production nodes: reliability (best-effort vs reliable), durability (transient local vs volatile), deadline, liveliness, and lifespan. Interviewers at autonomous vehicle and robotics companies regularly ask candidates to reason about which QoS settings to use for sensor data versus commanded velocities versus diagnostic topics — and why the wrong choice causes subtle runtime failures under load.

The node lifecycle model in ROS2 (unconfigured → inactive → active → finalized) is frequently asked in system design questions. Be prepared to explain how lifecycle nodes enable deterministic startup sequencing in complex systems where node ordering matters.

For code questions, expect to write or debug a publisher/subscriber pair, implement a service/client for synchronous request-response patterns, and reason about executor types (single-threaded, multi-threaded, static single-threaded). Understanding callback groups and re-entrant execution is a differentiator — most candidates know how to write a subscriber; fewer can explain why a default callback group will block your sensor processing if a slow service call is in flight.

## Motion Planning Algorithms

Motion planning interviews go deeper than "describe A*." You need to understand the tradeoffs between algorithm families and when each fails.

**Sampling-based planners (RRT, RRT*, PRM)** dominate high-dimensional configuration spaces. Know that RRT is probabilistically complete but not optimal; RRT* asymptotically converges to optimal but is computationally expensive. Informed RRT* and BIT* improve convergence in constrained environments. For manipulation arms, be ready to discuss how joint limits and singularities affect tree expansion in configuration space.

**Graph-based planners (Dijkstra, A*, D* Lite)** suit structured environments with explicit cost maps. The key interview question here is admissible vs consistent heuristics in A* — candidates who confuse these will get tripped up on optimality guarantees. D* Lite matters for dynamic replanning when the cost map changes during execution.

**Trajectory optimization (CHOMP, STOMP, TrajOpt)** is increasingly prominent, especially for manipulation. Be prepared to explain how CHOMP uses gradient descent on a functional defined over the trajectory, and why that leads to local minima. STOMP's stochastic approach avoids some of these issues but at higher computational cost. TrajOpt's sequential convex optimization approach handles constraints more explicitly.

For mobile robotics, know the difference between global and local planners. The common ROS2 Nav2 stack pairs a global planner (typically Smac or NavFn) with a local planner (DWB or MPPI) — interviewers at mobile robotics companies will expect you to reason about parameter tuning and failure modes for both layers.

## Sensor Fusion and SLAM

SLAM is the technical heart of autonomous navigation interviews. You should be able to derive the EKF update equations, explain why they fail for non-Gaussian noise, and describe how particle filters address that limitation.

**Extended Kalman Filter (EKF)** is the standard entry point. Know the predict-update cycle cold: propagate state through motion model, compute Jacobians for linearization, update with measurement residual weighted by Kalman gain. The critical failure mode — linearization error with highly nonlinear systems — should be something you can discuss concretely, not just name.

**Factor graphs** (as implemented in GTSAM and g2o) are the modern approach to back-end SLAM optimization. iSAM2 and its incremental Bayes tree structure comes up in senior-level interviews. If you have not worked with GTSAM directly, at minimum understand that factor graphs express SLAM as a maximum-likelihood estimation problem, and that incremental solvers amortize the cost of re-optimization as new measurements arrive.

For sensor-specific questions: LiDAR odometry (LOAM, LIO-SAM), visual odometry (ORB-SLAM3, VINS-Mono), and IMU preintegration. Know that IMU preintegration collapses the high-rate IMU measurements between keyframes into a single preintegrated factor — this is a common topic because it sits at the boundary of state estimation theory and software engineering.

## State Machines and Real-Time Control

Autonomous systems are not just perception and planning — they require reliable behavioral execution under real-time constraints. Two areas come up consistently.

**Behavior trees** have largely replaced monolithic state machines for autonomous behavior in modern robotics systems. Know the four node types: action (leaf, executes behavior), condition (leaf, checks state), sequence (succeeds if all children succeed), and selector (succeeds if any child succeeds). The advantage over FSMs is modularity and composability — interviewers will ask you to design a behavior tree for a concrete task like "robot picks up object and navigates to delivery location, handling failures at each step."

**Real-time control loops** require deterministic execution. Expect questions about priority inversion, why mutex locks can cause it, and how priority inheritance addresses it. Know the difference between hard real-time (missing a deadline causes system failure) and soft real-time (occasional misses are tolerable). In ROS2, understand how Executors interact with the underlying OS scheduler, and why you might use a dedicated real-time thread with `SCHED_FIFO` for control-critical callbacks rather than the default ROS2 executor.

## What the Interview Process Looks Like

Robotics software roles typically run four to five rounds:

**Coding** — Expect data structures and algorithms plus robotics-specific problems. Common prompts: implement A* on a grid, compute inverse kinematics for a 2-DOF arm, write a transform tree traversal. Python is acceptable for most, but C++ proficiency is often expected for roles working on embedded or real-time systems.

**System design** — Design the software architecture for a delivery robot, an industrial arm cell, or an autonomous forklift. Interviewers are evaluating whether you decompose the problem into sensible nodes/modules, reason about data flow and latency, and identify the failure modes that matter most in production.

**Domain depth** — This is the technical interview covering the areas above. Be prepared to derive, not just describe.

**Simulation and tooling** — Gazebo, Isaac Sim, or MuJoCo depending on the company. Knowing how to write a launch file, configure a URDF, and set up a simulation environment demonstrates the practical experience that separates candidates who have shipped real systems from those who have only read about them.

The robotics engineering market rewards specificity. Broad familiarity with robotics concepts is common; deep experience in one area — whether that is manipulation planning, outdoor SLAM, or real-time control — combined with solid software engineering fundamentals is rare and valuable.
