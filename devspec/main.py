"""
DevSpec CLI - 命令行入口点。

Usage:
    devspec init                   # 交互式初始化 .specgraph 目录结构
    devspec generate <feature_id>  # 生成 AI Context Prompt
    devspec sync                   # 同步 YAML 到 SQLite 数据库
    devspec tree                   # 显示项目全景视图
"""

from pathlib import Path

import pyperclip
import typer
from rich.console import Console

from devspec.context.builder import generate_context
from devspec.engine.loader import get_spec_paths
from devspec.engine.sync import run_sync
from devspec.engine.tree_view import print_tree
from devspec.init.collector import collect_project_info
from devspec.init.scaffold import (
    check_already_initialized,
    create_directory_structure,
    write_project_files,
)

app = typer.Typer(
    help="DevSpec - Self-bootstrapping development specification system.",
    no_args_is_help=True,
)
console = Console(force_terminal=True)


def get_project_root() -> Path:
    """获取项目根目录（当前工作目录）。"""
    return Path.cwd()


@app.command()
def init(
    force: bool = typer.Option(False, "--force", "-f", help="Force overwrite existing files"),
) -> None:
    """
    交互式初始化 .specgraph 目录结构。

    创建完整的 SpecGraph 目录层级，收集项目信息，生成 AI 协议文件。
    """
    root_dir = get_project_root()

    # 检查是否已初始化
    if check_already_initialized(root_dir) and not force:
        console.print(
            "[yellow]Project already initialized (.specgraph/product.yaml exists)[/yellow]"
        )
        console.print("Use --force to reinitialize.")
        raise typer.Exit(code=0)

    # 交互式收集项目信息
    info = collect_project_info()

    # 创建目录结构
    console.print(f"\n[blue]Creating .specgraph directory structure...[/blue]")
    spec_root = create_directory_structure(root_dir)

    # 生成文件
    console.print(f"\n[blue]Generating project files...[/blue]")
    write_project_files(root_dir, spec_root, info, force=force)

    # 初始化数据库
    console.print(f"\n[blue]Initializing database...[/blue]")
    stats = run_sync(root_dir, clean=True)
    console.print(f"  [green]Created:[/green] .specgraph/.runtime/index.db")

    # 完成提示
    console.print("\n[bold green]Success! Project initialized.[/bold green]")
    console.print("\nGenerated files:")
    console.print("  - .specgraph/product.yaml    (project metadata)")
    console.print("  - .specgraph/AGENT.md        (AI protocol guide)")
    from devspec.init.generator import get_cli_filename

    cli_file = get_cli_filename(info)
    console.print(f"  - {cli_file}                  (AI CLI instructions)")
    console.print("\nNext steps:")
    console.print("  1. Review and edit .specgraph/product.yaml")
    console.print("  2. Add feature specs in .specgraph/features/")
    console.print("  3. Run 'devspec generate <feature_id>' to build context")


@app.command()
def generate(
    feature_id: str = typer.Argument(..., help="Feature ID (e.g., feat_bootstrap)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Print prompt to console"),
) -> None:
    """
    根据 Feature ID 构建上下文，并复制 Prompt 到剪贴板。
    """
    root_dir = get_project_root()
    paths = get_spec_paths(root_dir)

    # 检查环境
    if not paths["root"].exists():
        console.print(
            f"[bold red]Critical Error: .specgraph directory not found at {paths['root']}[/bold red]"
        )
        console.print("Run 'devspec init' to create it.")
        raise typer.Exit(code=1)

    console.print(f"[blue]Bootstrapping Context for '{feature_id}'...[/blue]")

    try:
        prompt, _ = generate_context(root_dir, feature_id)
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)

    # 输出结果
    try:
        pyperclip.copy(prompt)
        token_est = len(prompt) // 4

        console.print("\n[bold green]Success! Prompt copied to clipboard.[/bold green]")
        console.print(f"   Size: {len(prompt)} chars (~{token_est} tokens)")
        console.print("\n[yellow]Action: Open your AI Chat (Cursor/Claude) and press Ctrl+V[/yellow]")

        if verbose:
            console.print("\n--- Prompt Preview ---")
            console.print(prompt[:500] + "\n... (truncated) ...")

    except Exception as e:
        console.print(f"\n[red]Clipboard failed: {e}[/red]")
        console.print("Dumping prompt to stdout instead:\n")
        console.print(prompt)


@app.command()
def sync(
    clean: bool = typer.Option(False, "--clean", "-c", help="Clean existing database before sync"),
) -> None:
    """
    同步 YAML 文件到 SQLite 数据库。

    遍历 .specgraph 目录中的所有 YAML 文件，解析并存储到数据库中，
    建立节点和边的关系索引。
    """
    root_dir = get_project_root()
    paths = get_spec_paths(root_dir)

    # 检查环境
    if not paths["root"].exists():
        console.print(
            f"[bold red]Critical Error: .specgraph directory not found at {paths['root']}[/bold red]"
        )
        console.print("Run 'devspec init' to create it.")
        raise typer.Exit(code=1)

    console.print("[blue]Syncing SpecGraph to SQLite...[/blue]")

    stats = run_sync(root_dir, clean=clean)

    console.print("\n[bold green]Sync complete![/bold green]")
    console.print(f"  Nodes created: {stats.nodes_created}")
    console.print(f"  Nodes updated: {stats.nodes_updated}")
    console.print(f"  Edges created: {stats.edges_created}")
    if stats.errors > 0:
        console.print(f"  [yellow]Errors: {stats.errors}[/yellow]")

    db_path = paths["root"] / ".runtime" / "index.db"
    console.print(f"\nDatabase: {db_path}")


@app.command()
def tree(
    components: bool = typer.Option(False, "--components", "-c", help="Show components"),
) -> None:
    """
    显示项目全景视图。

    以树形结构展示所有 Domain 和 Feature 的状态。
    """
    root_dir = get_project_root()
    paths = get_spec_paths(root_dir)

    # 检查环境
    if not paths["root"].exists():
        console.print(
            f"[bold red]Critical Error: .specgraph directory not found at {paths['root']}[/bold red]"
        )
        console.print("Run 'devspec init' to create it.")
        raise typer.Exit(code=1)

    print_tree(root_dir, show_components=components)


def main() -> None:
    """CLI 入口函数。"""
    app()


if __name__ == "__main__":
    main()
