from fastapi import APIRouter
from sqlalchemy import text

from social_manager.api.dependencies import SessionDependency

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(session: SessionDependency) -> dict[str, str]:
    await session.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}
