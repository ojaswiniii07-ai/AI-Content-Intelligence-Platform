"""
Mock adapter for offline tests and deterministic verification.
"""
import time
from typing import Any, Dict, Optional, Tuple
from app.services.integrations.base import (
    BaseIntegrationAdapter,
    ConnectionTestResult,
    ProviderMetadata,
)


class MockIntegrationAdapter(BaseIntegrationAdapter):
    provider_id = "mock"
    display_name = "Mock Adapter (Testing)"
    description = "In-memory mock adapter for deterministic testing without external API calls."
    category = "mock"
    official_docs_url = "https://docs.contentiq.internal/testing"

    def get_metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            provider_id=self.provider_id,
            display_name=self.display_name,
            description=self.description,
            category=self.category,
            auth_methods=["api_key", "bearer_token"],
            required_permissions=["test.simulate_connection"],
            official_docs_url=self.official_docs_url,
            config_schema={
                "type": "object",
                "properties": {
                    "simulate_failure": {"type": "boolean", "default": False},
                    "simulate_latency_ms": {"type": "number", "default": 10},
                    "mock_endpoint_name": {"type": "string"},
                },
            },
            secrets_schema={
                "type": "object",
                "properties": {
                    "api_key": {"type": "string"},
                },
                "required": ["api_key"],
            },
        )

    def validate_config(self, config: Dict[str, Any], auth_method: str) -> Tuple[bool, Optional[str]]:
        if not isinstance(config, dict):
            return False, "Configuration must be a dictionary"
        return True, None

    def validate_secrets(self, secrets: Dict[str, Any], auth_method: str) -> Tuple[bool, Optional[str]]:
        if not isinstance(secrets, dict):
            return False, "Secrets must be a dictionary"
        if "api_key" not in secrets or not str(secrets["api_key"]).strip():
            return False, "Missing required secret: 'api_key'"
        return True, None

    async def test_connection(
        self,
        config: Dict[str, Any],
        secrets: Dict[str, Any],
        auth_method: str,
    ) -> ConnectionTestResult:
        start_time = time.time()
        api_key = str(secrets.get("api_key", ""))
        simulate_failure = bool(config.get("simulate_failure", False))

        # Rejection for explicit invalid key test cases
        if api_key == "invalid_key" or "invalid" in api_key.lower():
            elapsed = (time.time() - start_time) * 1000
            return ConnectionTestResult(
                success=False,
                status="unauthorized",
                message="Mock authentication failed: invalid API key",
                latency_ms=round(elapsed, 2),
                details={"mock_status": 401, "error": "Invalid API key provided"},
            )

        if simulate_failure:
            elapsed = (time.time() - start_time) * 1000
            return ConnectionTestResult(
                success=False,
                status="failed",
                message="Simulated connection failure as requested in config",
                latency_ms=round(elapsed, 2),
                details={"mock_status": 500, "simulated": True},
            )

        elapsed = (time.time() - start_time) * 1000
        return ConnectionTestResult(
            success=True,
            status="connected",
            message="Mock connection test succeeded",
            latency_ms=round(elapsed, 2),
            details={"mock_status": 200, "verified": True},
        )
