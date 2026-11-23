# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository provides a Linux kernel crash-debugging skill using the crash utility. It includes evidence-first workflows, references, and an offline analysis wrapper for agents analyzing kernel crashes, panics, and vmcore dumps.

## Repository Structure

The source lives in `skills/linux-kernel-crash-debug/`. Keep `SKILL.md`,
`SKILL_CN.md`, `scripts/agent-crash.sh`, and the references together. The
`skills` CLI installs this directory for Codex, Claude Code, Antigravity CLI,
and other compatible agents.

## Development Commands

```bash
bash -n skills/linux-kernel-crash-debug/scripts/agent-crash.sh
python3 .github/tests/test_agent_crash.py
python3 .github/package-skill.py "$(mktemp -d)"
```

The packaging command builds both release archives from the 13-file whitelist.
See `AGENTS.md` for ClawHub dry-run and publication steps. See `README.md` for
client installation commands.

## Skill Architecture

The skill consists of a Markdown entry point and supporting files:
- **YAML frontmatter**: `name` and `description` fields control skill identification and triggering
- **Description field**: Primary triggering mechanism - should be "pushy" to avoid undertriggering
- **Body**: Step-by-step debugging workflow, command reference tables, and case studies

### ClawHub Metadata Format

The package builder adds this frontmatter structure for ClawHub registry compatibility:

```yaml
---
name: <skill-name>
description: <triggering description>
metadata:
  openclaw:
    requires:
      bins:          # Required binary tools
        - crash
    os:
      - linux
    homepage: https://github.com/<repo>
---
```

**Important**: ClawHub expects `metadata.openclaw.requires.bins`, not a top-level
`requires` field. Every entry in `requires.bins` is a hard requirement that must
be installed. Keep this list to cross-distro runtime essentials; do not add
conditional helpers such as RHEL's `kdumpctl` or Debian's `kdump-config` as
global requirements. Use `metadata.openclaw.os: [linux]` for this skill.

## Key Resources

- [Crash Utility Whitepaper](https://crash-utility.github.io/crash_whitepaper.html) - Primary source for skill content
- [Crash Utility Documentation](https://crash-utility.github.io/) - Official documentation
- [ClawHub Skill Format](https://github.com/openclaw/clawhub/blob/main/docs/skill-format.md) - Metadata standards
