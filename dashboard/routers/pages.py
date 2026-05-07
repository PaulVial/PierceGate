from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def overview(request: Request):
    return templates.TemplateResponse("overview.html", {"request": request})


@router.get("/teams/{team_id}", response_class=HTMLResponse)
async def team_detail(request: Request, team_id: str):
    return templates.TemplateResponse("team.html", {"request": request, "team_id": team_id})


@router.get("/logs", response_class=HTMLResponse)
async def logs(request: Request):
    return templates.TemplateResponse("logs.html", {"request": request})
