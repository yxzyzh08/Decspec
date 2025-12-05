"""
Frontend Component Library - CLI Commands
Part of comp_frontend_component_library
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .component_index import ComponentIndex, ComponentIndexError
from .component_registrar import ComponentRegistrar, ComponentRegistrarError
from .component_validator import ComponentValidator
from .usage_statistics import UsageStatistics

frontend_app = typer.Typer(name="frontend", help="Frontend component library management")
console = Console()


def get_default_root() -> Path:
    """获取默认组件库根目录"""
    return Path.cwd() / "templates" / "components"


def get_default_templates() -> Path:
    """获取默认模板根目录"""
    return Path.cwd() / "templates"


@frontend_app.command("register")
def register_cmd(
    category: str = typer.Argument(..., help="组件分类 (如 cards, badges, forms)"),
    name: str = typer.Argument(..., help="组件名称 (如 domain, status)"),
    desc: str = typer.Option(
        "",
        "--desc",
        "-d",
        help="组件描述",
    ),
    root: Optional[Path] = typer.Option(
        None,
        "--root",
        "-r",
        help="组件库根目录 (默认: templates/components/)",
    ),
) -> None:
    """注册新组件 (创建 MD 文档)

    遵循 Spec-First 原则：必须先注册（创建 MD 文档）再编码（写 HTML）
    """
    root_path = root or get_default_root()

    try:
        registrar = ComponentRegistrar(root_path)
        md_path = registrar.register(category, name, desc or f"{category}/{name} 组件")

        component_id = f"comp_{category}_{name}"
        console.print(f"\n[green]✓ 组件已注册:[/green] {component_id}")
        console.print(f"  MD 文档: {md_path}")
        console.print("\n[cyan]下一步:[/cyan]")
        console.print("  1. 编辑 MD 文档完善设计规范")
        console.print(f"  2. 创建 HTML 模板: {root_path}/{category}/{name}.html")
        console.print("  3. 运行 [bold]devspec frontend check[/bold] 验证一致性")

    except ComponentRegistrarError as e:
        console.print(f"[red]错误:[/red] {e}")
        raise typer.Exit(1)


@frontend_app.command("list")
def list_cmd(
    root: Optional[Path] = typer.Option(
        None,
        "--root",
        "-r",
        help="组件库根目录 (默认: templates/components/)",
    ),
    search: Optional[str] = typer.Option(
        None,
        "--search",
        "-s",
        help="搜索关键词",
    ),
) -> None:
    """列出所有已注册的组件"""
    root_path = root or get_default_root()

    try:
        index = ComponentIndex(root_path)
    except ComponentIndexError as e:
        console.print(f"[red]错误:[/red] {e}")
        raise typer.Exit(1)

    if search:
        components = index.search(search)
        console.print(f"搜索 '{search}' 的结果:")
    else:
        components = index.list_components()

    if not components:
        console.print("[yellow]未找到组件[/yellow]")
        return

    table = Table(title="Frontend Components")
    table.add_column("ID", style="cyan")
    table.add_column("Category", style="blue")
    table.add_column("Status", style="magenta")
    table.add_column("Description")

    for comp in components:
        # 根据状态显示不同颜色
        status_display = comp.status
        if comp.status == "registered":
            status_display = f"[yellow]{comp.status}[/yellow]"
        elif comp.status == "implemented":
            status_display = f"[blue]{comp.status}[/blue]"
        elif comp.status == "verified":
            status_display = f"[green]{comp.status}[/green]"

        table.add_row(comp.id, comp.category, status_display, comp.desc)

    console.print(table)
    console.print(f"\n共 {len(components)} 个组件")


@frontend_app.command("check")
def check_cmd(
    root: Optional[Path] = typer.Option(
        None,
        "--root",
        "-r",
        help="组件库根目录 (默认: templates/components/)",
    ),
) -> None:
    """检查组件库完整性"""
    root_path = root or get_default_root()

    try:
        index = ComponentIndex(root_path)
    except ComponentIndexError as e:
        console.print(f"[red]错误:[/red] {e}")
        raise typer.Exit(1)

    validator = ComponentValidator(index, root_path)
    result = validator.validate_all()

    # 显示错误
    if result.errors:
        console.print("\n[red]错误:[/red]")
        for error in result.errors:
            console.print(f"  • {error}")

    # 显示警告
    if result.warnings:
        console.print("\n[yellow]警告:[/yellow]")
        for warning in result.warnings:
            console.print(f"  • {warning}")

    # 显示结果摘要
    if result.is_valid:
        if not result.warnings:
            console.print("\n[green]✓ 组件库验证通过[/green]")
        else:
            console.print(
                f"\n[green]✓ 组件库验证通过[/green] (有 {len(result.warnings)} 个警告)"
            )
    else:
        console.print(
            f"\n[red]✗ 组件库验证失败[/red] ({len(result.errors)} 个错误, {len(result.warnings)} 个警告)"
        )
        raise typer.Exit(1)


@frontend_app.command("stats")
def stats_cmd(
    root: Optional[Path] = typer.Option(
        None,
        "--root",
        "-r",
        help="组件库根目录 (默认: templates/components/)",
    ),
    templates: Optional[Path] = typer.Option(
        None,
        "--templates",
        "-t",
        help="模板根目录 (默认: templates/)",
    ),
) -> None:
    """显示组件使用统计"""
    root_path = root or get_default_root()
    templates_path = templates or get_default_templates()

    try:
        index = ComponentIndex(root_path)
    except ComponentIndexError as e:
        console.print(f"[red]错误:[/red] {e}")
        raise typer.Exit(1)

    stats = UsageStatistics(index, templates_path)
    usage_count = stats.analyze()

    if not usage_count:
        console.print("[yellow]未找到组件[/yellow]")
        return

    table = Table(title="Component Usage Statistics")
    table.add_column("Component", style="cyan")
    table.add_column("Usage Count", justify="right")

    # 按使用次数排序
    sorted_items = sorted(usage_count.items(), key=lambda x: x[1], reverse=True)

    for comp_id, count in sorted_items:
        if count == 0:
            table.add_row(comp_id, f"[red]{count}[/red]")
        else:
            table.add_row(comp_id, f"[green]{count}[/green]")

    console.print(table)

    # 显示未使用组件
    unused = stats.get_unused()
    if unused:
        console.print(f"\n[yellow]未使用的组件 ({len(unused)}):[/yellow]")
        for comp_id in unused:
            console.print(f"  • {comp_id}")
