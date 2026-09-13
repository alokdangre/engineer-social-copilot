from fastapi import APIRouter, Query, status

from social_manager.api.dependencies import CurrentUser, SessionDependency
from social_manager.domain.enums import ContentType, Platform
from social_manager.domain.schemas import PlatformContentCreate, PlatformContentRead
from social_manager.services.content import ContentService

router = APIRouter(prefix="/content", tags=["source content"])


@router.post("", response_model=PlatformContentRead, status_code=status.HTTP_201_CREATED)
async def add_source_content(
    data: PlatformContentCreate,
    session: SessionDependency,
    user: CurrentUser,
) -> PlatformContentRead:
    record, _ = await ContentService().upsert(session, user.id, data)
    return PlatformContentRead.model_validate(record)


@router.get("", response_model=list[PlatformContentRead])
async def list_source_content(
    session: SessionDependency,
    user: CurrentUser,
    platform: Platform | None = None,
    content_type: ContentType | None = None,
    is_own: bool | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[PlatformContentRead]:
    records = await ContentService().list(
        session,
        user.id,
        platform=platform,
        content_type=content_type,
        is_own=is_own,
        limit=limit,
    )
    return [PlatformContentRead.model_validate(item) for item in records]
