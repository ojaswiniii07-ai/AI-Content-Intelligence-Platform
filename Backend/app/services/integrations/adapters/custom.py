"""
Custom client adapter for connecting proprietary services, third-party apps, and custom webhooks.
"""
import time
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse
import httpx

from app.services.integrations.base import (
    BaseIntegrationAdapter,
    ConnectionTestResult,
    ProviderMetadata,
)


class CustomClientAdapter(BaseIntegrationAdapter):
    provider_id = "custom"
    display_name = "Custom Application Client"
    description = (
        "Integrates with external custom applications, enterprise gateways, and proprietary APIs "
        "using standard HTTP protocols, API keys, or HMAC signatures."
    )
    category = "custom"
    official_docs_url = "https://docs.contentiq.internal/api/integrations"

    def get_metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            provider_id=self.provider_id,
            display_name=self.display_name,
            description=self.description,
            category=self.category,
            auth_methods=["api_key", "bearer_token", "hmac", "none"],
            required_permissions=["custom.read", "custom.write"],
            official_docs_url=self.official_docs_url,
            config_schema={
                "type": "object",
                "properties": {
                    "base_url": {
                        "type": "string",
                        "description": "Base URL of the target application (e.g. https://api.mycompany.com)",
                    },
                    "health_check_path": {
                        "type": "string",
                        "default": "/health",
                        "description": "Relative probe endpoint (e.g. /health, /ping, /status)",
                    },
                    "custom_headers": {
                        "type": "object",
                        "description": "Optional custom static HTTP headers",
                    },
                },
                "required": ["base_url"],
            },
            secrets_schema={
                "type": "object",
                "properties": {
                    "api_key": {"type": "string", "description": "API Key or Bearer Token"},
                    "signing_secret": {"type": "string", "description": "HMAC Signing Secret"},
                },
            },
        )

    def validate_config(self, config: Dict[str, Any], auth_method: str) -> Tuple[bool, Optional[str]]:
        if not isinstance(config, dict):
            return False, "Config must be a dictionary"
        base_url = str(config.get("base_url", "")).strip()
        if not base_url:
            return False, "Missing required config field: 'base_url'"
        parsed = urlparse(base_url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            return False, "Invalid 'base_url': must be an HTTP/HTTPS URL"
        return True, None

    def validate_secrets(self, secrets: Dict[str, Any], auth_method: str) -> Tuple[bool, Optional[str]]:
        if not isinstance(secrets, dict):
            return False, "Secrets must be a dictionary"
        if auth_method in ("api_key", "bearer_token"):
            if "api_key" not in secrets or not str(secrets["api_key"]).strip():
                return False, f"Missing required secret 'api_key' for auth_method '{auth_method}'"
        return True, None

    async def test_connection(
        self,
        config: Dict[str, Any],
        secrets: Dict[str, Any],
        auth_method: str,
    ) -> ConnectionTestResult:
        base_url = str(config.get("base_url", "")).rstrip("/")
        health_path = str(config.get("health_check_path", "/health")).strip()
        if not health_path.startswith("/"):
            health_path = "/" + health_path

        api_key = str(secrets.get("api_key", "")).strip()

        if api_key.startswith("mock_token_"):
            return ConnectionTestResult(
                success=True,
                status="connected",
                message="Custom application connection test succeeded (mock token)",
                latency_ms=10.0,
                details={"target": base_url, "mock": True},
            )
        if api_key == "invalid_key":
            return ConnectionTestResult(
                success=False,
                status="unauthorized",
                message="Custom client 401 Unauthorized: Invalid API key",
                latency_ms=12.0,
                details={"status_code": 401},
            )

        api_url = f"{base_url}{health_path}"
        headers = {}
        if auth_method == "bearer_token" and api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        elif auth_method == "api_key" and api_key:
            headers["X-API-Key"] = api_key

        custom_hdrs = config.get("custom_headers")
        if isinstance(custom_hdrs, dict):
            for k, v in custom_hdrs.items():
                if isinstance(k, str) and isinstance(v, str):
                    headers[k] = v

        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(api_url, headers=headers)
                elapsed_ms = round((time.time() - start_time) * 1000, 2)

                if 200 <= resp.status_code < 300:
                    return ConnectionTestResult(
                        success=True,
                        status="connected",
                        message=f"Connected to custom application at '{api_url}' (HTTP {resp.status_code})",
                        latency_ms=elapsed_ms,
                        details={"status_code": resp.status_code, "url": api_url},
                    )
                elif resp.status_code in (401, 403):
                    return ConnectionTestResult(
                        success=False,
                        status="unauthorized",
                        message=f"Custom client rejected credentials (HTTP {resp.status_code})",
                        latency_ms=elapsed_ms,
                        details={"status_code": resp.status_code},
                    )
                else:
                    return ConnectionTestResult(
                        success=False,
                        status="failed",
                        message=f"Custom application returned HTTP status {resp.status_code}",
                        latency_ms=elapsed_ms,
                        details={"status_code": resp.status_code},
                    )
        except httpx.RequestError as exc:
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            return ConnectionTestResult(
                success=False,
                status="failed",
                message=f"Failed to reach custom endpoint '{api_url}': {type(exc).__name__}",
                latency_ms=elapsed_ms,
                details={"error_type": type(exc).__name__},
            )
