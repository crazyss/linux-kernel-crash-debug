# Kernel Debug Tools Guide

> **This guide provides advanced debugging methods beyond crash utility analysis.**
> These tools typically require kernel recompilation with specific config options or writing kernel modules.

## Live-System Safety Gate

Prefer offline vmcore analysis. The commands below that load modules, change
boot parameters, write debugfs/procfs controls, or enable tracing mutate a live
kernel. Do not execute them unless the user explicitly authorizes the exact host
and action and confirms a disposable lab or approved maintenance window.

For every authorized live capture: record the current setting, select the
narrowest function/object and a short duration, write output only to a protected
case directory, and define cleanup before enabling the tool. Apply cleanup in
the same session. Do not capture pathnames, buffers, credentials, or business
payloads unless they are essential and explicitly approved. An agent must not
trigger a deliberate panic or reboot.

---

## Overview

When crash utility analysis cannot pinpoint the root cause, consider these advanced debugging approaches:

| Tool | Purpose | Requires Kernel Rebuild | Suitable For |
|------|---------|------------------------|--------------|
| **KASAN** | Memory error detection | Yes (CONFIG_KASAN) | Development |
| **KFENCE** | Sampled memory error detection | Yes (CONFIG_KFENCE) | Production / fleet |
| **KCSAN** | Data-race detection | Yes (CONFIG_KCSAN) | Testing / staging |
| **Kprobes** | Dynamic function tracing | No (module only) | Lab / approved maintenance |
| **Kmemleak** | Memory leak detection | Yes (CONFIG_DEBUG_KMEMLEAK) | Development |
| **UBSAN** | Undefined behavior detection | Yes (CONFIG_UBSAN) | Development |
| **SLUB Debug** | Slab corruption detection | Yes (CONFIG_SLUB_DEBUG) | Development |
| **Lockdep** | Locking issue detection | Yes (CONFIG_LOCKDEP) | Development |

---

## 1. KASAN - Kernel Address Sanitizer

### What It Detects

- **Out-of-bounds (OOB)** memory accesses
- **Use-after-free (UAF)** errors
- **Double-free** errors
- **Use-after-return (UAR)** errors

### Kernel Configuration

```bash
# Enable KASAN in kernel config
CONFIG_KASAN=y
CONFIG_KASAN_GENERIC=y           # Generic mode (best detection)
CONFIG_KASAN_OUTLINE=y           # Outline instrumentation (smaller)
# or
CONFIG_KASAN_INLINE=y            # Inline instrumentation (faster)

# Include allocation/free stack traces
CONFIG_STACKTRACE=y
# For physical-page allocation/free stacks
CONFIG_PAGE_OWNER=y            # boot with page_owner=on
```

### Overhead

| Mode | Relative Overhead | Intended Environment | Platform |
|------|-----------------|-------------------|----------|
| Generic | High | Precise development debugging | Multiple architectures |
| Software tag-based | Moderate | Real-workload testing | arm64 only |
| Hardware tag-based | Low | In-field detection / mitigation | arm64 with MTE |

### Usage

```bash
# Verify KASAN is enabled
$ grep KASAN /boot/config-$(uname -r)

# LAB ONLY: test_kasan intentionally exercises invalid accesses. Obtain
# explicit authorization for a disposable test kernel before loading it.
$ sudo modprobe test_kasan
$ sudo modprobe -r test_kasan  # cleanup when built as an unloadable module

# Test-kernel boot parameters: report repeatedly, or panic on invalid access
kasan_multi_shot
kasan.fault=panic
```

`kasan_multi_shot` is a boot parameter, not a runtime sysctl. On current
kernels, `kasan.fault=report|panic|panic_on_write` controls report/panic
behavior independently. Tag-based modes also have mode-specific boot controls.

### Sample Report

```
BUG: KASAN: slab-out-of-bounds in kmalloc_oob_right+0x6c/0x90
Write of size 1 at addr ffff88800a8a0100 by task insmod/1234
...
Allocated by task 1234:
 kasan_save_stack+0x1b/0x40
 __kasan_kmalloc+0x7c/0x90
```

## KFENCE - Low-Overhead Sampled Memory Safety

KFENCE samples heap allocations into guarded pages and detects out-of-bounds
access, use-after-free, and invalid free. It is designed for production kernels
with near-zero overhead, but sampling means it will not observe every object.

```bash
CONFIG_KFENCE=y
# Optional: build support but leave disabled until boot time
CONFIG_KFENCE_SAMPLE_INTERVAL=0

# Milliseconds; non-zero enables sampling
kfence.sample_interval=100
# Choose report, oops, or panic behavior
kfence.fault=report
```

Use KFENCE when the bug appears only under long-running production workloads.
Use KASAN when a deterministic reproducer exists and precise coverage matters
more than overhead. Preserve the KFENCE allocation/free stacks: the faulting
instruction is the detection site, while the lifetime stacks often identify
the root cause.

## KCSAN - Data-Race Detection

KCSAN is a dynamic, watchpoint-based sampling detector for data races. A normal
report contains both racing access stacks, access sizes/types, and sometimes an
observed value transition.

```bash
CONFIG_KCSAN=y
```

An `unknown origin` report can occur when the other access was not
instrumented or came from DMA. Treat it as a strong race lead, but do not invent
a second writer. Verify the intended memory-ordering primitive and reproduce
under the same workload.

---

## 2. Kprobes - Dynamic Kernel Probes

### What It Does

Allows dynamic instrumentation of almost any kernel function without modifying source code.

### Kernel Configuration

```bash
CONFIG_KPROBES=y
CONFIG_KALLSYMS=y
CONFIG_KALLSYMS_ALL=y
```

### Usage Methods

#### Method 1: Dynamic Kprobes (No Code Required)

Kprobe output may reveal function arguments and workload activity. Use a
non-secret-bearing target first, keep the capture bounded, and prepare cleanup
before enabling the event. The placeholder below is intentionally not a
copy-paste production probe.

```bash
# LAB / approved maintenance only
$ cd /sys/kernel/debug/tracing
$ echo 'p:myprobe <target_function>' > kprobe_events
$ echo 1 > events/kprobes/myprobe/enable

# Bounded capture into an access-controlled incident directory
$ timeout 30 cat trace_pipe > /secure/case/myprobe.trace

# Cleanup even when capture fails or is interrupted
$ echo 0 > events/kprobes/myprobe/enable
$ echo '-:myprobe' > kprobe_events
```

#### Method 2: Kernel Module (More Control)

```c
#include <linux/kprobes.h>

static struct kprobe kp = {
    .symbol_name = "do_sys_open",
    .pre_handler = my_pre_handler,
    .post_handler = my_post_handler,
};

// In init: register_kprobe(&kp);
// In exit: unregister_kprobe(&kp);
```

### Kretprobe (Return Value Tracing)

```bash
# LAB / approved maintenance only; avoid return values containing sensitive data
$ echo 'r:myretprobe <target_function> retval=$retval' > kprobe_events
$ echo 1 > events/kprobes/myretprobe/enable
$ timeout 30 cat trace_pipe > /secure/case/myretprobe.trace
$ echo 0 > events/kprobes/myretprobe/enable
$ echo '-:myretprobe' > kprobe_events
```

---

## 3. Kmemleak - Memory Leak Detector

### What It Does

Scans memory for orphaned allocations (memory that was allocated but is no longer referenced).

### Kernel Configuration

```bash
CONFIG_DEBUG_KMEMLEAK=y
CONFIG_DEBUG_KMEMLEAK_EARLY_LOG_SIZE=400
```

### Usage

`scan` and `dump` alter detector control state; `clear` discards the current
findings. Preserve the output first and require explicit confirmation before
clearing it on a shared incident host.

```bash
# Trigger a memory scan
$ echo scan > /sys/kernel/debug/kmemleak

# View detected leaks
$ cat /sys/kernel/debug/kmemleak

# Destructive to diagnostic state: export results and confirm before clearing
$ echo clear > /sys/kernel/debug/kmemleak

# Dump specific address info
$ echo "dump=0xffff88800a8a0100" > /sys/kernel/debug/kmemleak
```

### Sample Report

```
unreferenced object 0xffff88800a8a0100 (size 128):
  comm "insmod", pid 1234, jiffies 4294891234 (age 52.320s)
  backtrace:
    [<ffffffff81234567>] kmalloc+0x67/0x100
    [<ffffffffa0123456>] my_module_init+0x56/0x100 [my_module]
```

---

## 4. UBSAN - Undefined Behavior Sanitizer

### What It Detects

- Integer overflows/underflows
- Invalid bit shifts
- Misaligned memory accesses
- Division by zero

### Kernel Configuration

```bash
CONFIG_UBSAN=y
CONFIG_UBSAN_TRAP=y            # Trap on undefined behavior
```

---

## 5. SLUB Debug

> **Source**: [Kernel panic 实验室 - 内核维测之 slub_debug 用法参考](https://mp.weixin.qq.com/s/Chciyg7QHsMeWF3dNwQyBg) | [Kernel panic 实验室 - Slub use after free 问题讨论](https://mp.weixin.qq.com/s/SmFNmwoz4lr6F7zBi0VQqA)

### What It Does

Detects corruption in slab allocator (kmalloc/kfree), including OOB, UAF, and leaks.

### Kernel Configuration

```bash
CONFIG_SLUB_DEBUG=y
CONFIG_DEBUG_FS=y
CONFIG_SLUB_DEBUG_ON=y   # Opens all caches with fzpu by default
```

### Boot Parameters

```bash
# Syntax: slub_debug=<flags>,<cache1>,<cache2>,...
slub_debug=<Debug-Option>,<slab name1>,<slab_name2>

# Examples
slub_debug=u,kmalloc-512,kmalloc-256  # u flag for kmalloc-512 + kmalloc-256
slub_debug=P                          # Poison all caches
slub_debug=FZPU                       # All flags for all caches
```

### The 5 Flags: f/z/p/u/t

| Flag | Effect | Use Case |
|------|--------|----------|
| **f** | Check slab values on alloc/free | Detects OOB and UAF |
| **z** | Fill redzones (left/right) with pattern | Detects OOB access |
| **p** | Fill with `POISON_FREE`/`POISON_INUSE` | Detects UAF |
| **u** | Save alloc/free call stacks | Memory leak investigation |
| **t** | Print stack at every alloc/free | High overhead, debug only |

**Common combinations**:
- `fz` — minimum OOB detection
- `fzp` — OOB + UAF
- `fzpu` — full coverage
- `u` alone — for leak investigation (lower overhead)

### Reading slub_debug Traces

```bash
# After enabling slub_debug=u,<cache> in bootargs:
cat /sys/kernel/debug/slab/kmalloc-512/alloc_traces
cat /sys/kernel/debug/slab/kmalloc-512/free_traces
# Compare to find allocs without matching frees (leaks)
```

### Limitations

> **Key insight from Herbert**: slub_debug OOB detection only triggers on **alloc or free** — you can see the slab was corrupted, but **not who corrupted it**. Unlike KASAN, it cannot pinpoint the exact "culprit" instruction.

For UAF: see `references/case-studies.md` Case 12 for the **misalignment UAF** challenge.

### When CONFIG_SLUB_DEBUG_ON is Set

This option automatically applies `DEBUG_DEFAULT_FLAGS` to all slab caches. The `kmem_cache_flags()` function then propagates the flags to every cache's `flags` field at creation time.

---

## 6. Lockdep - Lock Dependency Validator

### What It Detects

- Potential deadlocks
- Lock inversion issues
- Incorrect lock usage

### Kernel Configuration

```bash
CONFIG_LOCKDEP=y
CONFIG_LOCK_STAT=y             # Lock statistics
CONFIG_DEBUG_LOCK_ALLOC=y      # Lock allocation tracking
```

### Usage

```bash
# View lock statistics
$ cat /proc/lock_stat

# View lock dependencies
$ cat /proc/lockdep

# Destructive to diagnostic state: save /proc/lock_stat and confirm first
$ echo 0 > /proc/lock_stat
```

---

## 7. Ftrace - Kernel Tracer

### What It Does

Provides comprehensive kernel tracing capabilities.

### Kernel Configuration

```bash
CONFIG_FTRACE=y
CONFIG_FUNCTION_TRACER=y
CONFIG_FUNCTION_GRAPH_TRACER=y
CONFIG_STACK_TRACER=y
```

### Usage

Function tracing can impose substantial overhead and generate sensitive,
high-volume output. Use a narrow filter and a short approved window; restore
`current_tracer` and clear the filter immediately afterward.

```bash
# List available tracers
$ cat /sys/kernel/debug/tracing/available_tracers

# Enable function tracer
$ echo function > /sys/kernel/debug/tracing/current_tracer

# Trace specific function
$ echo do_sys_open > /sys/kernel/debug/tracing/set_ftrace_filter

# View trace
$ cat /sys/kernel/debug/tracing/trace

# Cleanup
$ echo nop > /sys/kernel/debug/tracing/current_tracer
$ echo > /sys/kernel/debug/tracing/set_ftrace_filter
```

---

## Decision Tree: Which Tool to Use?

```
Problem: Kernel crash/panic
│
├─ Have vmcore file?
│  └─ YES → Use crash utility (main skill)
│
├─ Need a live-kernel change?
│  └─ Require exact-host authorization, a bounded window, and cleanup first
│
├─ Suspect memory corruption?
│  ├─ Deterministic test reproducer → Enable KASAN
│  ├─ Production-only / rare crash → Enable KFENCE sampling
│  ├─ Memory leak suspected → Enable Kmemleak
│  └─ Slab corruption → Enable SLUB debug
│
├─ Suspect a data race?
│  └─ Enable KCSAN and preserve both access stacks
│
├─ Need to trace function calls?
│  ├─ Quick check → Dynamic Kprobes
│  └─ Detailed analysis → Ftrace
│
├─ Suspect locking issues?
│  └─ Enable Lockdep
│
└─ Undefined behavior?
   └─ Enable UBSAN
```

---

## Additional Resources

- **KASAN**: https://www.kernel.org/doc/html/latest/dev-tools/kasan.html
- **KFENCE**: https://docs.kernel.org/dev-tools/kfence.html
- **KCSAN**: https://docs.kernel.org/dev-tools/kcsan.html
- **Kprobes**: https://www.kernel.org/doc/html/latest/trace/kprobes.html
- **Kmemleak**: https://www.kernel.org/doc/html/latest/dev-tools/kmemleak.html
- **Ftrace**: https://www.kernel.org/doc/html/latest/trace/ftrace.html
- **Lockdep**: https://www.kernel.org/doc/html/latest/locking/lockdep-design.html
- **Linux Kernel Debugging Book**: https://github.com/PacktPublishing/Linux-Kernel-Debugging
