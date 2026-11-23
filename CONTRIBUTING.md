# Contributing to Linux Kernel Crash Debug Skill

First off, thank you for considering contributing to the Linux Kernel Crash Debug Skill! It's people like you that make such tools useful for everyone.

## Where do I go from here?

If you've noticed a bug or have a feature request, [make one](https://github.com/crazyss/linux-kernel-crash-debug/issues)! It's generally best if you get confirmation of your bug or approval for your feature request this way before starting to code.

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/crazyss/linux-kernel-crash-debug.git
   cd linux-kernel-crash-debug
   ```

2. Edit the documentation or the skill under `skills/linux-kernel-crash-debug/`.

3. Build the OpenClaw-compatible release archives in a temporary directory:
   ```bash
   python3 .github/package-skill.py "$(mktemp -d)"
   ```

## Pull Request Process

1. Ensure any changes align with both `SKILL.md` (English) and `SKILL_CN.md` (Chinese).
2. Use descriptive commit messages.
3. Update the `README.md` and `README_CN.md` with details of changes, if appropriate.
4. Open your Pull Request and we will review it as soon as possible.

## Content Guidelines

- Keep explanations concise and debugging instructions clear.
- Provide real-world output examples where possible for better understanding.
- Ensure all commands are syntactically correct and safe to run.

Thank you!
