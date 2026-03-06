---
name: linux-kernel-crash-debug
description: 使用 crash 工具调试 Linux 内核崩溃。当用户提到 kernel crash、kernel panic、vmcore 分析、内核转储调试、crash utility、内核 oops 调试时，使用此 skill。也适用于用户询问如何分析内核崩溃转储文件、如何使用 crash 命令、如何定位内核问题根因等场景。
---

# Linux Kernel Crash Debugging

本 skill 指导如何使用 crash 工具分析 Linux 内核崩溃转储。

## 前置要求

- **crash 工具**: 需要安装 crash 调试工具
- **带调试信息的内核镜像**: 必须使用带 debug symbols 的 vmlinux
- **转储文件**: vmcore（内存转储）或运行中的系统

## 启动 Crash 会话

```bash
# 分析转储文件
crash vmlinux vmcore

# 调试运行中的系统
crash vmlinux

# 指定特定架构
crash vmlinux vmcore --machdep phys_base=0x100000
```

## 核心调试工作流

### 1. 确认 Panic 原因

启动后首先检查 PANIC 字符串：

```
crash> sys
```

输出示例：
```
PANIC: "Oops: 0002" (check log for details)
```

### 2. 查看内核日志

获取崩溃前的内核消息：

```
crash> log
```

按时间顺序输出内核环形缓冲区内容，帮助了解崩溃前发生了什么。

### 3. 分析调用栈

查看 panic 任务的调用栈：

```
crash> bt
```

常用选项：
- `bt` - 当前任务的调用栈
- `bt -a` - 所有 CPU 的调用栈
- `bt -f` - 展开每个栈帧的详细数据
- `bt -l` - 显示源文件和行号
- `bt <pid>` - 指定进程的调用栈

### 4. 切换上下文

```
# 切换到 panic 任务上下文
crash> set -p

# 切换到指定 PID
crash> set <pid>

# 切换到指定任务地址
crash> set <task_address>
```

### 5. 检查数据结构

查看结构体内容和成员：

```
# 查看结构体定义
crash> struct task_struct

# 查看特定地址的结构体
crash> struct task_struct ffff880123456000

# 只显示特定成员
crash> struct task_struct.pid ffff880123456000

# 支持成员简写
crash> struct file.f_dentry edf3f740
```

### 6. 打印内核变量

```
# 打印变量值
crash> p jiffies

# 十六进制输出
crash> px jiffies

# 十进制输出
crash> pd jiffies

# 打印数组元素
crash> p cpu_online_mask->bits[0]
```

### 7. 内存子系统分析

```
# 查看 slab 缓存信息
crash> kmem -S inode_cache

# 查看特定地址的内存信息
crash> kmem <address>

# 查看 page 结构
crash> kmem -p <address>
```

### 8. 批量任务操作

对多个任务执行同一命令：

```
# 所有进程的调用栈
crash> foreach bt

# 指定进程名
crash> foreach java bt

# 结合过滤
crash> foreach bt | grep -A5 "do_exit"
```

## 常用命令速查

| 命令 | 用途 |
|------|------|
| `sys` | 系统信息 |
| `bt` | 调用栈回溯 |
| `log` | 内核消息缓冲区 |
| `set` | 设置上下文 |
| `struct` | 结构体查看 |
| `p` / `px` / `pd` | 变量打印 |
| `kmem` | 内存分析 |
| `foreach` | 批量任务操作 |
| `task` | 任务结构信息 |
| `files` | 打开的文件 |
| `vm` | 虚拟内存信息 |
| `mount` | 挂载信息 |
| `dev` | 设备信息 |
| `net` | 网络信息 |
| `ps` | 进程列表 |
| `help` | 命令帮助 |

## 典型调试案例流程

### 案例：内核 BUG 定位

```
# 1. 查看 panic 信息
crash> sys

# 2. 查看内核日志，确认崩溃点
crash> log | tail -50

# 3. 分析调用栈
crash> bt

# 4. 如果调用栈不完整，展开详细帧
crash> bt -f

# 5. 检查相关数据结构
crash> struct <struct_name> <address>

# 6. 查找异常值（示例：查找非 1 的计数器）
crash> kmem -S <cache_name> | grep counter | grep -v "= 1"

# 7. 定位根因
crash> p <suspicious_variable>
```

### 案例：死锁分析

```
# 1. 查看所有 CPU 调用栈
crash> bt -a

# 2. 检查自旋锁持有情况
crash> foreach bt | grep -B5 "spin_lock"

# 3. 分析等待队列
crash> struct wait_queue_head <address>

# 4. 查看相关进程状态
crash> ps -m | grep UN
```

### 案例：内存问题分析

```
# 1. 查看内存使用
crash> kmem -I

# 2. 检查特定 slab
crash> kmem -S <cache_name>

# 3. 分析 page 状态
crash> kmem -p

# 4. 查看进程内存映射
crash> vm
```

## 获取帮助

```
# 列出所有命令
crash> help

# 特定命令帮助
crash> help bt
crash> help struct
crash> help kmem
```

## 注意事项

1. **必须使用匹配的 vmlinux**: vmlinux 版本必须与生成 vmcore 的内核完全匹配
2. **调试信息**: 确保 vmlinux 包含完整的 debug symbols
3. **地址验证**: 使用结构体地址前，确认地址有效性
4. **上下文切换**: 分析不同进程时，注意切换上下文
5. **日志先行**: 始终先查看 log 了解崩溃背景