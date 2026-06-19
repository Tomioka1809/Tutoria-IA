class DomainException(Exception):
    pass

class UserNotFoundError(DomainException):
    pass

class NotAuthorizedError(DomainException):
    pass

class ResourceNotFoundError(DomainException):
    pass

class InvalidCredentialsError(DomainException):
    pass
