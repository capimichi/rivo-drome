from abc import ABC, abstractmethod
from typing import List, Optional

from rivo_drome.entity.example_entity import ExampleEntity


class AbstractExampleRepository(ABC):
    """Abstract contract for storing and retrieving ExampleEntity instances."""

    @abstractmethod
    def save(self, entity: ExampleEntity) -> ExampleEntity:
        """Persist the entity and return it."""

    @abstractmethod
    def get_by_id(self, entity_id: int) -> Optional[ExampleEntity]:
        """Return one entity by id, if any."""

    @abstractmethod
    def list_all(self) -> List[ExampleEntity]:
        """Return all stored entities."""
