import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional

class SpecIndexer:
    """
    Scans the .specgraph directory to index all YAML definitions.
    Also extracts virtual nodes (like Domains defined inside product.yaml).
    """

    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.spec_dir = root_path / ".specgraph"

    def index_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Walks through .specgraph and loads all valid YAML files.
        Returns a dictionary: {node_id: node_data_dict}
        """
        if not self.spec_dir.exists():
            return {}

        index = {}

        # Walk through all subdirectories
        for file_path in self.spec_dir.rglob("*.yaml"):
            # Skip .runtime or hidden folders if necessary
            if ".runtime" in file_path.parts:
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    
                    if isinstance(data, dict) and "id" in data:
                        node_id = data["id"]
                        data["_file_path"] = str(file_path.relative_to(self.root_path))
                        index[node_id] = data

                        # Special handling for product.yaml to extract Domains
                        if "domains" in data and isinstance(data["domains"], list):
                            for dom in data["domains"]:
                                if "id" in dom:
                                    dom_id = dom["id"]
                                    # Create a virtual node for the domain
                                    index[dom_id] = {
                                        "id": dom_id,
                                        "type": "domain",
                                        "name": dom.get("name", dom_id),
                                        "description": dom.get("description", ""),
                                        "_file_path": data["_file_path"] + "#domains", # Virtual path
                                        "_is_virtual": True
                                    }
            except Exception as e:
                print(f"Warning: Failed to parse {file_path}: {e}")

        return index