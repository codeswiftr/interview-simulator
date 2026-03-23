# NVIDIA Engineering Deep Dive: GPU Computing and the AI Infrastructure Bar

NVIDIA is no longer just a chip company. It is the infrastructure layer underneath modern artificial intelligence — the company that built the picks and shovels of the AI gold rush and now owns the mine. For software engineers, working at NVIDIA means operating at the intersection of hardware and software at a scale and complexity few companies can match. The interview bar reflects that: deep C++ and CUDA knowledge, systems thinking, and the ability to reason about parallelism at the hardware level.

This guide covers what makes NVIDIA engineering distinctive, what the interview process demands, and how to prepare for a role at one of the most technically demanding companies in the industry.

---

## The Transformation: From Gaming to AI Infrastructure

NVIDIA was founded in 1993 to build graphics processing units for gaming. For two decades, that was the core business. The GPU's architecture — thousands of small, parallel processing cores executing the same instruction across many data elements — turned out to be exceptionally well-suited to a completely different workload: matrix multiplication.

Modern neural networks are, at their core, enormous matrix operations. A forward pass through a transformer model involves billions of multiply-accumulate operations that can be executed in parallel across millions of examples. The GPU's architecture was accidentally the perfect fit.

The pivot accelerated with the 2012 AlexNet moment, when a CUDA-trained deep convolutional network shattered the ImageNet benchmark by a margin that rattled the entire field. NVIDIA engineers had been building CUDA since 2007, but AlexNet demonstrated that GPU-accelerated deep learning was not a research curiosity — it was a step change in capability.

By 2023, NVIDIA had become one of the most valuable companies in the world. Its H100 GPU had a waiting list measured in months. Hyperscalers were spending billions to acquire GPU clusters. NVIDIA's data center revenue surpassed its gaming revenue by a factor of four and continues to grow. The company that made graphics cards for gamers now provides the compute substrate for training GPT-4, Gemini, Claude, and every large-scale AI model in production.

For engineers, this transformation means the work has changed. NVIDIA still employs graphics engineers, but the growth headcount is in AI infrastructure: CUDA software, deep learning frameworks, networking, compiler toolchains, and the systems software that makes a cluster of ten thousand GPUs behave as a single coherent accelerator.

---

## CUDA: The Parallel Computing Platform

CUDA (Compute Unified Device Architecture) is the programming model that made GPU computing accessible to developers who did not have a background in graphics programming. Introduced in 2007, it extended C++ to allow programmers to write kernels — functions that execute across thousands of threads in parallel — and launch them on the GPU.

Understanding CUDA is non-negotiable for systems roles at NVIDIA. The thread hierarchy is the mental model everything else builds on.

**Thread hierarchy: grid, block, warp**

A CUDA kernel launch specifies a grid of thread blocks. Each block contains a configurable number of threads (up to 1024 on modern hardware). Within a block, threads share fast on-chip shared memory and can synchronize with each other using `__syncthreads()`. Across blocks, communication happens through global GPU memory (DRAM), which has much higher latency.

Below the block level is the warp — the fundamental unit of execution on NVIDIA hardware. A warp is 32 threads that execute instructions in lockstep (SIMT: Single Instruction, Multiple Threads). If threads within a warp take divergent branches, the hardware serializes the execution, executing each path sequentially with the other threads masked off. This is warp divergence, and it is one of the primary performance killers in GPU code.

A minimal CUDA kernel looks like this:

```cpp
__global__ void vector_add(const float* a, const float* b, float* c, int n) {
    int tid = blockIdx.x * blockDim.x + threadIdx.x;
    if (tid < n) {
        c[tid] = a[tid] + b[tid];
    }
}

// Host-side launch
int main() {
    int n = 1 << 20;  // 1M elements
    size_t bytes = n * sizeof(float);

    float *d_a, *d_b, *d_c;
    cudaMalloc(&d_a, bytes);
    cudaMalloc(&d_b, bytes);
    cudaMalloc(&d_c, bytes);

    // ... copy data to device ...

    int threads_per_block = 256;
    int blocks_per_grid = (n + threads_per_block - 1) / threads_per_block;

    vector_add<<<blocks_per_grid, threads_per_block>>>(d_a, d_b, d_c, n);
    cudaDeviceSynchronize();

    // ... copy result back, free memory ...
    return 0;
}
```

The `<<<grid, block>>>` syntax specifies the launch configuration. `blockIdx.x` and `threadIdx.x` are built-in variables that give each thread its position in the grid. The global thread index `tid = blockIdx.x * blockDim.x + threadIdx.x` is the standard pattern for mapping threads to data elements.

**Memory hierarchy and occupancy**

Performance-critical CUDA code obsesses over memory. The GPU has several memory spaces:

- **Global memory**: the GPU's DRAM (80 GB on H100). High capacity, ~700 GB/s bandwidth, ~400 cycle latency.
- **Shared memory**: on-chip SRAM per block (up to 228 KB on H100). ~100x faster than global memory. Used for tiles and inter-thread communication within a block.
- **Registers**: per-thread, fastest storage. Limited — 65,536 32-bit registers per SM (Streaming Multiprocessor).
- **L2 cache**: shared across all SMs, 50 MB on H100.

Efficient kernels move data from global memory into shared memory in tiles, process it, and write results back. This is the tiling pattern that underlies high-performance matrix multiplication (GEMM) and most other compute-bound kernels.

Occupancy — the ratio of active warps to the maximum warps an SM can support — is the primary metric for understanding whether a kernel is utilizing the GPU efficiently. Low occupancy often means register pressure or excessive shared memory usage is limiting how many blocks can be resident on an SM simultaneously.

---

## The Deep Learning Software Stack

CUDA is the foundation, but a hierarchy of libraries sits on top of it, each providing progressively higher-level abstractions for deep learning workloads.

**cuDNN**

The CUDA Deep Neural Network library provides hand-tuned implementations of the primitives used in neural network training and inference: convolutions, pooling, batch normalization, activation functions, attention mechanisms. PyTorch and TensorFlow both use cuDNN under the hood for their GPU-accelerated operations. Writing correct cuDNN code requires understanding tensor descriptors, filter layouts (NCHW vs. NHWC), and algorithm selection — cuDNN exposes multiple convolution algorithms (IMPLICIT_GEMM, WINOGRAD, FFT-based) that trade memory for compute depending on the input size.

**cuBLAS**

The CUDA Basic Linear Algebra Subprograms library provides optimized implementations of BLAS operations — GEMM (general matrix multiply), GEMV (matrix-vector multiply), dot products. For transformer models, nearly all compute is GEMM. cuBLAS GEMM on an H100 can reach ~2,000 TFLOPS in FP8 precision. Understanding mixed-precision training (FP16/BF16 for compute, FP32 for accumulation) is required knowledge for NVIDIA systems roles.

**TensorRT**

NVIDIA's inference optimization toolkit takes a trained model (from PyTorch, TensorFlow, or ONNX format) and compiles it into a highly optimized inference engine. TensorRT performs graph optimization (layer fusion, constant folding), selects optimal kernel implementations for the target hardware, and generates calibration data for INT8 quantization. For production deployments where latency and throughput are critical, TensorRT inference is typically 2-4x faster than the unoptimized framework baseline.

**Triton and custom kernels**

For workloads where cuDNN and cuBLAS do not provide optimal implementations — fused attention, custom activation functions, sparse operations — NVIDIA engineers write custom CUDA kernels or use OpenAI Triton (which NVIDIA has invested in) to express GPU computation at a higher level than raw CUDA while maintaining hardware efficiency.

---

## NVIDIA Networking: Mellanox, InfiniBand, and RDMA

The 2020 acquisition of Mellanox Technologies for $6.9 billion was NVIDIA's signal that GPU compute alone was insufficient. Training large models requires clusters of thousands of GPUs communicating at extreme bandwidth. Network fabric is not a bottleneck that can be papered over — it determines whether a 1,000-GPU training run achieves 90% efficiency or 40% efficiency.

**InfiniBand**

InfiniBand is a high-bandwidth, low-latency interconnect fabric used in high-performance computing. NVIDIA (via Mellanox) dominates the InfiniBand market. The current HDR InfiniBand generation provides 200 Gb/s per port; NDR provides 400 Gb/s. For AI training clusters, multi-rail InfiniBand topologies (fat-tree, dragonfly) are standard.

**RDMA**

Remote Direct Memory Access allows one machine to read from or write to another machine's memory without involving the remote CPU. RoCE (RDMA over Converged Ethernet) and InfiniBand RDMA are both used in AI training clusters. RDMA is critical for the all-reduce operations used in data-parallel training, where gradient tensors must be aggregated across all GPUs in a cluster. With RDMA, the GPU can initiate the transfer directly rather than routing through the CPU and OS network stack.

**NVLink**

For GPUs within a single node, NVLink is the GPU-to-GPU interconnect. H100 NVLink provides 900 GB/s of total bidirectional bandwidth between GPUs, compared to ~64 GB/s for PCIe Gen5 x16. In an 8-GPU DGX H100 server, NVLink allows all-reduce operations to complete with near-memory bandwidth, making intra-node communication essentially free relative to inter-node InfiniBand.

---

## The AI Data Center Stack: H100, NVSwitch, DGX

Understanding the hardware that NVIDIA's software runs on is expected for systems engineers.

The **H100 SXM5** is NVIDIA's flagship training GPU. It contains 80 billion transistors, 80 GB of HBM3 memory with 3.35 TB/s memory bandwidth, and can execute 3,958 TFLOPS in sparse FP16. The GPU has 132 Streaming Multiprocessors, each with 4th-generation Tensor Cores that execute FP8 matrix operations natively.

**NVSwitch** is NVIDIA's custom switch ASIC that provides full all-to-all NVLink connectivity within and between nodes. In a DGX H100 server, six NVSwitch chips provide a 900 GB/s full bisection bandwidth fabric connecting all eight H100 GPUs. This means any GPU can communicate with any other at full NVLink bandwidth simultaneously — a critical property for collective operations.

**DGX systems** are NVIDIA's turnkey AI compute appliances. A DGX H100 contains 8 H100 GPUs, 640 GB of total GPU memory, 2 TB of system RAM, and eight 400 Gb/s InfiniBand ports. At scale, multiple DGX systems are connected via InfiniBand into a DGX SuperPOD — NVIDIA's reference architecture for AI training infrastructure at scale.

---

## Software vs. Hardware: Role Differentiation

NVIDIA engineering roles break cleanly into several distinct tracks, each with different technical requirements.

**CUDA kernel engineer**: The deepest technical role. Requires expert-level C++ and CUDA, understanding of GPU microarchitecture (pipeline stages, memory subsystem, warp scheduler), and the ability to profile and optimize kernels using Nsight Compute. Interview will include live CUDA kernel writing, profiling interpretation, and discussion of optimization techniques (tiling, vectorized loads, warp-level primitives, tensor core utilization).

**Systems software engineer**: Compiler teams (NVCC, PTX backend), driver development, CUDA runtime, profiling tools. Requires strong C++ and systems programming, compilers background (if applying to compiler roles), and understanding of the GPU execution model.

**Deep learning frameworks**: Contributions to TensorRT, cuDNN, cuBLAS, or framework integrations (PyTorch, JAX). Requires Python and C++, deep learning knowledge, and familiarity with model optimization techniques.

**Networking / interconnect**: InfiniBand software stack, RDMA, collective communication libraries (NCCL — NVIDIA Collective Communications Library). Requires distributed systems knowledge, network programming, and understanding of MPI-style collective operations.

**Tools and infrastructure**: Build systems, CI/CD, developer tooling, internal platforms. Python is acceptable here; C++ and CUDA are not required but are valued.

---

## System Design: Distributed GPU Training for Large Language Models

A common NVIDIA system design question: design a distributed training system that can train a 70-billion parameter language model on a cluster of 1,024 H100 GPUs.

This problem requires understanding three distinct parallelism strategies.

**Data parallelism**

Each GPU holds a complete copy of the model. The training batch is sharded across GPUs — each GPU processes a different mini-batch. After the forward and backward passes, gradients are all-reduced across all GPUs so every replica ends up with identical gradients before the optimizer step. With 1,024 GPUs and NCCL over InfiniBand, a ring all-reduce for a gradient tensor of size G requires 2 * (N-1)/N * G data movement per GPU, where N is the number of GPUs.

Data parallelism alone does not work for 70B parameter models — the model itself (roughly 140 GB in BF16) does not fit on a single 80 GB GPU.

**Tensor parallelism (model parallelism)**

Individual layers are sharded across GPUs. For a transformer's attention layer, the Q, K, V projection matrices can be column-partitioned across GPUs. Each GPU computes a partial result; the results are all-reduced to produce the complete layer output. Tensor parallelism within a node uses NVLink (900 GB/s) so the communication overhead is manageable. Typical tensor parallelism degree is 8 (one per GPU in a node).

**Pipeline parallelism**

The model is partitioned into stages, each assigned to a subset of GPUs. Stage 1 processes the first N layers, stage 2 processes the next N layers, and so on. Micro-batching (splitting the batch into micro-batches that flow through the pipeline) is required to keep all stages busy. NVIDIA GPT-style 1F1B (one-forward-one-backward) scheduling minimizes the pipeline bubble to approximately 1/(number of micro-batches) of total compute time.

**Combined strategy**

For a 70B model on 1,024 GPUs: tensor parallelism degree 8 (within a node, over NVLink), pipeline parallelism degree 8 (across nodes, over InfiniBand), data parallelism degree 16 (across pipeline-parallel groups). This gives 8 * 8 * 16 = 1,024 GPUs total.

The system must also handle: checkpointing (activation recomputation to reduce memory at the cost of 30% additional compute), gradient accumulation across micro-batches, optimizer state sharding (ZeRO-1/2/3 from DeepSpeed), and fault tolerance (checkpoint frequency, elastic training for node failures).

---

## The Interview Process

NVIDIA's interview process is among the most technically rigorous in the industry.

**Screening**: A phone screen with a recruiter followed by a technical screen with a senior engineer. For systems roles, the technical screen will include coding (LeetCode medium/hard in C++) and basic parallel computing questions.

**On-site (virtual or in person)**: Four to six rounds depending on the role.

- **Coding rounds (2)**: C++ required for systems and CUDA roles. Expect pointer arithmetic, memory management, template metaprogramming, and performance-aware code. Python is acceptable only for tools/infrastructure roles.
- **CUDA/parallel programming round (1-2 for GPU roles)**: Write a CUDA kernel on the whiteboard or shared editor. Optimize it. Discuss the memory access pattern. Explain why it would or would not achieve peak throughput. Questions about warp divergence, bank conflicts in shared memory, occupancy analysis.
- **System design round (1)**: Distributed training system, inference serving infrastructure, GPU cluster scheduler, or profiling tool design. Depth of technical knowledge matters more than breadth of architectural patterns.
- **Behavioral round (1)**: NVIDIA has a hardware-first, engineering-depth culture. Questions about handling technical disagreements, contributing to long-running projects, and cross-functional collaboration with hardware teams.

**Key preparation points**: Practice writing correct C++ without a compiler. Understand the GPU execution model deeply enough to reason about performance without running profiler. Be comfortable discussing cache coherence, memory bandwidth vs. compute bound analysis, and the difference between latency hiding through warps vs. achieving high arithmetic intensity.

---

## Compensation

NVIDIA's compensation has transformed dramatically since 2023. The AI infrastructure demand has pushed top-of-market offers significantly above the historical FAANG range.

Senior software engineer (L5 equivalent): $350,000 to $500,000 total compensation. Staff/principal: $500,000 to $800,000. Director-level technical roles: $800,000 to $1.2M+.

The RSU component is substantial, and NVIDIA stock has appreciated dramatically — engineers who joined in 2020 or 2021 and held their grants have seen extraordinary wealth creation. Current packages have normalized somewhat but remain at the top of the industry distribution.

Notably, compensation for CUDA kernel engineers and GPU compiler engineers commands a premium over generalist software roles due to the scarcity of people who combine deep GPU architecture knowledge with production software engineering skills. The supply of engineers who can write production-quality CUDA kernels and reason about hardware microarchitecture is genuinely limited.

---

## Culture: Hardware-First, Engineering Depth

NVIDIA's culture has been shaped by three decades of shipping products where getting the hardware wrong means a nine-month respawn on a new tape-out. This instills a rigor and depth-over-breadth mentality that permeates the engineering organization.

Decisions that might be deferred or handled with abstractions at software companies are taken seriously at NVIDIA because the software must match the hardware's characteristics precisely. A cuDNN kernel that is 10% slower than theoretical peak is not acceptable when that kernel runs billions of times per training run. This is not a culture that accepts "good enough" in performance-critical paths.

The collaboration between hardware and software teams is unusually tight. CUDA programming models evolve in lockstep with new GPU microarchitectures. Engineers working on software for H100 had access to the hardware specifications years before tape-out and wrote software against simulation models. This requires comfort with ambiguity and iterative refinement as hardware specs change.

The competitive intensity is high, but the engineering culture is described by most employees as collaborative within teams. The external competition (AMD with ROCm, Google with TPUs, custom silicon from Amazon, Meta, and Microsoft) creates a shared sense of purpose — maintaining NVIDIA's technical lead requires constant forward motion on both hardware and software.

For engineers who want to work at the absolute frontier of computing — where the software you write directly shapes how AI systems are trained and deployed at a planetary scale — NVIDIA is unlike anywhere else.

---

## Preparing for NVIDIA

The preparation arc for NVIDIA differs from standard FAANG prep.

Start with CUDA fundamentals. The official CUDA Programming Guide is required reading. Implement matrix multiplication from scratch and optimize it progressively: naive implementation, shared memory tiling, vectorized loads, tuned block dimensions. Profile with Nsight Compute. Understand where compute is going and where it is not.

Then study the cuDNN and NCCL documentation. Understand how collective operations (all-reduce, all-gather, reduce-scatter) work algorithmically and why ring all-reduce has the bandwidth characteristics it does.

For system design, study the Megatron-LM paper (NVIDIA's framework for large model training) and the ZeRO optimizer paper. These are foundational to understanding how NVIDIA thinks about distributed training.

For coding, shift your practice from Python to C++. Solve LeetCode problems in C++. Write data structures from scratch in C++ with careful attention to memory management. Understand move semantics, RAII, and template specialization.

The investment is substantial. But NVIDIA is one of those rare companies where the engineering problems are genuinely frontier work, the compensation reflects that, and the software you write becomes infrastructure that the rest of the industry depends on.
