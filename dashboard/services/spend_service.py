from datetime import datetime, timedelta

import asyncpg


def _period_clause(period: str) -> str:
    if period == "7d":
        return '"startTime" >= NOW() - INTERVAL \'7 days\''
    if period == "30d":
        return '"startTime" >= NOW() - INTERVAL \'30 days\''
    if period == "all":
        return "1=1"
    return f"TO_CHAR(\"startTime\", 'YYYY-MM') = '{datetime.now().strftime('%Y-%m')}'"


async def get_logs(
    pool: asyncpg.Pool,
    period: str = "month",
    model: str = "",
    status: str = "",
    page: int = 1,
    limit: int = 50,
) -> tuple[list[dict], int]:
    where = [_period_clause(period)]
    if model:
        where.append(f"model = '{model}'")

    where_sql = " AND ".join(where)
    offset = (page - 1) * limit

    rows = await pool.fetch(
        f"""
        SELECT
            "startTime", "endTime", model,
            prompt_tokens, completion_tokens, spend
        FROM "LiteLLM_SpendLogs"
        WHERE {where_sql}
        ORDER BY "startTime" DESC
        LIMIT $1 OFFSET $2
        """,
        limit, offset,
    )
    total = await pool.fetchval(
        f'SELECT COUNT(*) FROM "LiteLLM_SpendLogs" WHERE {where_sql}'
    )

    logs = []
    for r in rows:
        latency = "—"
        if r["endTime"] and r["startTime"]:
            latency = int((r["endTime"] - r["startTime"]).total_seconds() * 1000)
        logs.append({
            "time": r["startTime"].strftime("%Y-%m-%d %H:%M:%S"),
            "model": r["model"],
            "prompt_tokens": r["prompt_tokens"] or 0,
            "completion_tokens": r["completion_tokens"] or 0,
            "cost": float(r["spend"]),
            "latency": latency,
            "status": "success",
        })
    return logs, total


async def get_team_detail(pool: asyncpg.Pool, team_id: str) -> dict | None:
    team = await pool.fetchrow(
        'SELECT team_id, team_alias, max_budget, spend FROM "LiteLLM_TeamTable" WHERE team_id = $1',
        team_id,
    )
    if not team:
        return None

    year_month = datetime.now().strftime("%Y-%m")
    stats = await pool.fetchrow(
        """
        SELECT COUNT(*) AS total_requests, COALESCE(SUM(spend), 0) AS month_spend
        FROM "LiteLLM_SpendLogs"
        WHERE team_id = $1 AND TO_CHAR("startTime", 'YYYY-MM') = $2
        """,
        team_id, year_month,
    )
    budget = float(team["max_budget"] or 0)
    spend = float(stats["month_spend"])
    pct = round(spend / budget * 100, 1) if budget > 0 else 0

    keys = await pool.fetch(
        """
        SELECT token, key_alias, spend, created_at, "blocked"
        FROM "LiteLLM_VerificationToken"
        WHERE team_id = $1
        ORDER BY created_at DESC
        """,
        team_id,
    )

    return {
        "id": team_id,
        "name": team["team_alias"] or team_id,
        "budget": budget,
        "spend": spend,
        "pct": pct,
        "total_requests": stats["total_requests"],
        "active_keys": sum(1 for k in keys if not k["blocked"]),
        "api_keys": [
            {
                "prefix": k["token"][:12],
                "name": k["key_alias"] or "",
                "spend": float(k["spend"] or 0),
                "created_at": k["created_at"].strftime("%Y-%m-%d") if k["created_at"] else "—",
                "is_active": not k["blocked"],
            }
            for k in keys
        ],
    }


async def get_team_top_models(pool: asyncpg.Pool, team_id: str) -> list[dict]:
    year_month = datetime.now().strftime("%Y-%m")
    rows = await pool.fetch(
        """
        SELECT model,
               ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct
        FROM "LiteLLM_SpendLogs"
        WHERE team_id = $1 AND TO_CHAR("startTime", 'YYYY-MM') = $2
        GROUP BY model ORDER BY pct DESC LIMIT 5
        """,
        team_id, year_month,
    )
    return [{"name": r["model"], "pct": float(r["pct"])} for r in rows]


async def get_team_daily_spend(pool: asyncpg.Pool, team_id: str) -> list[dict]:
    rows = await pool.fetch(
        """
        SELECT DATE("startTime") AS day, COALESCE(SUM(spend), 0) AS cost
        FROM "LiteLLM_SpendLogs"
        WHERE team_id = $1 AND "startTime" >= NOW() - INTERVAL '30 days'
        GROUP BY day ORDER BY day
        """,
        team_id,
    )
    return [{"date": str(r["day"]), "cost": float(r["cost"])} for r in rows]


async def get_all_teams(pool: asyncpg.Pool) -> list[dict]:
    year_month = datetime.now().strftime("%Y-%m")
    rows = await pool.fetch(
        """
        SELECT
            t.team_id, t.team_alias, t.max_budget, t.spend,
            COALESCE(s.request_count, 0) AS request_count
        FROM "LiteLLM_TeamTable" t
        LEFT JOIN (
            SELECT team_id, COUNT(*) AS request_count
            FROM "LiteLLM_SpendLogs"
            WHERE TO_CHAR("startTime", 'YYYY-MM') = $1
            GROUP BY team_id
        ) s ON s.team_id = t.team_id
        ORDER BY t.team_alias
        """,
        year_month,
    )
    result = []
    for r in rows:
        budget = float(r["max_budget"] or 0)
        spend = float(r["spend"] or 0)
        pct = round(spend / budget * 100, 1) if budget > 0 else 0
        result.append({
            "id": r["team_id"],
            "name": r["team_alias"] or r["team_id"],
            "budget": budget,
            "spend": spend,
            "pct": pct,
            "request_count": r["request_count"],
        })
    return result


async def get_available_models(pool: asyncpg.Pool) -> list[str]:
    rows = await pool.fetch(
        'SELECT DISTINCT model FROM "LiteLLM_SpendLogs" ORDER BY model'
    )
    return [r["model"] for r in rows]


async def get_overview_stats(pool: asyncpg.Pool) -> dict:
    year_month = datetime.now().strftime("%Y-%m")
    row = await pool.fetchrow(
        """
        SELECT
            COUNT(*)                        AS total_requests,
            COALESCE(SUM(spend), 0)         AS total_cost
        FROM "LiteLLM_SpendLogs"
        WHERE TO_CHAR("startTime", 'YYYY-MM') = $1
        """,
        year_month,
    )
    return {
        "total_requests": row["total_requests"],
        "total_cost": float(row["total_cost"]),
        "budget_pct": 0,
        "active_teams": 0,
    }


async def get_model_distribution(pool: asyncpg.Pool) -> list[dict]:
    year_month = datetime.now().strftime("%Y-%m")
    rows = await pool.fetch(
        """
        SELECT
            model,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct
        FROM "LiteLLM_SpendLogs"
        WHERE TO_CHAR("startTime", 'YYYY-MM') = $1
        GROUP BY model
        ORDER BY pct DESC
        LIMIT 5
        """,
        year_month,
    )
    colors = ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"]
    return [
        {"model": r["model"], "pct": float(r["pct"]), "color": colors[i]}
        for i, r in enumerate(rows)
    ]


async def get_recent_logs(pool: asyncpg.Pool, limit: int = 10) -> list[dict]:
    rows = await pool.fetch(
        """
        SELECT
            "startTime",
            model,
            total_tokens,
            spend,
            "completionStartTime"
        FROM "LiteLLM_SpendLogs"
        ORDER BY "startTime" DESC
        LIMIT $1
        """,
        limit,
    )
    return [
        {
            "time": r["startTime"].strftime("%H:%M:%S"),
            "team": "—",
            "model": r["model"],
            "tokens": r["total_tokens"],
            "cost": float(r["spend"]),
            "latency": (
                int((r["completionStartTime"] - r["startTime"]).total_seconds() * 1000)
                if r["completionStartTime"] and r["startTime"]
                else "—"
            ),
            "status": "success",
        }
        for r in rows
    ]
