"""
API Routes — Worker management endpoints.
"""

from fastapi import APIRouter
from app.services.worker_manager import WorkerManager

router = APIRouter(prefix="/workers", tags=["Workers"])

# Singleton instance — shared across the app via lifespan
_manager: WorkerManager = None


def set_manager(manager: WorkerManager):
    global _manager
    _manager = manager


def get_manager() -> WorkerManager:
    return _manager


@router.post("/{account_id}/start")
async def start_worker(account_id: str):
    """Start a worker for the given account."""
    success = _manager.start_worker(account_id)
    return {"account_id": account_id, "started": success}


@router.post("/{account_id}/stop")
async def stop_worker(account_id: str):
    """Stop a worker for the given account."""
    success = _manager.stop_worker(account_id)
    return {"account_id": account_id, "stopped": success}


@router.get("/{account_id}/status")
async def worker_status(account_id: str):
    """Get the status of a worker."""
    status = _manager.get_status(account_id)
    return {"account_id": account_id, "status": status}


@router.get("/")
async def list_workers():
    """List all workers and their statuses."""
    return _manager.list_workers()
