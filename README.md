# Linux Kernel Crash Debug Skill

[中文文档](README_CN.md)

**Linux Kernel Crash Debug Skill** guides evidence-first Linux kernel crash analysis using the crash utility, with workflows, reference material, and an offline analysis wrapper for agents.

This skill was first published for OpenClaw via [ClawHub](https://clawhub.ai/crazyss/skills/linux-kernel-crash-debug), which remains its primary release channel. GitHub Releases and `npx skills` provide additional installation options.

If the skill helps you, [star it on GitHub](https://github.com/crazyss/linux-kernel-crash-debug).

## Features

- **Quick Start Guide**: Essential commands and debugging workflow
- **Evidence-First Triage**: Artifact validation, failure timeline, competing hypotheses, and confidence reporting
- **Complete Command Reference**: All crash utility commands with examples
- **Advanced Techniques**: Memory analysis, linked list traversal, address translation
- **Production Detection**: pstore/ramoops, watchdogs, KFENCE, KCSAN, and drgn automation
- **Targeted Evidence Playbooks**: KMSAN origins, DMA mapping checks, per-task fault injection, conditional trace capture, and RCU stall comparison ([recipes](skills/linux-kernel-crash-debug/references/debug-tools-guide.md#8-targeted-playbooks-close-a-specific-evidence-gap), [RCU](skills/linux-kernel-crash-debug/references/evidence-first-workflow.md#521-rcu-stalls-compare-the-same-grace-period))
- **Real-world Cases**: Kernel BUG, deadlock, OOM, NULL pointer, stack overflow
- **vmcore Knowledge**: ELF format, VMCOREINFO, dump file types

## Installation

### OpenClaw via ClawHub

```bash
clawhub install linux-kernel-crash-debug
```

### `npx skills` for Codex, Claude Code, and other agents

Run this from the project where you want to use the skill. Select your agent
if prompted. [View on skills.sh](https://www.skills.sh/crazyss/linux-kernel-crash-debug/linux-kernel-crash-debug)

```bash
npx skills@1.9.0 add crazyss/linux-kernel-crash-debug --skill linux-kernel-crash-debug
```

To select an agent explicitly, append `-a codex`, `-a claude-code`,
`-a antigravity-cli`, `-a cursor`, or `-a gemini-cli`. Repeat `-a` for multiple
agents. Add `-g` for a user-level installation. The pinned installer requires
Node.js 22.20.0 or later. Runtime analysis needs a Linux shell with `crash`,
Bash, GNU coreutils, and access to the offline dump and matching `vmlinux`.
[Skills CLI reference](https://github.com/vercel-labs/skills/blob/main/docs/commands.md)

### Manual installation

For OpenClaw, download `linux-kernel-crash-debug.skill` from the project's
release page. In the download directory, replace `v1.5.4` with the exact tag
you selected. Use `gh` and `sha256sum` to check the file against the SHA-256
digest recorded by GitHub for that release asset.
[GitHub Releases](https://github.com/crazyss/linux-kernel-crash-debug/releases)

```bash
(
  set -euo pipefail
  tag=v1.5.4
  asset=linux-kernel-crash-debug.skill
  digest=$(gh api "repos/crazyss/linux-kernel-crash-debug/releases/tags/$tag" \
    --jq '.assets[] | select(.name == "linux-kernel-crash-debug.skill") | .digest // empty')
  if [[ ! $digest =~ ^sha256:[0-9a-f]{64}$ ]]; then
    printf 'No SHA-256 digest found for %s in %s\n' "$asset" "$tag" >&2
    exit 1
  fi
  printf '%s  %s\n' "${digest#sha256:}" "$asset" | sha256sum --check --strict
)
```

Extract the archive into a new `linux-kernel-crash-debug` folder only after
the check prints `linux-kernel-crash-debug.skill: OK`. For other agents,
copy the complete portable skill directory from a reviewed Git revision. Put
that folder inside the selected skills directory with `SKILL.md` directly
alongside `scripts/` and `references/`.
[Portable skill directory](skills/linux-kernel-crash-debug/)

| Agent | Project skills directory | Personal skills directory |
| --- | --- | --- |
| Codex, Cursor, Gemini CLI | `.agents/skills/` | `~/.agents/skills/` |
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |
| Google Antigravity CLI (`agy`) | `.agents/skills/` | `~/.gemini/config/skills/` |
| OpenClaw | `<workspace>/skills/` | `~/.openclaw/skills/` |

## Quick Start

The session below is human reference. Agents use `scripts/agent-crash.sh` on
offline regular files and follow the safety contract in [SKILL.md](skills/linux-kernel-crash-debug/SKILL.md).

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

## Skill source

The [skill directory](skills/linux-kernel-crash-debug/) contains `SKILL.md`,
`SKILL_CN.md`, `scripts/`, and `references/`. Both release archives are built
from this directory. The packaged entry points include OpenClaw's Linux and
`crash` requirements.

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
