from __future__ import annotations

import builtins
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from social_manager.agent.runtime import GraphRuntime, graph_runtime
from social_manager.db.models import Recommendation, WorkflowRun
from social_manager.domain.enums import WorkflowKind, WorkflowStatus
from social_manager.domain.schemas import WorkflowResume, WorkflowStart


class WorkflowNotFoundError(ValueError):
    pass


class WorkflowStateError(ValueError):
    pass


class WorkflowService:
    def __init__(self, runtime: GraphRuntime | None = None) -> None:
        self.runtime = runtime or graph_runtime

    async def start(
        self,
        session: AsyncSession,
        user_id: str,
        data: WorkflowStart,
    ) -> tuple[WorkflowRun, list[Recommendation]]:
        thread_id = data.thread_id or f"{data.kind.value}:{user_id}:{uuid.uuid4()}"
        duplicate = await session.scalar(
            select(WorkflowRun).where(WorkflowRun.thread_id == thread_id)
        )
        if duplicate is not None:
            raise WorkflowStateError("thread_id already exists")
        run = WorkflowRun(
            user_id=user_id,
            kind=data.kind.value,
            thread_id=thread_id,
            status=WorkflowStatus.RUNNING.value,
            input_data=data.input,
            started_at=datetime.now(UTC),
        )
        session.add(run)
        await session.commit()
        await session.refresh(run)
        try:
            result = await self.runtime.start(
                data.kind,
                thread_id=thread_id,
                state={
                    "user_id": user_id,
                    "workflow_run_id": run.id,
                    "thread_id": thread_id,
                    "input": data.input,
                    "errors": [],
                    "warnings": [],
                },
            )
            await self._apply_result(session, run, data.kind, result)
        except Exception as exc:
            run.status = WorkflowStatus.FAILED.value
            run.error = str(exc)[:4000]
            run.completed_at = datetime.now(UTC)
            await session.commit()
            raise
        recommendations = await self._recommendations_for_run(session, run.id)
        return run, recommendations

    async def resume(
        self,
        session: AsyncSession,
        user_id: str,
        thread_id: str,
        data: WorkflowResume,
    ) -> tuple[WorkflowRun, list[Recommendation]]:
        run = await self.get_owned(session, user_id, thread_id)
        if run.status != WorkflowStatus.INTERRUPTED.value:
            raise WorkflowStateError("Workflow is not waiting for input")
        kind = WorkflowKind(run.kind)
        resume_value: Any = data.review.model_dump(mode="json") if data.review else data.value
        run.status = WorkflowStatus.RUNNING.value
        run.interrupt_data = {}
        await session.commit()
        try:
            result = await self.runtime.resume(
                kind,
                thread_id=thread_id,
                value=resume_value,
            )
            await self._apply_result(session, run, kind, result)
        except Exception as exc:
            run.status = WorkflowStatus.FAILED.value
            run.error = str(exc)[:4000]
            run.completed_at = datetime.now(UTC)
            await session.commit()
            raise
        recommendations = await self._recommendations_for_run(session, run.id)
        return run, recommendations

    async def get_owned(self, session: AsyncSession, user_id: str, thread_id: str) -> WorkflowRun:
        run = await session.scalar(
            select(WorkflowRun).where(
                WorkflowRun.user_id == user_id,
                WorkflowRun.thread_id == thread_id,
            )
        )
        if run is None:
            raise WorkflowNotFoundError("Workflow run not found")
        return run

    async def list(
        self,
        session: AsyncSession,
        user_id: str,
        *,
        kind: WorkflowKind | None = None,
        limit: int = 100,
    ) -> builtins.list[WorkflowRun]:
        query = select(WorkflowRun).where(WorkflowRun.user_id == user_id)
        if kind:
            query = query.where(WorkflowRun.kind == kind.value)
        result = await session.scalars(query.order_by(WorkflowRun.created_at.desc()).limit(limit))
        return builtins.list(result)

    async def _apply_result(
        self,
        session: AsyncSession,
        run: WorkflowRun,
        kind: WorkflowKind,
        result: dict[str, Any],
    ) -> None:
        interrupt_payload = self._extract_interrupt(result)
        next_nodes = await self.runtime.next_nodes(kind, run.thread_id)
        run.current_node = next_nodes[0] if next_nodes else None
        run.output_data = result.get("output", {})
        run.error = None
        if interrupt_payload:
            run.status = WorkflowStatus.INTERRUPTED.value
            run.interrupt_data = interrupt_payload
            run.completed_at = None
        else:
            run.status = WorkflowStatus.COMPLETED.value
            run.interrupt_data = {}
            run.completed_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(run)

    @staticmethod
    def _extract_interrupt(result: dict[str, Any]) -> dict[str, Any]:
        raw = result.get("__interrupt__")
        if not raw:
            return {}
        values: list[Any] = []
        for item in raw if isinstance(raw, (tuple, list)) else [raw]:
            values.append(getattr(item, "value", item))
        return {"items": values}

    @staticmethod
    async def _recommendations_for_run(
        session: AsyncSession, workflow_run_id: str
    ) -> builtins.list[Recommendation]:
        result = await session.scalars(
            select(Recommendation)
            .where(Recommendation.workflow_run_id == workflow_run_id)
            .order_by(Recommendation.score.desc())
        )
        return builtins.list(result)
