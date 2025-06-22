from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import session_manager, aget_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.application import router as application_router
from app.api.v1.routers.inspections import router as inspection_router
from app.api.v1.routers.payments import router as payment_router
from app.api.v1.routers.reviews import router as review_router
from app.api.v1.routers.users import router as users_router
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
import logging
from contextlib import asynccontextmanager
from app.core.config import settings
from scripts.seed_db import seed_all, needs_seeding

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Async context manager for app lifespan events with integrated seeding"""
    # Startup
    try:
        logger.info("🚀 Starting application initialization...")
        
        # 1. Initialize database connection pool
        logger.info("🔌 Initializing database connection pool...")
        await session_manager.init()
        logger.info("✅ Database connection pool ready")
        
        # 2. Conditionally seed database
        if settings.SEED_ON_STARTUP:
            logger.info("🌱 Checking database seeding requirements...")
            async with session_manager.session() as db:
                try:
                    if await needs_seeding(db) or settings.FORCE_SEED:
                        logger.info("🛠 Starting database seeding...")
                        await seed_all(db)
                        logger.info("🎉 Database seeding completed successfully")
                    else:
                        logger.info("⏩ Database already seeded, skipping")
                except Exception as e:
                    logger.error(f"❌ Database seeding failed: {str(e)}")
                    if settings.REQUIRE_SEED:
                        raise RuntimeError("Critical seeding failed") from e
                    logger.warning("⚠️ Continuing with potentially incomplete data")
        else:
            logger.info("⏭ Database seeding disabled (SEED_ON_STARTUP=False)")
            
    except Exception as e:
        logger.critical(f"🔥 Application startup failed: {str(e)}")
        raise
    
    # Application runtime
    try:
        logger.info("🏁 Application startup complete")
        yield
    finally:
        # Shutdown
        try:
            logger.info("🛑 Beginning application shutdown...")
            logger.info("🔌 Closing database connections...")
            await session_manager.close()
            logger.info("✅ Database connections closed cleanly")
        except Exception as e:
            logger.error(f"⚠️ Error during shutdown: {str(e)}")
            raise
        finally:
            logger.info("👋 Application shutdown complete")
            

app = FastAPI(
    title="DigiPermit GH",
    description="API for DigiPermit GH, a digital permit management system",
    lifespan=lifespan,
    dependencies=[Depends(aget_db)]  # Auto-inject db session to all routes
)

# configure Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # For production, specify your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/", tags=["Health Check"])
async def health_check(db: AsyncSession = Depends(aget_db)):
    try:
        # Verify database connection
        await db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }

# Include routers
app.include_router(auth_router, tags=["auth"])
app.include_router(application_router, tags=["applications"])
app.include_router(inspection_router, tags=["inspections"])
app.include_router(payment_router, tags=["payments"])
app.include_router(review_router, tags=["reviews"])
app.include_router(users_router, tags=["users"])
