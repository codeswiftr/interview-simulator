# AMD Engineering Deep Dive: CPU Microarchitecture and GPU at Datacenter Scale

AMD has undergone a remarkable architectural renaissance over the past eight years. The Zen microarchitecture family recaptured server market share from Intel's long-dominant Xeon lineup, while the Instinct MI300X has positioned AMD as a credible alternative to NVIDIA in AI inference workloads. For systems engineers interviewing at hyperscalers, cloud providers, or AI infrastructure companies, understanding AMD's design philosophy — chiplets, cache hierarchies, ROCm, and datacenter strategy — is increasingly expected.

## Zen Architecture and the Chiplet Revolution

AMD's most important architectural decision in the Zen era was not a microarchitectural innovation — it was a manufacturing strategy. Rather than designing a monolithic die like Intel's server chips, AMD decomposed the processor into **chiplets**: small, specialized dies connected by a high-speed interconnect called **Infinity Fabric**.

A modern EPYC Genoa (Zen 4) processor packages up to 12 **Core Complex Dies (CCDs)**, each containing 8 cores with their own L2 and L3 cache, connected to a central **I/O Die (IOD)** fabricated on an older 6nm node. The CCDs use TSMC's cutting-edge 5nm process. This separation has a crucial economic advantage: smaller dies have exponentially higher yields on advanced process nodes. AMD can produce many CCDs per wafer, discard defective ones, and bin the rest — a significant cost advantage over a monolithic 800mm² die.

The L3 cache topology matters deeply for performance. Each CCD in Zen 4 has 32 MB of L3 shared across 8 cores. On a 96-core Genoa, there are 12 L3 domains totaling 384 MB. Workloads that fit entirely within a single CCD's L3 — small in-memory databases, latency-sensitive microservices — benefit from sub-10ns cache access. Workloads that spill across CCDs pay Infinity Fabric latency (~50–100ns), and workloads that span sockets pay NUMA hop latency on top of that.

## NUMA Performance and Cache Topology

NUMA (Non-Uniform Memory Access) is not new, but AMD's chiplet design makes the topology more granular than Intel's traditional 2-socket NUMA. In a single EPYC socket, there are effectively multiple NUMA nodes — one per set of CCDs sharing a memory controller on the IOD.

Here is a NUMA-aware memory allocation pattern in C that systems engineers should be able to write or at least explain in an interview:

```c
#include <numa.h>
#include <numaif.h>
#include <stddef.h>

// Allocate memory local to the NUMA node of the current thread
void* numa_local_alloc(size_t size) {
    int node = numa_node_of_cpu(sched_getcpu());
    void* ptr = numa_alloc_onnode(size, node);
    if (!ptr) {
        // Fallback: interleaved allocation across all nodes
        ptr = numa_alloc_interleaved(size);
    }
    return ptr;
}

// Pin a thread to a specific NUMA node's CPUs
void pin_thread_to_numa_node(int node) {
    struct bitmask* cpumask = numa_allocate_cpumask();
    numa_node_to_cpus(node, cpumask);
    numa_run_on_node(node);
    numa_set_preferred(node);
    numa_free_cpumask(cpumask);
}
```

The key insight: `malloc` does not guarantee local allocation. On a freshly booted system with an empty page cache, the first thread to touch a page gets it allocated on the NUMA node where it is running. If a server-side application initializes all data structures in the main thread before spawning workers across sockets, every worker will pay cross-socket latency for every memory access. This is a real production bug that appears in systems interview questions disguised as "why is my 2-socket server slower than a 1-socket server at the same core count?"

`numactl --interleave=all` is a common quick fix — it distributes pages round-robin across NUMA nodes, averaging out the latency penalty. `numactl --membind=0 --cpunodebind=0` pins both computation and memory to node 0 for latency-sensitive single-threaded workloads.

## RDNA and CDNA: Two GPU Architectures

AMD maintains two distinct GPU lineages for different markets. **RDNA** targets gaming and consumer graphics, with architectural priorities around rasterization throughput and power efficiency. **CDNA** — Compute DNA — is AMD's datacenter GPU architecture, optimized entirely for matrix arithmetic, memory bandwidth, and multi-GPU communication.

The base execution unit in both architectures is the **Compute Unit (CU)**. Each CU contains 64 stream processors (shader engines), local data share (the AMD equivalent of CUDA shared memory), and a dedicated L1 cache. Where RDNA includes rasterizers and texture units, CDNA strips these out entirely in favor of additional matrix cores and higher HBM capacity.

CDNA 3, the architecture underlying the MI300 series, introduced a major structural change: the processor is a 3D-stacked package combining CDNA GPU dies with HBM3 memory stacks and an AMD EPYC CPU die. This is the MI300A (for supercomputing) and MI300X (for inference) configuration.

## ROCm: The CUDA Alternative

**ROCm** (Radeon Open Compute) is AMD's open-source GPU compute stack. It provides the software layer equivalent to NVIDIA's CUDA toolkit: a runtime (`HIP`), math libraries (`rocBLAS`, `rocFFT`, `MIOpen`), and profiling tools (`rocprof`).

HIP — Heterogeneous-compute Interface for Portability — is syntactically close to CUDA. Most CUDA kernels can be ported with `hipify-perl`, which mechanically translates API calls:

```hip
// CUDA original
__global__ void saxpy(float a, float* x, float* y, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) y[i] = a * x[i] + y[i];
}

// HIP equivalent (syntactically identical for basic kernels)
__global__ void saxpy(float a, float* x, float* y, int n) {
    int i = hipBlockIdx_x * hipBlockDim_x + hipThreadIdx_x;
    if (i < n) y[i] = a * x[i] + y[i];
}
```

PyTorch supports ROCm as a first-class backend since PyTorch 2.0. The major practical gap has been ecosystem maturity: CUDA has a decade head start in custom kernel libraries, profiler integrations, and community knowledge. ROCm has closed this gap significantly for standard workloads — transformer training and inference using stock PyTorch — but niche libraries often have no ROCm port.

## MI300X for AI Inference

The MI300X is AMD's most important datacenter GPU for AI workloads in 2024–2026. Its defining characteristics:

- **192 GB HBM3** — more than double the H100's 80 GB, enabling larger models to fit in a single accelerator without tensor parallelism
- **5.3 TB/s HBM3 bandwidth** — compared to H100's 3.35 TB/s
- **GPU-CPU unified memory** on the MI300A variant — CPU and GPU share the same HBM pool, eliminating PCIe transfer overhead for heterogeneous workloads

For inference workloads where the bottleneck is loading model weights (memory-bandwidth-bound, not compute-bound), higher HBM bandwidth directly translates to higher token throughput. This is why the MI300X is competitive on large LLM inference benchmarks despite NVIDIA's longer software ecosystem head start.

AMD's infinity fabric connects up to 8 MI300X GPUs in a node with 896 GB/s bidirectional bandwidth per GPU — comparable to NVLink-connected H100s in a DGX H100.

## EPYC vs. Xeon: System Design Implications

The competitive dynamics between AMD EPYC and Intel Xeon matter for system design interviews at cloud providers.

EPYC's core count advantage (up to 192 cores per socket in Bergamo, 96 in Genoa) makes it favorable for:
- **Virtualization density**: more vCPUs per socket means higher VM packing ratios
- **Memory capacity**: more memory channels per socket (12 in Genoa vs. 8 in Sapphire Rapids) means higher total DRAM capacity
- **Per-core cost**: AMD's pricing has historically been more aggressive at comparable performance

Intel Xeon's advantages:
- **AMX (Advanced Matrix Extensions)**: hardware accelerated BF16/INT8 matrix math without a discrete GPU, compelling for inference at low batch sizes
- **CXL adoption**: Intel has led CXL memory expansion ecosystem development
- **ISV certifications**: some enterprise software is still only formally certified on Xeon

In practice, cloud providers run mixed fleets. AWS Graviton (ARM) has taken significant share from both, which is worth noting in any architecture discussion.

## Interview Implications for Systems Engineers

AMD-specific questions tend to cluster around three themes:

**NUMA and memory locality:** Describe how you would profile and fix a NUMA-related performance regression on a dual-socket EPYC server running a key-value store. Expected answer involves `numastat`, `perf mem`, thread-to-core pinning, and memory policy review.

**GPU selection trade-offs:** When would you recommend MI300X over H100 for an inference deployment? Expected answer: large models (70B+ parameters) where single-GPU fit matters, bandwidth-bound inference workloads, or cost-sensitive deployments where AMD's lower list price offsets software integration work.

**Chiplet and cache topology:** A customer reports that their EPYC-based database server performs well at 32 threads but degrades non-linearly at 64+ threads. What is your hypothesis? Expected answer: cross-CCD cache traffic once working sets span multiple CCDs; investigate with `perf c2c` or `AMD uProf`; consider NUMA binding.

Understanding AMD at this depth signals to interviewers that you think in terms of hardware constraints, not just software abstractions — which is exactly the signal that separates infrastructure engineers who can own systems from those who merely operate them.
