#!/bin/bash
# agent-crash.sh - An Agent-friendly CLI wrapper for the crash utility
# Designed for autonomous agents to debug linux kernels without hanging or overloading context.

set -o pipefail
export LC_ALL=C

fail() { printf "ERROR: %s\n" "$*" >&2; exit 1; }

KERNEL=""
DUMP=""
MACRO=""

function show_help {
    echo "Usage: ./agent-crash.sh -k <vmlinux> -c <vmcore> <command> [args]"
    echo ""
    echo "Commands:"
    echo "  triage                                  - Run basic sys, log, bt triage."
    echo "  flow-deadlock                           - List UN tasks and their backtraces."
    echo "  flow-oom                                - Show overall memory, top 15 memory processes & SLABs."
    echo "  flow-arm64 <vabits> <phys> <voff> <kaslr>  - ARM64 crash with -m params injected."
    echo "  flow-lockdown                           - UN tasks + mutex/rwsem waiter extraction."
    echo "  dis-regs <func> <pid>                   - Disassemble function and show stack registers side-by-side."
    echo "  check-poison <addr>                     - Check memory near address for kernel poison patterns."
    echo "  read-memory <hex-address> [count]       - Read 1..256 memory words from an offline dump."
    echo "  backtrace <pid>                         - Show one task's full backtrace."
    echo "  disassemble <symbol>                    - Disassemble one kernel symbol."
    exit 1
}

while [[ "$#" -gt 0 ]]; do
    case $1 in
        -k|--kernel) [[ $# -ge 2 && -n "$2" ]] || fail "Missing kernel path"; KERNEL="$2"; shift ;;
        -c|--core) [[ $# -ge 2 && -n "$2" ]] || fail "Missing dump path"; DUMP="$2"; shift ;;
        -h|--help) show_help ;;
        *)
            MACRO="$1"
            shift
            MACRO_ARGS=("$@")
            break
            ;;
    esac
    shift
done

# This wrapper is offline-only. Regular-file checks reject live proc/device inputs,
# including symlinks resolved into those trees. Paths are absolute to avoid options.
[[ -n "$KERNEL" && -n "$DUMP" ]] || fail "Both -k vmlinux and -c offline vmcore are required"
[[ $EUID -ne 0 ]] || fail "Use an unprivileged account with read access to the offline files"
for input in "$KERNEL" "$DUMP"; do
    [[ -f "$input" && -r "$input" ]] || fail "Inputs must be readable regular files"
done
KERNEL=$(realpath -e -- "$KERNEL") || fail "Cannot resolve kernel path"
DUMP=$(realpath -e -- "$DUMP") || fail "Cannot resolve dump path"
for input in "$KERNEL" "$DUMP"; do
    case "$input" in /proc/*|/sys/*|/dev/*) fail "Live kernel and device inputs are forbidden" ;; esac
done
# Do not let startup files silently add GDB/shell commands or aliases.
[[ ! -e .gdbinit && ! -e "${HOME}/.gdbinit" ]] || fail "Run without local or home .gdbinit files"
CRASH_ARGS=("--no_crashrc" "-s" "$KERNEL" "$DUMP")

valid_address() { [[ "$1" =~ ^(0x)?[0-9a-fA-F]{1,16}$ ]]; }
valid_pid() { [[ "$1" =~ ^[0-9]{1,10}$ ]]; }
valid_symbol() { [[ "$1" =~ ^[a-zA-Z_][a-zA-Z0-9_.]{0,127}$ ]]; }
require_args() { [[ ${#MACRO_ARGS[@]} -eq "$1" ]] || fail "Incorrect argument count for $MACRO"; }

# Validate the complete record, including internally constructed commands. No
# shell escapes, GDB, file inclusion, pipes, redirection or write commands pass.
valid_command() {
    case "$1" in
        sys|"sys -i"|log|bt|"bt -a"|mod|"ps -m"|"ps -G"|"kmem -i"|"kmem -s"|"foreach UN bt") return 0 ;;
    esac
    [[ "$1" =~ ^bt\ -f\ [0-9]{1,10}$ ]] && return 0
    [[ "$1" =~ ^dis\ [a-zA-Z_][a-zA-Z0-9_.]{0,127}$ ]] && return 0
    if [[ "$1" =~ ^rd\ (0x)?[0-9a-fA-F]{1,16}\ ([0-9]{1,3})$ ]]; then
        [[ ${BASH_REMATCH[2]} -ge 1 && ${BASH_REMATCH[2]} -le 256 ]] && return 0
    fi
    return 1
}

run_crash() {
    local cmd="$1" status
    valid_command "$cmd" || fail "Command outside the offline read-only allowlist"
    printf '%s\n' 'set scroll off' "$cmd" quit |
        timeout 30s crash "${CRASH_ARGS[@]}" | sed '/^crash> /d'
    status=$?
    return "$status"
}

# Wrapper for truncating massive outputs that would crash the LLM
run_and_truncate() {
    local cmd="$1"
    local max_lines=400
    local output
    output=$(run_crash "$cmd") || return $?
    local lines=$(printf '%s\n' "$output" | wc -l)

    if [ "$lines" -gt "$max_lines" ]; then
        printf '%s\n' "$output" | head -n 200
        echo ""
        echo "=========================================================================="
        echo "[WARNING: Output truncated ($lines lines total > $max_lines limit).]"
        echo "[AGENT INSTRUCTION: Use tighter crash queries if needed.]"
        echo "=========================================================================="
        echo ""
        printf '%s\n' "$output" | tail -n 200
    else
        printf '%s\n' "$output"
    fi
}

case "$MACRO" in
    triage)
        require_args 0
        echo "=== [TRIAGE: SYSTEM INFO] ==="
        run_crash "sys"
        echo "=== [TRIAGE: HIGH-SIGNAL EVENT INDEX] ==="
        run_crash "log" | grep -E -i \
            'BUG:|Oops:|panic|KASAN:|KFENCE:|KCSAN:|lockdep|soft lockup|hard LOCKUP|hung task|Out of memory|oom-kill|Machine check|MCE:|SError|watchdog' \
            | head -n 120
        echo "=== [TRIAGE: KERNEL LOG (Last 100 lines)] ==="
        run_crash "log" | tail -n 100
        echo "=== [TRIAGE: PANIC BACKTRACE] ==="
        run_crash "bt"
        echo "=== [TRIAGE: ACTIVE CPU BACKTRACES] ==="
        run_and_truncate "bt -a"
        echo "=== [TRIAGE: LOADED MODULES] ==="
        run_and_truncate "mod"
        ;;
    flow-deadlock)
        require_args 0
        echo "=== [DEADLOCK: UNINTERRUPTIBLE TASKS] ==="
        run_crash "ps -m" | grep " UN "
        echo "=== [DEADLOCK: WAITING TASKS BACKTRACES] ==="
        run_and_truncate "foreach UN bt"
        ;;
    flow-oom)
        require_args 0
        echo "=== [OOM: MEMORY OVERVIEW] ==="
        run_crash "kmem -i" | head -n 30
        echo "=== [OOM: TOP 15 MEMORY HOG PROCESSES (VSZ/RSS)] ==="
        # Run ps -G, skip header, sort by memory column (usually 5th or 6th, sort by numbers backward), show top 15
        run_crash "ps -G" | sort -n -r -k 5 | head -n 15
        echo "=== [OOM: TOP 15 SLAB CACHES ALLOCATED] ==="
        run_crash "kmem -s" | sort -n -r -k 4 | head -n 15
        ;;
    flow-arm64)
        require_args 4
        # ARM64-specific macro: injects -m parameters for crash
        # Usage: flow-arm64 <vabits_actual> <phys_offset> <kimage_voffset> <kaslr>
        # Example: flow-arm64 39 0x80000000 0xffffffc000000000 0x0
        VABITS="${MACRO_ARGS[0]}"
        PHYS_OFF="${MACRO_ARGS[1]}"
        KIMAGE_VOFF="${MACRO_ARGS[2]}"
        KASLR_VAL="${MACRO_ARGS[3]}"
        [[ "$VABITS" =~ ^(39|42|48|52)$ ]] || fail "Unsupported ARM64 VA bits"
        for value in "$PHYS_OFF" "$KIMAGE_VOFF" "$KASLR_VAL"; do
            valid_address "$value" || fail "ARM64 offsets must be hexadecimal values"
        done
        echo "=== [ARM64: VERIFY CRASH CAN LOAD WITH -m PARAMS] ==="
        echo "  vabits_actual=$VABITS"
        echo "  phys_offset=$PHYS_OFF"
        echo "  kimage_voffset=$KIMAGE_VOFF"
        echo "  kaslr=$KASLR_VAL"
        echo ""
        CRASH_ARGS+=("-m" "vabits_actual=$VABITS" "-m" "phys_offset=$PHYS_OFF" "-m" "kimage_voffset=$KIMAGE_VOFF" "-m" "kaslr=$KASLR_VAL")
        run_crash "sys"
        run_crash "log" | tail -n 50
        run_crash "bt"
        echo "=== [ARM64: VMCOREINFO SANITY] ==="
        run_crash "sys -i" | head -n 20
        echo ""
        echo "=== [AGENT HINT] ==="
        echo "These derived -m parameters apply only to this invocation."
        echo "Normal distro vmcores should use triage without address overrides."
        ;;
    flow-lockdown)
        require_args 0
        # Lock contention analysis: extract UN tasks, then for each try to derive lock address
        echo "=== [LOCKDOWN: UN TASKS] ==="
        run_crash "ps -m" | grep " UN "
        echo ""
        echo "=== [LOCKDOWN: UN TASKS BACKTRACES] ==="
        run_and_truncate "foreach UN bt"
        echo ""
        echo "=== [LOCKDOWN: MUTEX/RWSEM WAITERS (top 10)] ==="
        run_crash "foreach UN bt" | grep -E "mutex|rwsem|down_write|down_read|spin_lock|rwsem_down" | head -20
        echo ""
        echo "=== [AGENT HINT: LOCK DERIVATION TECHNIQUE] ==="
        echo "For ARM64 tasks blocked on rwsem/mutex, the lock address is in a callee-saved register."
        echo "See references/case-studies.md Case 11 for the manual derivation."
        echo "Pattern: 1) bt to get FP, 2) dis -xl to find reg save offset, 3) rd to read saved value."
        ;;
    dis-regs)
        require_args 2
        FUNC="${MACRO_ARGS[0]}"
        PID="${MACRO_ARGS[1]}"
        valid_symbol "$FUNC" || fail "Invalid kernel symbol"
        valid_pid "$PID" || fail "Invalid PID"
        echo "=== [EXPERT: REGISTERS FOR PID $PID] ==="
        run_and_truncate "bt -f $PID"
        echo "=== [EXPERT: DISASSEMBLY FOR $FUNC] ==="
        run_and_truncate "dis $FUNC"
        ;;
    check-poison)
        require_args 1
        ADDR="${MACRO_ARGS[0]}"
        valid_address "$ADDR" || fail "Invalid hexadecimal address"
        echo "=== [POISON CHECK: MEMORY DUMP NEAR $ADDR] ==="
        out=$(run_crash "rd $ADDR 64")
        printf '%s\n' "$out"
        echo "=== [POISON CHECK: MAGIC NUMBER MATCHES] ==="
        # Grep for standard poison values:
        # 6b6b6b6b (UAF), 5a5a5a5a (SLUB uninitialized), deadbeef, 0x100/0x200 (LIST_POISON)
        printf '%s\n' "$out" | grep -E -i '6b6b6b6b|5a5a5a5a|deadbeef|0+100\b|0+200\b|abcd' || echo "No obvious poison match found. Agent should inspect payload manually."
        ;;
    read-memory)
        [[ ${#MACRO_ARGS[@]} -ge 1 && ${#MACRO_ARGS[@]} -le 2 ]] || fail "Expected address and optional count"
        ADDR="${MACRO_ARGS[0]}"
        COUNT="${MACRO_ARGS[1]:-1}"
        valid_address "$ADDR" || fail "Invalid hexadecimal address"
        [[ "$COUNT" =~ ^[1-9][0-9]{0,2}$ && "$COUNT" -le 256 ]] || fail "Count must be 1..256"
        run_and_truncate "rd $ADDR $COUNT"
        ;;
    backtrace)
        require_args 1
        valid_pid "${MACRO_ARGS[0]}" || fail "Invalid PID"
        run_and_truncate "bt -f ${MACRO_ARGS[0]}"
        ;;
    disassemble)
        require_args 1
        valid_symbol "${MACRO_ARGS[0]}" || fail "Invalid kernel symbol"
        run_and_truncate "dis ${MACRO_ARGS[0]}"
        ;;
    *)
        echo "Unknown macro: $MACRO"
        show_help
        ;;
esac
