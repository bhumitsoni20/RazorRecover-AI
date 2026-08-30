from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db
from app.core.logging import setup_logging, logger
from app.api.v1.api import api_router

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up RazorRecover AI backend...")
    await init_db()
    logger.info("RazorRecover AI backend initialized successfully.")
    yield
    logger.info("Shutting down RazorRecover AI backend...")


app = FastAPI(
    title="RazorRecover AI - Autonomous Revenue Recovery API",
    description="Autonomous AI revenue recovery platform for merchants built for Razorpay AI Buildathon 2026.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENVIRONMENT == "development" else settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": "RazorRecover AI Backend API",
        "status": "online",
        "docs_url": "/docs",
        "health_url": "/api/health",
        "dashboard_ui": "http://localhost:3000/dashboard",
    }


# Health endpoint
@app.get("/api/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "razorrecover-backend",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "razorpay_mode": "test_mode",
    }


# Include API v1 routes
app.include_router(api_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
