# Linux Kernel Crash Debug Skill

[English](README.md) | 中文

**Linux Kernel Crash Debug Skill** 提供基于 crash 工具的 Linux 内核崩溃分析流程、参考资料和供 agent 使用的离线分析封套，强调证据优先。

本技能最初面向 OpenClaw 发布，通过 [ClawHub](https://clawhub.ai/crazyss/skills/linux-kernel-crash-debug) 分发。ClawHub 仍是主要发布渠道，GitHub Releases 和 `npx skills` 提供其他安装入口。

如果这个技能对你有帮助，欢迎在 [GitHub 点个 Star](https://github.com/crazyss/linux-kernel-crash-debug)。

## 功能特性

- **快速入门指南**：核心命令和调试流程
- **证据优先分诊**：产物校验、故障时间线、竞争假设与置信度报告
- **完整命令参考**：所有 crash utility 命令及示例
- **高级技巧**：内存分析、链表遍历、地址翻译
- **生产环境检测**：pstore/ramoops、watchdog、KFENCE、KCSAN 与 drgn 自动化
- **定点取证打法**：KMSAN 来源链、DMA 映射核对、按任务故障注入、条件轨迹捕获与 RCU stall 差分（[操作方案](skills/linux-kernel-crash-debug/references/debug-tools-guide.md#8-targeted-playbooks-close-a-specific-evidence-gap)、[RCU 判读](skills/linux-kernel-crash-debug/references/evidence-first-workflow.md#521-rcu-stalls-compare-the-same-grace-period)）
- **实战案例**：kernel BUG、死锁、OOM、NULL 指针、栈溢出
- **vmcore 知识**：ELF 格式、VMCOREINFO、转储文件类型

## 安装

### OpenClaw（通过 ClawHub）

```bash
clawhub install linux-kernel-crash-debug
```

### `npx skills`（Codex、Claude Code 等）

在要使用技能的项目目录执行以下命令。出现提示时，选择你使用的 Agent。 [查看 skills.sh 页面](https://www.skills.sh/crazyss/linux-kernel-crash-debug/linux-kernel-crash-debug)

```bash
npx skills@1.9.0 add crazyss/linux-kernel-crash-debug --skill linux-kernel-crash-debug
```

也可以追加 `-a codex`、`-a claude-code`、`-a antigravity-cli`、`-a cursor` 或 `-a gemini-cli` 来指定 Agent。安装到多个 Agent 时可重复使用 `-a`，加 `-g` 可安装到用户级目录。上述安装器需要 Node.js 22.20.0 或更新版本。实际分析在 Linux 环境执行，需要 `crash`、Bash、GNU coreutils，以及可读取的离线转储和与之匹配的 `vmlinux`。 [Skills CLI 文档](https://github.com/vercel-labs/skills/blob/main/docs/commands.md)

### 手动安装

OpenClaw 用户可从项目发布页下载 `linux-kernel-crash-debug.skill`。在下载目录中执行以下命令，把 `v1.5.2` 换成所选的发布标签。命令用 `gh` 查询 GitHub 为该发布资产记录的 SHA-256，再用 `sha256sum` 校验本地文件。 [GitHub Releases](https://github.com/crazyss/linux-kernel-crash-debug/releases)

```bash
(
  set -euo pipefail
  tag=v1.5.2
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

看到 `linux-kernel-crash-debug.skill: OK` 后，再解压到新的 `linux-kernel-crash-debug` 目录。其他 Agent 可从已审阅的 Git 版本复制完整的通用技能目录。将该目录放入下表对应位置，目录内的 `SKILL.md` 应与 `scripts/` 和 `references/` 同级。 [通用技能目录](skills/linux-kernel-crash-debug/)

| Agent | 项目级技能目录 | 用户级技能目录 |
| --- | --- | --- |
| Codex、Cursor、Gemini CLI | `.agents/skills/` | `~/.agents/skills/` |
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |
| Google Antigravity CLI（`agy`） | `.agents/skills/` | `~/.gemini/config/skills/` |
| OpenClaw | `<workspace>/skills/` | `~/.openclaw/skills/` |

## 快速开始

以下为人工交互参考；Agent 使用 `scripts/agent-crash.sh` 分析离线普通文件，
并遵循 [SKILL_CN.md](skills/linux-kernel-crash-debug/SKILL_CN.md) 的安全契约。

```bash
# 启动 crash 会话
crash vmlinux vmcore

# 基本调试流程
crash> sys              # 查看 panic 原因
crash> log              # 查看内核日志
crash> bt               # 调用栈回溯
crash> struct <type>    # 检查数据结构
crash> kmem <addr>      # 内存分析
```

## 技能源文件

[技能目录](skills/linux-kernel-crash-debug/)包含 `SKILL.md`、`SKILL_CN.md`、`scripts/` 和 `references/`。两个发布包均从这里生成，包内的技能入口带有 OpenClaw 所需的 Linux 和 `crash` 依赖声明。

## 使用方法

此技能适用于以下 Linux 内核调试任务：
- kernel crash / kernel panic
- vmcore 分析
- crash utility
- kernel oops 调试
- 内核崩溃调试

## 参与贡献

欢迎参与贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

- 通过 [Issues](https://github.com/crazyss/linux-kernel-crash-debug/issues) 报告问题或请求功能
- 通过 Pull Requests 提交改进

## 资源链接

- [Crash Utility 白皮书](https://crash-utility.github.io/crash_whitepaper.html)
- [Crash Utility 文档](https://crash-utility.github.io/)
- [Crash 帮助页面](https://crash-utility.github.io/help_pages/)

## 致谢

`.agents/rules` 目录包含的代码规范与系统提示词源自 [awesome-claude-code-toolkit](https://github.com/rohitg00/awesome-claude-code-toolkit) 项目。

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

---

Made with passion for Linux kernel debugging
