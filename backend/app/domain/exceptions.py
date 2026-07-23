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

class StreakUnavailableForRoleError(DomainException):
    pass

class LLMServiceError(DomainException, RuntimeError):
    """Excepción base para errores del servicio LLM externo."""
    pass


class LLMAuthenticationError(LLMServiceError):
    """API Key inválida o error de autenticación con el servicio LLM."""
    pass

class LLMQuotaError(LLMServiceError):
    """Exceso de cuota o rate limit alcanzado en el servicio LLM."""
    pass

class LLMTimeoutError(LLMServiceError):
    """Timeout de comunicación con el servicio LLM."""
    pass

class LLMNetworkError(LLMServiceError):
    """Error de red o conectividad con el servicio LLM."""
    pass
