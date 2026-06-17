from __future__ import annotations

from collections import defaultdict
from typing import Callable, Type

from garage_app.domain.shared.domain_event import DomainEvent


class InMemoryEventBus:
    def __init__(self) -> None:
        self._handlers: dict[type, list[Callable]] = defaultdict(list)

    def subscribe(self, event_type: Type[DomainEvent], handler: Callable) -> None:
        self._handlers[event_type].append(handler)

    def publish(self, event: DomainEvent) -> None:
        for handler in self._handlers.get(type(event), []):
            handler(event)

    def publish_all(self, events: list[DomainEvent]) -> None:
        for event in events:
            self.publish(event)
