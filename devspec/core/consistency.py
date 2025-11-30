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
    """

    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.console = Console()
        self.parser = MarkdownParser(root_path)
        self.indexer = SpecIndexer(root_path)

    def _determine_domain(self, node_id: str, node_data: Dict, index: Dict) -> str:
        """
        Infers the domain of a node.
        Priority:
        1. 'domain' field in YAML
        2. Prefix matching (dom_xxx -> dom_xxx)
        3. Parent feature's domain (for components)
        4. '_general' fallback
        """
        # 1. Explicit domain field
        if node_data and "domain" in node_data:
            return node_data["domain"]
        
        # 2. Self is a domain
        if node_id.startswith("dom_"):
            return node_id

        # 3. Fallback: Attempt to guess from prefix or context (Simplified for Phase 0)
        # Real logic would require a full graph traversal
        return "_general"

    def run_check(self):
        """
        Executes the consistency check, prints grouped reports, and generates the dashboard.
        """
        self.console.print("[bold blue]DevSpec Consistency Monitor (Domain View)[/bold blue]")
        self.console.print(f"Scanning root: {self.root_path}\n")

        # 1. Extract Intent & Structure
        prd_anchors = self.parser.parse_anchors(Path("PRD.md"))
        yaml_nodes = self.indexer.index_all()
        all_ids = set(prd_anchors.keys()) | set(yaml_nodes.keys())

        # 2. Group by Domain
        domain_groups = defaultdict(list)
        
        # Statistics
        stats = {"total": len(all_ids), "synced": 0, "issues": 0}

        for node_id in all_ids:
            in_prd = node_id in prd_anchors
            in_spec = node_id in yaml_nodes
            node_data = yaml_nodes.get(node_id, {})

            # Determine Domain grouping
            domain = self._determine_domain(node_id, node_data, yaml_nodes)
            
            # Calculate Status
            status_obj = self._calculate_status(node_id, in_prd, in_spec, prd_anchors.get(node_id), node_data)
            
            if status_obj["is_synced"]:
                stats["synced"] += 1
            else:
                stats["issues"] += 1

            domain_groups[domain].append(status_obj)

        # 3. Display Tables per Domain
        sorted_domains = sorted(domain_groups.keys())
        # Move _general to end
        if "_general" in sorted_domains:
            sorted_domains.remove("_general")
            sorted_domains.append("_general")

        for domain in sorted_domains:
            items = domain_groups[domain]
            # Sort items by ID
            items.sort(key=lambda x: x["id"])
            
            title = f"Domain: {domain}" if domain != "_general" else "General / Unassigned"
            table = Table(title=title, show_header=True, header_style="bold magenta")
            table.add_column("Node ID", style="cyan")
            table.add_column("Type", style="white")
            table.add_column("Spec Status", style="green")
            table.add_column("Impl Status", style="blue")

            for item in items:
                table.add_row(
                    item["id"],
                    item["type"],
                    Text(item["spec_status"], style=item["spec_style"]),
                    Text(item["impl_status"], style=item["impl_style"])
                )
            
            self.console.print(table)
            self.console.print("") # Empty line

        # 4. Summary & Dashboard
        self._print_summary(stats)
        self.generate_dashboard_file(stats, domain_groups, sorted_domains)

    def _calculate_status(self, node_id: str, in_prd: bool, in_spec: bool, prd_meta, spec_data) -> Dict:
        """Helper to calculate status strings and flags."""
        # Type Inference
        node_type = "Unknown"
        if node_id.startswith("dom_"): node_type = "Domain"
        elif node_id.startswith("feat_"): node_type = "Feature"
        elif node_id.startswith("comp_"): node_type = "Component"
        elif node_id.startswith("prod_"): node_type = "Product"
        elif node_id.startswith("des_"): node_type = "Design"
        elif node_id.startswith("sub_"): node_type = "Substrate"

        # Status Text
        prd_text = "✅ Defined" if in_prd else "❌ Missing"
        if in_prd: prd_text += f" (L{prd_meta.line_number})"
        
        spec_text = "✅ Implemented" if in_spec else "❌ Missing"
        if in_spec: 
            path = spec_data.get('_file_path', 'unknown')
            spec_text += f"\n({path})"

        # Markdown Text (Simplified)
        md_prd = f"✅ (L{prd_meta.line_number})" if in_prd else "❌"
        md_spec = f"✅ ({spec_data.get('_file_path','')})" if in_spec else "❌"

        # Spec Status (PRD vs YAML)
        spec_status = "Unknown"
        spec_style = "white"
        is_synced = False

        if in_prd and in_spec:
            spec_status = "Synced"
            spec_style = "green"
            is_synced = True
        elif in_prd and not in_spec:
            spec_status = "PRD_Only"
            spec_style = "yellow"
        elif not in_prd and in_spec:
            spec_status = "YAML_Only"
            spec_style = "red"

        # Impl Status (Feature vs Component)
        impl_status = "-"
        impl_style = "dim"
        
        if node_type == "Feature":
            realized_by = spec_data.get("realized_by", [])
            if realized_by:
                impl_status = f"Assigned ({len(realized_by)})"
                impl_style = "cyan"
            else:
                impl_status = "Unassigned"
                impl_style = "red"
        
        return {
            "id": node_id,
            "type": node_type,
            "spec_status": spec_status,
            "spec_style": spec_style,
            "impl_status": impl_status,
            "impl_style": impl_style,
            "is_synced": is_synced,
            "md_prd": md_prd,
            "md_spec": md_spec
        }

    def _print_summary(self, stats: Dict):
        self.console.print("[bold]Global Summary:[/bold]")
        self.console.print(f"Total Nodes: {stats['total']}")
        self.console.print(f"Synced: [green]{stats['synced']}[/green]")
        self.console.print(f"Issues: [red]{stats['issues']}[/red]")

    def generate_dashboard_file(self, stats: Dict, groups: Dict, sorted_domains: List[str]):
        output_path = self.root_path / "PRODUCT_DASHBOARD.md"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        progress = 0
        if stats['total'] > 0:
            progress = int((stats['synced'] / stats['total']) * 100)
        
        bar = '█' * int(progress / 5) + '░' * (20 - int(progress / 5))

        content = f"""# 📊 DevSpec Product Dashboard

> **Generated At**: {timestamp}
> **Phase**: 0 (Genesis Spec)

## 📈 Progress Overview

**Completion**: {progress}%
`[{bar}]`

| Metric | Count |
| :--- | :--- |
| **Total Nodes** | {stats['total']} |
| **Synced** | {stats['synced']} |
| **Issues** | {stats['issues']} |

## 📋 Detailed Status by Domain
"""
        
        for domain in sorted_domains:
            title = domain if domain != "_general" else "General / Unassigned"
            content += f"\n### {title}\n\n"
            content += "| Node ID | Type | Spec Status | Impl Status |\n"
            content += "| :--- | :--- | :--- | :--- |\n"
            
            for item in groups[domain]:
                # Spec Icon
                spec_icon = "🟢" if item['spec_status'] == "Synced" else "🔴" if item['spec_status'] == "YAML_Only" else "🟡"
                
                # Impl Icon
                impl_icon = ""
                if item['type'] == "Feature":
                    impl_icon = "🟢" if "Assigned" in item['impl_status'] else "🔴"
                
                content += f"| `{item['id']}` | {item['type']} | {spec_icon} {item['spec_status']} | {impl_icon} {item['impl_status']} |\n"

        content += "\n---\n*Auto-generated by DevSpec Consistency Monitor*\n"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.console.print(f"\n[green]Dashboard updated: {output_path}[/green]")

if __name__ == "__main__":
    monitor = ConsistencyMonitor(Path("."))
    monitor.run_check()
