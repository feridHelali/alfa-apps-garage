from __future__ import annotations

import uuid

from garage_app.application.decorators import require_permission
from garage_app.domain.auth.permission import Permission
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.planification.client import Client
from garage_app.domain.planification.repositories import ClientRepository, VehiculeRepository
from garage_app.domain.planification.vehicule import Vehicule
from garage_app.infrastructure.db.session import SessionFactory


class ClientService:
    def __init__(
        self, sf: SessionFactory, client_repo: ClientRepository, vehicule_repo: VehiculeRepository
    ) -> None:
        self._sf = sf
        self._clients = client_repo
        self._vehicules = vehicule_repo

    @require_permission(Permission.VIEW_CLIENTS)
    def list_clients(self, session: UserSession) -> list[Client]:
        with self._sf.get_session():
            return self._clients.find_all()

    @require_permission(Permission.MANAGE_CLIENTS)
    def create_client(self, session: UserSession, **kwargs) -> Client:  # type: ignore[misc]
        client = Client(**kwargs)
        with self._sf.get_session():
            self._clients.save(client)
        return client

    @require_permission(Permission.MANAGE_CLIENTS)
    def update_client(self, session: UserSession, client: Client) -> None:
        with self._sf.get_session():
            self._clients.save(client)

    @require_permission(Permission.VIEW_CLIENTS)
    def get_vehicules(self, session: UserSession, client_id: uuid.UUID) -> list[Vehicule]:
        with self._sf.get_session():
            return self._vehicules.find_by_client(client_id)

    @require_permission(Permission.MANAGE_CLIENTS)
    def add_vehicule(self, session: UserSession, vehicule: Vehicule) -> None:
        with self._sf.get_session():
            self._vehicules.save(vehicule)
