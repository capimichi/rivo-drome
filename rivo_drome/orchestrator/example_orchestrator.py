from rivo_drome.generator.example_generator import ExampleGenerator
from rivo_drome.manager.example_manager import ExampleManager


class ExampleOrchestrator:
    """High-level flow combining generator and manager."""

    def __init__(self, generator: ExampleGenerator, manager: ExampleManager):
        self.generator = generator
        self.manager = manager

    def generate_and_store(self, title: str, description: str = ""):
        entity = self.generator.build(title, description)
        return self.manager.create(entity)
