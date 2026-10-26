from datetime import datetime, timezone
from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import APIResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/metrics")
async def get_dashboard_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[Dict[str, Any]]:
    """Returns platform-wide intelligence metrics, sparkline points, and confidence gauges."""
    metrics_data = {
        "stats": [
            {
                "label": "Submissions Analyzed",
                "value": "14,821",
                "change": "+12.4% vs last month",
                "dir": "positive",
                "color": "purple",
                "count": 14821,
            },
            {
                "label": "AI-Flagged Items",
                "value": "3,204",
                "change": "+8.1% vs last month",
                "dir": "negative",
                "color": "orange",
                "count": 3204,
                "prevalence_pct": 21.6,
            },
            {
                "label": "Detector Confidence",
                "value": "94.7%",
                "change": "+1.2% model improvement",
                "dir": "positive",
                "color": "cyan",
                "confidence_pct": 94.7,
            },
            {
                "label": "Human Reviewed",
                "value": "8,106",
                "change": "+22.3% reviewer activity",
                "dir": "positive",
                "color": "green",
                "count": 8106,
            },
        ],
        "active_model": "text-detector-v2.4",
        "vision_engine": "vision-engine-v3.1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return APIResponse(data=metrics_data, message="Dashboard metrics loaded")


@router.get("/activities")
async def get_recent_activities(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[Dict[str, Any]]]:
    """Returns the recent submission stream with AI involvement severity tags."""
    activities = [
        {"id": "sub_0041", "icon": "ai-flag", "name": "Essay — Climate Change Policy", "meta": "hackathon-batch-4 · 2 min ago", "badge": "high", "badgeLabel": "High"},
        {"id": "sub_0027", "icon": "media", "name": "Video — Interview Recording", "meta": "media-queue · 8 min ago", "badge": "medium", "badgeLabel": "Medium"},
        {"id": "sub_0089", "icon": "ok", "name": "Research Abstract — ML Systems", "meta": "edu-cohort-2026 · 15 min ago", "badge": "low", "badgeLabel": "Low"},
        {"id": "sub_0012", "icon": "ai-flag", "name": "Cover Letter — Product Manager", "meta": "recruiter-portal · 32 min ago", "badge": "high", "badgeLabel": "High"},
        {"id": "sub_0063", "icon": "ok", "name": "Business Case — Supply Chain", "meta": "corp-eval-q4 · 1 hr ago", "badge": "inconclusive", "badgeLabel": "N/A"},
    ]
    return APIResponse(data=activities, message="Recent activities retrieved")


@router.get("/cohort-distribution")
async def get_cohort_distribution(
    current_user: User = Depends(get_current_user),
) -> APIResponse[List[Dict[str, Any]]]:
    """Returns cohort distribution percentages for donut chart."""
    cohorts = [
        {"name": "Education", "percentage": 40, "color": "#a855f7"},
        {"name": "Recruiting", "percentage": 24, "color": "#06b6d4"},
        {"name": "Hackathon", "percentage": 18, "color": "#10b981"},
        {"name": "Media", "percentage": 18, "color": "#f97316"},
    ]
    return APIResponse(data=cohorts, message="Cohort distribution retrieved")
