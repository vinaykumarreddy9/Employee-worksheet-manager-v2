from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import auth, timesheets, admin
from backend.config import settings
from datetime import datetime
import logging

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    app = FastAPI(
        title="Employee Timesheet Manager API",
        description="Professional backend for employee weekly timesheets.",
        version="1.0.0"
    )

    # CORS Configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], # In strict production, replace with specific domain
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include Routers
    app.include_router(auth.router)
    app.include_router(timesheets.router)
    app.include_router(admin.router)

    @app.on_event("startup")
    async def startup_event():
        from backend.database.db_config import engine
        from backend.database.models import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Application started successfully.")

    @app.get("/")
    async def root():
        return {"message": "Timesheet Manager API is running!"}

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}

    # Silent handlers for Streamlit internal checks to clean up logs
    @app.get("/_stcore/health")
    async def st_health():
        return {"status": "ok"}

    @app.get("/_stcore/host-config")
    async def st_host_config():
        return {"allowedOrigins": ["*"]}

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    # Settings derived from backend/config.py
    uvicorn.run("backend.main:app", host="0.0.0.0", port=settings.BACKEND_PORT, reload=True)
