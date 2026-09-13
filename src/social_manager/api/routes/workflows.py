from fastapi import APIRouter, HTTPException, Query, status

from social_manager.api.dependencies import CurrentUser, SessionDependency
from social_manager.domain.enums import WorkflowKind
from social_manager.domain.schemas import (
    RecommendationRead,
    WorkflowInvocationResult,
    WorkflowResume,
    WorkflowRunRead,
    WorkflowStart,
)
from social_manager.services.workflows import (
    WorkflowNotFoundError,
    WorkflowService,
    WorkflowStateError,
)

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("/start", response_model=WorkflowInvocationResult, status_code=status.HTTP_201_CREATED)
async def start_workflow(
    data: WorkflowStart, session: SessionDependency, user: CurrentUser
) -> WorkflowInvocationResult:
    try:
        run, recommendations = await WorkflowService().start(session, user.id, data)
    except (WorkflowStateError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return WorkflowInvocationResult(
        run=WorkflowRunRead.model_validate(run),
        recommendations=[RecommendationRead.model_validate(item) for item in recommendations],
    )


@router.post("/{thread_id}/resume", response_model=WorkflowInvocationResult)
async def resume_workflow(
    thread_id: str,
    data: WorkflowResume,
    session: SessionDependency,
    user: CurrentUser,
) -> WorkflowInvocationResult:
    try:
        run, recommendations = await WorkflowService().resume(session, user.id, thread_id, data)
    except WorkflowNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (WorkflowStateError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return WorkflowInvocationResult(
        run=WorkflowRunRead.model_validate(run),
        recommendations=[RecommendationRead.model_validate(item) for item in recommendations],
    )


@router.get("", response_model=list[WorkflowRunRead])
async def list_workflows(
    session: SessionDependency,
    user: CurrentUser,
    kind: WorkflowKind | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[WorkflowRunRead]:
    records = await WorkflowService().list(session, user.id, kind=kind, limit=limit)
    return [WorkflowRunRead.model_validate(item) for item in records]


@router.get("/{thread_id}", response_model=WorkflowRunRead)
async def get_workflow(
    thread_id: str, session: SessionDependency, user: CurrentUser
) -> WorkflowRunRead:
    try:
        run = await WorkflowService().get_owned(session, user.id, thread_id)
    except WorkflowNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return WorkflowRunRead.model_validate(run)
