from pathlib import Path
from typing import Dict, List, Set, Optional
import datetime
import sys
from collections import defaultdict
from rich.console import Console
from rich.table import Table
from rich.text import Text

from devspec.core.markdown_parser import MarkdownParser
from devspec.core.spec_indexer import SpecIndexer

# Force UTF-8 for Windows consoles
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')


class ConsistencyMonitor:
    """
    Orchestrates the comparison between PRD Intent and Spec Structure.
    Generates a layered dashboard with separate tables for Domain/Design, Features, and Components.
    """

    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.console = Console()
        self.parser = MarkdownParser(root_path)
        self.indexer = SpecIndexer(root_path)

    def run_check(self):
        """
        Executes the consistency check, prints layered reports, and generates the dashboard.
        """
        self.console.print("[bold blue]DevSpec Consistency Monitor (Layered View)[/bold blue]")
        self.console.print(f"Scanning root: {self.root_path}\n")

        # 1. Extract Intent & Structure
        prd_anchors = self.parser.parse_anchors(Path("PRD.md"))
        yaml_nodes = self.indexer.index_all()
        all_ids = set(prd_anchors.keys()) | set(yaml_nodes.keys())

        # 2. Categorize nodes by type
        design_nodes = []  # Domain, Design, Product, Substrate
        feature_nodes = []  # Features
        component_nodes = []  # Components

        # Build reverse index: component_id -> list of feature_ids
        component_to_features = self._build_component_feature_map(yaml_nodes)

        for node_id in all_ids:
            in_prd = node_id in prd_anchors
            in_spec = node_id in yaml_nodes
            node_data = yaml_nodes.get(node_id, {})
            prd_meta = prd_anchors.get(node_id)

            node_info = self._build_node_info(node_id, in_prd, in_spec, prd_meta, node_data, component_to_features)

            # Categorize by type
            if node_info["type"] in ("Domain", "Design", "Product", "Substrate"):
                design_nodes.append(node_info)
            elif node_info["type"] == "Feature":
                feature_nodes.append(node_info)
            elif node_info["type"] == "Component":
                component_nodes.append(node_info)
            else:
                design_nodes.append(node_info)  # Unknown goes to design

        # Sort all lists
        design_nodes.sort(key=lambda x: x["id"])
        feature_nodes.sort(key=lambda x: x["id"])
        component_nodes.sort(key=lambda x: x["id"])

        # 3. Calculate statistics
        stats = self._calculate_stats(design_nodes, feature_nodes, component_nodes)

        # 4. Display Tables
        self._display_design_table(design_nodes)
        self._display_feature_table(feature_nodes)
        self._display_component_table(component_nodes)

        # 5. Summary & Dashboard
        self._print_summary(stats)
        self.generate_dashboard_file(stats, design_nodes, feature_nodes, component_nodes)

    def _build_component_feature_map(self, yaml_nodes: Dict) -> Dict[str, List[str]]:
        """Build reverse index from component_id to feature_ids."""
        comp_to_feat = defaultdict(list)
        for node_id, node_data in yaml_nodes.items():
            if node_id.startswith("feat_"):
                realized_by = node_data.get("realized_by", [])
                if realized_by:
                    for comp_id in realized_by:
                        comp_to_feat[comp_id].append(node_id)
        return comp_to_feat

    def _build_node_info(self, node_id: str, in_prd: bool, in_spec: bool,
                         prd_meta, node_data: Dict, comp_to_feat: Dict) -> Dict:
        """Build comprehensive node information."""
        # Type Inference
        node_type = "Unknown"
        if node_id.startswith("dom_"): node_type = "Domain"
        elif node_id.startswith("feat_"): node_type = "Feature"
        elif node_id.startswith("comp_"): node_type = "Component"
        elif node_id.startswith("prod_"): node_type = "Product"
        elif node_id.startswith("des_"): node_type = "Design"
        elif node_id.startswith("sub_"): node_type = "Substrate"

        # Spec Status (PRD vs YAML)
        spec_status = "Unknown"
        spec_synced = False
        if in_prd and in_spec:
            spec_status = "Synced"
            spec_synced = True
        elif in_prd and not in_spec:
            spec_status = "PRD Only"
        elif not in_prd and in_spec:
            spec_status = "YAML Only"

        # Domain (for Features)
        domain = node_data.get("domain", "-")

        # Assignment Status (for Features)
        assignment_status = "-"
        assignment_count = 0
        if node_type == "Feature":
            realized_by = node_data.get("realized_by", [])
            if realized_by:
                assignment_status = f"Assigned ({len(realized_by)})"
                assignment_count = len(realized_by)
            else:
                assignment_status = "Unassigned"

        # Parent Feature (for Components)
        parent_features = comp_to_feat.get(node_id, [])
        parent_feature_str = ", ".join(parent_features) if parent_features else "-"

        return {
            "id": node_id,
            "type": node_type,
            "domain": domain,
            "spec_status": spec_status,
            "spec_synced": spec_synced,
            "assignment_status": assignment_status,
            "assignment_count": assignment_count,
            "parent_features": parent_feature_str,
        }

    def _calculate_stats(self, design_nodes: List, feature_nodes: List, component_nodes: List) -> Dict:
        """Calculate multi-dimensional statistics."""
        all_nodes = design_nodes + feature_nodes + component_nodes

        # Spec Sync stats
        total_nodes = len(all_nodes)
        spec_synced = sum(1 for n in all_nodes if n["spec_synced"])

        # Feature Assignment stats
        total_features = len(feature_nodes)
        features_assigned = sum(1 for f in feature_nodes if f["assignment_count"] > 0)

        # Calculate percentages
        spec_sync_pct = int((spec_synced / total_nodes * 100)) if total_nodes > 0 else 0
        feature_assign_pct = int((features_assigned / total_features * 100)) if total_features > 0 else 0

        # Overall progress: Spec Sync (40%) + Feature Assignment (60%)
        overall_pct = int(spec_sync_pct * 0.4 + feature_assign_pct * 0.6)

        return {
            "total_nodes": total_nodes,
            "spec_synced": spec_synced,
            "spec_sync_pct": spec_sync_pct,
            "total_features": total_features,
            "features_assigned": features_assigned,
            "feature_assign_pct": feature_assign_pct,
            "overall_pct": overall_pct,
            "design_count": len(design_nodes),
            "component_count": len(component_nodes),
        }

    def _display_design_table(self, nodes: List[Dict]):
        """Display System Design table (Domain, Design, Product, Substrate)."""
        table = Table(title="System Design (Domain & Design)", show_header=True, header_style="bold magenta")
        table.add_column("Node ID", style="cyan")
        table.add_column("Type", style="white")
        table.add_column("Spec Status", style="green")

        for item in nodes:
            spec_style = "green" if item["spec_synced"] else "yellow" if "PRD" in item["spec_status"] else "red"
            table.add_row(
                item["id"],
                item["type"],
                Text(item["spec_status"], style=spec_style),
            )

        self.console.print(table)
        self.console.print("")

    def _display_feature_table(self, nodes: List[Dict]):
        """Display Features table with Spec Status and Assignment Status."""
        table = Table(title="Features", show_header=True, header_style="bold magenta")
        table.add_column("Node ID", style="cyan")
        table.add_column("Domain", style="white")
        table.add_column("Spec Status", style="green")
        table.add_column("Assignment Status", style="blue")

        for item in nodes:
            spec_style = "green" if item["spec_synced"] else "yellow" if "PRD" in item["spec_status"] else "red"
            assign_style = "cyan" if item["assignment_count"] > 0 else "red"
            table.add_row(
                item["id"],
                item["domain"],
                Text(item["spec_status"], style=spec_style),
                Text(item["assignment_status"], style=assign_style),
            )

        self.console.print(table)
        self.console.print("")

    def _display_component_table(self, nodes: List[Dict]):
        """Display Components table with parent Feature reference."""
        table = Table(title="Components", show_header=True, header_style="bold magenta")
        table.add_column("Node ID", style="cyan")
        table.add_column("Parent Feature", style="white")
        table.add_column("Spec Status", style="green")

        for item in nodes:
            spec_style = "green" if item["spec_synced"] else "yellow" if "PRD" in item["spec_status"] else "red"
            table.add_row(
                item["id"],
                item["parent_features"],
                Text(item["spec_status"], style=spec_style),
            )

        self.console.print(table)
        self.console.print("")

    def _print_summary(self, stats: Dict):
        self.console.print("[bold]Progress Summary:[/bold]")
        self.console.print(f"Spec Sync: [green]{stats['spec_sync_pct']}%[/green] ({stats['spec_synced']}/{stats['total_nodes']})")
        self.console.print(f"Feature Assignment: [cyan]{stats['feature_assign_pct']}%[/cyan] ({stats['features_assigned']}/{stats['total_features']})")
        self.console.print(f"Overall: [bold yellow]{stats['overall_pct']}%[/bold yellow]")

    def generate_dashboard_file(self, stats: Dict, design_nodes: List, feature_nodes: List, component_nodes: List):
        output_path = self.root_path / "PRODUCT_DASHBOARD.md"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Progress bars
        spec_bar = '█' * int(stats['spec_sync_pct'] / 5) + '░' * (20 - int(stats['spec_sync_pct'] / 5))
        assign_bar = '█' * int(stats['feature_assign_pct'] / 5) + '░' * (20 - int(stats['feature_assign_pct'] / 5))
        overall_bar = '█' * int(stats['overall_pct'] / 5) + '░' * (20 - int(stats['overall_pct'] / 5))

        content = f"""# 📊 DevSpec Product Dashboard

> **Generated At**: {timestamp}
> **Phase**: 0 (Genesis Spec)

## 📈 Progress Overview

| Dimension | Progress | Detail |
| :--- | :--- | :--- |
| **Spec Sync** | `[{spec_bar}]` {stats['spec_sync_pct']}% | {stats['spec_synced']}/{stats['total_nodes']} nodes |
| **Feature Assignment** | `[{assign_bar}]` {stats['feature_assign_pct']}% | {stats['features_assigned']}/{stats['total_features']} features |
| **Overall** | `[{overall_bar}]` {stats['overall_pct']}% | Weighted: Spec(40%) + Assignment(60%) |

---

## 📐 System Design (Domain & Design)

| Node ID | Type | Spec Status |
| :--- | :--- | :--- |
"""
        for item in design_nodes:
            spec_icon = "🟢" if item['spec_synced'] else "🟡" if "PRD" in item['spec_status'] else "🔴"
            content += f"| `{item['id']}` | {item['type']} | {spec_icon} {item['spec_status']} |\n"

        content += f"""
---

## 🎯 Features

| Node ID | Domain | Spec Status | Assignment Status |
| :--- | :--- | :--- | :--- |
"""
        for item in feature_nodes:
            spec_icon = "🟢" if item['spec_synced'] else "🟡" if "PRD" in item['spec_status'] else "🔴"
            assign_icon = "🟢" if item['assignment_count'] > 0 else "🔴"
            content += f"| `{item['id']}` | {item['domain']} | {spec_icon} {item['spec_status']} | {assign_icon} {item['assignment_status']} |\n"

        content += f"""
---

## 🔧 Components

| Node ID | Parent Feature | Spec Status |
| :--- | :--- | :--- |
"""
        for item in component_nodes:
            spec_icon = "🟢" if item['spec_synced'] else "🟡" if "PRD" in item['spec_status'] else "🔴"
            content += f"| `{item['id']}` | {item['parent_features']} | {spec_icon} {item['spec_status']} |\n"

        content += "\n---\n*Auto-generated by DevSpec Consistency Monitor*\n"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        self.console.print(f"\n[green]Dashboard updated: {output_path}[/green]")


if __name__ == "__main__":
    monitor = ConsistencyMonitor(Path("."))
    monitor.run_check()
