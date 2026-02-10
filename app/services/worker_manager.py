"""
WorkerManager — Spawns and tracks worker processes for Telegram accounts.
"""

import subprocess
import sys
import logging
from typing import Dict

from app.core.database import get_supabase

logger = logging.getLogger(__name__)


class WorkerManager:
    """Manages worker sub-processes, one per Telegram account."""

    def __init__(self):
        self._processes: Dict[str, subprocess.Popen] = {}
        self.db = get_supabase()

    def start_worker(self, account_id: str) -> bool:
        """Start a worker process for the given account."""
        if account_id in self._processes:
            proc = self._processes[account_id]
            if proc.poll() is None:
                logger.warning(f"Worker {account_id} is already running (pid={proc.pid}).")
                return False

        cmd = [
            sys.executable, "-m", "app.workers.runner",
            "--account-id", account_id,
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self._processes[account_id] = proc
        logger.info(f"Started worker for {account_id} (pid={proc.pid}).")
        return True

    def stop_worker(self, account_id: str) -> bool:
        """Stop the worker process for the given account."""
        proc = self._processes.get(account_id)
        if proc is None or proc.poll() is not None:
            logger.warning(f"No running worker for {account_id}.")
            self._processes.pop(account_id, None)
            return False

        proc.terminate()
        proc.wait(timeout=10)
        self._processes.pop(account_id, None)
        logger.info(f"Stopped worker for {account_id}.")
        return True

    def get_status(self, account_id: str) -> str:
        """Return the status of a worker: running, stopped, or unknown."""
        proc = self._processes.get(account_id)
        if proc is None:
            return "stopped"
        if proc.poll() is None:
            return "running"
        return "stopped"

    def list_workers(self) -> dict:
        """Return dict of {account_id: status}."""
        result = {}
        for aid, proc in list(self._processes.items()):
            result[aid] = "running" if proc.poll() is None else "stopped"
        return result

    def start_all(self):
        """Start workers for all accounts marked as 'connected' or 'disconnected'."""
        accounts = (
            self.db.table("telegram_accounts")
            .select("id")
            .neq("status", "banned")
            .execute()
        )
        for acc in accounts.data:
            self.start_worker(acc["id"])

    def stop_all(self):
        """Stop all running workers."""
        for aid in list(self._processes.keys()):
            self.stop_worker(aid)
