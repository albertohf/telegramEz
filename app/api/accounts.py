"""
API Routes — Account management endpoints.
"""

from fastapi import APIRouter, HTTPException
from app.core.database import get_supabase
from app.models.schemas import AccountCreate, AccountResponse

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.post("/", response_model=AccountResponse)
async def create_account(req: AccountCreate):
    """Register a new Telegram account."""
    db = get_supabase()
    try:
        result = db.table("telegram_accounts").insert({
            "api_id": req.api_id,
            "api_hash": req.api_hash,
            "phone_number": req.phone_number,
            "session_name": req.session_name,
            "status": "disconnected",
        }).execute()
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list)
async def list_accounts():
    """List all registered accounts."""
    db = get_supabase()
    result = db.table("telegram_accounts").select(
        "id, api_id, phone_number, session_name, status, last_seen"
    ).execute()
    return result.data


@router.get("/{account_id}")
async def get_account(account_id: str):
    """Get a single account by ID."""
    db = get_supabase()
    result = db.table("telegram_accounts").select("*").eq("id", account_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Account not found")
    return result.data[0]


@router.delete("/{account_id}")
async def delete_account(account_id: str):
    """Delete a Telegram account."""
    db = get_supabase()
    result = db.table("telegram_accounts").delete().eq("id", account_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"success": True, "deleted": account_id}
