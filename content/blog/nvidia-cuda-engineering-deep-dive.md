# NVIDIA Engineering Deep Dive: GPU Architecture and CUDA at AI Scale

Understanding NVIDIA's GPU architecture is not optional for engineers working on AI infrastructure, high-performance computing, or distributed training systems. Whether you are interviewing at a company deploying large language models or building real-time inference pipelines, the interviewer expects you to reason clearly about parallelism, memory hierarchies, and communication bottlenecks. This post walks through the core concepts with enough technical depth to hold that conversation confidently.

## The SM/Warp/Thread Hierarchy

NVIDIA GPUs are built around **Streaming Multiprocessors (SMs)**. An H100 SX contains 132 SMs. Each SM can run thousands of threads concurrently, but the fundamental scheduling unit is the **warp**: 32 threads that execute in lockstep on the same instruction.

When you launch a CUDA kernel, you specify a **grid** of **blocks**, and each block is assigned to one SM. Threads within a block share L1 cache and can synchronize via `__syncthreads()`. Threads across blocks cannot synchronize directly — this is a deliberate design constraint that enables massive parallelism.

The warp scheduler issues instructions every clock cycle. If all 32 threads in a warp follow the same control flow path, throughput is optimal. If threads diverge — half take a branch, half do not — the warp executes both paths serially, effectively halving throughput. This is **warp divergence**, and avoiding it is one of the first things interviewers probe when discussing GPU kernel optimization.

## Memory Hierarchy: From Registers to HBM

CUDA exposes a layered memory system, each level with different latency and bandwidth characteristics:

| Memory Level | Latency | Bandwidth | Scope |
|---|---|---|---|
| Registers | ~1 cycle | ~20 TB/s | Per thread |
| L1 / Shared Memory | ~20 cycles | ~19 TB/s | Per SM (configurable split) |
| L2 Cache | ~200 cycles | ~7 TB/s | Chip-wide |
| HBM3 (H100) | ~400 cycles | 3.35 TB/s | Global |

The key insight: getting data off HBM is the bottleneck. Kernels that repeatedly load the same data from global memory without caching it in shared memory leave performance on the table. This is exactly why **tiled matrix multiplication** exists.

## Coalesced Memory Access and the Tiled Matrix Multiply Pattern

When a warp of 32 threads reads from global memory, the hardware coalesces those reads into a single transaction if the addresses are contiguous. Non-coalesced reads — where each thread accesses a random address — result in 32 separate transactions and a ~32x bandwidth penalty.

Here is a simplified CUDA kernel illustrating tiled matrix multiplication with coalesced access:

```cuda
#define TILE_SIZE 32

__global__ void tiledMatMul(float* A, float* B, float* C,
                             int M, int N, int K) {
    __shared__ float tileA[TILE_SIZE][TILE_SIZE];
    __shared__ float tileB[TILE_SIZE][TILE_SIZE];

    int row = blockIdx.y * TILE_SIZE + threadIdx.y;
    int col = blockIdx.x * TILE_SIZE + threadIdx.x;
    float acc = 0.0f;

    for (int t = 0; t < K / TILE_SIZE; ++t) {
        // Coalesced load: consecutive threads load consecutive columns
        tileA[threadIdx.y][threadIdx.x] = A[row * K + t * TILE_SIZE + threadIdx.x];
        tileB[threadIdx.y][threadIdx.x] = B[(t * TILE_SIZE + threadIdx.y) * N + col];
        __syncthreads();

        for (int k = 0; k < TILE_SIZE; ++k)
            acc += tileA[threadIdx.y][k] * tileB[k][threadIdx.x];

        __syncthreads();
    }

    if (row < M && col < N) C[row * N + col] = acc;
}
```

The shared memory tile acts as a manually managed L1 cache. Each tile is loaded once from HBM, reused `TILE_SIZE` times in the inner loop, then discarded. This converts an O(M×N×K) HBM access pattern into an O(M×N×K / TILE_SIZE) one — a 32x reduction in global memory traffic for a 32×32 tile.

**Bank conflicts** are the shared memory equivalent of non-coalesced access. Shared memory is divided into 32 banks; simultaneous access to the same bank serializes. A classic mistake: accessing a 2D tile with a non-power-of-two leading dimension can cause all threads in a warp to hit the same bank.

## CUTLASS and Tensor Cores

Writing a performant GEMM kernel from scratch is a multi-week project. NVIDIA's **CUTLASS** library abstracts the complexity while exposing composable primitives for warp-level and thread-level MMA (Matrix Multiply-Accumulate) operations.

Tensor Cores — introduced in the Volta architecture — execute 4×4 matrix multiplications in a single cycle at the warp level. On H100, the warp-level MMA instruction `wmma::mma_sync` operates on 16×16×16 tiles in FP16 or BF16, producing FP32 accumulation. CUTLASS structures its template hierarchy to map cleanly onto this: a grid-level tiling feeds into a threadblock-level tiling, which feeds into warp-level MMA tiles.

An interviewer question you will hear: *"What is the arithmetic intensity of a matrix multiplication, and how does it change with batch size?"* Arithmetic intensity is FLOPs / bytes of memory traffic. For GEMM on M×N×K matrices, it is `2MNK / (MK + KN + MN) × element_size`. For large square matrices, this approaches `N / element_size`, meaning larger problems become more compute-bound and more efficiently use Tensor Cores.

## NVLink and NVSwitch: Multi-GPU All-Reduce

Single-GPU training of frontier models is not feasible. Distributed training requires synchronizing gradients across GPUs — the canonical operation is **all-reduce**, where each GPU contributes a gradient tensor and receives the sum across all GPUs.

PCIe all-reduce between 8 GPUs with 80 GB HBM each bottlenecks at PCIe gen 5's 128 GB/s bidirectional bandwidth. **NVLink** (900 GB/s per GPU on H100 NVLink) and **NVSwitch** (all-to-all fabric connecting up to 256 GPUs in an NVL72 rack) change the math entirely.

The ring all-reduce algorithm — used in NCCL — operates in two phases: reduce-scatter (each GPU sends chunks to neighbors, accumulating partial sums) and all-gather (each GPU broadcasts its final chunk). Total data transferred is `2 × (N-1)/N × data_size` per GPU, which approaches `2 × data_size` for large N. With NVSwitch, the topology is a complete graph, so NCCL can use a direct all-to-all pattern instead, cutting latency proportionally.

## Interview Implications

When NVIDIA topics come up in system design interviews, the questions typically fall into three clusters:

**Memory management:** Can you explain why gradient checkpointing trades compute for memory? (Answer: recompute activations during backward pass instead of storing them, reducing memory from O(layers) to O(sqrt(layers)) with recomputation cost.) Can you describe mixed precision training with loss scaling?

**Communication bottlenecks:** Given a model with 70B parameters in BF16, how much all-reduce traffic is generated per step across 1024 GPUs? (Answer: ~140 GB per parameter tensor, scaled by the ring formula above.) How does tensor parallelism differ from pipeline parallelism in terms of communication volume?

**Kernel performance:** What causes a kernel to be memory-bound versus compute-bound? How would you profile it? (Answer: use `ncu` to check arithmetic intensity against the roofline model; memory-bound kernels sit below the memory bandwidth roof, compute-bound kernels are near the FLOP roof.)

Knowing these answers at the level of hardware constraints — not just framework API calls — is what separates strong candidates from exceptional ones.
