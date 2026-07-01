from dataclasses import dataclass


@dataclass
class ExampleConfig:
    """Minimal configuration placeholder for the boilerplate."""

    app_name: str = "Example App"
    debug: bool = False
    default_limit: int = 10
