#!/usr/bin/env python3
"""
DevSpec Bootstrap Script (Phase 0)
----------------------------------
This script acts as the temporary "kernel" to drive the self-bootstrapping process.
It primarily runs the Consistency Monitor to check if the PRD (Intent) matches
the SpecGraph (Structure).

Usage:
    python bootstrap.py [monitor]
"""

import sys
from pathlib import Path

# Add the current directory to sys.path so we can import devspec modules
sys.path.append(str(Path(__file__).parent))

from devspec.core.consistency import ConsistencyMonitor

def main():
    # Simple command dispatch for Phase 0
    command = "monitor"
    if len(sys.argv) > 1:
        command = sys.argv[1]

    if command == "monitor":
        monitor = ConsistencyMonitor(Path("."))
        monitor.run_check()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: monitor")

if __name__ == "__main__":
    main()
