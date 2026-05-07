import httpx

from config import settings


async def _post(path: str, payload: dict) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{settings.litellm_url}{path}",
            json=payload,
            headers={"Authorization": f"Bearer {settings.litellm_master_key}"},
            timeout=10.0,
        )
        r.raise_for_status()
        return r.json()


async def create_team(name: str, budget: float) -> dict:
    return await _post("/team/new", {"team_alias": name, "max_budget": budget})


async def update_team_budget(team_id: str, budget: float) -> dict:
    return await _post("/team/update", {"team_id": team_id, "max_budget": budget})


async def delete_team(team_id: str) -> None:
    await _post("/team/delete", {"team_ids": [team_id]})


async def generate_key(team_id: str, alias: str, budget: float | None) -> dict:
    payload: dict = {"team_id": team_id, "key_alias": alias}
    if budget is not None:
        payload["max_budget"] = budget
    return await _post("/key/generate", payload)
