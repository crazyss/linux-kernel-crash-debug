# Linux Kernel Crash Debug Skill

A Claude Code skill for debugging Linux kernel crashes using the crash utility.

## Installation

Download the `.skill` file and install it in Claude Code:

```bash
claude skill install linux-kernel-crash-debug.skill
```

## Features

### Core Capabilities
- **Quick Start Guide**: Essential commands and debugging workflow
- **Command Reference**: Complete crash utility command cheat sheet
- **Context Management**: Understanding and switching crash session contexts

### Advanced Commands
- **list**: Kernel linked list traversal
- **rd**: Memory reading with multiple formats
- **search**: Memory pattern searching
- **vtop**: Virtual to physical address translation
- **kmem**: Memory subsystem analysis
- **foreach**: Batch task operations
- **bt**: Advanced backtrace options
- **gdb passthrough**: Direct GDB command access

### vmcore Knowledge
- ELF format structure and parsing
- VMCOREINFO contents and usage
- Supported dump formats (kdump, diskdump, netdump, LKCD, raw RAM)

### Debugging Scenarios
- kernel BUG location
- Deadlock analysis
- Memory exhaustion (OOM)
- NULL pointer dereference
- Stack overflow detection

## Structure

```
linux-kernel-crash-debug/
├── SKILL.md                    # Main skill file (quick reference)
├── README.md                   # This file
├── linux-kernel-crash-debug.skill  # Packaged skill
└── references/                 # Detailed documentation
    ├── advanced-commands.md    # In-depth command usage
    ├── vmcore-format.md        # vmcore file format details
    └── case-studies.md         # Real-world debugging examples
```

## Usage

This skill triggers when you mention:
- kernel crash / kernel panic
- vmcore analysis
- crash utility
- kernel oops debugging
- kernel debugging

### Quick Start

```
# Start crash session
crash vmlinux vmcore

# Basic debugging flow
crash> sys              # Check panic reason
crash> log              # View kernel log
crash> bt               # Backtrace
crash> struct <type>    # Inspect data structures
crash> kmem <addr>      # Memory analysis
```

## Resources

- [Crash Utility Whitepaper](https://crash-utility.github.io/crash_whitepaper.html)
- [Crash Utility Documentation](https://crash-utility.github.io/)
- [Crash Help Pages](https://crash-utility.github.io/help_pages/)

## License

MIT