"""
Webhook endpoint and delivery schemas.

Security guarantees:
- HMAC signing secret is revealed ONCE upon creation in WebhookEndpointCreatedResponse.
- Subsequent GET or list operations NEVER return the signing secret.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class WebhookEndpointCreate(BaseModel):
    integration_id: str = Field(..., description="Target integration to bind this webhook to")
    target_url: str = Field(..., description="Target HTTPS or HTTP URL to receive POST events")
    display_name: str = Field(..., min_length=1, max_length=255)
    event_types: Optional[List[str]] = Field(
        default_factory=lambda: ["job.completed", "job.failed", "batch.completed", "batch.partial_failure"],
        description="Event types that will trigger this webhook",
    )
    include_full_payload: bool = Field(
        False,
        description="If True, includes full excerpts/details (still excluding binary files). Default is summary only for privacy.",
    )


class WebhookEndpointUpdate(BaseModel):
    display_name: Optional[str] = Field(None, max_length=255)
    target_url: Optional[str] = None
    event_types: Optional[List[str]] = None
    is_active: Optional[bool] = None
    include_full_payload: Optional[bool] = None


class WebhookEndpointResponse(BaseModel):
    id: str
    integration_id: str
    target_url: str
    display_name: str
    event_types: Optional[List[str]] = None
    is_active: bool
    include_full_payload: bool
    last_test_status: Optional[str] = None
    last_test_at: Optional[datetime] = None
    total_delivered: int = 0
    total_failed: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WebhookEndpointCreatedResponse(WebhookEndpointResponse):
    signing_secret: str = Field(
        ...,
        description="HMAC-SHA256 signing secret. SAVE THIS SECRET NOW. It will never be shown again.",
    )
    verification_instructions: str = Field(
        "Verify outgoing events by computing HMAC-SHA256(signing_secret, raw_body) "
        "and comparing with 'X-ContentIQ-Signature-256: sha256=<hex>'. "
        "Also verify 'X-ContentIQ-Timestamp' is within your allowed replay window."
    )


class WebhookDeliveryResponse(BaseModel):
    id: str
    endpoint_id: str
    event_id: str
    event_type: str
    attempt_number: int
    status: str
    http_status_code: Optional[int] = None
    response_body_truncated: Optional[str] = None
    delivered_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None
    event_timestamp: int
    signature_header: Optional[str] = None
    error_message: Optional[str] = None
    submission_id: Optional[str] = None
    batch_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WebhookVerifyRequest(BaseModel):
    signing_secret: str = Field(..., description="Shared HMAC signing secret")
    payload: str = Field(..., description="Raw JSON payload string exactly as received")
    signature_header: str = Field(..., description="Value of X-ContentIQ-Signature-256 header")
    timestamp_header: Optional[str] = Field(None, description="Value of X-ContentIQ-Timestamp header")
    tolerance_seconds: int = Field(300, description="Max allowed clock skew in seconds (replay protection)")


class WebhookVerifyResponse(BaseModel):
    valid: bool
    reason: str
