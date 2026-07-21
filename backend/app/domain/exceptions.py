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

class UserAlreadyExistsError(DomainException):
    pass

class AccountInactiveError(DomainException):
    pass

class InvalidTokenError(DomainException):
    pass

class PasswordMismatchError(DomainException):
    pass

class PasswordValidationError(DomainException):
    pass

class PasswordUpdateError(DomainException):
    pass

class TutorAssignmentRequiredError(DomainException):
    pass
