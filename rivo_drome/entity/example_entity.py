from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ExampleEntity:
    """Simple entity with an id and content fields."""

    title: str
    description: str = ""
    id: Optional[int] = field(default=None)
