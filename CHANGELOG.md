# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.3.2] - 2026-06-14

### Fixed
- **GitHub Release "Source code" archive leaked 27 repository metadata files.** The auto-generated `<tag>.zip` on the Release page was built by `git archive` and shipped `.github/`, `.agents/`, `.gitignore`, `LICENSE`, `CONTRIBUTING.md`, `CHANGELOG.md`, `CLAUDE.md`, and the two `README*.md` files alongside the skill content.
  - Added `.gitattributes` with `export-ignore` for those paths so `git archive` skips them.
  - Added a `Create Clean Source Archive` step in `release.yml` that explicitly builds a clean `<tag>.zip` via `git archive` and uploads it as a release asset (defence in depth in case the auto-generated asset ever changes behavior).
  - Added a `Verify Clean Source Archive` step that inspects the produced zip and fails the build if any of the forbidden paths reappear, catching future `.gitattributes` regressions early.
- `SKILL.md` / `SKILL_CN.md`: bumped `version: 1.3.1` → `1.3.2` to match this release.

### Notes
- These paths remain in the repository (for maintainers and the GitHub project page) but are excluded from the published skill artifacts: `README.md`, `README_CN.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `LICENSE`, `CLAUDE.md`, `.github/`, `.agents/`. The `SKILL.md` reference to `CONTRIBUTING.md` uses a `https://github.com/...` URL, so the local file exclusion does not break that link.
- Skill consumers see exactly the same 13 files in both the `.skill` package and the new `<tag>.zip` source archive.

## [1.3.1] - 2026-06-14

### Changed
- `.github/workflows/release.yml`: removed `LICENSE` and `CONTRIBUTING.md` from the zip whitelist so the published `.skill` package contains only the skill manifest and runtime content. ClawHub defaults to MIT-0 and the registry validates the package against the skill manifest; an embedded `LICENSE` is redundant and can shadow the registry license.
- `CLAUDE.md`: synchronized the local packaging command with `release.yml` and restated the whitelist-only contract (no `LICENSE`, `CONTRIBUTING.md`, `.github/`, or any repository metadata).
- `SKILL.md` / `SKILL_CN.md`:
  - Added `version: 1.3.1` to frontmatter so the package version matches the git tag.
  - Completed `metadata.openclaw.requires.bins` with `kexec`, `kdumpctl`, `systemctl`, and `journalctl`, which are referenced throughout `references/kdump-setup-guide.md`. The English and Chinese frontmatters remain in lockstep.

## [1.3.0] - 2026-06-14

### Added
- `references/kdump-setup-guide.md`: end-to-end kdump configuration covering x86_64 and ARM64. Includes all 5 `crashkernel=` syntaxes, dump-capture kernel config per arch, `kdump.conf` field reference, sysrq triggers, `makedumpfile` dump-level bitmasks, distribution-specific commands, and troubleshooting.
- `references/arm64-crash-params.md`: derives the 4 `-m` parameters required by `crash_arm64` (`vabits_actual`, `phys_offset`, `kimage_voffset`, `kaslr`) with worked example, and compares against x86_64's VMCOREINFO-driven automatic handling.
- `references/sources.md`: full bibliography of 21 sources, with arch comparison matrix and acknowledgments.
- New case study in `references/case-studies.md`:
  - Case 11 — ARM64 `rwsem` lock-point pointer derivation via callee-saved register walking.
  - Case 12 — SLUB use-after-free (simple variant and misalignment variant where the victim module is wrongly reported).
- `SKILL.md` / `SKILL_CN.md`:
  - "ARM64 / x86_64 Quick Reference" table.
  - "Deriving Lock Pointers from Stack Backtrace" technique.
  - "Three-Layer Memory Leak Diagnostic" workflow (meminfo/slabinfo/buddyinfo + slub_debug + page_owner + kmemleak alternatives).
- `scripts/agent-crash.sh`:
  - `flow-arm64 <vabits> <phys> <voff> <kaslr>` macro: injects ARM64 `-m` parameters and runs triage with the new args.
  - `flow-lockdown` macro: extracts UN tasks and their backtraces, surfaces mutex/rwsem waiter signatures for lock-contention analysis.

### Changed
- `references/debug-tools-guide.md`: SLUB Debug section rewritten with Herbert's practical f/z/p/u/t flag reference and a key limitation note (`slub_debug` cannot pinpoint the corruption culprit the way KASAN can).
- Extended Reference table in `SKILL.md` and `SKILL_CN.md` updated to include the 3 new reference files.
- `CLAUDE.md`: documented ClawHub metadata format (`metadata.openclaw.requires.bins`) to prevent future format regressions.
- New `.agents/rules/*.md` agent rule documentation (16 files covering accessibility, agents, api-design, code-review, coding-rules, coding-style, database, dependency-management, documentation, error-handling, git-workflow, monitoring, naming, performance, security, testing).

## [1.2.3] - 2026-04-11

### Changed
- License switched to MIT No Attribution (MIT-0).
- Copyright holder information revised.

## [1.2.2] - 2026-04-11

### Changed
- Moved `agent-crash.sh` to `scripts/` and updated all references and release packaging.

## [1.2.1] - 2026-04-11

### Changed
- Granted `contents: write` permission to the release workflow so it can publish tag-triggered releases.

## [1.2.0] - 2026-04-11

### Changed
- Release trigger switched to tag push (`on.push.tags: 'v*'`).
- Enabled Node 24 for JavaScript actions via `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24`.

## [1.1.0] - 2026-03-28

### Added
- 5 new crash debugging case studies.
- `references/debug-tools-guide.md`: KASAN, Kprobes, Kmemleak guide.
- `references/advanced-commands.md`: advanced crash commands reference.
- `references/agentic-heuristics.md`: agent debugging heuristics.
- `references/vmcore-format.md`: vmcore file format details.

## [1.0.0] - 2026-03-06

### Added
- Initial release: `SKILL.md` and `SKILL_CN.md` skill definitions.
- `scripts/agent-crash.sh`: agent-safe crash wrapper.
- `references/case-studies.md`: foundational debugging case studies.
- GitHub Issue templates.
- `CLAUDE.md` with project guidance.

[Unreleased]: https://github.com/crazyss/linux-kernel-crash-debug/compare/v1.3.0...HEAD
[1.3.0]: https://github.com/crazyss/linux-kernel-crash-debug/compare/v1.2.3...v1.3.0
[1.2.3]: https://github.com/crazyss/linux-kernel-crash-debug/compare/v1.2.2...v1.2.3
[1.2.2]: https://github.com/crazyss/linux-kernel-crash-debug/compare/v1.2.1...v1.2.2
[1.2.1]: https://github.com/crazyss/linux-kernel-crash-debug/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/crazyss/linux-kernel-crash-debug/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/crazyss/linux-kernel-crash-debug/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/crazyss/linux-kernel-crash-debug/releases/tag/v1.0.0
