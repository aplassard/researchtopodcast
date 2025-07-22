"""Script formatting utilities for YAML output."""

from pathlib import Path
from typing import Dict, Any
from ruamel.yaml import YAML
from .persona import Script, ScriptMetadata, Host, Segment, PodcastMode
from datetime import datetime


class ScriptFormatter:
    """Formats scripts to YAML files."""
    
    def __init__(self):
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.width = 4096  # Prevent line wrapping
    
    def to_dict(self, script: Script) -> Dict[str, Any]:
        """Convert script to dictionary format."""
        return {
            'meta': {
                'title': script.meta.title,
                'duration_sec': script.meta.duration_sec,
                'created': script.meta.created.isoformat(),
                'mode': script.meta.mode.value,
                'source_document': script.meta.source_document
            },
            'hosts': [
                {
                    'name': host.name,
                    'persona': host.persona,
                    'voice_id': host.voice_id
                }
                for host in script.hosts
            ],
            'segments': [
                {
                    'speaker': segment.speaker,
                    'text': segment.text
                }
                for segment in script.segments
            ]
        }
    
    def to_yaml_string(self, script: Script) -> str:
        """Convert script to YAML string."""
        from io import StringIO
        
        stream = StringIO()
        self.yaml.dump(self.to_dict(script), stream)
        return stream.getvalue()
    
    def save_to_file(self, script: Script, file_path: Path) -> None:
        """Save script to YAML file."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            self.yaml.dump(self.to_dict(script), f)
    
    def load_from_file(self, file_path: Path) -> Script:
        """Load script from YAML file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = self.yaml.load(f)
        
        return self.from_dict(data)
    
    def from_dict(self, data: Dict[str, Any]) -> Script:
        """Convert dictionary to Script object."""
        # Parse metadata
        meta_data = data['meta']
        metadata = ScriptMetadata(
            title=meta_data['title'],
            duration_sec=meta_data['duration_sec'],
            created=datetime.fromisoformat(meta_data['created']),
            mode=PodcastMode(meta_data['mode']),
            source_document=meta_data.get('source_document')
        )
        
        # Parse hosts
        hosts = [
            Host(
                name=host_data['name'],
                persona=host_data['persona'],
                voice_id=host_data['voice_id']
            )
            for host_data in data['hosts']
        ]
        
        # Parse segments
        segments = [
            Segment(
                speaker=segment_data['speaker'],
                text=segment_data['text']
            )
            for segment_data in data['segments']
        ]
        
        return Script(meta=metadata, hosts=hosts, segments=segments)
