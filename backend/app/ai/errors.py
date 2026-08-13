"""AI provider error hierarchy.

Controlled errors raised by the provider layer. The HTTP surface maps these
to stable status codes so callers can react predictably without exposing
provider internals or credentials.
"""

from __future__ import annotations


class AIProviderError(Exception):
    """Base class for all controlled AI provider errors."""


class ProviderNotConfigured(AIProviderError):
    """The provider is selected but its credentials are not configured."""


class ProviderTimeout(AIProviderError):
    """The upstream model call exceeded the configured timeout."""


class ProviderAPIError(AIProviderError):
    """The upstream API call failed (transport, auth, rate limit...)."""


class InvalidDesignResponse(AIProviderError):
    """The model returned content that is not a valid DesignSpecification.

    Raised after a single structured-correction retry has also failed.
    """
