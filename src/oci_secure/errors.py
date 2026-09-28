class OciSecureError(RuntimeError):
    """Expected operational or policy failure."""


class ToolMissingError(OciSecureError):
    """A required external executable is unavailable."""


class PolicyViolation(OciSecureError):
    """An image failed the configured security policy."""
