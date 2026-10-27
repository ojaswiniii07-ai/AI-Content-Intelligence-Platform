"""
Registry of supported integration adapters.
"""
from typing import Dict, List, Optional
from app.services.integrations.base import BaseIntegrationAdapter, ProviderMetadata
from app.services.integrations.adapters import (
    GoogleFormsAdapter,
    TypeformAdapter,
    CanvasLMSAdapter,
    MoodleAdapter,
    BlackboardAdapter,
    CustomClientAdapter,
    MockIntegrationAdapter,
)

_ADAPTERS: Dict[str, BaseIntegrationAdapter] = {
    "google_forms": GoogleFormsAdapter(),
    "typeform": TypeformAdapter(),
    "canvas_lms": CanvasLMSAdapter(),
    "moodle": MoodleAdapter(),
    "blackboard": BlackboardAdapter(),
    "custom": CustomClientAdapter(),
    "mock": MockIntegrationAdapter(),
}


def get_adapter(provider_id: str) -> Optional[BaseIntegrationAdapter]:
    """Retrieves an adapter instance by its unique provider identifier."""
    return _ADAPTERS.get(provider_id.lower().strip())


def is_valid_provider(provider_id: str) -> bool:
    """Checks whether the provider is supported."""
    return provider_id.lower().strip() in _ADAPTERS


def list_supported_providers() -> List[ProviderMetadata]:
    """Returns metadata for all registered platform adapters."""
    return [adapter.get_metadata() for adapter in _ADAPTERS.values()]
