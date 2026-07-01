from rivo_drome.entity.example_entity import ExampleEntity
from rivo_drome.helper.example_helper import ExampleHelper


class ExampleFactory:
    """Factory that instantiates ExampleEntity with sensible defaults."""

    @staticmethod
    def create(title: str, description: str = "") -> ExampleEntity:
        normalized_title = title.strip() or "Example"
        normalized_description = description.strip() if description else ""
        return ExampleEntity(
            title=normalized_title,
            description=normalized_description or f"Factory-created {ExampleHelper.slugify(normalized_title)}",
        )
