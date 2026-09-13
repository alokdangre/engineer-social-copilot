from __future__ import annotations

from typing import Any, cast

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.types import Command

from social_manager.agent.graphs.daily import build_daily_capture_graph
from social_manager.agent.graphs.outcome import build_outcome_graph
from social_manager.agent.graphs.profile import build_profile_graph
from social_manager.agent.graphs.recommendation import build_recommendation_graph
from social_manager.agent.graphs.research import build_research_graph
from social_manager.config import Settings, get_settings
from social_manager.domain.enums import WorkflowKind


class GraphRuntime:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.checkpointer: BaseCheckpointSaver[Any] | None = None
        self._postgres_context: Any = None
        self.graphs: dict[WorkflowKind, Any] = {}

    async def initialize(self) -> None:
        if self.checkpointer is not None:
            return
        if self.settings.checkpoint_database_url:
            self._postgres_context = AsyncPostgresSaver.from_conn_string(
                self.settings.checkpoint_database_url
            )
            postgres_saver = await self._postgres_context.__aenter__()
            await postgres_saver.setup()
            self.checkpointer = postgres_saver
        else:
            self.checkpointer = InMemorySaver()
        self.graphs = {
            WorkflowKind.PROFILE: build_profile_graph().compile(checkpointer=self.checkpointer),
            WorkflowKind.DAILY_CAPTURE: build_daily_capture_graph().compile(
                checkpointer=self.checkpointer
            ),
            WorkflowKind.RESEARCH: build_research_graph().compile(checkpointer=self.checkpointer),
            WorkflowKind.RECOMMENDATION_REVIEW: build_recommendation_graph().compile(
                checkpointer=self.checkpointer
            ),
            WorkflowKind.OUTCOME_STRATEGY: build_outcome_graph().compile(
                checkpointer=self.checkpointer
            ),
        }

    async def close(self) -> None:
        if self._postgres_context is not None:
            await self._postgres_context.__aexit__(None, None, None)
        self._postgres_context = None
        self.checkpointer = None
        self.graphs = {}

    async def start(
        self,
        kind: WorkflowKind,
        *,
        thread_id: str,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        graph = self._graph(kind)
        config = {"configurable": {"thread_id": thread_id}}
        return cast(dict[str, Any], await graph.ainvoke(state, config=config))

    async def resume(
        self,
        kind: WorkflowKind,
        *,
        thread_id: str,
        value: Any,
    ) -> dict[str, Any]:
        graph = self._graph(kind)
        config = {"configurable": {"thread_id": thread_id}}
        return cast(dict[str, Any], await graph.ainvoke(Command(resume=value), config=config))

    async def next_nodes(self, kind: WorkflowKind, thread_id: str) -> tuple[str, ...]:
        graph = self._graph(kind)
        snapshot = await graph.aget_state({"configurable": {"thread_id": thread_id}})
        return tuple(snapshot.next)

    def _graph(self, kind: WorkflowKind) -> Any:
        if not self.graphs:
            raise RuntimeError("Graph runtime has not been initialized")
        try:
            return self.graphs[kind]
        except KeyError as exc:
            raise ValueError(f"No graph is registered for {kind.value}") from exc


graph_runtime = GraphRuntime()
