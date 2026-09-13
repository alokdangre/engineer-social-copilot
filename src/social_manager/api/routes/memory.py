from fastapi import APIRouter, HTTPException, Query, status

from social_manager.api.dependencies import CurrentUser, SessionDependency
from social_manager.domain.enums import MemoryCategory, Visibility
from social_manager.domain.schemas import (
    MemoryCreate,
    MemoryLinkCreate,
    MemoryLinkRead,
    MemoryRead,
    MemoryUpdate,
)
from social_manager.services.memory import MemoryNotFoundError, MemoryService

router = APIRouter(prefix="/memory", tags=["memory"])


@router.post("", response_model=MemoryRead, status_code=status.HTTP_201_CREATED)
async def create_memory(
    data: MemoryCreate, session: SessionDependency, user: CurrentUser
) -> MemoryRead:
    try:
        record = await MemoryService().create(session, user.id, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return MemoryRead.model_validate(record)


@router.get("", response_model=list[MemoryRead])
async def list_memory(
    session: SessionDependency,
    user: CurrentUser,
    category: MemoryCategory | None = None,
    visibility: Visibility | None = None,
    query: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[MemoryRead]:
    records = await MemoryService().list(
        session,
        user.id,
        category=category,
        visibility=visibility,
        query=query,
        limit=limit,
    )
    return [MemoryRead.model_validate(item) for item in records]


@router.get("/{record_id}", response_model=MemoryRead)
async def get_memory(record_id: str, session: SessionDependency, user: CurrentUser) -> MemoryRead:
    try:
        record = await MemoryService().get_owned(session, user.id, record_id)
    except MemoryNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return MemoryRead.model_validate(record)


@router.patch("/{record_id}", response_model=MemoryRead)
async def update_memory(
    record_id: str,
    data: MemoryUpdate,
    session: SessionDependency,
    user: CurrentUser,
) -> MemoryRead:
    try:
        record = await MemoryService().update(session, user.id, record_id, data)
    except MemoryNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return MemoryRead.model_validate(record)


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(record_id: str, session: SessionDependency, user: CurrentUser) -> None:
    try:
        await MemoryService().soft_delete(session, user.id, record_id)
    except MemoryNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/links", response_model=MemoryLinkRead, status_code=status.HTTP_201_CREATED)
async def create_memory_link(
    data: MemoryLinkCreate, session: SessionDependency, user: CurrentUser
) -> MemoryLinkRead:
    try:
        link = await MemoryService().create_link(session, user.id, data)
    except MemoryNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return MemoryLinkRead.model_validate(link)
