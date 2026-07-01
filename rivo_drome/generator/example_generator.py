from rivo_drome.entity.example_entity import ExampleEntity
from rivo_drome.helper.example_helper import ExampleHelper


class ExampleGenerator:
    """Produces ExampleEntity instances with derived content."""

    def build(self, title: str, description: str = "") -> ExampleEntity:
        slug = ExampleHelper.slugify(title)
        full_description = description or f"Auto-generated description for {slug}"
        return ExampleEntity(title=title, description=full_description)
