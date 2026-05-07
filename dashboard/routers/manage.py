from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from database import get_pool
from services.litellm_service import (
    create_team,
    delete_team,
    generate_key,
    update_team_budget,
)

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# ── Teams ──────────────────────────────────────────────────────────────────────

@router.get("/teams/new", response_class=HTMLResponse)
async def team_new_form(request: Request):
    return templates.TemplateResponse("team_new.html", {"request": request, "error": None})


@router.post("/teams/new")
async def team_new(
    request: Request,
    name: str = Form(...),
    budget: float = Form(...),
):
    try:
        await create_team(name, budget)
    except Exception as e:
        return templates.TemplateResponse(
            "team_new.html", {"request": request, "error": str(e)}, status_code=400
        )
    return RedirectResponse(url="/teams", status_code=302)


@router.post("/teams/{team_id}/budget")
async def team_update_budget(team_id: str, budget: float = Form(...)):
    await update_team_budget(team_id, budget)
    return RedirectResponse(url=f"/teams/{team_id}", status_code=302)


@router.post("/teams/{team_id}/delete")
async def team_delete(team_id: str):
    await delete_team(team_id)
    return RedirectResponse(url="/teams", status_code=302)


# ── Keys ───────────────────────────────────────────────────────────────────────

@router.get("/teams/{team_id}/keys/new", response_class=HTMLResponse)
async def key_new_form(request: Request, team_id: str):
    return templates.TemplateResponse(
        "key_new.html", {"request": request, "team_id": team_id, "error": None}
    )


@router.post("/teams/{team_id}/keys/new")
async def key_new(
    request: Request,
    team_id: str,
    alias: str = Form(...),
    budget: str = Form(""),
):
    budget_val = float(budget) if budget.strip() else None
    try:
        result = await generate_key(team_id, alias, budget_val)
    except Exception as e:
        return templates.TemplateResponse(
            "key_new.html",
            {"request": request, "team_id": team_id, "error": str(e)},
            status_code=400,
        )
    return templates.TemplateResponse("key_created.html", {
        "request": request,
        "team_id": team_id,
        "key": result["key"],
        "alias": alias,
    })


@router.post("/keys/revoke")
async def key_revoke(token: str = Form(...), team_id: str = Form(...)):
    pool = get_pool()
    await pool.execute(
        'UPDATE "LiteLLM_VerificationToken" SET "blocked" = true WHERE token = $1',
        token,
    )
    return RedirectResponse(url=f"/teams/{team_id}", status_code=302)
