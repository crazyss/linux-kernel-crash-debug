# Repository Agent Guide

This file applies to the entire repository. It records the release, packaging,
cross-distribution, and ClawHub verification lessons learned through the v1.4.x
release cycle. Treat it as an operational runbook, not as runtime skill content.

## Mission and Safety Boundary

- Improve the Linux kernel crash-debugging skill without weakening its
  evidence-first or safety contracts.
- Default to offline, read-only analysis. Do not make a live-kernel mutation
  unless the user explicitly authorizes the exact host and action in a lab or
  approved maintenance window.
- Never have an agent deliberately panic, reboot, or SysRq-crash a host, and
  never have an agent execute a destructive `kdumpctl test`. Hand the final
  trigger to an authorized human with console access and a recovery plan.
- Treat vmcores, trace output, panic logs, module names, hostnames, paths, and
  search signatures as potentially sensitive. Minimize and sanitize material
  before any external search, upload, or transfer.
- Preserve unrelated tracked and untracked files. This worktree commonly
  contains editor configuration, research caches, generated images, and local
  scripts that do not belong to the skill.

## Repository and Artifact Invariants

The runtime skill is whitelist-only. As of v1.4.3 it contains exactly these 13
files:

```text
SKILL.md
SKILL_CN.md
scripts/agent-crash.sh
references/advanced-commands.md
references/agentic-heuristics.md
references/arm64-crash-params.md
references/arm64-lock-analysis.md
references/case-studies.md
references/debug-tools-guide.md
references/evidence-first-workflow.md
references/kdump-setup-guide.md
references/sources.md
references/vmcore-format.md
```

Do not copy the whole local `scripts/` directory into a staging folder without
checking it first. An untracked helper once made a local dry-run report 14 files
even though the clean release artifact correctly contained 13. Prefer an
explicit file list or stage from the downloaded GitHub release asset.

Repository-only files such as `AGENTS.md`, `CLAUDE.md`, `.github/`, `.agents/`,
`.firecrawl/`, changelogs, READMEs, and contribution metadata must remain under
`export-ignore`. Keep `.gitattributes` and the forbidden-path expression in
`.github/workflows/release.yml` synchronized.

The two skill manifests must remain aligned:

- `SKILL.md` and `SKILL_CN.md` use the same semantic version.
- Both declare `metadata.openclaw.os: [linux]`.
- `metadata.openclaw.requires.bins` contains only `crash`. ClawHub interprets
  every item in `bins` as a hard requirement, so distribution-specific helpers
  such as `kdumpctl`, `kdump-config`, `systemctl`, and `journalctl` must not be
  global requirements.
- Never add `skill-card.md` to the repository or upload bundle. ClawHub creates
  it asynchronously and rejects publisher-authored copies.

## Cross-Distribution Compatibility

Do not present one distribution's commands as universal. Keep the following
families explicit and verify them against current official documentation:

| Family | Packages and tools | Primary configuration | Service or validation |
|---|---|---|---|
| Debian / Ubuntu | `kdump-tools`, `kexec-tools`, `crash`, matching debug symbols | `/etc/default/kdump-tools`, including `USE_KDUMP=1` where applicable | `kdump-config test`, `show`, or `status` |
| RHEL / CentOS / Rocky / AlmaLinux | `kexec-tools`, `makedumpfile`, `crash`; newer releases may package `kdump-utils` separately | `/etc/kdump.conf` | `kdumpctl status`; treat `kdumpctl test` as a human-only destructive drill |
| SLES / openSUSE | `kexec-tools`, `makedumpfile`, `crash`, optional `yast2-kdump` | `/etc/sysconfig/kdump` | `kdump.service`; default dump area is normally `/var/crash` |

Important distinctions:

- Debian's `kdump-config test` evaluates configuration and is not the same as
  RHEL-family `kdumpctl test`.
- Debug-symbol package names and repositories differ across distributions and
  releases. Query the exact running-kernel package rather than guessing a
  suffix.
- Modern x86_64 and ARM64 kdump vmcores should first use
  `crash vmlinux vmcore`. ARM64 `-m` address parameters are a recovery path for
  raw RAM or damaged/missing VMCOREINFO, not the normal distro command.
- When guidance changes, update English and Chinese entry points plus
  `references/kdump-setup-guide.md` as needed.

Useful primary references:

- Debian `kdump-config(8)`: https://manpages.debian.org/testing/kdump-tools/kdump-config.8.en.html
- RHEL kdump installation: https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/10/html/managing_monitoring_and_updating_the_kernel/installing-kdump
- SLES Kexec/Kdump: https://documentation.suse.com/sles/15-SP7/html/SLES-all/cha-tuning-kexec.html

## Change and Validation Workflow

1. Inspect before editing:

   ```bash
   git status --short --branch
   git log -5 --oneline --decorate
   git remote -v
   gh auth status
   npx --yes clawhub@0.23.3 whoami
   ```

   A successful ClawHub `whoami` proves that the stored credential can perform
   an authenticated read. Do not print or request the token unless an actual
   authentication error occurs.

2. Use official distribution, kernel, GitHub, and ClawHub sources for unstable
   commands or formats. Record durable sources in `references/sources.md` when
   they shape runtime guidance.

3. Make narrowly scoped edits. For verifier findings, put safeguards beside the
   risky command or data flow, not only in a distant global warning. Typical
   local requirements are exact authorization, bounded scope and time, protected
   output, same-session cleanup, rollback, and sanitization.

4. Validate before committing:

   ```bash
   git diff --check
   bash -n scripts/agent-crash.sh
   rg -n 'echo +c +> */proc/sysrq-trigger' SKILL.md SKILL_CN.md references scripts
   ```

   Parse both YAML frontmatters, confirm the versions match the intended tag,
   and confirm both OpenClaw metadata blocks still declare Linux plus only the
   cross-distro hard requirement. Review all matches for `kdumpctl test`; safe
   warning text is expected, but executable agent instructions are not.

5. Build a clean ClawHub dry-run directory with explicit files. Never use a
   publisher-authored `skill-card.md`:

   ```bash
   publish_root="$(mktemp -d)"
   publish_dir="$publish_root/linux-kernel-crash-debug"
   mkdir -p "$publish_dir/references" "$publish_dir/scripts"
   cp SKILL.md SKILL_CN.md "$publish_dir/"
   cp references/*.md "$publish_dir/references/"
   cp scripts/agent-crash.sh "$publish_dir/scripts/"
   npx --yes clawhub@0.23.3 skill publish "$publish_dir" \
     --slug linux-kernel-crash-debug \
     --name linux-kernel-crash-debug \
     --owner crazyss \
     --version X.Y.Z \
     --changelog "Concise release summary" \
     --categories development,operations \
     --topics linux,kernel-debugging,kdump,vmcore \
     --dry-run --json
   ```

   The dry-run should report the expected version, latest predecessor, file
   count, and fingerprint. Supply GitHub provenance only after the commit exists;
   `--source-repo` and `--source-commit` must be provided together.

## GitHub Release Procedure

1. Update both frontmatter versions, `CHANGELOG.md`, and comparison links.
2. Commit only intended files. Re-run `git status` before and after staging.
3. Create an annotated tag and atomically push the branch and tag:

   ```bash
   git tag -a vX.Y.Z -m 'vX.Y.Z - short description'
   git push --atomic origin main vX.Y.Z
   ```

4. Use `gh`, not browser assumptions, to monitor and describe the release:

   ```bash
   gh run list --workflow release.yml --limit 5 \
     --json databaseId,headSha,headBranch,status,conclusion,url
   gh release view vX.Y.Z --json url,name,tagName,isDraft,isPrerelease,assets
   gh release edit vX.Y.Z --title '...' --notes '...'
   ```

5. Download both assets to a temporary directory, run `unzip -t`, compute
   SHA-256, and compare normalized file sets. The source ZIP has a versioned
   top-level directory while `.skill` does not, so strip that prefix and sort
   before `diff`. A raw archive-list diff will falsely report every path.

6. The GitHub ZIP is a user download artifact, not a ClawHub input file. It does
   not block ClawHub publication because the publish directory contains only the
   extracted 13 runtime files.

## ClawHub Publish and Verification Procedure

Pin a CLI version that has been inspected for the release; v1.4.x used
`clawhub@0.23.3`. Recheck `--help` before changing versions because options and
publication behavior can evolve.

Publish from the verified GitHub release archive or an equivalent explicit
whitelist directory, and attach real source provenance:

```bash
npx --yes clawhub@0.23.3 skill publish "$publish_dir" \
  --slug linux-kernel-crash-debug \
  --name linux-kernel-crash-debug \
  --owner crazyss \
  --version X.Y.Z \
  --changelog "Concise release summary" \
  --categories development,operations \
  --topics linux,kernel-debugging,kdump,vmcore \
  --source-repo crazyss/linux-kernel-crash-debug \
  --source-commit "$full_commit_sha" \
  --source-ref "vX.Y.Z" \
  --source-path . \
  --json
```

Observed ClawHub behavior and stop conditions:

- A publish can remain on a spinner for several minutes and later return
  `pending-publication`. This means the artifact and credential were accepted;
  do not upload the same version again.
- If the CLI appears stuck, first query the public versions API. If the process
  has no child or active network connection, interrupting it may flush the
  already-produced JSON result. Preserve `versionId`, `attemptId`, file count,
  and fingerprint in the release notes or handoff.
- A retry that says `Version X.Y.Z already exists` is an idempotency signal that
  an earlier request committed. Stop retrying and query status.
- `pending-publication` is followed by asynchronous publication checks. Poll the
  same version at a low frequency; never create a new patch version solely to
  escape a pending state.
- Skill Card generation is a separate asynchronous stage. It has taken several
  minutes and can still be pending after a five-minute check. During that
  window `/verify` can fail only with `card.missing` even while security is
  clean. Treat five minutes as an observation point, not an SLA; continue
  low-frequency polling before diagnosing it.
- ClawHub generates `skill-card.md` server-side. Publishing one directly is
  explicitly rejected.

Public status endpoints:

```text
https://clawhub.ai/api/v1/skills/linux-kernel-crash-debug?ownerHandle=crazyss
https://clawhub.ai/api/v1/skills/linux-kernel-crash-debug/versions?ownerHandle=crazyss
https://clawhub.ai/api/v1/skills/linux-kernel-crash-debug/verify?ownerHandle=crazyss&version=X.Y.Z
https://clawhub.ai/api/v1/skills/linux-kernel-crash-debug/scan?ownerHandle=crazyss&version=X.Y.Z
```

Interpret verifier components separately:

- `card`: generated presentation artifact; absence immediately after publish is
  normally asynchronous, not a packaging defect.
- `staticScan`: deterministic suspicious-pattern scan.
- `virusTotal`: archive-engine result; record engine counts when available.
- `llm`: purpose and guardrail assessment.
- `skillSpector`: heuristic score and findings. Kernel debugging legitimately
  contains privileged commands and sensitive artifacts, so inspect whether each
  finding is expected and locally guarded instead of deleting valid capability.
- Top-level `ok=true`, `decision=pass`, empty `reasons`, and
  `security.status=clean` are the completion criteria. Also inspect `hasWarnings`
  and scanner details; a pass can still offer useful hardening opportunities.

Historical lesson: v1.3.3 failed because live tracing, detector writes, crash
tests, and persistent configuration lacked local guardrails. v1.4.1 added exact
authorization, bounded collection, cleanup, rollback, human-only crash tests,
and corrected distro guidance. v1.4.2 passed overall after asynchronous card
generation but retained three expected warnings around external searches,
vmcore sensitivity, and netdump. v1.4.3 moved those safeguards next to the
relevant data flows; its first exact five-minute check still showed only the
asynchronous `card.missing` reason while security remained clean.

## Completion Checklist

- Intended files committed; unrelated local artifacts untouched.
- `main` and `origin/main` point to the expected commit.
- Annotated tag points to that commit and the GitHub action succeeded.
- GitHub release is neither draft nor prerelease unless intentionally chosen.
- `.skill` and clean ZIP pass decompression, checksums are recorded, and their
  normalized file sets match the whitelist.
- ClawHub latest version matches the tag and fingerprint/file count match the
  dry-run.
- Waited for asynchronous Skill Card and scanners.
- Final verifier passes with security clean; any remaining expected warnings are
  explained rather than hidden.
