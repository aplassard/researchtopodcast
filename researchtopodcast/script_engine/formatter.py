"""Script formatting utilities."""

from typing import Dict, Any
from pathlib import Path
from ruamel.yaml import YAML


class ScriptFormatter:
    """Formats scripts to .podcast.yaml files."""
    
    def __init__(self):
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.width = 4096
    
    def save_script(self, script_data: Dict[str, Any], output_path: Path) -> None:
        """Save script data to a .podcast.yaml file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            self.yaml.dump(script_data, f)
    
    def load_script(self, script_path: Path) -> Dict[str, Any]:
        """Load script data from a .podcast.yaml file."""
        with open(script_path, 'r', encoding='utf-8') as f:
            return self.yaml.load(f)
