"""API v1 router composition."""

from fastapi import APIRouter

from backend.app.api.v1.routes import analysis, health, interview, jd, reports, resume, sessions

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(jd.router, tags=["jd"])
api_router.include_router(resume.router, tags=["resume"])
api_router.include_router(analysis.router, tags=["analysis"])
api_router.include_router(interview.router, tags=["interview"])
api_router.include_router(reports.router, tags=["reports"])
api_router.include_router(sessions.router, tags=["sessions"])

# Future PRD-aligned routers belong here:
# - jd intake and analysis preview
# - resume intake and analysis preview
# - gap analysis and resume optimization
# - interview session orchestration
# - reports and dashboard history
