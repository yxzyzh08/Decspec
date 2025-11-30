import re
from pathlib import Path
from typing import Dict, List, NamedTuple

class SectionMeta(NamedTuple):
    title: str
    anchor_id: str
    line_number: int

class MarkdownParser:
    """
    Parses Markdown files to extract structural anchors defined by the
    DevSpec 'Anchor Injection' principle: <!-- id: node_id -->
    """
    
    ANCHOR_PATTERN = re.compile(r'<!--\s*id:\s*([a-zA-Z0-9_]+)\s*-->')
    HEADER_PATTERN = re.compile(r'^(#+)\s+(.*)')

    def __init__(self, root_path: Path):
        self.root_path = root_path

    def parse_anchors(self, file_path: Path) -> Dict[str, SectionMeta]:
        """
        Scans a markdown file and returns a dictionary mapping anchor_ids to their metadata.
        """
        full_path = self.root_path / file_path
        if not full_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {full_path}")

        results = {}
        
        with open(full_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            # Check for anchor
            anchor_match = self.ANCHOR_PATTERN.search(line)
            if anchor_match:
                anchor_id = anchor_match.group(1)
                
                # Try to find the header title in the same line
                # (Usually the anchor is at the end of the header)
                header_match = self.HEADER_PATTERN.match(line)
                title = "Unknown Section"
                if header_match:
                    # Remove the anchor from the title for display
                    raw_title = header_match.group(2)
                    title = self.ANCHOR_PATTERN.sub('', raw_title).strip()
                
                results[anchor_id] = SectionMeta(
                    title=title,
                    anchor_id=anchor_id,
                    line_number=i + 1
                )

        return results
