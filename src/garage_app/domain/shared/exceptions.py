class GarageAppError(Exception):
    """Base for all domain/application errors."""


class InvariantViolationError(GarageAppError):
    """An aggregate invariant was violated."""


class BusinessRuleError(GarageAppError):
    """A business rule was violated."""


class PermissionDeniedError(GarageAppError):
    """User lacks the required permission."""


class EntityNotFoundError(GarageAppError):
    """Entity not found in repository."""


class DuplicateEntityError(GarageAppError):
    """Entity with that identity already exists."""
