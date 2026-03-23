---
title: "Spatial Computing and XR Engineer Interview Guide"
description: "Technical interview preparation for spatial computing, AR/VR/MR engineering roles: 3D math, real-time rendering for headsets, hand tracking, SLAM, comfort/latency requirements, and what Apple, Meta, and XR startups expect."
date: "2026-03-19"
category: "Specialty Engineering Roles"
---

XR engineering sits at the intersection of computer graphics, computer vision, real-time systems, and human factors. The interview bar is high and the domain is narrow enough that shallow preparation is immediately visible. This guide covers what you need to know to pass technical screens at Meta Reality Labs, Apple's Vision Products Group, and XR-focused startups.

## The XR Platform Landscape

Know the ecosystem before you walk in. Interviewers expect you to understand where the platforms fit and where they diverge technically.

**Consumer VR:** Meta Quest is the dominant consumer VR platform. Quest 3 and Quest Pro run standalone on Snapdragon XR chipsets with no tethered PC required. Meta's entire SDK stack — Presence Platform, Hand Tracking SDK, Scene Understanding — is built on top of Android. PlayStation VR2 is Sony's tethered headset, running on custom silicon with eye tracking and haptic feedback built into the controllers.

**Spatial computing:** Apple Vision Pro runs visionOS, which Apple intentionally separates from "VR." Apps are built with RealityKit and SwiftUI. The privacy model is fundamental: apps never get direct camera access. The system handles pass-through and spatial awareness; your app gets anchors and scene understanding output, not raw sensor data.

**Enterprise AR:** Microsoft HoloLens 2 targets industrial and healthcare deployments. Magic Leap 2 is purpose-built for enterprise AR with a focus on optical waveguide displays. HTC Vive Focus is used in enterprise VR training scenarios.

**Consumer AR:** Snap Spectacles are developer-targeted AR glasses running Snap OS with a Lens Studio development environment. This segment is still maturing — expect interview questions about the hardware constraints (thermal, battery, optical) rather than deep SDK questions.

**Engines:** Unity (with XR Interaction Toolkit) and Unreal Engine (with OpenXR plugin) cover 90% of XR development. For visionOS roles, the stack is RealityKit with SwiftUI scene containers. Know which engine the team uses before your interview.

## Engineering Disciplines in XR

XR engineering is not a single role. The interview will be scoped to one of these:

- **Rendering engineer:** Stereoscopic pipelines, foveated rendering, reprojection, shader optimization for mobile GPU
- **Tracking engineer:** Sensor fusion, SLAM, hand/eye tracking algorithms
- **Interaction engineer:** Gesture recognition, gaze-dwell input, voice integration, haptics
- **Spatial mapping engineer:** Scene reconstruction, plane detection, mesh anchoring
- **Comfort engineer:** Latency analysis, VR sickness mitigation, photon pipeline profiling

## Technical Areas: What Interviews Actually Test

### 3D Math

You will be asked to derive or implement 3D math on a whiteboard or in code. The two topics that come up most:

**Quaternions.** Know why they are used instead of Euler angles: Euler angles suffer from gimbal lock — when two rotation axes align, you lose a degree of freedom. Quaternions represent rotations as a four-component unit vector (w, x, y, z) that avoids this. The key operation for XR is SLERP (Spherical Linear Interpolation): smoothly interpolating between two orientations without distortion. Implement SLERP from scratch — it comes up in both coding rounds and system design discussions around head pose prediction.

**Affine transforms.** The model-view-projection (MVP) matrix pipeline you know from 3D graphics extends to stereoscopic rendering. For VR, you render two views: one per eye. The view matrices differ by the IPD offset (interpupillary distance, typically 63–65mm). The projection matrices may also differ slightly between eyes depending on the lens geometry. Frustum culling needs to account for both eye frustums — a common interview question is how to optimize this without doing two independent culling passes.

### Stereoscopic Rendering

The rendering pipeline for VR has several stages that do not exist in flat-screen rendering:

**Lens distortion correction.** VR lenses introduce barrel distortion. The pre-warp pass applies inverse barrel distortion to the rendered image so it looks correct through the lens. Get this wrong and the image looks warped.

**Foveated rendering.** Human vision is only high-resolution in the fovea — the central 2–5 degrees of the visual field. Foveated rendering exploits this: render the center of the image at full resolution, reduce resolution at the periphery. Without eye tracking, you use Fixed Foveated Rendering (FFR), which assumes the user looks at the center. With eye tracking (Meta Quest Pro, Vision Pro), you use Dynamic Foveated Rendering (DFR), which tracks gaze and moves the high-resolution region to where the user is looking. DFR can reduce GPU load by 30–50% at equivalent perceived quality.

### Latency and Comfort

**Motion-to-photon latency** is the time from head movement to updated pixels on display. It must stay below 20ms to avoid VR sickness. Miss this and users feel nausea within minutes.

Latency sources: render time (CPU + GPU frame), display scan-out delay, display response time (LCD vs OLED; OLED is preferred for lower persistence). The render pipeline alone can consume 10–15ms on mobile hardware.

**Asynchronous TimeWarp (ATW):** When the GPU misses a frame deadline, ATW warps the last rendered frame to match the current head pose. It runs at display refresh rate in a high-priority thread that can preempt the render thread. It is not a substitute for hitting frame rate — it is a fallback.

**Asynchronous SpaceWarp (ASW):** Synthesizes an intermediate frame using motion vectors from the previous two frames. Halves the effective render rate requirement (e.g., renders at 45 Hz, displays at 90 Hz). SpaceWarp introduces artifacts on object boundaries and fails on fast-moving objects — a common interview discussion point.

### Tracking

**SLAM (Simultaneous Localization and Mapping):** Inside-out tracking means the headset determines its position in the world using only its own cameras, with no external base stations. SLAM builds a sparse map of the environment and localizes the headset within it. Visual-inertial odometry (VIO) fuses camera frames with IMU data. The IMU (accelerometer + gyroscope) provides high-frequency pose updates between camera frames; camera frames provide drift correction.

**Hand tracking:** Modern hand tracking runs a neural network on camera frames to predict 21 joint positions per hand at 30–60 Hz. MediaPipe Hands is the canonical open-source example. At Meta, hand tracking is part of Presence Platform. Expect questions about latency, occlusion handling (when hands overlap), and confidence scoring.

**Eye tracking:** Uses corneal reflection (Purkinje images) from near-infrared illuminators. The system detects the reflection pattern to infer gaze direction. Eye tracking is used for foveated rendering and gaze-based interaction.

### visionOS-Specific (Apple Roles)

For Apple, the relevant framework is RealityKit. Apps cannot access raw camera frames — all spatial understanding is mediated through the system. Scene anchors, hand anchors, and image anchors are the API surface. SwiftUI hosts 3D scenes via `RealityView`. SharePlay enables shared spatial experiences across multiple Vision Pro headsets. The privacy model is not just policy — it is enforced in hardware and kernel. Understand it before your interview.

## Meta Reality Labs Interview Specifics

Meta interviews for Reality Labs blend ML, systems, and graphics depending on the sub-team. Codec Avatars (photorealistic avatar rendering from sparse sensor input) requires ML knowledge. Presence Platform SDK roles are closer to SDK engineering. Graphics-track roles emphasize the rendering pipeline and ATW/ASW internals. Expect questions about custom ASIC tradeoffs — Meta designs its own VR chips and interviewers may ask why certain workloads benefit from dedicated silicon.

## How to Prepare

1. Build a VR app using Unity XR Interaction Toolkit or the Unreal VR template. Shipping something — even a simple scene — forces you to confront the rendering pipeline, input system, and performance constraints.
2. Implement quaternion SLERP from scratch in your language of choice. Then implement a gimbal lock demonstration using Euler angles so you can explain the problem concretely.
3. Read the Oculus developer documentation on ATW and ASW. The implementation details are public and come up directly in interviews.
4. Watch GDC talks on VR best practices. Valve's talks on VR rendering from 2015–2016 remain foundational; Meta's GDC talks cover mobile VR constraints.
5. Study John Carmack's work at Oculus. His writing and talks on mobile VR performance — latency, thermal throttling, fixed-function render pipelines — define the engineering culture at Meta Reality Labs. Understanding his reasoning on tradeoffs signals seriousness to interviewers.

XR engineering rewards engineers who understand the full stack from sensor hardware to display photons. Interviewers can tell within the first ten minutes whether a candidate has actually shipped something that runs on a headset. Build first, then prepare for the interview.
