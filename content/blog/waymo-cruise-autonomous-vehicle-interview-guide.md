# Autonomous Vehicle Engineer Interview Guide 2024: Waymo, Cruise, and Self-Driving Tech

The autonomous vehicle industry has a talent problem unlike any other in software engineering. The skills required span robotics, computer vision, control theory, embedded systems, machine learning, and high-performance C++ — and companies like Waymo and Cruise need engineers who can work fluently across multiple of these disciplines while maintaining the rigor demanded by systems that can kill people if they get it wrong.

If you are interviewing at an AV company in 2024, you are not competing against web developers who learned some robotics. You are competing against PhDs, former aerospace engineers, and people who have spent years building autonomous systems in shipping robots, drones, and military platforms. The bar is exceptional, and the interview process reflects that.

This guide is written for engineers who already have relevant experience and want to understand exactly what Waymo and Cruise are looking for, how to demonstrate it, and where most candidates fall short.

---

## Engineering Environment

### Waymo

Waymo emerged from Google's self-driving car project, which means the engineering culture carries Google DNA: strong emphasis on research-grade rigor, data-driven decision making, and a long-term horizon. Waymo operates Waymo One, a commercial robotaxi service in Phoenix and San Francisco, which means engineers work on systems that handle real commercial trips daily. This is not research theater — the code you write gets deployed to vehicles carrying paying passengers.

The tech stack is deeply C++ at the core. Python is used for tooling, data processing pipelines, and ML training infrastructure. The internal codebase uses Bazel for build management and has strong continuous integration requirements. Engineers write substantial amounts of simulation infrastructure alongside production code, because testing on real roads at scale is impossible.

Waymo's technical culture values precision. Engineers are expected to understand the mathematical foundations of what they build — if you implement a Kalman filter, you should be able to derive the update equations from first principles and explain under what conditions the filter's Gaussian assumptions break down. The interview process will probe this depth.

The engineering organization is structured around functional teams: Perception, Prediction, Planning, Mapping, Simulation, and Fleet Operations. When you apply, you often apply to a specific team, and the interview loop is calibrated for that team's domain. Understanding which team you are interviewing for fundamentally changes your preparation strategy.

### Cruise

Cruise has a different character. Born as a startup and acquired by GM, it operates with more startup urgency while having automotive industry backing. Cruise was deploying driverless commercial robotaxi service in San Francisco before its operations were suspended in late 2023 following an incident — and has since undergone significant restructuring. As of 2024, Cruise is rebuilding and refocusing, which means the interview culture has shifted toward hiring engineers who can operate with less organizational certainty, move faster on proving out specific technical capabilities, and work well in a more constrained resource environment.

The tech stack at Cruise also uses C++17 and Python heavily. ROS2 is part of their infrastructure. The company has strong roots in SLAM-based localization and dense urban perception given their San Francisco deployment focus.

For candidates, the key difference between Waymo and Cruise in 2024 is scale and certainty: Waymo is a mature operational deployment with stable engineering processes; Cruise is rebuilding and offers more ambiguity alongside potentially more opportunity for engineers who want to have outsized impact.

### Shared Principles Across the Industry

Both companies, and the broader AV industry, operate under shared technical and cultural principles that will surface throughout your interviews:

**Safety is not a feature.** Engineers at AV companies are expected to internalize safety as a design constraint, not an optimization target. During interviews, when you discuss design decisions, you will be evaluated on whether you naturally reason about failure modes, degradation paths, and what happens when your component receives bad input.

**Uncertainty is first-class.** Everything in autonomous driving is probabilistic. Object detections have confidence scores. Localization estimates have uncertainty ellipses. Predictions have probability distributions over trajectories. Engineers who think in terms of binary outputs rather than distributions do not fit in this environment.

**Data and simulation drive decisions.** You cannot run field tests for every edge case. Engineers are expected to understand how to build simulation environments, generate synthetic data, and measure system performance at scale. Interview questions about how you would validate a change to the perception pipeline will require you to reason about simulation fidelity and statistical significance.

---

## Interview Process

### Waymo Process

Waymo's interview process typically consists of:

1. **Recruiter screen** (30 minutes) — fit and experience overview
2. **Technical phone screen** (45-60 minutes) — coding and domain knowledge, usually with a team member
3. **Virtual onsite** (4-5 rounds, 45 minutes each):
   - Coding round 1: Data structures and algorithms, often graph or search problems
   - Coding round 2: Domain-specific algorithmic problem (spatial queries, sensor processing, planning)
   - System design: Design a component of the AV stack or a supporting infrastructure system
   - Technical depth: Deep dive on your experience, domain expertise probing
   - Behavioral: Googleyness/culture fit, structured behavioral questions

The coding rounds are harder than standard FAANG coding rounds because they often incorporate domain context. You might be asked to implement A* search in a problem framed around route planning, or write a function to efficiently query points within a 3D bounding box.

### Cruise Process

Cruise's process in 2024 is more compressed given the company's current state:

1. **Recruiter and hiring manager screen** (30-45 minutes)
2. **Technical phone screen** (60 minutes) — heavier on domain depth than pure coding
3. **Onsite or virtual onsite** (3-4 rounds):
   - Coding round: Standard algorithms plus system-specific problem
   - System design: Domain-specific design problem
   - Technical experience deep dive: Detailed exploration of your most relevant past work
   - Behavioral/culture round

Expect more explicit conversation about the company's current situation and what you would be working on. Interviewers at Cruise are generally direct about the rebuilding period and are looking for engineers who are energized by that challenge rather than deterred.

---

## Technical Deep Dives

### Sensor Fusion: The Foundation of Everything

Autonomous vehicles rely on multiple sensor modalities because no single sensor is sufficient. LiDAR provides precise 3D point clouds but is expensive and affected by rain. Cameras provide rich texture and color information but require inference to derive depth. Radar is weather-resistant and provides reliable velocity measurements but has low angular resolution. The perception pipeline fuses these sources to build a representation of the world that is more reliable than any individual sensor.

In interviews, sensor fusion questions often come in two forms: algorithmic (how does this fusion algorithm work?) and systems design (how would you architect the fusion pipeline?).

**Kalman Filter and EKF**

The extended Kalman filter is the standard tool for fusing noisy measurements from multiple sensors over time. You should be able to explain:

- The predict step: propagate state estimate forward using motion model
- The update step: incorporate new measurement, weight by relative uncertainties
- Why the extended version is needed: AV state spaces are nonlinear (vehicle dynamics, polar-to-Cartesian coordinate conversions)
- The unscented Kalman filter as an alternative for highly nonlinear systems

A common interview question: "You have a LiDAR detection at position (x1, y1, z1) and a radar detection at (x2, y2, z2) for what appears to be the same object. How do you fuse them?"

A strong answer discusses the coordinate transforms required to put both measurements in the same frame, the covariance matrices representing each sensor's uncertainty, gating (checking whether detections are plausibly from the same object before fusing), and the actual fusion computation. A very strong answer also discusses what happens when the sensors disagree beyond the expected noise level — which might indicate a sensor failure, a rapidly moving object, or an association error.

**LiDAR Processing**

LiDAR produces a point cloud: millions of (x, y, z, intensity) points per frame. Processing this for object detection requires:

- Ground removal: Distinguishing road surface points from objects above it. RANSAC-based plane fitting is common.
- Clustering: Grouping points that likely belong to the same object. DBSCAN is a standard approach.
- Bounding box fitting: Given a cluster, estimating a tight 3D bounding box. The L-shape fitting algorithm is a classic approach for vehicles.

In modern pipelines, deep learning methods (PointNet, PointPillars, VoxelNet) have largely replaced classical clustering for primary detection, but understanding the classical methods remains important for interviews because they reveal your understanding of the underlying geometry.

**Camera-Based Detection**

Deep learning dominates camera-based perception. You should understand the object detection landscape: two-stage detectors (R-CNN family) vs. single-stage detectors (YOLO, SSD, RetinaNet), anchor-based vs. anchor-free approaches, and the transition toward transformer-based architectures (DETR, BEVFormer).

For AV interviews, depth estimation from cameras is important. Know the difference between monocular depth estimation (underdetermined without additional constraints), stereo vision (triangulation between two cameras), and the structured approaches like using camera + LiDAR for ground truth depth to train a monocular depth model.

**Multi-Object Tracking**

Detection produces a set of bounding boxes per frame. Tracking links these detections across frames to produce persistent object tracks with velocity estimates. The core algorithmic challenge is data association: which detection in frame t+1 corresponds to which track from frame t?

The Hungarian algorithm solves the assignment problem. The similarity metric it optimizes over combines spatial distance (IoU of bounding boxes or centroid distance) and appearance features. SORT (Simple Online and Realtime Tracking) and DeepSORT are important references to know.

In an interview, you might be asked to walk through how your tracking system handles:
- Occlusion: an object is temporarily hidden behind another object
- Track initiation: a new object enters the scene
- Track termination: an object leaves the scene or is no longer detectable

### Prediction: What Will Other Agents Do?

Given the current state of all detected agents (vehicles, pedestrians, cyclists), the prediction module estimates their future trajectories over a 3-8 second horizon. This is what enables planning to anticipate conflicts rather than just react.

**Occupancy Grids**

The classical approach represents future occupancy as a 2D grid where each cell contains a probability that it will be occupied at each future time step. Occupancy grids are interpretable and easy to consume downstream, but they lose the structure of individual agents.

**Trajectory Prediction**

Modern approaches predict future trajectories directly for each agent. The challenge is that futures are multimodal: a vehicle at an intersection might go straight, turn left, or turn right. Predicting a single trajectory conflates these modes.

Key approaches:
- **Constant velocity/acceleration models**: Simple physics-based baselines that work surprisingly well for short horizons on highways
- **Social force models**: Model agents as influenced by forces from nearby agents
- **LSTM/RNN-based**: Sequence models that capture temporal dependencies
- **Graph neural networks**: Model interactions between agents as a graph where message passing propagates social context
- **Diffusion models**: Most recent state-of-the-art, model the distribution over futures directly

An interview question you should be ready for: "Your prediction model works well in most conditions but consistently underperforms at 4-way stop intersections. How would you diagnose this and what approaches would you try?"

Strong answers discuss: what metrics reveal the failure, what training data you would look at (is this a data distribution issue?), whether the model architecture captures the relevant interaction context (do agents at the intersection need to communicate intent through eye contact, which isn't in your feature set?), and what ablations you would run.

### Planning: Deciding What to Do

The planning stack transforms the world representation (what exists) and prediction (what will exist) into a trajectory for the ego vehicle to execute. It operates at multiple timescales:

**Route Planning**: Given origin and destination, find a path through the road network. This is graph search over an HD map — A* or Dijkstra variants. The interesting complexity is the cost function: you want to minimize time while avoiding difficult maneuvers, and the graph is dynamic (construction, traffic).

**Behavior Planning**: Decides high-level behaviors: follow lane, change lanes, yield, merge. This is often a finite state machine or a behavior tree, though learned approaches are increasingly common. The key challenges are edge cases at the intersection of behaviors: what happens when you are changing lanes while a pedestrian steps off the curb?

**Motion Planning**: Given a target behavior, generates a smooth, dynamically feasible trajectory in continuous space. Classic approaches include polynomial trajectory generation (quintic splines), lattice planning, and RRT/RRT* variants. Waymo is known for significant work in optimization-based trajectory planning.

**Interview question**: "How would you design a planner for a roundabout? Walk me through the key challenges and your approach."

This is a behavior planning question masquerading as a system design question. Strong answers address: entry timing (gap acceptance), yielding to circulating traffic, multi-lane roundabout complexity, handling vehicles that don't follow the rules, and how you would represent the roundabout in the HD map.

### Localization and HD Maps

Self-driving vehicles need centimeter-level localization — GPS provides meter-level accuracy at best and fails in tunnels. AV companies build HD maps with lane geometry, lane markings, traffic signs, and 3D features. At runtime, the localization module matches sensor data against the HD map to estimate the vehicle's precise pose.

This is a point cloud registration problem. ICP (Iterative Closest Point) is the classical algorithm. Modern approaches use deep learning for feature extraction combined with classical registration.

Know the SLAM (Simultaneous Localization and Mapping) problem: building a map while using it to localize. Graph-based SLAM formulates this as a nonlinear least squares optimization. Factor graphs are the standard mathematical representation.

---

## System Design

### Design Problem: Perception Pipeline for a School Zone

This type of problem tests whether you can think at the system level while being precise about interfaces and failure modes.

"Design the perception pipeline for detecting and tracking children in a school zone. You have LiDAR, camera, and radar. What does the system look like, and how does it behave differently than standard pedestrian detection?"

Key dimensions of a strong answer:

**Why school zones are different**: Small stature (hard for LiDAR returns below sensor mounting height), unpredictable motion (children dart into the road), occlusion by parked vehicles, group dynamics (one child implies more children), time-of-day patterns.

**Sensor selection**: Camera is essential for appearance-based classification (child vs. adult vs. small dog). LiDAR provides the geometry. Radar confirms detections at range.

**Pipeline architecture**: Early fusion (combine raw sensor data before detection), late fusion (run detectors independently, fuse detections), or mid-level fusion (share intermediate representations). Discuss the tradeoffs.

**Special handling**: Higher recall over precision (false negatives cost more than false positives in this context), lower confidence thresholds for detection, longer time-to-occupancy predictions, tighter safety margins in the planner.

**Validation**: How do you know the system works? Simulation with synthetic children? Closed-course testing? Staged scenarios with adults? Statistical significance requirements before deployment change.

### Design Problem: Fallback and Degraded Mode Architecture

"The primary LiDAR fails mid-ride. Design the system's fallback behavior."

This tests your safety architecture thinking. Strong answers include: detecting the failure (heartbeat monitoring, sanity checks on point cloud density), triggering a managed degradation (not an emergency stop unless required), communicating uncertainty increase to the planning stack, operating in a reduced envelope (slower speed, more conservative gap acceptance, no lane changes), and orchestrating a minimal risk condition (pulling over safely).

---

## Behavioral Signals AV Companies Value

**Judgment about risk**: AV companies need engineers who make conservative decisions under uncertainty, not engineers who ship fast and learn from incidents. When discussing past projects, emphasize decisions where you chose a more robust approach over a faster one because of safety implications.

**Data-driven thinking**: Every answer about whether something works should reference how you would measure it. "We tried it and it seemed better" is not a good answer. "We ran a 10,000 scenario simulation and saw 15% reduction in hard braking events with p < 0.01" is.

**Cross-disciplinary curiosity**: The best AV engineers understand at least two disciplines deeply and have working knowledge of several others. Show that you have reached beyond your immediate specialty.

**Incident handling**: Be prepared to discuss a time a system you built failed in production and how you handled it. AV companies specifically want to see methodical incident response, no-blame post-mortems, and systemic fixes.

---

## The Specialization Question: Which Team?

Your interview experience will differ substantially based on which team you are targeting:

**Perception**: Expect deep ML questions, point cloud processing, tracking algorithms. Strong background in computer vision or robotics perception is expected.

**Prediction**: ML background with particular emphasis on sequence models and probabilistic methods. Understanding of motion planning is helpful because you need to know what your outputs feed into.

**Planning**: Control theory, optimization, formal methods are valued. Some teams lean heavily into machine learning planners; others are classical planning. Know which direction the team you are interviewing for leans.

**Mapping**: SLAM, graph optimization, large-scale data processing. Interesting intersection of robotics and distributed systems.

**Simulation**: Infrastructure engineering meets domain knowledge. Strong software architecture skills, experience with physics simulation, understanding of what makes a simulation valid.

---

## Preparation Timeline

**Six weeks out:**
- Solidify C++ fundamentals: RAII, smart pointers, templates, concurrency primitives
- Review core algorithms: Kalman filtering, ICP, A* and variants, RANSAC
- Read the Waymo and Cruise research papers from the past two years (arXiv)
- Work through one project end-to-end: implement a simple multi-object tracker from scratch

**Four weeks out:**
- Practice domain-specific coding problems: 3D geometry, spatial data structures, graph search
- Prepare system design answers for 5 AV-specific problems
- Write out detailed answers to behavioral questions using the STAR framework
- Review ISO 26262 and FMEA concepts if interviewing for safety-critical roles

**Two weeks out:**
- Mock interviews with focus on domain depth questions
- Read the specific papers cited in the job description
- Prepare specific questions about the team's current challenges and roadmap

**One week out:**
- Consolidate your "greatest hits" stories for behavioral rounds
- Confirm your mental model of the full AV stack and where your target team sits within it

---

## What Separates Candidates Who Get Offers

The engineers who receive offers at Waymo and Cruise share a few characteristics that are hard to fake:

They understand probability at a deep level and speak in distributions naturally. When asked about an algorithm, they immediately discuss its assumptions and where those assumptions break down.

They have built systems that failed and learned from those failures in specific, technical ways. Their stories about past work include the things that went wrong, not just the triumphs.

They can operate at multiple levels of abstraction in the same conversation — moving from the mathematical formulation of a filter to the systems architecture consideration of where that filter fits in the pipeline to the product question of what happens to the user experience when the filter's uncertainty is high.

They are genuinely excited about the domain. The AV problem is unsolved. The best candidates have thought deeply about the unsolved problems and have opinions about why they are hard and what approaches seem promising.

If you can demonstrate these qualities while also meeting the technical bar on algorithms and system design, you are a competitive candidate. The interview process is designed to surface exactly these qualities — so your preparation strategy should be to develop them, not just to memorize answers.
