---
name: linux-kernel-crash-debug
description: 使用 crash 工具调试 Linux 内核崩溃。当用户提到 kernel crash、kernel panic、vmcore 分析、内核转储调试、crash utility、内核 oops 调试时，使用此 skill。也适用于用户询问如何分析内核崩溃转储文件、如何使用 crash 命令、如何定位内核问题根因等场景。
---

# Linux Kernel Crash Debugging

本 skill 基于 [crash utility 白皮书](https://crash-utility.github.io/crash_whitepaper.html)，指导如何使用 crash 工具分析 Linux 内核崩溃转储。

## 核心概念

Crash utility 合并了 SVR4 UNIX crash 命令与 GNU gdb 调试器，提供：
- **内核感知能力**: 理解内核数据结构和内存布局
- **源码级调试**: 结合 gdb 的符号调试能力
- **多格式支持**: Kdump、Netdump、Diskdump、Xen、KVM、s390 等
- **向后兼容**: 支持 Linux 2.2.5 以来的所有版本

## 前置要求

### 1. 内核对象文件 (vmlinux)

必须使用带 `-g` 编译标志的内核：

| 系统 | 获取方式 |
|------|----------|
| RHEL3 | debuginfo 分离，需安装 kernel-debuginfo 包 |
| RHEL4/5/6+ | vmlinux 位于 kernel-debuginfo 包中 |
| 自编译内核 | 确保 CONFIG_DEBUG_INFO=y |

如果 vmlinux 无调试信息，可使用 `-S` 指定 System.map：
```bash
crash -S vmlinux.dbg vmcore
```

### 2. 内存镜像

- **转储文件**: vmcore (kdump)、netdump、diskdump 等
- **活系统**: `/dev/mem` 或 `/dev/crash`

### 3. 支持的架构

x86, x86_64, ia64, ppc64, arm, arm64, s390, s390x

## 安装

### RPM 安装
```bash
# RHEL/CentOS/Fedora
rpm -ivh crash-<version>.rpm

# 或使用 yum/dnf
yum install crash
```

### 源码编译
```bash
tar xvzmf crash-<version>.tar.gz
cd crash-<version>
make
make install
```

## 启动 Crash 会话

```bash
# 分析转储文件（两个参数：namelist + dumpfile）
crash vmlinux vmcore

# 调试运行中的系统
crash vmlinux
crash  # 自动搜索 vmlinux

# 指定架构参数
crash vmlinux vmcore --machdep phys_base=0x100000
```

### 常见启动错误

```
crash: vmlinux and vmcore do not match!
# 解决：确保 vmlinux 版本与转储内核完全匹配

crash: cannot find booted kernel -- please enter namelist argument
# 解决：明确指定 vmlinux 路径
```

## 会话控制

### 输入控制

```
crash> h          # 查看历史命令
crash> r          # 重运行最后命令（或 !!）
crash> < input    # 从文件读取命令
```

配置文件：`.crashrc`（位于 $HOME 或当前目录）

### 输出控制

```
crash> set scroll on   # 分页输出（默认）
crash> set scroll off  # 禁用分页
crash> sf              # scroll off 别名
crash> sn              # scroll on 别名

# 重定向输出
crash> ps >> process.data
crash> foreach bt > bt.all

# 进制切换
crash> set radix 16    # 十六进制
crash> hex             # 同上
crash> set radix 10    # 十进制
crash> dec             # 同上
```

## 上下文管理

Crash 会话有一个"当前上下文"：
- **转储文件**: 默认为 panic 时的任务
- **活系统**: 默认为 crash 任务本身

```
# 查看当前上下文
crash> set

# 切换上下文
crash> set <pid>          # 按 PID
crash> set <task_addr>    # 按任务地址
crash> set -p             # 恢复到 panic 任务
```

**上下文敏感命令**：`bt`, `files`, `vm`, `sig`, `net`, `task`, `vtop`
这些命令若未指定参数，作用于当前上下文。

## 核心调试工作流

### Step 1: 确认 Panic 原因

```
crash> sys
```

输出示例：
```
PANIC: "kernel BUG at pipe.c:120!"
```

### Step 2: 查看内核日志

```
crash> log
```

按时间顺序输出内核环形缓冲区，获取崩溃前的系统消息。

### Step 3: 分析调用栈

`bt` 是最有用的 crash 命令：

```
crash> bt              # 当前任务调用栈
crash> bt -a           # 所有 CPU 调用栈
crash> bt -f           # 展开每个栈帧的详细数据
crash> bt -l           # 显示源文件和行号
crash> bt -t           # 显示所有线程栈
crash> bt <pid>        # 指定进程
```

### Step 4: 检查数据结构

```
# 查看结构体定义
crash> struct task_struct

# 查看特定地址的结构体
crash> struct task_struct ffff880123456000

# 只显示特定成员
crash> struct task_struct.pid ffff880123456000

# 成员简写（推荐）
crash> struct file.f_dentry edf3f740
```

### Step 5: 打印内核变量

```
crash> p jiffies        # 默认进制
crash> px jiffies       # 强制十六进制
crash> pd jiffies       # 强制十进制

# 复杂表达式
crash> p cpu_online_mask->bits[0]
crash> p/x current->pid  # 十六进制输出
```

### Step 6: 内存分析

```
# 查看 slab 缓存
crash> kmem -S inode_cache

# 查看特定地址内存信息
crash> kmem <address>

# 查看 page 结构
crash> kmem -p <address>

# 内存统计
crash> kmem -I
```

### Step 7: 批量操作

```
# 所有进程调用栈
crash> foreach bt

# 指定进程名
crash> foreach java bt

# 结合过滤
crash> foreach bt | grep -A5 "do_exit"
```

## 完整命令分类

### 符号显示

| 命令 | 用途 |
|------|------|
| `struct` | 显示内核数据结构 |
| `union` | 显示联合体 |
| `*` | 指针命令，自动判断 struct/union |
| `p` | 打印变量（传递给 gdb） |
| `whatis` | 显示符号表信息 |
| `sym` | 符号与地址转换 |
| `dis` | 反汇编内核文本 |

### 系统状态

| 命令 | 用途 |
|------|------|
| `bt` | 内核栈回溯（最重要） |
| `dev` | 设备、端口、PCI 数据 |
| `files` | 任务打开的文件描述符 |
| `fuser` | 引用指定文件的任务 |
| `irq` | 中断请求数据 |
| `kmem` | 内存子系统状态 |
| `log` | 内核消息缓冲区 |
| `mach` | 机器/处理器特定数据 |
| `mod` | 加载的内核模块 |
| `mount` | 挂载的文件系统 |
| `net` | 网络设备、ARP、套接字 |
| `ps` | 进程状态 |
| `pte` | 页表项翻译 |
| `runq` | 运行队列任务 |
| `sig` | 信号信息 |
| `swap` | 交换设备数据 |
| `sys` | 系统信息 (uname, uptime 等) |
| `task` | task_struct 内容 |
| `timer` | 定时器队列 |
| `vm` | 虚拟内存数据 |
| `vtop` | 虚拟地址到物理地址翻译 |
| `waitq` | 等待队列任务 |

### 实用功能

| 命令 | 用途 |
|------|------|
| `ascii` | 十六进制转 ASCII |
| `btop` | 字节值转页号 |
| `eval` | 计算器 |
| `list` | 遍历链表条目 |
| `ptob` | 页框号转字节值 |
| `ptov` | 物理地址转内核虚拟地址 |
| `search` | 搜索内存值 |
| `rd` | 读取内存 |
| `wr` | 修改活系统内存（谨慎使用） |

### 会话控制

| 命令 | 用途 |
|------|------|
| `alias` | 创建命令别名 |
| `exit` / `q` | 退出会话 |
| `extend` | 动态加载扩展模块 |
| `foreach` | 对一组任务执行命令 |
| `gdb` | 直接传递参数给 gdb |
| `repeat` | 重复执行命令（活系统） |
| `set` | 设置上下文或内部变量 |

## 高级技巧：链式查询

当分析复杂问题时，需要链式追踪数据结构：

```
# 案例：从 file 指针追踪到 inode 的信号量

# 1. 从栈帧获取 file 指针
crash> bt -f
# ... 找到 file 指针地址，如 edf3f740

# 2. 链式查询
crash> struct file.f_dentry edf3f740
  f_dentry = edf3f800

crash> struct dentry.d_inode edf3f800
  d_inode = edf3f900

crash> struct inode.i_sem edf3f900
  i_sem = {
    count = {
      counter = 2    # 异常！信号量 counter 应 <= 1
    }
    ...
  }
```

### 批量检查 Slab 对象

```
# 生成所有 inode 地址列表
crash> kmem -S inode_cache

# 批量检查特定成员（使用输入文件）
crash> kmem -S inode_cache > /tmp/inodes.txt
crash> !cat /tmp/inodes.txt | while read addr rest; do \
        echo "inode.i_sem $addr"; done > /tmp/check.txt
crash> < /tmp/check.txt | grep counter | grep -v "= 1"
```

## 典型调试案例

### 案例 1: kernel BUG 定位

**症状**: `PANIC: "kernel BUG at pipe.c:120!"`

```
# 1. 查看 panic 信息
crash> sys

# 2. 查看内核日志
crash> log | tail -50

# 3. 分析调用栈
crash> bt

# 4. 确认函数参数类型
crash> whatis pipe_read

# 5. 展开栈帧获取参数
crash> bt -f

# 6. 链式追踪数据结构
crash> struct file.f_dentry <addr>
crash> struct dentry.d_inode <addr>
crash> struct inode.i_sem <addr>

# 7. 批量检查异常值
crash> kmem -S inode_cache | grep counter | grep -v "= 1"
```

### 案例 2: 死锁分析

```
# 1. 查看所有 CPU 调用栈
crash> bt -a

# 2. 检查自旋锁持有情况
crash> foreach bt | grep -B5 "spin_lock"

# 3. 分析等待队列
crash> struct wait_queue_head <address>

# 4. 查看 UN 状态进程
crash> ps -m | grep UN
```

### 案例 3: 内存问题

```
# 1. 查看内存统计
crash> kmem -I

# 2. 检查特定 slab
crash> kmem -S <cache_name>

# 3. 分析 page 状态
crash> kmem -p

# 4. 查看进程内存映射
crash> vm

# 5. 搜索内存特征
crash> search -s <pattern>
```

## 命令扩展

Crash 支持动态加载扩展模块：

```
# 加载扩展模块
crash> extend /path/to/module.so

# 查看已加载扩展
crash> extend -l
```

扩展资源：
- [crash extension modules](https://crash-utility.github.io/extensions.html)
- [EPPIC scripts](https://crash-utility.github.io/eppic.html)
- [Python scripts](https://crash-utility.github.io/python.html)

## 帮助系统

```
crash> help           # 列出所有命令
crash> help <cmd>     # 特定命令帮助
crash> help input     # 输入帮助
crash> help output    # 输出帮助
```

## 注意事项

1. **版本匹配**: vmlinux 必须与 vmcore 的内核版本完全匹配
2. **调试信息**: 必须使用带 `-g` 编译的 vmlinux
3. **地址验证**: 使用地址前确认其有效性
4. **上下文意识**: 注意当前上下文对命令的影响
5. **活系统修改**: `wr` 命令会修改运行中的内核，极其危险
6. **资源**: [crash-utility.github.io](https://crash-utility.github.io/)