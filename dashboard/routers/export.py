import csv
import io
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from database import get_pool
from services.spend_service import get_logs_for_export

router = APIRouter()


@router.get("/logs")
async def export_logs(
    request: Request,
    period: str = "month",
    model: str = "",
    status: str = "",
):
    pool = get_pool()
    rows = await get_logs_for_export(pool, period, model)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "time", "model", "team_id",
        "prompt_tokens", "completion_tokens", "total_tokens",
        "cost", "latency_ms",
    ])
    writer.writeheader()
    writer.writerows(rows)

    filename = f"piercegate_logs_{datetime.now().strftime('%Y-%m-%d')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
