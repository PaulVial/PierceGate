from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from database import get_pool
from services.spend_service import (
    get_all_teams,
    get_available_models,
    get_logs,
    get_model_distribution,
    get_overview_stats,
    get_recent_logs,
    get_team_daily_spend,
    get_team_detail,
    get_team_top_models,
)

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def base_context(active_page: str) -> dict:
    return {
        "active_page": active_page,
        "current_month": datetime.now().strftime("%B %Y"),
    }


@router.get("/", response_class=HTMLResponse)
async def overview(request: Request):
    pool = get_pool()
    stats = await get_overview_stats(pool)
    model_distribution = await get_model_distribution(pool)
    recent_logs = await get_recent_logs(pool)

    return templates.TemplateResponse("overview.html", {
        "request": request,
        "stats": stats,
        "teams": [],
        "model_distribution": model_distribution,
        "recent_logs": recent_logs,
        **base_context("overview"),
    })


@router.get("/teams", response_class=HTMLResponse)
async def teams_list(request: Request):
    pool = get_pool()
    teams = await get_all_teams(pool)
    return templates.TemplateResponse("teams_list.html", {
        "request": request,
        "teams": teams,
        **base_context("teams"),
    })


@router.get("/logs", response_class=HTMLResponse)
async def logs(
    request: Request,
    period: str = "month",
    model: str = "",
    status: str = "",
    page: int = 1,
):
    pool = get_pool()
    limit = 50
    log_rows, total_count = await get_logs(pool, period, model, status, page, limit)
    available_models = await get_available_models(pool)

    return templates.TemplateResponse("logs.html", {
        "request": request,
        "logs": log_rows,
        "total_count": total_count,
        "total_pages": max(1, -(-total_count // limit)),
        "page": page,
        "available_models": available_models,
        "filters": {"period": period, "model": model, "status": status},
        "query_string": request.url.query,
        **base_context("logs"),
    })


@router.get("/teams/{team_id}", response_class=HTMLResponse)
async def team_detail(request: Request, team_id: str):
    pool = get_pool()
    team = await get_team_detail(pool, team_id)
    if not team:
        return HTMLResponse("Team not found", status_code=404)

    top_models = await get_team_top_models(pool, team_id)
    daily_spend = await get_team_daily_spend(pool, team_id)
    recent_logs = await get_recent_logs(pool, limit=10)

    return templates.TemplateResponse("team.html", {
        "request": request,
        "team": team,
        "top_models": top_models,
        "daily_spend": daily_spend,
        "recent_logs": recent_logs,
        **base_context("teams"),
    })
