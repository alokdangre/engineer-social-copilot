"""Bounded LangGraph workflow definitions."""

from social_manager.agent.graphs.daily import daily_capture_graph
from social_manager.agent.graphs.outcome import outcome_strategy_graph
from social_manager.agent.graphs.profile import profile_graph
from social_manager.agent.graphs.recommendation import recommendation_review_graph
from social_manager.agent.graphs.research import ecosystem_research_graph

__all__ = [
    "daily_capture_graph",
    "ecosystem_research_graph",
    "outcome_strategy_graph",
    "profile_graph",
    "recommendation_review_graph",
]
