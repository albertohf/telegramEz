"""
TelegramEz — SaaS Telegram Automation Platform
Main API entry point.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn

from app.core.config import settings
from app.api import accounts, flows, workers as workers_api
from app.services.worker_manager import WorkerManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialize WorkerManager. Shutdown: stop all workers."""
    manager = WorkerManager()
    workers_api.set_manager(manager)

    logger.info("API started. WorkerManager ready.")
    yield

    logger.info("Shutting down — stopping all workers...")
    manager.stop_all()
    logger.info("All workers stopped.")


app = FastAPI(
    title="TelegramEz",
    description="SaaS Telegram Automation — Multi-account, Flows & Workers",
    version="1.0.0",
    lifespan=lifespan,
)

# Register routers
app.include_router(accounts.router)
app.include_router(flows.router)
app.include_router(workers_api.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL,
    )