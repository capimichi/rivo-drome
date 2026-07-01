from injector import inject

from rivo_drome.client.example_client import ExampleClient
from rivo_drome.model.example_model import ExampleModel


class ExampleService:
    """Service layer that wraps ExampleClient."""

    @inject
    def __init__(self, example_client: ExampleClient):
        self.example_client = example_client

    def get_example(self, title: str | None = None, message: str | None = None) -> ExampleModel:
        """Return the boilerplate example payload with optional overrides."""
        resolved_title = title or "Example"
        resolved_message = message or self.example_client.fetch_message()
        return ExampleModel(title=resolved_title, message=resolved_message)
