class DomainError(Exception):
    """Base class for safe domain failures."""


class ConflictError(DomainError):
    pass


class ForbiddenError(DomainError):
    pass


class NotFoundError(DomainError):
    pass


class AuthenticationError(DomainError):
    pass


class UnsupportedContentError(DomainError):
    pass


class ProviderUnavailableError(DomainError):
    pass


class GenerationError(DomainError):
    pass
