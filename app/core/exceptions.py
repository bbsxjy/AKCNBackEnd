"""
Custom exception classes
"""


class ApplicationError(Exception):
    """Base application exception."""

    def __init__(self, message: str = None, details: dict = None):
        self.message = message or "An application error occurred"
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(ApplicationError):
    """Raised when validation fails."""

    def __init__(self, message: str = None, field: str = None, value: any = None):
        self.field = field
        self.value = value
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = value
        super().__init__(message or "Validation failed", details)


class NotFoundError(ApplicationError):
    """Raised when a resource is not found."""

    def __init__(self, resource_type: str = None, resource_id: any = None):
        self.resource_type = resource_type
        self.resource_id = resource_id

        if resource_type and resource_id:
            message = f"{resource_type} with ID '{resource_id}' not found"
            details = {"resource_type": resource_type, "resource_id": resource_id}
        else:
            message = "Resource not found"
            details = {}

        super().__init__(message, details)


class ConflictError(ApplicationError):
    """Raised when there's a conflict with existing data."""

    def __init__(self, message: str = None, resource_type: str = None, conflicting_value: any = None):
        self.resource_type = resource_type
        self.conflicting_value = conflicting_value
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if conflicting_value:
            details["conflicting_value"] = conflicting_value
        super().__init__(message or "Resource conflict", details)


class AuthenticationError(ApplicationError):
    """Raised when authentication fails."""

    def __init__(self, message: str = None):
        super().__init__(message or "Authentication failed")


class AuthorizationError(ApplicationError):
    """Raised when authorization fails."""

    def __init__(self, message: str = None, required_permission: str = None):
        self.required_permission = required_permission
        details = {}
        if required_permission:
            details["required_permission"] = required_permission
        super().__init__(message or "Access denied", details)


class ExternalServiceError(ApplicationError):
    """Raised when external service call fails."""

    def __init__(self, service_name: str = None, message: str = None, status_code: int = None):
        self.service_name = service_name
        self.status_code = status_code
        details = {}
        if service_name:
            details["service_name"] = service_name
        if status_code:
            details["status_code"] = status_code
        super().__init__(message or f"External service error: {service_name}", details)