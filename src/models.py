# src/models.py

from __future__ import annotations
from typing import List, Optional, Union, Literal
from pathlib import Path
from pydantic import BaseModel, AnyUrl, Field, TypeAdapter


class Node(BaseModel):
    name: str
    description: Optional[str] = None
    node_type: str

    def save_json(self, path: Union[str, Path], indent: int = 2) -> None:
        """Save this model to a JSON file."""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.model_dump_json(indent=indent))

    @classmethod
    def load_json(cls, path: Union[str, Path]) -> Node:
        """Load a model from a JSON file."""
        with open(path, 'r', encoding='utf-8') as f:
            json_data = f.read()
        return adapter.validate_json(json_data)

class File(Node):
    node_type: Literal['file'] = 'file'
    file: Path

class Link(Node):
    node_type: Literal['link'] = 'link'
    url: AnyUrl

class Assignment(Node):
    node_type: Literal['assignment'] = 'assignment'
    url: Optional[str] = None
    due_date: Optional[str] = None

class Directory(Node):
    node_type: Literal['directory'] = 'directory'
    children: List[NodeType] = Field(default_factory=list)

NodeType = Union[Directory, File, Link, Assignment]

Directory.model_rebuild()

adapter = TypeAdapter(NodeType)