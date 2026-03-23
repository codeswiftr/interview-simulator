---
title: "Edge AI Engineer Interview: On-Device Inference and TinyML"
description: "A technical guide to Edge AI and TinyML interviews covering quantization, pruning, deployment frameworks, and hardware targets from MCUs to mobile NPUs."
date: "2026-03-20"
category: "Specialty Role Interviews"
---

# Edge AI Engineer Interview: On-Device Inference and TinyML

Edge AI engineering sits at the intersection of machine learning, embedded systems, and hardware architecture. As inference moves from cloud servers to phones, microcontrollers, and IoT devices, specialized engineers who can shrink models to fit killobyte-scale RAM budgets while preserving accuracy have become genuinely scarce. Interviews for these roles are technically rigorous across multiple disciplines simultaneously.

## Edge AI vs Cloud AI: The Core Trade-offs

The first conceptual area interviewers probe is *why* edge deployment makes sense for a given use case. The three canonical reasons are latency, privacy, and connectivity independence.

Latency arguments are strongest for real-time applications: wake-word detection, predictive text, gesture recognition, autonomous vehicle obstacle avoidance. A round trip to a cloud API adds 50–500ms minimum; on-device inference on a mobile NPU can complete in under 5ms.

Privacy arguments apply when the raw data is sensitive: medical wearable readings, in-home audio, facial recognition for access control. Running inference locally means the raw signal never leaves the device — only the inference result does.

Connectivity independence matters for industrial IoT in RF-noisy environments, agricultural sensors in remote fields, or consumer devices that must work offline. Candidates who can map these three dimensions to concrete business scenarios demonstrate they understand the problem space, not just the techniques.

## Frameworks and Runtimes

Strong candidates know the deployment framework ecosystem in detail.

**TensorFlow Lite** remains the most widely deployed edge inference runtime. Its FlatBuffer model format enables zero-copy deserialization — critical for MCUs with no dynamic memory allocator. TFLite's delegate system allows hardware-specific acceleration: the GPU delegate uses OpenCL/Metal, the NNAPI delegate routes to Android's hardware abstraction layer.

**ONNX Runtime** is the cross-platform alternative with stronger coverage of quantized transformer models. Its execution providers (CUDA, CoreML, DirectML, TensorRT) follow the same delegate pattern. For edge deployment, the minimal build mode strips unused operators, reducing binary size from ~1.5MB to under 200KB.

**Core ML** is Apple's proprietary runtime, mandatory for efficient Neural Engine access on iPhone and Apple Watch. Core ML models are compiled to .mlmodelc packages and benefit from Apple's hardware/software co-design — quantized BERT variants run in under 10ms on A-series chips.

**NCNN** is the framework most often used in camera and embedded Linux applications. Written in C++ with no dependencies, it targets ARM NEON and Vulkan acceleration and is common in devices running stripped Linux without Android.

## Quantization and Pruning

This is the technical heart of most edge AI interviews.

**Post-training quantization (PTQ)** converts FP32 weights to INT8 or INT4 using a calibration dataset to determine scale factors. It requires no retraining but can lose 1–3% accuracy on sensitive tasks. Interviewers often ask candidates to explain how scale factors are computed — the answer involves determining the dynamic range of activations per layer during calibration and mapping that range to the integer type's representable values.

**Quantization-aware training (QAT)** inserts fake quantization nodes during training, allowing the model to learn weight distributions that survive quantization. It recovers most accuracy loss but requires access to training infrastructure and labeled data.

**Structured pruning** removes entire filters or attention heads, producing a smaller dense model compatible with standard inference runtimes. **Unstructured pruning** zeros individual weights, which requires sparse matrix support in the runtime to realize speedups — often absent on embedded hardware.

A common interview question: "You have a ResNet-50 that's too large for your target device. Walk me through your compression pipeline." The answer should sequence: structured pruning → QAT → INT8 quantization → operator fusion → runtime-specific optimization.

## Hardware Targets

Understanding the hardware hierarchy separates junior from senior candidates.

MCUs (ARM Cortex-M series) have tens of kilobytes of RAM and no OS. TensorFlow Lite Micro targets this tier with static memory allocation and a fixed arena allocator.

Mobile NPUs (Apple Neural Engine, Qualcomm Hexagon DSP, Google Tensor) are purpose-built for matrix operations. They execute quantized models at dramatically lower power than CPU or GPU. Access is always through vendor SDKs — direct NPU programming is not exposed publicly.

Edge inference accelerators (NVIDIA Jetson, Google Coral TPU, Hailo) sit between mobile and server. The Coral TPU executes only fully-quantized INT8 models compiled specifically for its architecture — interviewers often test whether candidates know this constraint.

## Sample Interview Questions

**"What is operator fusion and why does it matter?"** Fusing consecutive operations (Conv + BatchNorm + ReLU) into a single kernel eliminates intermediate memory writes and reduces memory bandwidth, which is often the binding constraint on mobile hardware.

**"How do you validate that your quantized model is production-ready?"** Beyond accuracy metrics, measure latency variance (tail latency matters for UX), power draw under sustained inference, and thermal behavior over extended operation.

**"What's the difference between dynamic and static quantization?"** Static quantization calibrates scale factors offline; dynamic quantization computes them at runtime per-batch, trading slight overhead for simpler deployment.

Candidates who have shipped an edge model to production and can discuss real accuracy/latency/power trade-offs they navigated will consistently outperform those who have only studied the techniques academically.
