"""AI domain errors for provider and job execution."""

from __future__ import annotations


class AIDomainError(Exception):
    """Base AI domain error."""

    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


class ProviderConfigurationError(AIDomainError):
    """Invalid credentials, inactive model, or missing encryption key."""


class ProviderRequestError(AIDomainError):
    """Provider rejected the request or returned an error."""


class StructuredOutputError(AIDomainError):
    """Model output failed schema validation."""


class JobCancelledError(AIDomainError):
    """Job was cancelled before or during execution."""
