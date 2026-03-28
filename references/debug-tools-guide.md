# Kernel Debug Tools Guide

> **This guide provides advanced debugging methods beyond crash utility analysis.**
> These tools typically require kernel recompilation with specific config options or writing kernel modules.

---

## Overview

When crash utility analysis cannot pinpoint the root cause, consider these advanced debugging approaches:

| Tool | Purpose | Requires Kernel Rebuild | Suitable For |
|------|---------|------------------------|--------------|
| **KASAN** | Memory error detection | Yes (CONFIG_KASAN) | Development |
| **Kprobes** | Dynamic function tracing | No (module only) | Development/Production |
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

# Optional: Enable stack tracking
CONFIG_KASAN_STACK=y
```

### Overhead

| Mode | Memory Overhead | Performance Impact | Platform |
|------|-----------------|-------------------|----------|
| Generic | ~1/8 of RAM | ~3x slowdown | x86_64, arm64, arm |
| Software tag-based | Lower | ~1.5x slowdown | arm64 only |
| Hardware tag-based | Minimal | ~1.1x slowdown | arm64 (MTE) |

### Usage

```bash
# Verify KASAN is enabled
$ grep KASAN /boot/config-$(uname -r)

# Run KASAN tests
$ sudo modprobe test_kasan

# Enable kasan_multi_shot for multiple reports
$ echo 1 > /proc/sys/kernel/kasan_multi_shot
```

### Sample Report

```
BUG: KASAN: slab-out-of-bounds in kmalloc_oob_right+0x6c/0x90
Write of size 1 at addr ffff88800a8a0100 by task insmod/1234
...
Allocated by task 1234:
 kasan_save_stack+0x1b/0x40
 __kasan_kmalloc+0x7c/0x90
```

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

```bash
# Add a kprobe event
$ cd /sys/kernel/debug/tracing
$ echo 'p:myprobe do_sys_open dfd=%di pathname=%si flags=%dx' > kprobe_events
$ echo 1 > events/kprobes/myprobe/enable

# View trace output
$ cat trace_pipe

# Cleanup
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
# Trace function return values
$ echo 'r:myretprobe do_sys_open retval=$retval' > kprobe_events
$ echo 1 > events/kprobes/myretprobe/enable
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

```bash
# Trigger a memory scan
$ echo scan > /sys/kernel/debug/kmemleak

# View detected leaks
$ cat /sys/kernel/debug/kmemleak

# Clear all reported leaks (after fixing)
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

### What It Does

Detects corruption in slab allocator (kmalloc/kfree).

### Kernel Configuration

```bash
CONFIG_SLUB_DEBUG=y
CONFIG_SLUB_DEBUG_ON=y
```

### Boot Parameters

```bash
# Enable all SLUB debug features
slub_debug

# Enable for specific caches
slub_debug=,kmalloc-128,kmalloc-256

# Enable with poisoning
slub_debug=P
```

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

# Clear lock statistics
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

```bash
# List available tracers
$ cat /sys/kernel/debug/tracing/available_tracers

# Enable function tracer
$ echo function > /sys/kernel/debug/tracing/current_tracer

# Trace specific function
$ echo do_sys_open > /sys/kernel/debug/tracing/set_ftrace_filter

# View trace
$ cat /sys/kernel/debug/tracing/trace
```

---

## Decision Tree: Which Tool to Use?

```
Problem: Kernel crash/panic
│
├─ Have vmcore file?
│  └─ YES → Use crash utility (main skill)
│
├─ Suspect memory corruption?
│  ├─ Random crashes → Enable KASAN
│  ├─ Memory leak suspected → Enable Kmemleak
│  └─ Slab corruption → Enable SLUB debug
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
- **Kprobes**: https://www.kernel.org/doc/html/latest/trace/kprobes.html
- **Kmemleak**: https://www.kernel.org/doc/html/latest/dev-tools/kmemleak.html
- **Ftrace**: https://www.kernel.org/doc/html/latest/trace/ftrace.html
- **Lockdep**: https://www.kernel.org/doc/html/latest/locking/lockdep-design.html
- **Linux Kernel Debugging Book**: https://github.com/PacktPublishing/Linux-Kernel-Debugging