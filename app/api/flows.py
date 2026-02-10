"""
API Routes — Flow management endpoints.
"""

from fastapi import APIRouter, HTTPException
from app.core.database import get_supabase
from app.models.schemas import FlowCreate, FlowResponse

router = APIRouter(prefix="/flows", tags=["Flows"])


@router.post("/", response_model=FlowResponse)
async def create_flow(req: FlowCreate):
    """Create a new flow with its steps."""
    db = get_supabase()
    try:
        # Insert the flow
        flow_result = db.table("flows").insert({
            "account_id": req.account_id,
            "name": req.name,
            "trigger_type": req.trigger_type.value,
            "trigger_content": req.trigger_content,
            "is_active": True,
        }).execute()
        flow = flow_result.data[0]

        # Insert steps
        steps_data = []
        for step in req.steps:
            steps_data.append({
                "flow_id": flow["id"],
                "step_order": step.order,
                "type": step.type.value,
                "payload": step.payload,
            })

        if steps_data:
            db.table("flow_steps").insert(steps_data).execute()

        # Return flow with steps
        flow["steps"] = steps_data
        return flow

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list)
async def list_flows(account_id: str = None):
    """List flows, optionally filtered by account."""
    db = get_supabase()
    query = db.table("flows").select("*")
    if account_id:
        query = query.eq("account_id", account_id)
    result = query.execute()
    return result.data


@router.get("/{flow_id}")
async def get_flow(flow_id: str):
    """Get a flow with all its steps."""
    db = get_supabase()
    flow = db.table("flows").select("*").eq("id", flow_id).execute()
    if not flow.data:
        raise HTTPException(status_code=404, detail="Flow not found")

    steps = (
        db.table("flow_steps")
        .select("*")
        .eq("flow_id", flow_id)
        .order("step_order")
        .execute()
    )

    result = flow.data[0]
    result["steps"] = steps.data
    return result


@router.patch("/{flow_id}/toggle")
async def toggle_flow(flow_id: str):
    """Toggle a flow's active status."""
    db = get_supabase()
    flow = db.table("flows").select("is_active").eq("id", flow_id).execute()
    if not flow.data:
        raise HTTPException(status_code=404, detail="Flow not found")

    new_status = not flow.data[0]["is_active"]
    db.table("flows").update({"is_active": new_status}).eq("id", flow_id).execute()
    return {"flow_id": flow_id, "is_active": new_status}


@router.delete("/{flow_id}")
async def delete_flow(flow_id: str):
    """Delete a flow and its steps (cascade)."""
    db = get_supabase()
    result = db.table("flows").delete().eq("id", flow_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Flow not found")
    return {"success": True, "deleted": flow_id}
