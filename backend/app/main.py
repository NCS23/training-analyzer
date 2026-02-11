"""
Training Analyzer Backend API

FastAPI application with Clean Architecture implementation.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.infrastructure.database.session import engine, init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan events"""
    # Startup
    print("🚀 Starting Training Analyzer API...")
    await init_db()
    print("✅ Database initialized")
    
    yield
    
    # Shutdown
    print("👋 Shutting down Training Analyzer API...")
    await engine.dispose()


# Create FastAPI app
app = FastAPI(
    title="Training Analyzer API",
    description="AI-powered half-marathon training analysis platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(
        content={
            "status": "healthy",
            "version": "0.1.0",
            "api_docs": "/docs",
        }
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return JSONResponse(
        content={
            "message": "Training Analyzer API",
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/health",
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
