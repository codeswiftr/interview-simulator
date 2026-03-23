---
title: "Embedded Linux Engineer Interview Guide: Kernel, Drivers & Real-Time Systems"
description: "Land embedded Linux roles — kernel internals, device driver development, real-time Linux (PREEMPT_RT), cross-compilation, BSP development, and debugging embedded systems."
date: "2026-03-20"
category: "Specialty Engineering Roles"
---

# Embedded Linux Engineer Interview Guide: Kernel, Drivers & Real-Time Systems

Embedded Linux roles sit at the intersection of software engineering and electrical engineering — you are expected to reason about hardware constraints, memory-mapped I/O, interrupt latency, and kernel scheduler behavior all in the same conversation. The interview process reflects this breadth. Candidates who treat it as a standard software engineering interview will struggle. Those who come prepared with deep systems knowledge and practical debugging experience will stand out immediately.

## Kernel Internals: What Interviewers Actually Ask

The Linux kernel is a large codebase, but embedded interviews focus on a specific slice: memory management, scheduling, interrupt handling, and the driver model. Expect to be asked how the kernel manages virtual memory through page tables, what happens during a page fault, and how DMA (Direct Memory Access) interacts with the CPU's cache coherency model.

Scheduling questions are common because real-time behavior depends on them. Know the difference between `SCHED_FIFO`, `SCHED_RR`, and `SCHED_OTHER`. Be able to explain what a priority inversion is and how the priority inheritance mutex (`PI mutex`) addresses it. If you are interviewing at a company building safety-critical or industrial systems, expect follow-up questions about how PREEMPT_RT patches the mainline kernel to reduce worst-case interrupt latency — specifically, how converting interrupt handlers to kernel threads and making spinlocks preemptible reduces latency spikes.

Synchronization primitives are another reliable topic. Walk through when you would use a spinlock versus a mutex in kernel context. Explain why spinlocks cannot sleep and why that matters in interrupt context. Be ready to describe how RCU (Read-Copy-Update) achieves lock-free reads for frequently-read, infrequently-written data structures.

## Device Driver Development

Character drivers, platform drivers, and the device tree are the core of most embedded Linux driver work. Interviewers will often ask you to sketch the structure of a simple character device driver — the `file_operations` struct, how `open`, `read`, `write`, and `ioctl` handlers are registered, and how `copy_to_user` / `copy_from_user` safely cross the kernel/userspace boundary.

Platform drivers and the device tree go hand in hand on modern SoCs. Know how the kernel matches a driver to a device node using the `compatible` string, how resources (IRQ numbers, memory regions) are described in the device tree and parsed with helpers like `of_iomap` and `platform_get_irq`. If you have written DTS (Device Tree Source) files before, be ready to describe the process of enabling a peripheral — clock, pinmux, interrupt configuration, and binding verification.

For interrupt-driven drivers, walk through the top-half / bottom-half model: the hardirq handler that runs with interrupts disabled should do minimal work (read status registers, acknowledge the interrupt), then defer processing to a tasklet, workqueue, or threaded IRQ handler. Interviewers probe here to see whether you understand why sleeping in interrupt context causes a kernel BUG and what alternatives exist.

ioctl design is a frequent topic for candidates with driver experience. Be prepared to discuss versioning, the `_IOW` / `_IOR` / `_IOWR` macros, and the security implications of blindly trusting userspace-provided pointers.

## Cross-Compilation, BSP Development, and Toolchains

Embedded Linux development almost always involves cross-compiling: building binaries on an x86 development machine that run on an ARM, RISC-V, or MIPS target. Interviewers expect you to be comfortable with Yocto Project or Buildroot for building complete Linux distributions, configuring the kernel with `menuconfig`, and managing sysroot and toolchain paths.

BSP (Board Support Package) development questions focus on what you add to bring up a new hardware platform: bootloader configuration (U-Boot is most common — know how it hands off to the kernel via the device tree blob), kernel port or device tree authoring, and the bringup sequence from ROM bootloader through userspace init.

Yocto-specific interviews may ask about recipes, layers, `bitbake` concepts, and how to add a custom driver or application to an image. Even if you have not used Yocto deeply, demonstrating familiarity with the layer model and how it enables reproducible embedded Linux builds is valuable.

## Debugging Embedded Systems

Embedded debugging is where practical experience shows most clearly. Walk interviewers through how you would approach a system that intermittently panics: starting with the oops message in the kernel log (`dmesg`), decoding the stack trace with `addr2line` or `gdb`, and identifying whether the crash is a NULL pointer dereference, use-after-free, or stack overflow. Mention `KASAN` (Kernel Address Sanitizer) and `lockdep` as tools for catching memory errors and locking violations in development builds.

For timing and latency analysis on real-time systems, know how to use `ftrace` and the `latency_hist` module to characterize interrupt latency distributions. `cyclictest` is the standard benchmark for measuring scheduling latency under PREEMPT_RT — be ready to explain what it measures and what "good" numbers look like for your target use case (industrial automation typically requires worst-case latency under 100 microseconds on appropriate hardware).

Hardware debugging tools matter too. JTAG debuggers (`OpenOCD` is common), logic analyzers for bus protocol verification, and oscilloscopes for electrical signal validation are standard parts of the embedded toolkit. If you have experience setting hardware breakpoints via JTAG, describing the workflow impresses interviewers who have seen too many candidates claim embedded experience without hands-on hardware debugging.

Finally, prepare for questions about production debugging constraints. In many embedded deployments, you cannot attach a debugger. Know how to instrument code with lightweight tracing (`printk` with appropriate log levels, custom trace points), how to capture and decode crash dumps, and how to design firmware that fails safely and provides useful diagnostic information when something goes wrong.
