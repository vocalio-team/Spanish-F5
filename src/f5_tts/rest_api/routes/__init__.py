"""
API route modules for F5-TTS REST API.

This package contains all API endpoint definitions organized by functionality.
"""

from fastapi import APIRouter

from . import tts, upload, tasks, analysis


def create_router() -> APIRouter:
    """
    Create and configure the main API router with all sub-routers.

    Returns:
        Configured APIRouter with all endpoints
    """
    router = APIRouter()

    # Include all sub-routers
    router.include_router(tts.router, tags=["TTS"])
    router.include_router(upload.router, tags=["Upload"])
    router.include_router(tasks.router, tags=["Tasks"])
    router.include_router(analysis.router, tags=["Analysis"])

    return router


__all__ = ["create_router"]
