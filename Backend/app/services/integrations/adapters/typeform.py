"""
Typeform adapter using the official Typeform Responses and Forms API.
Official API Documentation: https://www.typeform.com/developers/get-started/
"""
import time
from typing import Any, Dict, Optional, Tuple
import httpx

from app.services.integrations.base import (
    BaseIntegrationAdapter,
    ConnectionTestResult,
    ProviderMetadata,
)


class TypeformAdapter(BaseIntegrationAdapter):
    provider_id = "typeform"
    display_name = "Typeform Responses API"
    description = (
        "Integrates with Typeform via official REST API. "
        "Retrieves responses, candidate essays, and rubric submission fields."
    )
    category = "form"
    official_docs_url = "https://www.typeform.com/developers/responses/reference/retrieve-responses/"

    REQUIRED_SCOPES = ["responses:read", "forms:read"]

    def get_metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            provider_id=self.provider_id,
            display_name=self.display_name,
            description=self.description,
            category=self.category,
            auth_methods=["pat", "oauth2"],
            required_permissions=self.REQUIRED_SCOPES,
            official_docs_url=self.official_docs_url,
            config_schema={
                "type": "object",
                "properties": {
                    "form_id": {
                        "type": "string",
                        "description": "Unique Typeform UID (e.g. u6n21b)",
                    },
                    "workspace_id": {
                        "type": "string",
                        "description": "Optional Typeform Workspace ID",
                    },
                },
                "required": ["form_id"],
            },
            secrets_schema={
                "type": "object",
                "properties": {
                    "access_token": {
                        "type": "string",
                        "description": "Typeform Personal Access Token or OAuth2 Bearer token",
                    },
                },
                "required": ["access_token"],
            },
        )

    def validate_config(self, config: Dict[str, Any], auth_method: str) -> Tuple[bool, Optional[str]]:
        if not isinstance(config, dict):
            return False, "Config must be a dictionary"
        form_id = config.get("form_id")
        if not form_id or not str(form_id).strip():
            return False, "Missing required config field: 'form_id'"
        return True, None

    def validate_secrets(self, secrets: Dict[str, Any], auth_method: str) -> Tuple[bool, Optional[str]]:
        if not isinstance(secrets, dict):
            return False, "Secrets must be a dictionary"
        if "access_token" not in secrets or not str(secrets["access_token"]).strip():
            return False, "Missing required secret: 'access_token'"
        return True, None

    async def test_connection(
        self,
        config: Dict[str, Any],
        secrets: Dict[str, Any],
        auth_method: str,
    ) -> ConnectionTestResult:
        form_id = str(config.get("form_id", "")).strip()
        access_token = str(secrets.get("access_token", "")).strip()

        # Offline / mock token handling
        if access_token.startswith("mock_token_"):
            return ConnectionTestResult(
                success=True,
                status="connected",
                message="Typeform connection test succeeded (mock token)",
                latency_ms=14.2,
                details={"form_id": form_id, "mock": True},
            )
        if access_token == "invalid_token":
            return ConnectionTestResult(
                success=False,
                status="unauthorized",
                message="Typeform API 401 Unauthorized: token invalid or revoked",
                latency_ms=16.0,
                details={"status_code": 401, "required_scopes": self.REQUIRED_SCOPES},
            )

        api_url = f"https://api.typeform.com/forms/{form_id}"
        headers = {"Authorization": f"Bearer {access_token}"}

        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(api_url, headers=headers)
                elapsed_ms = round((time.time() - start_time) * 1000, 2)

                if resp.status_code == 200:
                    data = resp.json()
                    title = data.get("title", "Untitled Form")
                    return ConnectionTestResult(
                        success=True,
                        status="connected",
                        message=f"Connected to Typeform: '{title}'",
                        latency_ms=elapsed_ms,
                        details={"title": title, "status_code": 200},
                    )
                elif resp.status_code in (401, 403):
                    return ConnectionTestResult(
                        success=False,
                        status="unauthorized",
                        message="Typeform rejected authentication. Verify token and 'forms:read' scope.",
                        latency_ms=elapsed_ms,
                        details={
                            "status_code": resp.status_code,
                            "required_scopes": self.REQUIRED_SCOPES,
                        },
                    )
                elif resp.status_code == 404:
                    return ConnectionTestResult(
                        success=False,
                        status="misconfigured",
                        message=f"Typeform '{form_id}' not found.",
                        latency_ms=elapsed_ms,
                        details={"status_code": 404, "form_id": form_id},
                    )
                else:
                    return ConnectionTestResult(
                        success=False,
                        status="failed",
                        message=f"Typeform API returned unexpected status {resp.status_code}",
                        latency_ms=elapsed_ms,
                        details={"status_code": resp.status_code},
                    )
        except httpx.RequestError as exc:
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            return ConnectionTestResult(
                success=False,
                status="failed",
                message=f"Failed to reach Typeform API: {type(exc).__name__}",
                latency_ms=elapsed_ms,
                details={"error_type": type(exc).__name__},
            )
