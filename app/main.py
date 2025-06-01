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
from sqlalchemy import text
import logging
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Async context manager for app lifespan events"""
    # Startup
    try:
        logger.info("Initializing database...")
        await session_manager.init()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise
    
    yield  # App runs here
    
    # Shutdown
    try:
        logger.info("Closing database connections...")
        await session_manager.close()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {str(e)}")

app = FastAPI(
    title="DigiPermit GH",
    description="API for DigiPermit GH, a digital permit management system",
    lifespan=lifespan,
    dependencies=[Depends(aget_db)]  # Auto-inject db session to all routes
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify your frontend URLs
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
