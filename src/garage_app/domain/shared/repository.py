from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class Repository(ABC, Generic[T]):
    @abstractmethod
    def get_by_id(self, entity_id: uuid.UUID) -> T | None: ...

    @abstractmethod
    def save(self, entity: T) -> None: ...

    @abstractmethod
    def delete(self, entity_id: uuid.UUID) -> None: ...

    @abstractmethod
    def find_all(self) -> list[T]: ...
