"""
Integration schemas for ContentIQ adapter-based external platforms.

Security guarantee:
- 'encrypted_secrets' is NEVER exposed or returned by any response schema.
- 'has_secrets' is exposed as a safe boolean flag.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class IntegrationBase(BaseModel):
    provider: str = Field(..., min_length=2, max_length=100, description="Provider identifier (e.g. google_forms, canvas_lms, mock)")
    display_name: str = Field(..., min_length=1, max_length=255, description="Human readable label")
    auth_method: str = Field("api_key", description="Auth method: api_key | oauth2 | bearer_token | token | pat | custom | none")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Non-sensitive adapter configuration")
    is_active: bool = True


class IntegrationCreate(IntegrationBase):
    workspace_id: Optional[str] = Field(None, description="Workspace ID (defaults to active user's workspace if omitted)")
    secrets: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Sensitive API keys or tokens (encrypted at rest; never returned)")


class IntegrationUpdate(BaseModel):
    display_name: Optional[str] = Field(None, max_length=255)
    auth_method: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    secrets: Optional[Dict[str, Any]] = Field(None, description="New credentials to overwrite existing secrets (encrypted at rest)")
    is_active: Optional[bool] = None


class IntegrationResponse(BaseModel):
    id: str
    workspace_id: str
    provider: str
    display_name: str
    auth_method: str
    config: Optional[Dict[str, Any]] = None
    has_secrets: bool = Field(False, description="True if credentials are encrypted and stored")
    connection_status: str = Field("not_configured", description="connected | disconnected | error | pending | not_configured")
    connection_error: Optional[str] = None
    last_connection_test_at: Optional[datetime] = None
    last_synced_at: Optional[datetime] = None
    total_submissions_received: int = 0
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Backwards compatibility alias
IntegrationRead = IntegrationResponse


class IntegrationTestResponse(BaseModel):
    success: bool
    status: str
    message: str
    latency_ms: Optional[float] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class ProviderMetadataResponse(BaseModel):
    provider_id: str
    display_name: str
    description: str
    category: str
    auth_methods: List[str]
    required_permissions: List[str]
    official_docs_url: str
    config_schema: Dict[str, Any]
    secrets_schema: Dict[str, Any]
