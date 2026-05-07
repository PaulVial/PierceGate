# PierceGate

> Open-source AI gateway for European enterprises — built on LiteLLM, designed for DSI, DAF and DPO teams.

PierceGate sits between your applications and any LLM provider (OpenAI, Anthropic, Mistral, vLLM). It gives your organization real-time cost visibility, per-team budget enforcement, and tamper-proof audit logs — with a dashboard readable by non-technical decision makers.

**Self-hosted. EU data residency. AI Act ready.**

---

## Features

- **Transparent proxy** — swap `base_url` and `api_key`, zero code changes required
- **Multi-provider routing** — OpenAI, Anthropic, Mistral, vLLM (self-hosted)
- **Virtual API keys** — map team keys to real provider keys, stored server-side only
- **Budget caps** — monthly limits per team, automatic blocking at 100%, alerts at 80%
- **Structured logging** — every request logged with tokens, cost, latency, and integrity hash
- **AI Act compliance** — use case classification, immutable logs, DPO export
- **Governance dashboard** — consumption overview readable by a CFO in under 2 minutes

---

## Requirements

- Docker and Docker Compose
- API key for at least one provider (OpenAI, Anthropic, or Mistral)

---

## Quick start

```bash
# 1. Clone the repository
git clone https://github.com/your-org/piercegate.git
cd piercegate

# 2. Configure your environment
cp .env.example .env
# Edit .env — add your provider API keys and set strong secret values

# 3. Start
docker-compose up -d

# 4. Verify
curl http://localhost:8000/health   # LiteLLM proxy
curl http://localhost:3000/health   # Dashboard
```

The proxy is now live at `http://localhost:8000`.

---

## Connecting your application

Change two environment variables in your existing code — nothing else.

```bash
OPENAI_API_KEY=gw_sk_your_virtual_key   # issued from the dashboard
OPENAI_BASE_URL=http://your-gateway:8000
```

All OpenAI-compatible SDKs (Python, Node.js, curl) will route through PierceGate automatically.

---

## Configuration

### `.env` reference

| Variable | Required | Description |
|----------|----------|-------------|
| `POSTGRES_USER` | Yes | PostgreSQL username |
| `POSTGRES_PASSWORD` | Yes | PostgreSQL password |
| `POSTGRES_DB` | Yes | PostgreSQL database name |
| `DATABASE_URL` | Yes | Full PostgreSQL connection URL |
| `LITELLM_MASTER_KEY` | Yes | Admin key for LiteLLM proxy (`sk-...`) |
| `SECRET_KEY` | Yes | Dashboard session secret (min 32 chars) |
| `OPENAI_API_KEY` | No | Required if routing to OpenAI |
| `ANTHROPIC_API_KEY` | No | Required if routing to Anthropic |
| `MISTRAL_API_KEY` | No | Required if routing to Mistral |
| `SMTP_HOST` | No | SMTP server for budget alerts |
| `SLACK_WEBHOOK_URL` | No | Slack webhook for budget alerts |

### Adding providers

Edit `litellm_config.yaml` to add or remove providers. Changes take effect after restarting the `litellm` container.

---

## Architecture

```
Your application
    │  OPENAI_BASE_URL=http://gateway:8000
    ▼
┌─────────────────────┐
│   LiteLLM Proxy     │  :8000 — routing, virtual keys, budget enforcement
└─────────────────────┘
    │                 └──→ PostgreSQL (logs, spend, keys)
    ▼
Provider API (OpenAI / Anthropic / Mistral / vLLM)

┌─────────────────────┐
│   Dashboard         │  :3000 — governance UI, alerts, DPO export
└─────────────────────┘
    │
    └──→ PostgreSQL (reads same database)
```

---

## Development

```bash
# Run database migrations
python migrations/run.py

# Start dashboard in dev mode (hot reload)
cd dashboard
pip install -r requirements.txt
uvicorn main:app --reload --port 3000

# Run tests
pytest tests/ -v
```

---

## Project structure

```
piercegate/
├── docker-compose.yml       # Orchestrates litellm + postgres + dashboard
├── litellm_config.yaml      # Provider routing configuration
├── .env.example             # Environment variables template
├── dashboard/               # Governance dashboard (FastAPI)
│   ├── routers/             # HTTP routes (pages, admin, export)
│   ├── services/            # Business logic (spend, budgets, alerts, AI Act)
│   ├── templates/           # Jinja2 HTML templates
│   └── tests/
└── migrations/              # SQL migrations (run once at setup)
```

---

## Roadmap

- **Sprint 1** — Proxy + governance dashboard + AI Act compliance fields
- **Sprint 2** — Redis cache, Prometheus/Grafana monitoring, SSO
- **Sprint 3** — SaaS hosted option, semantic caching, PII detection

---

## License

MIT
