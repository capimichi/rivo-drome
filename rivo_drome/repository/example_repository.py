from typing import List, Optional

from rivo_drome.entity.example_entity import ExampleEntity
from rivo_drome.repository.abstract_example_repository import AbstractExampleRepository


class ExampleRepository(AbstractExampleRepository):
    """In-memory implementation suitable for boilerplate demos."""

    def __init__(self):
        self._storage: List[ExampleEntity] = []
        self._next_id: int = 1

    def save(self, entity: ExampleEntity) -> ExampleEntity:
        if entity.id is None:
            entity.id = self._next_id
            self._next_id += 1
            self._storage.append(entity)
        else:
            self._storage = [
                entity if item.id == entity.id else item for item in self._storage
            ]
        return entity

    def get_by_id(self, entity_id: int) -> Optional[ExampleEntity]:
        return next((item for item in self._storage if item.id == entity_id), None)

    def list_all(self) -> List[ExampleEntity]:
        return list(self._storage)
