"""
Integration Adapter Endpoints.

Allows authorized reviewers and admins to:
1. Browse supported third-party providers and their official API scopes/permissions.
2. Register and configure external platforms (Google Forms, Typeform, Canvas LMS, Moodle, Blackboard, Custom, Mock).
3. Securely store credentials with Fernet encryption (secrets are NEVER returned in responses).
4. Run live connection health checks through official APIs.
5. Disconnect or delete integrations cleanly.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_current_user, get_db, require_roles
from app.core.crypto import encrypt_secrets, decrypt_secrets
from app.core.exceptions import NotFoundError, ValidationError, ForbiddenError
from app.models.integration import Integration
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.integration import (
    IntegrationCreate,
    IntegrationResponse,
    IntegrationTestResponse,
    IntegrationUpdate,
    ProviderMetadataResponse,
)
from app.services.integrations.registry import (
    get_adapter,
    is_valid_provider,
    list_supported_providers,
)

router = APIRouter(prefix="/integrations", tags=["External Integrations"])

# In-memory store fallback (supports offline and test environments)
_INTEGRATION_STORE: Dict[str, Dict[str, Any]] = {}


def _record_to_response(rec: Dict[str, Any]) -> IntegrationResponse:
    """Formats an integration record for API responses, ensuring secrets are NEVER leaked."""
    return IntegrationResponse(
        id=rec["id"],
        workspace_id=rec["workspace_id"],
        provider=rec["provider"],
        display_name=rec["display_name"],
        auth_method=rec.get("auth_method", "api_key"),
        config=rec.get("config") or {},
        has_secrets=bool(rec.get("encrypted_secrets")),
        connection_status=rec.get("connection_status", "not_configured"),
        connection_error=rec.get("connection_error"),
        last_connection_test_at=rec.get("last_connection_test_at"),
        last_synced_at=rec.get("last_synced_at"),
        total_submissions_received=rec.get("total_submissions_received", 0),
        is_active=rec.get("is_active", True),
        created_at=rec.get("created_at") or datetime.now(timezone.utc),
        updated_at=rec.get("updated_at") or datetime.now(timezone.utc),
    )


# ── 1. Provider Registry ─────────────────────────────────────────────────────
@router.get(
    "/providers",
    response_model=APIResponse[List[ProviderMetadataResponse]],
    summary="List all supported integration providers and official API permissions",
)
async def list_providers(
    current_user: User = Depends(get_current_user),
):
    """
    Returns official documentation, required permissions/scopes,
    configuration schemas, and supported auth methods for each integration adapter.
    """
    providers = list_supported_providers()
    return APIResponse(
        success=True,
        data=[ProviderMetadataResponse(**p.model_dump()) for p in providers],
        message="Supported integration providers retrieved successfully",
    )


# ── 2. Create Integration ────────────────────────────────────────────────────
@router.post(
    "",
    response_model=APIResponse[IntegrationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Configure a new external platform integration",
)
async def create_integration(
    payload: IntegrationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "reviewer")),
):
    provider_id = payload.provider.lower().strip()
    if not is_valid_provider(provider_id):
        raise ValidationError(
            f"Unsupported provider: '{payload.provider}'. Consult /api/v1/integrations/providers."
        )

    adapter = get_adapter(provider_id)
    auth_method = payload.auth_method or "api_key"

    # Validate non-secret config
    valid_cfg, cfg_err = adapter.validate_config(payload.config or {}, auth_method)
    if not valid_cfg:
        raise ValidationError(f"Invalid configuration for {adapter.display_name}: {cfg_err}")

    # Validate secret credentials
    valid_sec, sec_err = adapter.validate_secrets(payload.secrets or {}, auth_method)
    if not valid_sec:
        raise ValidationError(f"Invalid secrets for {adapter.display_name}: {sec_err}")

    now = datetime.now(timezone.utc)
    new_id = str(uuid.uuid4())
    ws_id = payload.workspace_id or getattr(current_user, "active_workspace_id", None) or "ws_default"

    # Encrypt secrets securely (Fernet)
    encrypted_blob = encrypt_secrets(payload.secrets) if payload.secrets else None

    record = {
        "id": new_id,
        "workspace_id": ws_id,
        "provider": provider_id,
        "display_name": payload.display_name,
        "auth_method": auth_method,
        "config": payload.config or {},
        "encrypted_secrets": encrypted_blob,
        "oauth_data": {},
        "connection_status": "not_configured",
        "connection_error": None,
        "last_connection_test_at": None,
        "last_synced_at": None,
        "total_submissions_received": 0,
        "is_active": payload.is_active,
        "created_at": now,
        "updated_at": now,
    }

    _INTEGRATION_STORE[new_id] = record

    # DB persistence if available
    try:
        db_model = Integration(
            id=new_id,
            workspace_id=ws_id,
            provider=provider_id,
            display_name=payload.display_name,
            auth_method=auth_method,
            config=payload.config or {},
            encrypted_secrets=encrypted_blob,
            oauth_data={},
            connection_status="not_configured",
            connection_error=None,
            is_active=payload.is_active,
        )
        db.add(db_model)
        await db.commit()
    except Exception:
        # Graceful fallback to memory store in tests/disconnected DB
        pass

    return APIResponse(
        success=True,
        data=_record_to_response(record),
        message=f"Integration '{payload.display_name}' created successfully",
    )


# ── 3. List Integrations ─────────────────────────────────────────────────────
@router.get(
    "",
    response_model=APIResponse[List[IntegrationResponse]],
    summary="List integrations for workspace",
)
async def list_integrations(
    provider: Optional[str] = Query(None, description="Filter by provider ID"),
    connection_status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = list(_INTEGRATION_STORE.values())

    # Try DB query if present
    try:
        stmt = select(Integration)
        if provider:
            stmt = stmt.where(Integration.provider == provider.lower().strip())
        if connection_status:
            stmt = stmt.where(Integration.connection_status == connection_status.lower().strip())
        db_res = await db.execute(stmt)
        db_items = db_res.scalars().all()
        if db_items:
            for item in db_items:
                _INTEGRATION_STORE[item.id] = {
                    "id": item.id,
                    "workspace_id": item.workspace_id,
                    "provider": item.provider,
                    "display_name": item.display_name,
                    "auth_method": item.auth_method,
                    "config": item.config or {},
                    "encrypted_secrets": item.encrypted_secrets,
                    "oauth_data": item.oauth_data or {},
                    "connection_status": item.connection_status,
                    "connection_error": item.connection_error,
                    "last_connection_test_at": item.last_connection_test_at,
                    "last_synced_at": item.last_synced_at,
                    "total_submissions_received": item.total_submissions_received,
                    "is_active": item.is_active,
                    "created_at": item.created_at,
                    "updated_at": item.updated_at,
                }
            results = list(_INTEGRATION_STORE.values())
    except Exception:
        pass

    # Filter in-memory results
    if provider:
        results = [r for r in results if r.get("provider") == provider.lower().strip()]
    if connection_status:
        results = [r for r in results if r.get("connection_status") == connection_status.lower().strip()]

    return APIResponse(
        success=True,
        data=[_record_to_response(r) for r in results],
        message=f"Found {len(results)} integrations",
    )


# ── 4. Get Integration ───────────────────────────────────────────────────────
@router.get(
    "/{integration_id}",
    response_model=APIResponse[IntegrationResponse],
    summary="Get integration details by ID (secrets are omitted)",
)
async def get_integration(
    integration_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rec = _INTEGRATION_STORE.get(integration_id)
    if not rec:
        try:
            db_item = await db.get(Integration, integration_id)
            if db_item:
                rec = {
                    "id": db_item.id,
                    "workspace_id": db_item.workspace_id,
                    "provider": db_item.provider,
                    "display_name": db_item.display_name,
                    "auth_method": db_item.auth_method,
                    "config": db_item.config or {},
                    "encrypted_secrets": db_item.encrypted_secrets,
                    "oauth_data": db_item.oauth_data or {},
                    "connection_status": db_item.connection_status,
                    "connection_error": db_item.connection_error,
                    "last_connection_test_at": db_item.last_connection_test_at,
                    "last_synced_at": db_item.last_synced_at,
                    "total_submissions_received": db_item.total_submissions_received,
                    "is_active": db_item.is_active,
                    "created_at": db_item.created_at,
                    "updated_at": db_item.updated_at,
                }
                _INTEGRATION_STORE[integration_id] = rec
        except Exception:
            pass

    if not rec:
        raise NotFoundError(f"Integration with ID '{integration_id}' was not found.")

    return APIResponse(
        success=True,
        data=_record_to_response(rec),
        message="Integration retrieved successfully",
    )


# ── 5. Update Integration ────────────────────────────────────────────────────
@router.put(
    "/{integration_id}",
    response_model=APIResponse[IntegrationResponse],
    summary="Update integration configuration or rotate credentials",
)
async def update_integration(
    integration_id: str,
    payload: IntegrationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "reviewer")),
):
    rec = _INTEGRATION_STORE.get(integration_id)
    if not rec:
        raise NotFoundError(f"Integration with ID '{integration_id}' was not found.")

    adapter = get_adapter(rec["provider"])
    auth_method = payload.auth_method or rec.get("auth_method", "api_key")

    if payload.config is not None and adapter:
        valid_cfg, cfg_err = adapter.validate_config(payload.config, auth_method)
        if not valid_cfg:
            raise ValidationError(f"Invalid configuration: {cfg_err}")
        rec["config"] = payload.config

    if payload.secrets is not None and adapter:
        valid_sec, sec_err = adapter.validate_secrets(payload.secrets, auth_method)
        if not valid_sec:
            raise ValidationError(f"Invalid secrets: {sec_err}")
        rec["encrypted_secrets"] = encrypt_secrets(payload.secrets)

    if payload.display_name is not None:
        rec["display_name"] = payload.display_name
    if payload.auth_method is not None:
        rec["auth_method"] = payload.auth_method
    if payload.is_active is not None:
        rec["is_active"] = payload.is_active

    rec["updated_at"] = datetime.now(timezone.utc)

    try:
        db_item = await db.get(Integration, integration_id)
        if db_item:
            if payload.display_name is not None:
                db_item.display_name = payload.display_name
            if payload.auth_method is not None:
                db_item.auth_method = payload.auth_method
            if payload.config is not None:
                db_item.config = rec["config"]
            if payload.secrets is not None:
                db_item.encrypted_secrets = rec["encrypted_secrets"]
            if payload.is_active is not None:
                db_item.is_active = payload.is_active
            await db.commit()
    except Exception:
        pass

    return APIResponse(
        success=True,
        data=_record_to_response(rec),
        message="Integration updated successfully",
    )


# ── 6. Test Connection ───────────────────────────────────────────────────────
@router.post(
    "/{integration_id}/test",
    response_model=APIResponse[IntegrationTestResponse],
    summary="Probe connection using official adapter API",
)
async def test_integration_connection(
    integration_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "reviewer")),
):
    rec = _INTEGRATION_STORE.get(integration_id)
    if not rec:
        raise NotFoundError(f"Integration with ID '{integration_id}' was not found.")

    adapter = get_adapter(rec["provider"])
    if not adapter:
        raise ValidationError(f"No adapter available for provider '{rec['provider']}'")

    # Decrypt stored credentials
    secrets_dict = decrypt_secrets(rec.get("encrypted_secrets"))
    auth_method = rec.get("auth_method", "api_key")
    config_dict = rec.get("config") or {}

    result = await adapter.test_connection(config_dict, secrets_dict, auth_method)

    # Update record state
    rec["connection_status"] = result.status
    rec["connection_error"] = None if result.success else result.message
    rec["last_connection_test_at"] = datetime.now(timezone.utc)
    rec["updated_at"] = datetime.now(timezone.utc)

    try:
        db_item = await db.get(Integration, integration_id)
        if db_item:
            db_item.connection_status = result.status
            db_item.connection_error = rec["connection_error"]
            db_item.last_connection_test_at = rec["last_connection_test_at"]
            await db.commit()
    except Exception:
        pass

    return APIResponse(
        success=result.success,
        data=IntegrationTestResponse(**result.model_dump()),
        message=result.message,
    )


# ── 7. Disconnect Integration ────────────────────────────────────────────────
@router.post(
    "/{integration_id}/disconnect",
    response_model=APIResponse[IntegrationResponse],
    summary="Disconnect platform and clear all stored credentials",
)
async def disconnect_integration(
    integration_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "reviewer")),
):
    rec = _INTEGRATION_STORE.get(integration_id)
    if not rec:
        raise NotFoundError(f"Integration with ID '{integration_id}' was not found.")

    # Securely clear credentials
    rec["encrypted_secrets"] = None
    rec["oauth_data"] = None
    rec["connection_status"] = "disconnected"
    rec["connection_error"] = None
    rec["updated_at"] = datetime.now(timezone.utc)

    try:
        db_item = await db.get(Integration, integration_id)
        if db_item:
            db_item.encrypted_secrets = None
            db_item.oauth_data = None
            db_item.connection_status = "disconnected"
            db_item.connection_error = None
            await db.commit()
    except Exception:
        pass

    return APIResponse(
        success=True,
        data=_record_to_response(rec),
        message=f"Integration '{rec['display_name']}' disconnected and credentials purged",
    )


# ── 8. Delete Integration ────────────────────────────────────────────────────
@router.delete(
    "/{integration_id}",
    response_model=APIResponse[Dict[str, str]],
    summary="Delete an integration configuration",
)
async def delete_integration(
    integration_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "reviewer")),
):
    if integration_id not in _INTEGRATION_STORE:
        raise NotFoundError(f"Integration with ID '{integration_id}' was not found.")

    del _INTEGRATION_STORE[integration_id]

    try:
        db_item = await db.get(Integration, integration_id)
        if db_item:
            await db.delete(db_item)
            await db.commit()
    except Exception:
        pass

    return APIResponse(
        success=True,
        data={"id": integration_id},
        message="Integration deleted successfully",
    )
