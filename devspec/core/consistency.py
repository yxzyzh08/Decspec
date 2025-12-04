"""
Consistency Monitor - PRD-YAML consistency checking and YAML schema validation.

This module provides consistency checking between PRD and YAML files,
as well as YAML schema validation against sub_meta_schema.yaml definitions.

Component: comp_consistency_monitor
Feature: feat_consistency_monitor
"""

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
from devspec.core.yaml_schema_validator import (
    YAMLSchemaValidator,
    SchemaValidationReport,
    ValidationResult,
)

# Force UTF-8 for Windows consoles
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')


class ConsistencyMonitor:
    """
    Orchestrates the comparison between PRD Intent and Spec Structure.
    Validates YAML files against schema definitions.
    Generates a layered dashboard with separate tables for Schema, Domain/Design, Features, and Components.
    """

    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.console = Console()
        self.parser = MarkdownParser(root_path)
        self.indexer = SpecIndexer(root_path)
        self.schema_validator = YAMLSchemaValidator(root_path / ".specgraph")

    def run_check(self):
        """
        Executes the consistency check, prints layered reports, and generates the dashboard.
        """
        self.console.print("[bold blue]DevSpec Consistency Monitor (Layered View)[/bold blue]")
        self.console.print(f"Scanning root: {self.root_path}\n")

        # 1. Schema Validation Phase (NEW)
        self.console.print("[bold cyan]Phase 1: YAML Schema Validation[/bold cyan]")
        schema_report = self.schema_validator.validate_all()
        self._display_schema_validation_summary(schema_report)

        # 2. Extract Intent & Structure
        self.console.print("\n[bold cyan]Phase 2: PRD-YAML Consistency Check[/bold cyan]")
        prd_anchors = self.parser.parse_anchors(Path("PRD.md"))
        yaml_nodes = self.indexer.index_all()
        all_ids = set(prd_anchors.keys()) | set(yaml_nodes.keys())

        # 3. Categorize nodes by type
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

        # 4. Calculate statistics (including schema compliance)
        stats = self._calculate_stats(design_nodes, feature_nodes, component_nodes, schema_report)

        # 5. Display Tables
        self._display_design_table(design_nodes)
        self._display_feature_table(feature_nodes)
        self._display_component_table(component_nodes)

        # 6. Summary & Dashboard
        self._print_summary(stats)
        self.generate_dashboard_file(stats, design_nodes, feature_nodes, component_nodes, schema_report)

    def run_schema_validation(self) -> SchemaValidationReport:
        """
        Run only YAML schema validation.

        Returns:
            SchemaValidationReport: The validation report
        """
        return self.schema_validator.validate_all()

    def _display_schema_validation_summary(self, report: SchemaValidationReport):
        """Display schema validation summary and errors."""
        # Summary
        valid_pct = int((report.valid_count / report.total_files * 100)) if report.total_files > 0 else 0

        self.console.print(f"Total files: {report.total_files}")
        self.console.print(f"Valid: [green]{report.valid_count}[/green] ({valid_pct}%)")
        self.console.print(f"Invalid: [red]{report.invalid_count}[/red]")
        self.console.print(f"With warnings: [yellow]{report.warning_count}[/yellow]")

        # Display errors if any
        if report.invalid_count > 0:
            self.console.print("\n[bold red]Schema Validation Errors:[/bold red]")
            for result in report.results:
                if not result.is_valid:
                    self.console.print(f"\n  [red]✗[/red] {result.file_path} ({result.node_type})")
                    for error in result.errors:
                        self.console.print(f"    - {error.field}: {error.message}")

        # Display warnings if any
        if report.warning_count > 0:
            self.console.print("\n[bold yellow]Schema Validation Warnings:[/bold yellow]")
            for result in report.results:
                if result.warnings:
                    self.console.print(f"\n  [yellow]⚠[/yellow] {result.file_path} ({result.node_type})")
                    for warning in result.warnings:
                        self.console.print(f"    - {warning.field}: {warning.message}")

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

    def _calculate_stats(self, design_nodes: List, feature_nodes: List,
                         component_nodes: List, schema_report: SchemaValidationReport) -> Dict:
        """Calculate multi-dimensional statistics including schema compliance."""
        all_nodes = design_nodes + feature_nodes + component_nodes

        # Spec Sync stats
        total_nodes = len(all_nodes)
        spec_synced = sum(1 for n in all_nodes if n["spec_synced"])

        # Feature Assignment stats
        total_features = len(feature_nodes)
        features_assigned = sum(1 for f in feature_nodes if f["assignment_count"] > 0)

        # Schema Compliance stats (NEW)
        schema_total = schema_report.total_files
        schema_valid = schema_report.valid_count

        # Calculate percentages
        spec_sync_pct = int((spec_synced / total_nodes * 100)) if total_nodes > 0 else 0
        feature_assign_pct = int((features_assigned / total_features * 100)) if total_features > 0 else 0
        schema_compliance_pct = int((schema_valid / schema_total * 100)) if schema_total > 0 else 0

        # Overall progress: Spec Sync (30%) + Feature Assignment (40%) + Schema Compliance (30%)
        overall_pct = int(spec_sync_pct * 0.3 + feature_assign_pct * 0.4 + schema_compliance_pct * 0.3)

        return {
            "total_nodes": total_nodes,
            "spec_synced": spec_synced,
            "spec_sync_pct": spec_sync_pct,
            "total_features": total_features,
            "features_assigned": features_assigned,
            "feature_assign_pct": feature_assign_pct,
            "schema_total": schema_total,
            "schema_valid": schema_valid,
            "schema_invalid": schema_report.invalid_count,
            "schema_warnings": schema_report.warning_count,
            "schema_compliance_pct": schema_compliance_pct,
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
        self.console.print("\n[bold]Progress Summary:[/bold]")
        self.console.print(f"Schema Compliance: [green]{stats['schema_compliance_pct']}%[/green] ({stats['schema_valid']}/{stats['schema_total']})")
        self.console.print(f"Spec Sync: [green]{stats['spec_sync_pct']}%[/green] ({stats['spec_synced']}/{stats['total_nodes']})")
        self.console.print(f"Feature Assignment: [cyan]{stats['feature_assign_pct']}%[/cyan] ({stats['features_assigned']}/{stats['total_features']})")
        self.console.print(f"Overall: [bold yellow]{stats['overall_pct']}%[/bold yellow] (Schema 30% + Spec 30% + Assignment 40%)")

    def generate_dashboard_file(self, stats: Dict, design_nodes: List, feature_nodes: List,
                                component_nodes: List, schema_report: SchemaValidationReport):
        output_path = self.root_path / "PRODUCT_DASHBOARD.md"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Progress bars
        schema_bar = self._make_progress_bar(stats['schema_compliance_pct'])
        spec_bar = self._make_progress_bar(stats['spec_sync_pct'])
        assign_bar = self._make_progress_bar(stats['feature_assign_pct'])
        overall_bar = self._make_progress_bar(stats['overall_pct'])

        content = f"""# DevSpec Product Dashboard

> **Generated At**: {timestamp}
> **Phase**: 0 (Genesis Spec)

## Progress Overview

| Dimension | Progress | Detail |
| :--- | :--- | :--- |
| **Schema Compliance** | `[{schema_bar}]` {stats['schema_compliance_pct']}% | {stats['schema_valid']}/{stats['schema_total']} files |
| **Spec Sync** | `[{spec_bar}]` {stats['spec_sync_pct']}% | {stats['spec_synced']}/{stats['total_nodes']} nodes |
| **Feature Assignment** | `[{assign_bar}]` {stats['feature_assign_pct']}% | {stats['features_assigned']}/{stats['total_features']} features |
| **Overall** | `[{overall_bar}]` {stats['overall_pct']}% | Weighted: Schema(30%) + Spec(30%) + Assignment(40%) |

---

## Schema Validation Results

| File | Type | Status | Issues |
| :--- | :--- | :--- | :--- |
"""
        for result in schema_report.results:
            status_icon = "Valid" if result.is_valid else "Invalid"
            status_emoji = "O" if result.is_valid else "X"
            if result.is_valid and result.warnings:
                status_icon = "Warnings"
                status_emoji = "!"

            issues = []
            if result.errors:
                issues.extend([f"[E] {e.field}: {e.message}" for e in result.errors[:2]])
            if result.warnings:
                issues.extend([f"[W] {w.field}: {w.message}" for w in result.warnings[:2]])
            issue_str = "; ".join(issues) if issues else "-"

            content += f"| `{result.file_path}` | {result.node_type} | {status_emoji} {status_icon} | {issue_str} |\n"

        content += f"""
---

## System Design (Domain & Design)

| Node ID | Type | Spec Status |
| :--- | :--- | :--- |
"""
        for item in design_nodes:
            spec_icon = "O" if item['spec_synced'] else "!" if "PRD" in item['spec_status'] else "X"
            content += f"| `{item['id']}` | {item['type']} | {spec_icon} {item['spec_status']} |\n"

        content += f"""
---

## Features

| Node ID | Domain | Spec Status | Assignment Status |
| :--- | :--- | :--- | :--- |
"""
        for item in feature_nodes:
            spec_icon = "O" if item['spec_synced'] else "!" if "PRD" in item['spec_status'] else "X"
            assign_icon = "O" if item['assignment_count'] > 0 else "X"
            content += f"| `{item['id']}` | {item['domain']} | {spec_icon} {item['spec_status']} | {assign_icon} {item['assignment_status']} |\n"

        content += f"""
---

## Components

| Node ID | Parent Feature | Spec Status |
| :--- | :--- | :--- |
"""
        for item in component_nodes:
            spec_icon = "O" if item['spec_synced'] else "!" if "PRD" in item['spec_status'] else "X"
            content += f"| `{item['id']}` | {item['parent_features']} | {spec_icon} {item['spec_status']} |\n"

        content += "\n---\n*Auto-generated by DevSpec Consistency Monitor*\n"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        self.console.print(f"\n[green]Dashboard updated: {output_path}[/green]")

    def _make_progress_bar(self, percentage: int) -> str:
        """Create a text progress bar."""
        filled = int(percentage / 5)
        empty = 20 - filled
        return '#' * filled + '-' * empty


if __name__ == "__main__":
    monitor = ConsistencyMonitor(Path("."))
    monitor.run_check()
