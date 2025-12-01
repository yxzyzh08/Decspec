"""
DevSpec Validate PRD Command.

Component: comp_cli_validate_prd
Feature: feat_cli_command_structure

执行 PRD 格式校验，输出结果到控制台。
"""
from pathlib import Path

import typer
from rich.console import Console

from devspec.core.prd_validator import PRDValidator

console = Console()


def validate_prd(prd_path: Path = Path("PRD.md")) -> None:
    """执行 PRD 格式校验。

    Args:
        prd_path: PRD 文件路径，默认为当前目录的 PRD.md
    """
    console.print("[bold blue]DevSpec: Validating PRD format...[/bold blue]\n")

    # 检查文件是否存在
    if not prd_path.exists():
        console.print(f"[red]✗ {prd_path} not found[/red]")
        raise typer.Exit(1)

    # 创建校验器并执行校验
    validator = PRDValidator(prd_path)
    result = validator.validate()

    # 输出结果
    if result.errors:
        console.print(
            f"[red]✗ Validation failed with {len(result.errors)} error(s):[/red]"
        )
        for error in result.errors:
            console.print(f"  [red]•[/red] {error}")

        if result.warnings:
            console.print(
                f"\n[yellow]⚠ {len(result.warnings)} warning(s):[/yellow]"
            )
            for warning in result.warnings:
                console.print(f"  [yellow]•[/yellow] {warning}")

        raise typer.Exit(1)

    if result.warnings:
        console.print(
            f"[yellow]⚠ Validation passed with {len(result.warnings)} warning(s):[/yellow]"
        )
        for warning in result.warnings:
            console.print(f"  [yellow]•[/yellow] {warning}")
    else:
        console.print("[green]✓ PRD.md format is valid![/green]")
