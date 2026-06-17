from __future__ import annotations

from abc import abstractmethod

from garage_app.domain.societe.societe import Societe
from garage_app.domain.shared.repository import Repository


class SocieteRepository(Repository[Societe]):
    @abstractmethod
    def get_singleton(self) -> Societe | None: ...
