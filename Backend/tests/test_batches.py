"""
Tests for Batch Processing and Cohort Reporting module.

Covers
------
1.  Empty batch handling — run on a batch with zero submissions.
2.  Duplicate submission deduplication via source_identifier.
3.  Partial failures — some submissions fail, batch reaches partial_failure.
4.  Pagination — page / page_size / total_pages arithmetic.
5.  Filtering — by status, analysis_type, date_from/date_to.
6.  Privacy suppression — cohorts with < 5 items suppress granular distributions.
7.  CSV formula-injection protection — cells starting with =, +, -, @, TAB, CR.
8.  JSON export structure — disclaimer and suppression fields present.
9.  Authorization — unauthorized roles blocked on write endpoints.
10. Report structure — dimension_breakdown decouples text/media/similarity/rubric.
11. Authorship disclaimer — always present in cohort reports.
12. Metric definitions — glossary always returned.
"""
from __future__ import annotations

import csv
import io
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# ── Path setup ────────────────────────────────────────────────────────────────
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import app
from app.api.deps import get_db
from app.core.security import create_access_token
from app.services.reporting.cohort import build_cohort_report
from app.services.reporting.exporter import sanitize_csv_cell, generate_batch_csv


# ── Auth fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def admin_headers() -> dict:
    token = create_access_token(
        subject="usr_admin_01",
        extra_claims={"email": "admin@platform.io", "name": "Admin User", "role": "admin"},
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def reviewer_headers() -> dict:
    token = create_access_token(
        subject="usr_reviewer_01",
        extra_claims={"email": "reviewer@platform.io", "name": "Reviewer", "role": "reviewer"},
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user_headers() -> dict:
    token = create_access_token(
        subject="usr_user_01",
        extra_claims={"email": "user@platform.io", "name": "Regular User", "role": "user"},
    )
    return {"Authorization": f"Bearer {token}"}


# ── DB mock fixture ───────────────────────────────────────────────────────────

@pytest.fixture
def mock_db():
    """Mock async DB session.

    Configures scalar_one_or_none() to return None so that get_current_user
    falls back to the ephemeral-user path, which builds a User object from JWT
    claims (including the real 'role' value).  This ensures RBAC tests work
    correctly without a live database.
    """
    db = MagicMock()
    # scalar_one_or_none() must return None to trigger ephemeral user path
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = None
    execute_result.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=execute_result)
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.close = AsyncMock()
    return db


@pytest_asyncio.fixture
async def async_client(mock_db) -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_db] = lambda: mock_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sample_submission_item(idx: int, source_id: str | None = None) -> dict:
    return {
        "title": f"Essay {idx}",
        "content_type": "text",
        "text_content": f"This is sample text content number {idx}.",
        "source_identifier": source_id or f"sub_{idx:04d}",
    }


async def _create_fresh_batch(client: AsyncClient, headers: dict) -> str:
    """Helper: create a new batch and return its ID."""
    resp = await client.post(
        "/api/v1/batches",
        json={
            "name": f"test-batch-{uuid.uuid4().hex[:6]}",
            "workspace_id": "ws_test",
            "source_type": "Direct Upload",
            "analysis_types": ["text"],
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]["id"]


# ═══════════════════════════════════════════════════════════════════════════════
# 1. EMPTY BATCH HANDLING
# ═══════════════════════════════════════════════════════════════════════════════

class TestEmptyBatch:
    @pytest.mark.asyncio
    async def test_run_empty_batch_returns_done(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        """Running a batch with no submissions should immediately return done."""
        batch_id = await _create_fresh_batch(async_client, admin_headers)

        resp = await async_client.post(
            f"/api/v1/batches/{batch_id}/run",
            headers=admin_headers,
        )
        assert resp.status_code == 202, resp.text
        data = resp.json()["data"]
        assert data["status"] == "done"
        assert data["total_items"] == 0
        assert data["processed_items"] == 0
        assert data["failed_items"] == 0

    @pytest.mark.asyncio
    async def test_empty_batch_report_privacy_suppressed(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        """Empty batch report should suppress distributions (0 < 5)."""
        batch_id = await _create_fresh_batch(async_client, admin_headers)
        await async_client.post(
            f"/api/v1/batches/{batch_id}/run", headers=admin_headers
        )
        resp = await async_client.get(
            f"/api/v1/batches/{batch_id}/report", headers=admin_headers
        )
        assert resp.status_code == 200, resp.text
        report = resp.json()["data"]
        assert report["privacy_suppressed"] is True
        assert report["score_distribution"] is None


# ═══════════════════════════════════════════════════════════════════════════════
# 2. DUPLICATE DEDUPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

class TestDuplicateDeduplication:
    @pytest.mark.asyncio
    async def test_duplicate_source_identifier_skipped(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        """Submissions with the same source_identifier should be deduplicated."""
        batch_id = await _create_fresh_batch(async_client, admin_headers)

        submissions = [
            {"title": "Essay A", "content_type": "text",
             "text_content": "Content A", "source_identifier": "dup_001"},
            {"title": "Essay A copy", "content_type": "text",
             "text_content": "Content A again", "source_identifier": "dup_001"},
            {"title": "Essay B", "content_type": "text",
             "text_content": "Content B", "source_identifier": "dup_002"},
        ]

        resp = await async_client.post(
            f"/api/v1/batches/{batch_id}/submissions",
            json={"submissions": submissions},
            headers=admin_headers,
        )
        assert resp.status_code == 200, resp.text
        attach = resp.json()["data"]
        assert attach["added_count"] == 2
        assert attach["duplicates_skipped"] == 1
        assert attach["total_items"] == 2

    @pytest.mark.asyncio
    async def test_attach_twice_deduplicates_all(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        """Attaching the same submissions a second time should skip all."""
        batch_id = await _create_fresh_batch(async_client, admin_headers)
        subs = [{"title": "X", "content_type": "text",
                 "text_content": "text", "source_identifier": "dup_only"}]

        r1 = await async_client.post(
            f"/api/v1/batches/{batch_id}/submissions",
            json={"submissions": subs}, headers=admin_headers,
        )
        r2 = await async_client.post(
            f"/api/v1/batches/{batch_id}/submissions",
            json={"submissions": subs}, headers=admin_headers,
        )
        # First attach succeeds; second detects duplicate
        assert r1.json()["data"]["added_count"] == 1
        assert r2.json()["data"]["added_count"] == 0
        assert r2.json()["data"]["duplicates_skipped"] == 1

    @pytest.mark.asyncio
    async def test_attach_empty_list_accepted(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        """Attaching an empty submissions list should be valid and return 0 added."""
        batch_id = await _create_fresh_batch(async_client, admin_headers)
        resp = await async_client.post(
            f"/api/v1/batches/{batch_id}/submissions",
            json={"submissions": []},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["added_count"] == 0


# ═══════════════════════════════════════════════════════════════════════════════
# 3. PARTIAL FAILURES
# ═══════════════════════════════════════════════════════════════════════════════

class TestPartialFailures:
    @pytest.mark.asyncio
    async def test_run_batch_produces_valid_status(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        """Running a batch with 10 submissions should yield a valid final status."""
        batch_id = await _create_fresh_batch(async_client, admin_headers)

        submissions = [_sample_submission_item(i) for i in range(10)]
        await async_client.post(
            f"/api/v1/batches/{batch_id}/submissions",
            json={"submissions": submissions},
            headers=admin_headers,
        )
        resp = await async_client.post(
            f"/api/v1/batches/{batch_id}/run", headers=admin_headers
        )
        assert resp.status_code == 202, resp.text
        data = resp.json()["data"]
        assert data["status"] in ("done", "partial_failure", "failed")
        assert data["total_items"] == 10
        assert data["processed_items"] + data["failed_items"] == data["total_items"]

    @pytest.mark.asyncio
    async def test_partial_failure_exposes_failure_details(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        """A batch that reaches partial_failure must expose failure_details."""
        # We create a large batch so that the ~8% random failure rate likely
        # triggers at least one failure (with 50 submissions, probability ≈ 98%).
        batch_id = await _create_fresh_batch(async_client, admin_headers)
        submissions = [_sample_submission_item(i) for i in range(50)]
        await async_client.post(
            f"/api/v1/batches/{batch_id}/submissions",
            json={"submissions": submissions},
            headers=admin_headers,
        )
        resp = await async_client.post(
            f"/api/v1/batches/{batch_id}/run", headers=admin_headers
        )
        data = resp.json()["data"]
        if data["status"] == "partial_failure":
            assert data["failure_details"] is not None
            assert len(data["failure_details"]) > 0
            record = data["failure_details"][0]
            assert "submission_id" in record
            assert "error" in record

    @pytest.mark.asyncio
    async def test_double_run_rejected(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        """Triggering run on a batch already running should return 409."""
        # Use a demo batch that is "running"
        resp = await async_client.post(
            "/api/v1/batches/b2/run", headers=admin_headers
        )
        assert resp.status_code == 409


# ═══════════════════════════════════════════════════════════════════════════════
# 4. PAGINATION
# ═══════════════════════════════════════════════════════════════════════════════

class TestPagination:
    @pytest.mark.asyncio
    async def test_default_pagination(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        """List batches returns items, total, page, page_size, total_pages."""
        resp = await async_client.get("/api/v1/batches", headers=admin_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        assert data["page"] == 1

    @pytest.mark.asyncio
    async def test_page_size_respected(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        """page_size=2 should return at most 2 items per page."""
        resp = await async_client.get(
            "/api/v1/batches?page=1&page_size=2", headers=admin_headers
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["items"]) <= 2
        assert data["page_size"] == 2

    @pytest.mark.asyncio
    async def test_page2_returns_different_items(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        """Page 2 should not contain the same items as page 1."""
        r1 = await async_client.get(
            "/api/v1/batches?page=1&page_size=2", headers=admin_headers
        )
        r2 = await async_client.get(
            "/api/v1/batches?page=2&page_size=2", headers=admin_headers
        )
        ids1 = {b["id"] for b in r1.json()["data"]["items"]}
        ids2 = {b["id"] for b in r2.json()["data"]["items"]}
        # Pages may overlap only when total <= page_size; otherwise disjoint
        total = r1.json()["data"]["total"]
        if total > 2:
            assert ids1.isdisjoint(ids2), "Page 1 and page 2 share items."

    @pytest.mark.asyncio
    async def test_out_of_range_page_returns_empty(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        """Requesting a page beyond the last page should return 0 items."""
        resp = await async_client.get(
            "/api/v1/batches?page=9999&page_size=10", headers=admin_headers
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["items"] == []

    @pytest.mark.asyncio
    async def test_total_pages_calculation(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        """total_pages should equal ceil(total / page_size)."""
        import math
        resp = await async_client.get(
            "/api/v1/batches?page=1&page_size=3", headers=admin_headers
        )
        data = resp.json()["data"]
        expected = math.ceil(data["total"] / 3) if data["total"] > 0 else 1
        assert data["total_pages"] == expected


# ═══════════════════════════════════════════════════════════════════════════════
# 5. FILTERING
# ═══════════════════════════════════════════════════════════════════════════════

class TestFiltering:
    @pytest.mark.asyncio
    async def test_filter_by_status_done(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        resp = await async_client.get(
            "/api/v1/batches?status=done", headers=admin_headers
        )
        assert resp.status_code == 200
        for item in resp.json()["data"]["items"]:
            assert item["status"] == "done"

    @pytest.mark.asyncio
    async def test_filter_by_status_queued(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        resp = await async_client.get(
            "/api/v1/batches?status=queued", headers=admin_headers
        )
        assert resp.status_code == 200
        for item in resp.json()["data"]["items"]:
            assert item["status"] == "queued"

    @pytest.mark.asyncio
    async def test_filter_by_analysis_type(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        resp = await async_client.get(
            "/api/v1/batches?analysis_type=media", headers=admin_headers
        )
        assert resp.status_code == 200
        for item in resp.json()["data"]["items"]:
            assert "media" in (item.get("analysis_types") or [])

    @pytest.mark.asyncio
    async def test_filter_by_nonexistent_status(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        resp = await async_client.get(
            "/api/v1/batches?status=nonexistent", headers=admin_headers
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["items"] == []


# ═══════════════════════════════════════════════════════════════════════════════
# 6. PRIVACY SUPPRESSION
# ═══════════════════════════════════════════════════════════════════════════════

class TestPrivacySuppression:
    def _make_small_batch(self, n: int) -> dict:
        return {
            "id": f"small_{n}",
            "name": f"SmallBatch-{n}",
            "total_items": n,
            "processed_items": n,
            "failed_items": 0,
            "flagged_items": 1 if n > 0 else 0,
            "mean_confidence": 65.0,
            "status": "done",
            "score_distribution": {"0-20%": 0, "20-40%": 0, "40-60%": 1, "60-80%": 0, "80-100%": 0},
            "analysis_types": ["text"],
        }

    def test_cohort_with_4_items_is_suppressed(self):
        """build_cohort_report must suppress distributions for n < 5."""
        batch = self._make_small_batch(4)
        report = build_cohort_report(batch=batch, submission_records=None)
        assert report.privacy_suppressed is True
        assert report.score_distribution is None
        assert report.suppression_reason is not None
        assert "4" in report.suppression_reason

    def test_cohort_with_5_items_not_suppressed(self):
        """build_cohort_report must NOT suppress distributions for n >= 5."""
        batch = self._make_small_batch(5)
        subs = [
            {"confidence_pct": 30 + i * 10, "status": "completed",
             "content_type": "text", "flagged": False, "inconclusive": False}
            for i in range(5)
        ]
        report = build_cohort_report(batch=batch, submission_records=subs)
        assert report.privacy_suppressed is False
        assert report.score_distribution is not None

    def test_cohort_with_0_items_is_suppressed(self):
        """Empty batch (0 submissions) must trigger suppression."""
        batch = self._make_small_batch(0)
        report = build_cohort_report(batch=batch, submission_records=[])
        assert report.privacy_suppressed is True

    @pytest.mark.asyncio
    async def test_small_batch_report_via_api_is_suppressed(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        """API cohort report for a 3-submission batch should suppress distributions."""
        batch_id = await _create_fresh_batch(async_client, admin_headers)
        subs = [_sample_submission_item(i) for i in range(3)]
        await async_client.post(
            f"/api/v1/batches/{batch_id}/submissions",
            json={"submissions": subs},
            headers=admin_headers,
        )
        # Do NOT run the batch — it has 3 items total
        resp = await async_client.get(
            f"/api/v1/batches/{batch_id}/report",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        report = resp.json()["data"]
        assert report["privacy_suppressed"] is True
        assert report["score_distribution"] is None


# ═══════════════════════════════════════════════════════════════════════════════
# 7. CSV FORMULA-INJECTION PROTECTION
# ═══════════════════════════════════════════════════════════════════════════════

class TestCsvFormulaInjection:
    """Verify that sanitize_csv_cell correctly neutralizes formula-trigger chars."""

    @pytest.mark.parametrize("dangerous_input,expected_prefix", [
        ("=SUM(A1:A10)", "'"),
        ("+calc()", "'"),
        ("-1+2", "'"),
        ("@IMPORTRANGE(A1)", "'"),
        ("\t=cmd", "'"),
        ("\r=cmd", "'"),
    ])
    def test_dangerous_values_prefixed(self, dangerous_input, expected_prefix):
        result = sanitize_csv_cell(dangerous_input)
        assert result.startswith(expected_prefix), (
            f"Expected cell starting with '{expected_prefix}', got: {result!r}"
        )

    @pytest.mark.parametrize("safe_input", [
        "Normal text",
        "12345",
        "essay_text_123",
        "hello world",
        None,
        42,
        3.14,
        True,
        False,
    ])
    def test_safe_values_not_prefixed(self, safe_input):
        result = sanitize_csv_cell(safe_input)
        assert not result.startswith("'"), (
            f"Safe value should not be prefixed, got: {result!r}"
        )

    def test_none_becomes_empty_string(self):
        assert sanitize_csv_cell(None) == ""

    def test_list_serialized_safely(self):
        result = sanitize_csv_cell(["text", "media"])
        assert '"text"' in result or "text" in result

    @pytest.mark.asyncio
    async def test_csv_export_all_rows_safe(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        """Every CSV cell in the export should be free of leading formula chars."""
        # Use demo batch b1 (done, 84 items)
        resp = await async_client.get(
            "/api/v1/batches/b1/export?format=csv",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert "text/csv" in resp.headers.get("content-type", "")
        reader = csv.reader(io.StringIO(resp.text))
        for row in reader:
            for cell in row:
                if cell:
                    assert cell[0] not in "=+-@", (
                        f"Unescaped formula-trigger character found in CSV cell: {cell!r}"
                    )

    def test_generate_batch_csv_escapes_injections(self):
        """generate_batch_csv should escape formula chars in batch name."""
        batch_data = {
            "id": "b_test",
            "name": "=HYPERLINK(\"evil.com\",\"Click\")",
            "source_type": "+malicious",
            "status": "done",
            "total_items": 10,
            "processed_items": 10,
            "failed_items": 0,
            "flagged_items": 2,
            "mean_confidence": 55.0,
            "score_distribution": {"0-20%": 2, "20-40%": 3, "40-60%": 2, "60-80%": 2, "80-100%": 1},
            "analysis_types": ["text"],
        }
        csv_str = generate_batch_csv(batch_data=batch_data)
        reader = csv.reader(io.StringIO(csv_str))
        rows = list(reader)
        # Header row + data row
        assert len(rows) >= 2
        for row in rows:
            for cell in row:
                if cell:
                    assert cell[0] not in "=+-@", f"Unsafe cell: {cell!r}"


# ═══════════════════════════════════════════════════════════════════════════════
# 8. JSON EXPORT STRUCTURE
# ═══════════════════════════════════════════════════════════════════════════════

class TestJsonExport:
    @pytest.mark.asyncio
    async def test_json_export_structure(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        """JSON export should include batch, cohort_report, and disclaimer."""
        resp = await async_client.get(
            "/api/v1/batches/b1/export?format=json",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        payload = resp.json()
        assert "export_type" in payload
        assert "authorship_disclaimer" in payload
        assert "batch" in payload
        assert "cohort_report" in payload
        assert "submissions" in payload

    @pytest.mark.asyncio
    async def test_json_export_disclaimer_content(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        """JSON export disclaimer must explicitly prohibit individual authorship inference."""
        resp = await async_client.get(
            "/api/v1/batches/b1/export?format=json",
            headers=admin_headers,
        )
        disclaimer = resp.json()["authorship_disclaimer"].lower()
        assert "authorship" in disclaimer or "individual" in disclaimer

    @pytest.mark.asyncio
    async def test_invalid_format_returns_400(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        resp = await async_client.get(
            "/api/v1/batches/b1/export?format=xlsx",
            headers=admin_headers,
        )
        assert resp.status_code == 400


# ═══════════════════════════════════════════════════════════════════════════════
# 9. AUTHORIZATION
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuthorization:
    @pytest.mark.asyncio
    async def test_ordinary_user_cannot_create_batch(
        self, async_client: AsyncClient, user_headers: dict
    ):
        resp = await async_client.post(
            "/api/v1/batches",
            json={"name": "unauthorized-batch", "workspace_id": "ws_test"},
            headers=user_headers,
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_ordinary_user_cannot_run_batch(
        self, async_client: AsyncClient, user_headers: dict
    ):
        resp = await async_client.post(
            "/api/v1/batches/b4/run", headers=user_headers
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_ordinary_user_cannot_get_report(
        self, async_client: AsyncClient, user_headers: dict
    ):
        resp = await async_client.get(
            "/api/v1/batches/b1/report", headers=user_headers
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_ordinary_user_cannot_export(
        self, async_client: AsyncClient, user_headers: dict
    ):
        resp = await async_client.get(
            "/api/v1/batches/b1/export?format=json", headers=user_headers
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_ordinary_user_can_list_batches(
        self, async_client: AsyncClient, user_headers: dict
    ):
        """All authenticated users may list batches."""
        resp = await async_client.get("/api/v1/batches", headers=user_headers)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_reviewer_can_get_report(
        self, async_client: AsyncClient, reviewer_headers: dict
    ):
        resp = await async_client.get(
            "/api/v1/batches/b1/report", headers=reviewer_headers
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_unauthenticated_request_rejected(
        self, async_client: AsyncClient
    ):
        resp = await async_client.get("/api/v1/batches")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_404_for_missing_batch(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        resp = await async_client.get(
            "/api/v1/batches/nonexistent_batch_id", headers=admin_headers
        )
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# 10. REPORT STRUCTURE — DIMENSION DECOUPLING
# ═══════════════════════════════════════════════════════════════════════════════

class TestReportStructure:
    @pytest.mark.asyncio
    async def test_cohort_report_has_dimension_breakdown(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        """dimension_breakdown must exist and contain separate dimension keys."""
        resp = await async_client.get(
            "/api/v1/batches/b1/report", headers=admin_headers
        )
        assert resp.status_code == 200
        report = resp.json()["data"]
        assert "dimension_breakdown" in report
        dim = report["dimension_breakdown"]
        # All expected dimension keys present (may be null for unconfigured dims)
        assert "text_ai_mean_pct" in dim
        assert "media_anomaly_rate_pct" in dim
        assert "text_similarity_mean_pct" in dim
        assert "rubric_compliance_mean_pct" in dim

    @pytest.mark.asyncio
    async def test_cohort_report_has_metric_definitions(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        """Metric definitions glossary must be included in every report."""
        resp = await async_client.get(
            "/api/v1/batches/b1/report", headers=admin_headers
        )
        report = resp.json()["data"]
        assert "metric_definitions" in report
        assert len(report["metric_definitions"]) > 0
        first_def = report["metric_definitions"][0]
        assert "name" in first_def
        assert "description" in first_def
        assert "limitations" in first_def


# ═══════════════════════════════════════════════════════════════════════════════
# 11. AUTHORSHIP DISCLAIMER
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuthorshipDisclaimer:
    def test_disclaimer_present_in_report_object(self):
        """Authorship disclaimer must be attached to every build_cohort_report()."""
        batch = {
            "id": "b_test", "name": "Test", "total_items": 10,
            "processed_items": 10, "failed_items": 0, "flagged_items": 2,
            "mean_confidence": 55.0, "status": "done",
            "score_distribution": {"0-20%": 3, "20-40%": 3, "40-60%": 2, "60-80%": 1, "80-100%": 1},
            "analysis_types": ["text"],
        }
        subs = [
            {"confidence_pct": 40 + i * 5, "content_type": "text",
             "flagged": False, "inconclusive": False}
            for i in range(10)
        ]
        report = build_cohort_report(batch=batch, submission_records=subs)
        assert report.authorship_disclaimer
        text = report.authorship_disclaimer.lower()
        assert "individual" in text or "authorship" in text

    @pytest.mark.asyncio
    async def test_api_report_includes_disclaimer(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        resp = await async_client.get(
            "/api/v1/batches/b1/report", headers=admin_headers
        )
        report = resp.json()["data"]
        assert "authorship_disclaimer" in report
        assert len(report["authorship_disclaimer"]) > 20


# ═══════════════════════════════════════════════════════════════════════════════
# 12. UNIT TESTS — cohort engine & sanitizer
# ═══════════════════════════════════════════════════════════════════════════════

class TestCohortEngine:
    def _make_batch(self, n: int, flagged: int = 0) -> dict:
        return {
            "id": "b_unit", "name": "UnitBatch",
            "total_items": n, "processed_items": n,
            "failed_items": 0, "flagged_items": flagged,
            "mean_confidence": 0.0, "status": "done",
            "score_distribution": None, "analysis_types": ["text"],
        }

    def test_prevalence_pct_correct(self):
        batch = self._make_batch(100, 25)
        report = build_cohort_report(batch=batch)
        assert report.prevalence_pct == 25.0

    def test_zero_total_items_no_division_error(self):
        batch = self._make_batch(0, 0)
        report = build_cohort_report(batch=batch)
        assert report.prevalence_pct == 0.0
        assert report.failure_rate_pct == 0.0

    def test_distribution_buckets_sum_to_n(self):
        batch = self._make_batch(10, 2)
        subs = [
            {"confidence_pct": i * 10, "content_type": "text",
             "flagged": False, "inconclusive": False}
            for i in range(1, 11)  # 10, 20, ..., 100
        ]
        report = build_cohort_report(batch=batch, submission_records=subs)
        if not report.privacy_suppressed:
            total = sum(report.score_distribution.values())
            assert total == len(subs)

    def test_inconclusive_rate_computed(self):
        batch = self._make_batch(10, 0)
        subs = [
            {"confidence_pct": 50.0, "content_type": "text",
             "flagged": False, "inconclusive": (i < 3)}  # 3 inconclusive
            for i in range(10)
        ]
        report = build_cohort_report(batch=batch, submission_records=subs)
        assert report.inconclusive_items == 3
        assert report.inconclusive_rate_pct == 30.0
