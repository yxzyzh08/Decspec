"""
交互式项目信息采集器。

通过命令行交互收集项目初始化所需的信息。
"""

from dataclasses import dataclass
from enum import Enum

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt

console = Console(force_terminal=True)


class AICli(str, Enum):
    """支持的 AI CLI 类型。"""

    CLAUDE = "claude"
    GEMINI = "gemini"


@dataclass
class ProjectInfo:
    """项目信息数据类。"""

    name: str
    vision: str
    domains: list[str]
    ai_cli: AICli


def collect_project_info() -> ProjectInfo:
    """
    交互式收集项目信息。

    Returns:
        ProjectInfo: 收集到的项目信息
    """
    console.print("\n[bold blue]DevSpec Project Initialization[/bold blue]\n")

    # 项目名称
    name = Prompt.ask(
        "[cyan]? Project name[/cyan]",
        default="my-project",
    )

    # 项目愿景
    vision = Prompt.ask(
        "[cyan]? Project vision (one sentence)[/cyan]",
        default="A great software project.",
    )

    # 主要域
    domains_input = Prompt.ask(
        "[cyan]? Main domains (comma separated)[/cyan]",
        default="core",
    )
    domains = [d.strip() for d in domains_input.split(",") if d.strip()]

    # AI CLI 选择
    console.print("\n[cyan]? Select AI CLI:[/cyan]")
    console.print("  [1] Claude CLI")
    console.print("  [2] Gemini CLI")

    cli_choice = Prompt.ask(
        "Enter choice",
        choices=["1", "2"],
        default="1",
    )

    ai_cli = AICli.CLAUDE if cli_choice == "1" else AICli.GEMINI

    return ProjectInfo(
        name=name,
        vision=vision,
        domains=domains,
        ai_cli=ai_cli,
    )


def confirm_overwrite(file_name: str) -> bool:
    """
    确认是否覆盖已存在的文件。

    Args:
        file_name: 文件名

    Returns:
        bool: 是否覆盖
    """
    return Confirm.ask(
        f"[yellow]{file_name} already exists. Overwrite?[/yellow]",
        default=False,
    )
