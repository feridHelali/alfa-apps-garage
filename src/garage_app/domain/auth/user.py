from __future__ import annotations

from dataclasses import dataclass, field

from garage_app.domain.shared.aggregate_root import AggregateRoot


@dataclass
class User(AggregateRoot):
    username: str = ""
    password_hash: bytes = field(default=b"", repr=False)
    full_name: str = ""
    role: str = "technicien"
    is_active: bool = True
