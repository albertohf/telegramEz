"""
Worker Runner — Entry point for a standalone worker process.

Usage:
    python -m app.workers.runner --account-id <UUID>
"""

import argparse
import asyncio
import logging
import sys

from app.core.database import get_supabase
from app.workers.client import TelegramWorker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


def get_account(account_id: str) -> dict:
    db = get_supabase()
    result = db.table("telegram_accounts").select("*").eq("id", account_id).execute()
    if not result.data:
        logger.error(f"Account {account_id} not found in database.")
        sys.exit(1)
    return result.data[0]


async def main(account_id: str):
    account = get_account(account_id)
    logger.info(f"Starting worker for account: {account['session_name']} ({account_id})")

    worker = TelegramWorker(account)
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Shutting down worker...")
    finally:
        await worker.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a Telegram worker process")
    parser.add_argument("--account-id", required=True, help="UUID of the telegram_accounts row")
    args = parser.parse_args()

    asyncio.run(main(args.account_id))
