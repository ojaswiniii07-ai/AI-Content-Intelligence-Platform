"""
Base definitions and interfaces for external integration adapters.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class ConnectionTestResult(BaseModel):
    """Result of an integration connectivity check."""
    success: bool
    status: str = Field(..., description="connected | failed | misconfigured | unauthorized")
    message: str
    latency_ms: Optional[float] = None
    details: Dict[str, Any] = Field(default_factory=dict, description="Non-sensitive diagnostics")


class ProviderMetadata(BaseModel):
    """Metadata describing an integration provider and its requirements."""
    provider_id: str
    display_name: str
    description: str
    category: str = Field(..., description="form | lms | custom | mock")
    auth_methods: List[str]
    required_permissions: List[str]
    official_docs_url: str
    config_schema: Dict[str, Any]
    secrets_schema: Dict[str, Any]


class BaseIntegrationAdapter(ABC):
    """
    Abstract adapter for communicating with an external service via its official API.
    Does not scrape private HTML pages or invent unofficial endpoints.
    """
    provider_id: str
    display_name: str
    description: str
    category: str
    official_docs_url: str

    @abstractmethod
    def get_metadata(self) -> ProviderMetadata:
        """Returns provider capabilities, required permissions, and configuration schema."""
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any], auth_method: str) -> Tuple[bool, Optional[str]]:
        """Validates that non-secret configuration satisfies schema requirements."""
        pass

    @abstractmethod
    def validate_secrets(self, secrets: Dict[str, Any], auth_method: str) -> Tuple[bool, Optional[str]]:
        """Validates that secret credentials (keys/tokens) meet format requirements."""
        pass

    @abstractmethod
    async def test_connection(
        self,
        config: Dict[str, Any],
        secrets: Dict[str, Any],
        auth_method: str,
    ) -> ConnectionTestResult:
        """
        Executes a live health/connectivity probe using the official platform API.
        Never leaks secret values into the returned result details.
        """
        pass
