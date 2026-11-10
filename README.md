# Linux Kernel Crash Debug Skill

[中文文档](README_CN.md)

**Linux Kernel Crash Debug Skill** guides evidence-first Linux kernel crash analysis using the crash utility, with workflows, reference material, and an offline analysis wrapper for agents.

## Features

- **Quick Start Guide**: Essential commands and debugging workflow
- **Evidence-First Triage**: Artifact validation, failure timeline, competing hypotheses, and confidence reporting
- **Complete Command Reference**: All crash utility commands with examples
- **Advanced Techniques**: Memory analysis, linked list traversal, address translation
- **Production Detection**: pstore/ramoops, watchdogs, KFENCE, KCSAN, and drgn automation
- **Targeted Evidence Playbooks**: KMSAN origins, DMA mapping checks, per-task fault injection, conditional trace capture, and RCU stall comparison ([recipes](references/debug-tools-guide.md#8-targeted-playbooks-close-a-specific-evidence-gap), [RCU](references/evidence-first-workflow.md#521-rcu-stalls-compare-the-same-grace-period))
- **Real-world Cases**: Kernel BUG, deadlock, OOM, NULL pointer, stack overflow
- **vmcore Knowledge**: ELF format, VMCOREINFO, dump file types

## Installation

Download and verify `linux-kernel-crash-debug.skill` from
[GitHub Releases](https://github.com/crazyss/linux-kernel-crash-debug/releases/latest),
then extract all 13 runtime files into an empty directory:

```bash
mkdir -p ./linux-kernel-crash-debug
unzip linux-kernel-crash-debug.skill -d ./linux-kernel-crash-debug
```

Place the complete directory in your agent's skill directory. See
[installation examples](SKILL.md#installation) for platform-specific locations.

## Quick Start

The session below is human reference. Agents use `scripts/agent-crash.sh` on
offline regular files and follow the safety contract in `SKILL.md`.

```bash
# Start crash session
crash vmlinux vmcore

# Basic debugging flow
crash> sys              # Check panic reason
crash> log              # View kernel log
crash> bt               # Backtrace
crash> struct <type>    # Inspect data structures
crash> kmem <addr>      # Memory analysis
```

## Structure

```
linux-kernel-crash-debug/
├── SKILL.md                    # Main skill file (English)
├── SKILL_CN.md                 # Chinese version of skill
├── README.md                   # English documentation
├── README_CN.md                # Chinese documentation
├── CONTRIBUTING.md             # Contribution guide
├── LICENSE                     # MIT License
├── CLAUDE.md                   # Repository assistant guidance
├── scripts/                    # Utility scripts
│   └── agent-crash.sh          # Agent-safe crash wrapper
├── references/                 # Detailed documentation
│   ├── advanced-commands.md    # In-depth command usage
│   ├── agentic-heuristics.md   # Agent debugging heuristics
│   ├── evidence-first-workflow.md # Evidence gates, routing, verification, report template
│   ├── case-studies.md         # Real-world debugging examples
│   ├── debug-tools-guide.md    # KASAN, Kprobes, Kmemleak guide
│   └── vmcore-format.md        # vmcore file format details
└── .github/                    # CI & Issue templates
    ├── ISSUE_TEMPLATE/
    └── workflows/release.yml
```

## Usage

Use this skill for Linux kernel debugging tasks such as:
- kernel crash / kernel panic
- vmcore analysis
- crash utility
- kernel oops debugging

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

- Report bugs or request features via [Issues](https://github.com/crazyss/linux-kernel-crash-debug/issues)
- Submit improvements via Pull Requests

## Resources

- [Crash Utility Whitepaper](https://crash-utility.github.io/crash_whitepaper.html)
- [Crash Utility Documentation](https://crash-utility.github.io/)
- [Crash Help Pages](https://crash-utility.github.io/help_pages/)

## Acknowledgements

The code repository `.agents/rules` is derived from [awesome-claude-code-toolkit](https://github.com/rohitg00/awesome-claude-code-toolkit).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Made with passion for kernel debugging
