#!/usr/bin/env python3
"""heavy_lock.py - POSIX heavy execution mutex with macOS Unified Memory checking.

Serialises heavy execution workloads (e.g. Ollama 14b/12b local inference,
Playwright perception browser suites, pytest/vitest runs, audio transcription)
using kernel-managed fcntl.flock and monitors macOS memory headroom.
"""

import argparse
import fcntl
import json
import os
import subprocess
import sys
import time

LOCK_DIR = "/tmp"
DEFAULT_MIN_FREE_GB = 1.5
DEFAULT_WAIT_TIMEOUT = 600


def get_macos_free_memory_gb() -> float:
    """Calculates available memory on macOS in GB using memory_pressure or vm_stat."""
    try:
        total_bytes_out = subprocess.check_output(
            ["sysctl", "-n", "hw.memsize"], text=True
        ).strip()
        total_bytes = int(total_bytes_out)
    except Exception:
        total_bytes = 16 * (1024**3)

    # Prefer memory_pressure's authoritative free percentage
    try:
        mp_out = subprocess.check_output(["memory_pressure"], text=True)
        for line in mp_out.splitlines():
            if "memory free percentage:" in line.lower():
                pct_str = line.split(":")[-1].replace("%", "").strip()
                pct = float(pct_str)
                return (total_bytes * (pct / 100.0)) / (1024**3)
    except Exception:
        pass

    # Fallback to vm_stat
    try:
        page_size_out = subprocess.check_output(
            ["sysctl", "-n", "hw.pagesize"], text=True
        ).strip()
        page_size = int(page_size_out)
    except Exception:
        page_size = 16384

    try:
        vm_out = subprocess.check_output(["vm_stat"], text=True)
        stats = {}
        for line in vm_out.splitlines():
            parts = line.split(":")
            if len(parts) == 2:
                key = parts[0].strip()
                val = parts[1].strip().rstrip(".")
                try:
                    stats[key] = int(val)
                except ValueError:
                    pass

        free_pages = stats.get("Pages free", 0)
        speculative_pages = stats.get("Pages speculative", 0)
        inactive_pages = stats.get("Pages inactive", 0)
        purgeable_pages = stats.get("Pages purgeable", 0)

        available_bytes = (
            free_pages + speculative_pages + inactive_pages + purgeable_pages
        ) * page_size
        return available_bytes / (1024**3)
    except Exception:
        return 4.0


def acquire_slot_lock(slot: str, name: str) -> int:
    lock_path = os.path.join(LOCK_DIR, f"artifice-heavy-{slot}.lock")
    status_path = os.path.join(LOCK_DIR, f"artifice-heavy-{slot}.status")

    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o666)

    # Blocking lock with status check
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
    except Exception as e:
        print(f"Failed to acquire flock on {lock_path}: {e}", file=sys.stderr)
        os.close(fd)
        return -1

    status_data = {
        "pid": os.getpid(),
        "name": name,
        "slot": slot,
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cwd": os.getcwd(),
    }
    try:
        with open(status_path, "w", encoding="utf-8") as sf:
            json.dump(status_data, sf)
    except Exception:
        pass

    return fd


def release_slot_lock(fd: int, slot: str):
    status_path = os.path.join(LOCK_DIR, f"artifice-heavy-{slot}.status")
    try:
        if os.path.exists(status_path):
            os.remove(status_path)
    except Exception:
        pass
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
    except Exception:
        pass


def run_command(args: argparse.Namespace) -> int:
    slot = args.slot
    name = args.name or " ".join(args.command)
    min_free_gb = args.min_free_gb
    timeout = args.wait_sec

    start_time = time.time()
    print(f"[heavy_lock] Waiting for lock on slot '{slot}' ({name})...")
    fd = acquire_slot_lock(slot, name)
    if fd < 0:
        return 1

    try:
        # Check memory floor
        while True:
            free_gb = get_macos_free_memory_gb()
            if free_gb >= min_free_gb:
                break

            elapsed = time.time() - start_time
            if elapsed >= timeout:
                print(
                    f"[heavy_lock] Error: Memory below floor ({free_gb:.2f} GB < {min_free_gb:.2f} GB) after {timeout}s timeout.",
                    file=sys.stderr,
                )
                return 9  # Exit 9 = Insufficient Memory

            print(
                f"[heavy_lock] Memory at {free_gb:.2f} GB (floor: {min_free_gb:.2f} GB). Waiting 5s..."
            )
            time.sleep(5)

        print(
            f"[heavy_lock] Slot '{slot}' acquired (Free RAM: {free_gb:.2f} GB). Executing: {' '.join(args.command)}"
        )
        res = subprocess.run(args.command)
        return res.returncode
    finally:
        release_slot_lock(fd, slot)


def show_status():
    slots = ["gpu", "suite", "all"]
    print("=== artifice Heavy Lock Status ===")
    active = 0
    for slot in slots:
        status_path = os.path.join(LOCK_DIR, f"artifice-heavy-{slot}.status")
        if os.path.exists(status_path):
            try:
                with open(status_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Check if pid is alive
                pid = data.get("pid", -1)
                try:
                    os.kill(pid, 0)
                    alive = True
                except OSError:
                    alive = False

                if alive:
                    print(
                        f"  • Slot '{slot}': BUSY (PID {pid}, Job: '{data.get('name')}', Started: {data.get('started_at')})"
                    )
                    active += 1
                else:
                    print(f"  • Slot '{slot}': STALE STATUS (PID {pid} dead)")
            except Exception:
                print(f"  • Slot '{slot}': Status unreadable")
        else:
            print(f"  • Slot '{slot}': IDLE")

    free_gb = get_macos_free_memory_gb()
    print(f"\nAvailable Unified Memory (macOS estimate): {free_gb:.2f} GB")


def main():
    parser = argparse.ArgumentParser(
        description="POSIX Heavy Execution Lock & Memory Mutex"
    )
    subparsers = parser.add_subparsers(dest="action")

    # Run subparser
    run_parser = subparsers.add_parser("run", help="Execute command under heavy lock")
    run_parser.add_argument(
        "--slot",
        choices=["gpu", "suite", "all"],
        default="all",
        help="Lock slot category (default: all)",
    )
    run_parser.add_argument(
        "--min-free-gb",
        type=float,
        default=DEFAULT_MIN_FREE_GB,
        help="Minimum free memory floor in GB (default: 2.5)",
    )
    run_parser.add_argument(
        "--wait-sec",
        type=int,
        default=DEFAULT_WAIT_TIMEOUT,
        help="Maximum wait time for lock/memory in seconds (default: 600)",
    )
    run_parser.add_argument(
        "--name",
        type=str,
        default="",
        help="Human-readable job label for status line",
    )
    run_parser.add_argument(
        "command", nargs=argparse.REMAINDER, help="Command to execute"
    )

    # Status subparser
    subparsers.add_parser("status", help="Show active lock slots and memory")

    args = parser.parse_args()

    if args.action == "status":
        show_status()
        sys.exit(0)
    elif args.action == "run":
        if not args.command:
            print("Error: No command specified to run.", file=sys.stderr)
            sys.exit(1)
        # Strip leading '--' if present
        if args.command and args.command[0] == "--":
            args.command = args.command[1:]
        sys.exit(run_command(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
