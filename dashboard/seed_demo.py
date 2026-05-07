#!/usr/bin/env python3
"""
DEMO DATA ONLY — do not run in production.

Inserts fake teams, API keys, and spend logs to populate the dashboard for demos.
All data is fictional and will replace existing data when run with --force.

Usage:
    docker-compose exec dashboard python seed_demo.py
    docker-compose exec dashboard python seed_demo.py --force   # clears existing data first
"""
import asyncio
import os
import random
import uuid
from datetime import datetime, timedelta, timezone

import asyncpg

DATABASE_URL = os.environ["DATABASE_URL"]

# EUR costs per token (USD price × 0.92)
MODELS = [
    {"name": "gpt-4o",            "input": 2.30e-6, "output": 9.20e-6, "weight": 35},
    {"name": "gpt-4o-mini",       "input": 0.138e-6,"output": 0.552e-6,"weight": 45},
    {"name": "claude-3-5-sonnet", "input": 2.76e-6, "output": 13.80e-6,"weight": 20},
]

TEAMS = [
    {
        "alias": "Data Science",
        "budget": 200.0,
        "target_spend": 171.0,   # 85% — triggers alert
        "num_logs": 220,
        "keys": ["notebook-analysis", "ml-pipeline", "experimentation"],
    },
    {
        "alias": "Engineering",
        "budget": 300.0,
        "target_spend": 126.0,   # 42%
        "num_logs": 160,
        "keys": ["backend-api", "ci-testing"],
    },
    {
        "alias": "Marketing",
        "budget": 100.0,
        "target_spend": 21.0,    # 21%
        "num_logs": 45,
        "keys": ["content-gen", "social-media"],
    },
    {
        "alias": "Finance",
        "budget": 50.0,
        "target_spend": 3.20,    # 6%
        "num_logs": 12,
        "keys": ["reports-gen"],
    },
]

NOW = datetime.now(timezone.utc)


def random_timestamp(days: int = 30) -> datetime:
    """Random timestamp within last N days, weighted toward recent days."""
    # beta distribution: more requests in recent days
    days_ago = random.betavariate(1.5, 4) * days
    hour = random.uniform(7, 22)  # business hours biased
    return NOW - timedelta(days=days_ago, hours=hour % 24)


def make_log(team_id: str, api_key: str, target_cost_remaining: float) -> dict:
    model = random.choices(MODELS, weights=[m["weight"] for m in MODELS])[0]
    prompt_tokens = random.randint(150, 2500)
    completion_tokens = random.randint(60, 900)
    spend = round(
        prompt_tokens * model["input"] + completion_tokens * model["output"], 6
    )
    start = random_timestamp()
    latency_ms = random.randint(350, 4000)
    return {
        "request_id": str(uuid.uuid4()),
        "call_type": "completion",
        "api_key": api_key,
        "model": model["name"],
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "spend": spend,
        "startTime": start.replace(tzinfo=None),
        "endTime": (start + timedelta(milliseconds=latency_ms)).replace(tzinfo=None),
        "completionStartTime": (start + timedelta(milliseconds=random.randint(100, latency_ms - 50))).replace(tzinfo=None),
        "team_id": team_id,
    }


async def seed(force: bool = False):
    conn = await asyncpg.connect(DATABASE_URL)

    existing = await conn.fetchval('SELECT COUNT(*) FROM "LiteLLM_TeamTable"')
    if existing > 0 and not force:
        print(f"Already {existing} teams in DB — skipping seed. Use --force to override.")
        await conn.close()
        return

    if force and existing > 0:
        print("--force: clearing existing data...")
        await conn.execute('DELETE FROM "LiteLLM_SpendLogs"')
        await conn.execute('DELETE FROM "LiteLLM_VerificationToken"')
        await conn.execute('DELETE FROM "LiteLLM_TeamTable"')
        print("Cleared.\n")

    print("Seeding demo data...\n")

    for team_data in TEAMS:
        team_id = str(uuid.uuid4())
        created = (NOW - timedelta(days=random.randint(45, 90))).replace(tzinfo=None)

        # ── Team ──────────────────────────────────────────────────────────────
        await conn.execute(
            """
            INSERT INTO "LiteLLM_TeamTable" (
                team_id, team_alias, max_budget, spend,
                members_with_roles, metadata, model_spend, model_max_budget,
                blocked, allow_team_guardrail_config,
                created_at, updated_at
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
            """,
            team_id, team_data["alias"], team_data["budget"], 0.0,
            "[]", "{}", "{}", "{}",
            False, False,
            created, created,
        )

        # ── API keys ──────────────────────────────────────────────────────────
        team_keys = []
        for alias in team_data["keys"]:
            token = f"sk-demo-{uuid.uuid4().hex[:24]}"
            team_keys.append(token)
            key_created = (NOW - timedelta(days=random.randint(10, 44))).replace(tzinfo=None)
            await conn.execute(
                """
                INSERT INTO "LiteLLM_VerificationToken" (
                    token, key_alias, team_id, spend,
                    aliases, config, permissions, metadata,
                    model_spend, model_max_budget, soft_budget_cooldown,
                    created_at
                ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
                """,
                token, alias, team_id, 0.0,
                "{}", "{}", "{}", "{}",
                "{}", "{}", False,
                key_created,
            )

        # ── Spend logs ────────────────────────────────────────────────────────
        # Scale number of logs so total spend ≈ target
        logs = []
        for _ in range(team_data["num_logs"]):
            key = random.choice(team_keys)
            logs.append(make_log(team_id, key, team_data["target_spend"]))

        # Normalise spend to hit target exactly
        raw_total = sum(l["spend"] for l in logs)
        scale = team_data["target_spend"] / raw_total if raw_total > 0 else 1.0
        total_spend = 0.0
        for log in logs:
            log["spend"] = round(log["spend"] * scale, 6)
            total_spend += log["spend"]

        await conn.executemany(
            """
            INSERT INTO "LiteLLM_SpendLogs" (
                request_id, call_type, api_key, model,
                prompt_tokens, completion_tokens, total_tokens,
                spend, "startTime", "endTime", "completionStartTime",
                team_id
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
            """,
            [
                (
                    l["request_id"], l["call_type"], l["api_key"], l["model"],
                    l["prompt_tokens"], l["completion_tokens"], l["total_tokens"],
                    l["spend"], l["startTime"], l["endTime"], l["completionStartTime"],
                    l["team_id"],
                )
                for l in logs
            ],
        )

        # Update team spend to match logs
        await conn.execute(
            'UPDATE "LiteLLM_TeamTable" SET spend = $1 WHERE team_id = $2',
            total_spend, team_id,
        )
        # Update key spends proportionally
        for token in team_keys:
            await conn.execute(
                'UPDATE "LiteLLM_VerificationToken" SET spend = $1 WHERE token = $2',
                round(total_spend / len(team_keys), 4), token,
            )

        pct = round(total_spend / team_data["budget"] * 100, 1)
        print(f"  ✓ {team_data['alias']:15} {team_data['num_logs']} requests  €{total_spend:.2f} / €{team_data['budget']:.0f}  ({pct}%)")

    await conn.close()
    print("\nDone — refresh localhost:3000")


if __name__ == "__main__":
    import sys
    asyncio.run(seed(force="--force" in sys.argv))
