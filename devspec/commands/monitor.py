"""
DevSpec Monitor Command.

Component: comp_cli_monitor
Feature: feat_cli_command_structure

执行 PRD-Spec 一致性检查，输出分层报告并生成 PRODUCT_DASHBOARD.md。
"""
from pathlib import Path

from devspec.core.consistency import ConsistencyMonitor


def monitor():
    """
    Run PRD-Spec consistency check and generate dashboard.

    Invokes ConsistencyMonitor to compare PRD anchors with SpecGraph YAML definitions,
    then outputs a layered report and generates PRODUCT_DASHBOARD.md.
    """
    root_path = Path(".")
    monitor_instance = ConsistencyMonitor(root_path)
    monitor_instance.run_check()
