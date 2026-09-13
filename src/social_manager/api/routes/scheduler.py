from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from social_manager.api.dependencies import CurrentUser, SessionDependency
from social_manager.services.scheduler import SchedulerService, app_scheduler

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


@router.get("/status")
async def get_scheduler_status(_: CurrentUser) -> dict[str, Any]:
    """Inspect the background scheduler status and recent run results."""
    return {
        "is_running": app_scheduler.is_running,
        "enabled": app_scheduler.settings.scheduler_enabled,
        "interval_seconds": app_scheduler.settings.scheduler_interval_seconds,
        "last_run_at": (
            app_scheduler.last_run_at.isoformat() if app_scheduler.last_run_at else None
        ),
        "last_run_result": app_scheduler.last_run_result,
    }


@router.post("/run")
async def run_scheduler_jobs(
    session: SessionDependency,
    _: CurrentUser,
    job: str | None = Query(
        default=None,
        description="Optional job filter: retention, expiry, measurements, connectors",
    ),
) -> dict[str, Any]:
    """Manually trigger due scheduler maintenance jobs."""
    service = SchedulerService()
    if job == "retention":
        result: Any = await service.purge_expired_retention(session)
    elif job == "expiry":
        result = {"expired_recommendations": await service.expire_stale_recommendations(session)}
    elif job == "measurements":
        result = {"scheduled_measurements": await service.trigger_due_measurements(session)}
    elif job == "connectors":
        result = {"expired_connectors": await service.check_connector_health(session)}
    else:
        result = await service.run_all_due_jobs(session)

    return {"status": "success", "job": job or "all", "result": result}
