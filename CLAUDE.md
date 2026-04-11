# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Claude Code skill repository for Linux kernel crash debugging using the crash utility. The skill provides comprehensive guidance for analyzing kernel crashes, panics, and vmcore dumps.

## Repository Structure

```
linux-kernel-crash-debug/
├── SKILL.md                        # Main skill definition (YAML frontmatter + Markdown)
├── SKILL_CN.md                     # Chinese version of the skill
├── README.md                       # Installation and usage instructions
├── scripts/                        # Utility scripts
│   └── agent-crash.sh              # Agent-safe crash wrapper
├── references/                     # Detailed reference documents
│   ├── advanced-commands.md        # Advanced crash commands reference
│   ├── agentic-heuristics.md       # Agent debugging heuristics
│   ├── case-studies.md             # Debugging case studies
│   ├── debug-tools-guide.md        # KASAN, Kprobes, Kmemleak guide
│   └── vmcore-format.md            # vmcore file format details
└── linux-kernel-crash-debug.skill  # Packaged skill file (zip format)
```

**Note**: The `.skill` file is a standard zip archive. Use `unzip -l` to inspect contents.

## Development Commands

### Package the skill (full)
```bash
cd linux-kernel-crash-debug
zip ../linux-kernel-crash-debug.skill SKILL.md SKILL_CN.md references/*.md scripts/*.sh
```

### Update existing package
```bash
zip -u linux-kernel-crash-debug.skill SKILL.md
```

### Install locally
```bash
claude skill install linux-kernel-crash-debug.skill
```

## Skill Architecture

The skill follows the standard Claude Code skill format:
- **YAML frontmatter**: `name` and `description` fields control skill identification and triggering
- **Description field**: Primary triggering mechanism - should be "pushy" to avoid undertriggering
- **Body**: Step-by-step debugging workflow, command reference tables, and case studies

### ClawHub Metadata Format

For ClawHub registry compatibility, use this frontmatter structure:

```yaml
---
name: <skill-name>
description: <triggering description>
metadata:
  openclaw:
    requires:
      bins:          # Required binary tools
        - tool1
        - tool2
      env:           # Required environment variables (optional)
        - API_KEY
    homepage: https://github.com/<repo>
---
```

**Important**: ClawHub expects `metadata.openclaw.requires.bins`, not a top-level `requires` field. Using the wrong format will cause "Required binaries: none" in the registry.

## Key Resources

- [Crash Utility Whitepaper](https://crash-utility.github.io/crash_whitepaper.html) - Primary source for skill content
- [Crash Utility Documentation](https://crash-utility.github.io/) - Official documentation
- [ClawHub Skill Format](https://github.com/openclaw/clawhub/blob/main/docs/skill-format.md) - Metadata standards