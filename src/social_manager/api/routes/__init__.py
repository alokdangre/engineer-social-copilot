from fastapi import APIRouter

from social_manager.api.routes import (
    auth,
    connectors,
    content,
    goals,
    health,
    memory,
    recommendations,
    scheduler,
    strategies,
    users,
    workflows,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(connectors.router)
api_router.include_router(content.router)
api_router.include_router(memory.router)
api_router.include_router(goals.router)
api_router.include_router(workflows.router)
api_router.include_router(recommendations.router)
api_router.include_router(strategies.router)
api_router.include_router(scheduler.router)
