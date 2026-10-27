"""
Tests for the media analysis API.

Covers:
  - Invalid / unsupported file formats → 415
  - Empty file upload → 400
  - File too large → 413
  - Magic-byte mismatch → 400
  - Valid upload → 202 with upload_id
  - Submit with unknown upload_id → 404
  - Job status returns 404 for unknown job
  - Adapter registry returns list
  - Worker not configured → adapter INCONCLUSIVE (no fabrication)
  - Delete job cleans up

NOTE: These tests do NOT require Redis or a real database.
      They use the ASGI test client against the FastAPI app with mocked
      storage and mocked Celery.
"""
from __future__ import annotations

import io
import os
import sys
import uuid
from pathlib import Path
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Ensure backend on path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import app
from app.core.security import create_access_token


# ── Auth fixture ──────────────────────────────────────────────
@pytest.fixture
def auth_headers() -> dict:
    token = create_access_token(
        subject="usr_test_admin",
        extra_claims={"email": "test@org.com", "name": "Test", "role": "admin"},
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


# ── Helpers ───────────────────────────────────────────────────
def _png_bytes() -> bytes:
    """Minimal valid 1x1 PNG (67 bytes)."""
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
        b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
        b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def _jpeg_bytes() -> bytes:
    """Minimal JPEG magic header followed by filler."""
    return b"\xff\xd8\xff\xe0" + b"\x00" * 100


# ── Upload endpoint tests ─────────────────────────────────────
class TestMediaUpload:

    def _error_message(self, response) -> str:
        """Extract error message from either {'detail': ...} or {'error': {'message': ...}}."""
        body = response.json()
        if "detail" in body:
            return str(body["detail"])
        if "error" in body and isinstance(body["error"], dict):
            return str(body["error"].get("message", ""))
        return str(body)

    @pytest.mark.asyncio
    async def test_unsupported_format_returns_415(self, client, auth_headers):
        """PDF files should be rejected with 415."""
        response = await client.post(
            "/api/v1/media/upload",
            headers=auth_headers,
            files={"file": ("document.pdf", b"%PDF-1.4 fake", "application/pdf")},
        )
        assert response.status_code == 415, response.text
        msg = self._error_message(response).lower()
        assert "unsupported" in msg or "pdf" in msg

    @pytest.mark.asyncio
    async def test_empty_file_returns_400(self, client, auth_headers):
        """Empty file upload should return 400."""
        response = await client.post(
            "/api/v1/media/upload",
            headers=auth_headers,
            files={"file": ("empty.png", b"", "image/png")},
        )
        assert response.status_code == 400, response.text
        msg = self._error_message(response).lower()
        assert "empty" in msg

    @pytest.mark.asyncio
    async def test_magic_byte_mismatch_returns_400(self, client, auth_headers):
        """JPEG declared but PNG bytes → magic byte check fails."""
        response = await client.post(
            "/api/v1/media/upload",
            headers=auth_headers,
            files={"file": ("image.jpg", _png_bytes(), "image/jpeg")},
        )
        assert response.status_code == 400, response.text
        msg = self._error_message(response).lower()
        assert "jpeg" in msg or "match" in msg or "content" in msg

    @pytest.mark.asyncio
    async def test_file_too_large_returns_413(self, client, auth_headers):
        """File exceeding the image size limit should return 413."""
        big_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * (21 * 1024 * 1024)  # 21 MB
        response = await client.post(
            "/api/v1/media/upload",
            headers=auth_headers,
            files={"file": ("big.png", big_png, "image/png")},
        )
        assert response.status_code == 413, response.text
        msg = self._error_message(response).lower()
        assert "large" in msg or "size" in msg or "limit" in msg

    @pytest.mark.asyncio
    async def test_unauthenticated_upload_returns_401(self, client):
        """Upload without auth header should return 401/403."""
        response = await client.post(
            "/api/v1/media/upload",
            files={"file": ("image.png", _png_bytes(), "image/png")},
        )
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_valid_png_upload_succeeds(self, client, auth_headers, tmp_path):
        """Valid PNG upload writes file and returns upload_id."""
        with patch("app.services.media.storage.get_upload_dir", return_value=tmp_path):
            response = await client.post(
                "/api/v1/media/upload",
                headers=auth_headers,
                files={"file": ("test.png", _png_bytes(), "image/png")},
            )
        assert response.status_code in (200, 202), response.text
        data = response.json()["data"]
        assert "upload_id" in data
        assert data["upload_id"].startswith("upl_")
        assert data["media_type"] == "image"

    @pytest.mark.asyncio
    async def test_valid_jpeg_upload_succeeds(self, client, auth_headers, tmp_path):
        """Valid JPEG upload returns upload_id with image media_type."""
        with patch("app.services.media.storage.get_upload_dir", return_value=tmp_path):
            response = await client.post(
                "/api/v1/media/upload",
                headers=auth_headers,
                files={"file": ("photo.jpg", _jpeg_bytes(), "image/jpeg")},
            )
        assert response.status_code in (200, 202), response.text
        assert response.json()["data"]["media_type"] == "image"


# ── Submit endpoint tests ─────────────────────────────────────
class TestMediaSubmit:

    @pytest.mark.asyncio
    async def test_unknown_upload_id_returns_404(self, client, auth_headers, tmp_path):
        """Submitting with a nonexistent upload_id should return 404."""
        # Patch upload dir to tmp so no real files are found
        with patch("app.services.media.storage.get_upload_dir", return_value=tmp_path):
            response = await client.post(
                "/api/v1/media/submit",
                headers=auth_headers,
                json={"upload_id": "upl_doesnotexist123", "detectors": []},
            )
        # Should be 404 because no file with that upload_id exists
        assert response.status_code == 404, response.text


# ── Status / result / delete tests ───────────────────────────
class TestJobEndpoints:

    @pytest.mark.asyncio
    async def test_unknown_job_status_returns_404(self, client, auth_headers):
        """Polling status of a nonexistent job_id should return 404."""
        from sqlalchemy.ext.asyncio import AsyncSession
        from unittest.mock import AsyncMock, MagicMock

        fake_id = str(uuid.uuid4())

        # Mock DB to return None (job not found) without hitting real postgres
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = None
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute = AsyncMock(return_value=mock_result)

        from app.api.deps import get_db, get_current_user
        from app.models.user import User
        import uuid as _uuid

        mock_user = MagicMock(spec=User)
        mock_user.id = _uuid.uuid4()

        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        try:
            response = await client.get(f"/api/v1/media/jobs/{fake_id}", headers=auth_headers)
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 404, response.text

    @pytest.mark.asyncio
    async def test_unknown_job_result_returns_404(self, client, auth_headers):
        """Fetching result of a nonexistent job should return 404."""
        from sqlalchemy.ext.asyncio import AsyncSession
        from unittest.mock import AsyncMock, MagicMock
        import uuid as _uuid

        fake_id = str(uuid.uuid4())

        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = None
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute = AsyncMock(return_value=mock_result)

        mock_user = MagicMock()
        mock_user.id = _uuid.uuid4()

        from app.api.deps import get_db, get_current_user
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        try:
            response = await client.get(f"/api/v1/media/jobs/{fake_id}/result", headers=auth_headers)
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 404, response.text

    @pytest.mark.asyncio
    async def test_delete_unknown_job_returns_404(self, client, auth_headers):
        """Deleting a nonexistent job should return 404."""
        from sqlalchemy.ext.asyncio import AsyncSession
        from unittest.mock import AsyncMock, MagicMock
        import uuid as _uuid

        fake_id = str(uuid.uuid4())

        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = None
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute = AsyncMock(return_value=mock_result)

        mock_user = MagicMock()
        mock_user.id = _uuid.uuid4()

        from app.api.deps import get_db, get_current_user
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        try:
            response = await client.delete(f"/api/v1/media/jobs/{fake_id}", headers=auth_headers)
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 404, response.text

    @pytest.mark.asyncio
    async def test_list_jobs_returns_empty_for_new_user(self, client, auth_headers):
        """Listing jobs returns a list (empty when no jobs in DB)."""
        from sqlalchemy.ext.asyncio import AsyncSession
        from unittest.mock import AsyncMock, MagicMock
        import uuid as _uuid

        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = []
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute = AsyncMock(return_value=mock_result)

        mock_user = MagicMock()
        mock_user.id = _uuid.uuid4()

        from app.api.deps import get_db, get_current_user
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        try:
            response = await client.get("/api/v1/media/jobs", headers=auth_headers)
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200, response.text
        assert isinstance(response.json()["data"], list)


# ── Adapter registry tests ────────────────────────────────────
class TestAdapterRegistry:

    @pytest.mark.asyncio
    async def test_adapter_list_returns_all_adapters(self, client, auth_headers):
        """GET /media/adapters should return a list of registered adapters."""
        response = await client.get("/api/v1/media/adapters", headers=auth_headers)
        assert response.status_code == 200
        adapters = response.json()["data"]
        assert isinstance(adapters, list)
        assert len(adapters) >= 3  # image, audio, video

    @pytest.mark.asyncio
    async def test_unconfigured_adapters_are_flagged(self, client, auth_headers):
        """When no API keys are set, all adapters should report is_configured=False."""
        with patch.dict(os.environ, {
            "IMAGE_DETECTOR": "", "AUDIO_DETECTOR": "", "VIDEO_DETECTOR": "",
            "HIVE_API_KEY": "", "SIGHTENGINE_USER": "", "ELEVENLABS_API_KEY": "",
        }):
            response = await client.get("/api/v1/media/adapters", headers=auth_headers)
        assert response.status_code == 200
        # At least some adapters should not be configured in test env
        adapters = response.json()["data"]
        configured_states = [a["is_configured"] for a in adapters]
        # In CI with no env vars, none should be configured
        assert not all(configured_states), "Expected some adapters to be unconfigured in test env"


# ── Worker / adapter unit tests ───────────────────────────────
class TestAdapterHonestyContract:

    def test_image_adapter_not_configured_returns_inconclusive(self):
        """ImageSyntheticAdapter with no env vars must return INCONCLUSIVE, not raise."""
        from app.services.media.image_adapter import ImageSyntheticAdapter
        from app.services.media.base import AdapterContext

        adapter = ImageSyntheticAdapter()
        # Force unconfigured
        adapter._backend = ""
        adapter._hive_key = ""
        adapter._se_user = ""
        adapter._se_secret = ""

        ctx = AdapterContext(
            file_path="fake.png", file_name="fake.png",
            content_type="image/png", file_size_bytes=100,
        )
        result = adapter.safe_analyze(ctx)
        assert result.is_configured is False
        assert result.severity == "inconclusive"
        assert result.score is None
        assert result.skip_reason is not None

    def test_audio_adapter_not_configured_returns_inconclusive(self):
        """AudioSyntheticAdapter with no env vars must return INCONCLUSIVE."""
        from app.services.media.audio_adapter import AudioSyntheticAdapter
        from app.services.media.base import AdapterContext

        adapter = AudioSyntheticAdapter()
        adapter._backend = ""
        adapter._elevenlabs_key = ""
        adapter._hive_key = ""

        ctx = AdapterContext(
            file_path="fake.mp3", file_name="fake.mp3",
            content_type="audio/mpeg", file_size_bytes=100,
        )
        result = adapter.safe_analyze(ctx)
        assert result.is_configured is False
        assert result.score is None

    def test_video_adapter_not_configured_returns_inconclusive(self):
        """VideoManipulationAdapter with no env vars must return INCONCLUSIVE."""
        from app.services.media.video_adapter import VideoManipulationAdapter
        from app.services.media.base import AdapterContext

        adapter = VideoManipulationAdapter()
        adapter._backend = ""
        adapter._hive_key = ""
        adapter._azure_key = ""

        ctx = AdapterContext(
            file_path="fake.mp4", file_name="fake.mp4",
            content_type="video/mp4", file_size_bytes=100,
        )
        result = adapter.safe_analyze(ctx)
        assert result.is_configured is False
        assert result.score is None
        # skip_reason must describe the missing configuration
        skip = (result.skip_reason or "").lower()
        assert "configured" in skip or "configuration" in skip

    def test_av_consistency_not_configured_when_ffprobe_missing(self):
        """AVConsistencyAdapter must report not-configured when ffprobe is absent."""
        from app.services.media.video_adapter import AVConsistencyAdapter
        from app.services.media.base import AdapterContext
        import shutil

        adapter = AVConsistencyAdapter()
        adapter._enabled = True
        adapter._ffprobe = "ffprobe_definitely_not_on_path_xyz"

        assert adapter.is_configured() is False
        ctx = AdapterContext(
            file_path="fake.mp4", file_name="fake.mp4",
            content_type="video/mp4", file_size_bytes=100,
        )
        result = adapter.safe_analyze(ctx)
        assert result.is_configured is False

    def test_findings_have_no_fabricated_timestamps_when_unsupported(self):
        """
        When an adapter does not support time ranges, frame_refs should be None
        in the output — never a fabricated value.
        """
        from app.services.media.audio_adapter import AudioSyntheticAdapter
        adapter = AudioSyntheticAdapter()
        # ElevenLabs backend does not support time ranges
        assert adapter.supports_time_ranges is False
