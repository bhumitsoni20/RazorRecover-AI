from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import init_db
from app.core.logging import logger, setup_logging

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up RazorRecover AI backend...")
    await init_db()
    from app.db.seed import seed_database
    await seed_database()
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

# CORS configuration - explicit origins required when allow_credentials=True
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$|^https://.*\.vercel\.app$",
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
        "dashboard_ui": f"{settings.FRONTEND_URL}/dashboard",
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
app.include_router(api_router, prefix="/api/v1")



if __name__ == "__main__":
    import os

    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=settings.ENVIRONMENT == "development")
