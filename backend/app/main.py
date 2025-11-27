"""FastAPI application entry point for Interview Simulator."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import feedback, health, interviews, questions, transcription, users
from app.config import settings
from app.data.seed_questions import seed_questions
from app.db import SessionLocal


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    print(f"Starting Interview Simulator v{app.version}")
    # TODO: Initialize database connections
    # TODO: Initialize Redis connection
    # TODO: Warm up AI models
    # Seed data in debug/local environments
    if settings.debug:
        async with SessionLocal() as session:
            await seed_questions(session)

    yield

    # Shutdown
    print("Shutting down Interview Simulator")
    # TODO: Close database connections
    # TODO: Close Redis connection


app = FastAPI(
    title="CareerSwiftr Interview Simulator",
    description="AI-powered interview practice platform for software engineers",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(questions.router, prefix="/api/v1/questions", tags=["Questions"])
app.include_router(interviews.router, prefix="/api/v1/interviews", tags=["Interviews"])
app.include_router(feedback.router, prefix="/api/v1/feedback", tags=["Feedback"])
app.include_router(transcription.router, prefix="/api/v1/transcription", tags=["Transcription"])


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint with API information."""
    return {
        "name": "CareerSwiftr Interview Simulator",
        "version": "0.1.0",
        "docs": "/docs",
    }
