from __future__ import annotations

from dataclasses import dataclass, field

from garage_app.domain.shared.entity import Entity
from garage_app.domain.shared.domain_event import DomainEvent


@dataclass
class AggregateRoot(Entity):
    _domain_events: list[DomainEvent] = field(default_factory=list, init=False, repr=False)

    def _raise_event(self, event: DomainEvent) -> None:
        self._domain_events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        events = list(self._domain_events)
        self._domain_events.clear()
        return events
