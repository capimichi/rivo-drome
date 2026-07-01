from rivo_drome.entity.example_entity import ExampleEntity


class ExampleMapper:
    """Converts ExampleEntity objects to and from dictionaries."""

    @staticmethod
    def to_dict(entity: ExampleEntity) -> dict:
        return {
            "id": entity.id,
            "title": entity.title,
            "description": entity.description,
        }

    @staticmethod
    def from_dict(payload: dict) -> ExampleEntity:
        return ExampleEntity(
            id=payload.get("id"),
            title=payload.get("title", "Example"),
            description=payload.get("description", ""),
        )
