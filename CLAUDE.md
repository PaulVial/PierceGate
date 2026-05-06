# CLAUDE.md — Gateway IA Gouvernance EU

## Contexte du projet

Tu travailles sur **un gateway IA de gouvernance** destiné aux entreprises françaises et européennes.

Le produit est un **proxy transparent** qui s'intercale entre les applications d'une organisation et ses LLMs (APIs externes comme OpenAI, Anthropic, Mistral — et modèles internes self-hosted via vLLM ou Ollama).

L'objectif : donner aux équipes DSI, DAF et DPO une visibilité totale sur leur consommation LLM, des contrôles budgétaires automatiques, et une traçabilité conforme à l'AI Act européen.

**Positionnement :** l'alternative européenne à Portkey/LiteLLM — hébergé en France, conforme AI Act, avec des interfaces pensées pour les décideurs non-techniques.

**Choix stratégique :** LiteLLM est utilisé comme fondation (proxy core), pas réimplémenté. La valeur ajoutée est dans le dashboard de gouvernance, la conformité AI Act, et le packaging pour le marché français — pas dans le routage LLM que LiteLLM gère déjà très bien.

---

## Philosophie de développement

**Solid over clever.** À chaque fois que tu as le choix entre une solution simple et une solution élégante mais complexe, prends la simple. Ce projet doit être maintenable par une équipe de 2 personnes.

**Règles absolues :**
- Pas de sur-ingénierie. Pas de patterns abstraits inutiles.
- Chaque fonction fait une seule chose.
- Chaque module a une responsabilité claire.
- Si une feature n'est pas dans le sprint en cours, ne la code pas.
- Toujours écrire le test avant ou immédiatement après la feature.
- Pas de dépendance externe si la stdlib suffit.
- Zéro TODO laissé dans le code sans issue GitHub associée.

**Avant chaque feature :** demande si elle est dans le sprint actuel. Si non, on ne la code pas.

---

## Stack technique

```
Proxy core : LiteLLM proxy (configuré, pas réimplémenté)
Dashboard  : Python 3.11+ / FastAPI + Jinja2 (HTML server-side)
Base de données : PostgreSQL (asyncpg)
Cache      : Redis (optionnel, sprint 2)
Auth       : Clés API virtuelles LiteLLM + auth admin session cookie
Infra      : Docker + Docker Compose (gateway + postgres)
Hébergement: Scaleway Paris (région fr-par-1)
Monitoring : Prometheus + Grafana (sprint 2)
Frontend   : Next.js 14 + Tailwind CSS (sprint 2)
Tests      : pytest + httpx (async)
```

**Pourquoi ces choix :**
- LiteLLM proxy : le routing multi-provider est un problème résolu — on ne le réimplémente pas
- FastAPI + Jinja2 : le dashboard sprint 1 est du HTML server-side, pas besoin de React pour des tableaux
- PostgreSQL : LiteLLM peut logger directement dedans, on étend avec nos champs AI Act
- Docker Compose : deux services en sprint 1 (litellm + postgres), extensible en sprint 2

---

## Architecture du projet

```
docker-compose.yml           # litellm + postgres (+ redis sprint 2)
litellm_config.yaml          # Configuration providers, virtual keys, budgets
.env                         # Secrets (jamais en dur)

dashboard/                   # Notre code — la valeur ajoutée
├── main.py                  # Entrypoint FastAPI
├── config.py                # Config via env vars (pydantic-settings)
├── database.py              # Connexion PostgreSQL (asyncpg pool)
│
├── routers/
│   ├── dashboard.py         # Pages HTML (Jinja2) — vue DAF/DPO
│   ├── admin.py             # Gestion équipes, clés, budgets
│   └── export.py            # Export CSV, rapport DPO
│
├── services/
│   ├── spend_service.py     # Agrégation consommation par équipe/période
│   ├── budget_service.py    # Lecture budgets, calcul % consommé
│   ├── alert_service.py     # Email/Slack à 80% et 100% budget
│   └── aiact_service.py     # Hash intégrité, champs conformité, export DPO
│
├── templates/               # Jinja2 HTML
│   ├── overview.html        # Vue globale tokens + coût du mois
│   ├── team.html            # Vue par équipe
│   └── logs.html            # Historique avec filtres
│
├── migrations/              # SQL migrations (pas d'ORM, SQL pur)
│   ├── 001_initial.sql      # Tables LiteLLM étendues + nos champs AI Act
│   └── 002_budgets.sql
│
└── tests/
    ├── test_spend.py
    ├── test_budget.py
    └── test_aiact.py
```

**Ce que LiteLLM gère (configuration, pas code) :**
- Routing vers providers (OpenAI, Anthropic, Mistral, vLLM)
- Virtual keys et auth
- Logging tokens/coûts en PostgreSQL
- Budget caps et blocage automatique
- Streaming SSE

**Ce qu'on code (notre valeur) :**
- Dashboard lisible par un DAF
- Champs de conformité AI Act (hash intégrité, classification use case)
- Export DPO formaté
- Alertes email/Slack
- Packaging docker-compose clé en main

---

## Sprint 1 — MVP (objectif : 6 semaines)

**Ce qu'on build dans ce sprint, rien de plus.**

### Semaines 1-2 — Setup et configuration LiteLLM
Pas de code proxy à écrire. On configure LiteLLM avec les providers, on valide que le routing fonctionne, on branche PostgreSQL pour les logs.

- [ ] `docker-compose.yml` : litellm + postgres
- [ ] `litellm_config.yaml` : providers OpenAI, Anthropic, Mistral, vLLM
- [ ] Virtual keys configurées dans LiteLLM
- [ ] Budget caps configurés dans LiteLLM
- [ ] Logs qui tombent dans PostgreSQL
- [ ] Test end-to-end : appel via clé virtuelle → log en BDD
- [ ] Health check fonctionnel

### Semaines 2-4 — Le dashboard — notre vraie valeur
Interface que le DAF comprend en 2 minutes. Chiffres clairs, tableaux, pas de graphiques complexes.

- [ ] Auth admin (login/password, session cookie)
- [ ] Page overview : tokens totaux, coût total du mois, nb requêtes, budget global
- [ ] Vue par équipe : consommation, budget restant, % utilisé, top modèles
- [ ] Tableau logs : timestamp, équipe, modèle, tokens, coût, latence, statut
- [ ] Filtres logs : par équipe, par date, par modèle
- [ ] Export CSV des logs

### Semaines 4-5 — Champs AI Act
LiteLLM logge les métadonnées basiques. On ajoute par-dessus ce qui manque pour la conformité.

- [ ] Hash d'intégrité SHA-256 sur chaque log (immuabilité)
- [ ] Champ `use_case` sur chaque clé API (classification obligatoire AI Act)
- [ ] Champ `data_residency` : confirmation que les données restent en EU
- [ ] Export DPO : rapport formaté CSV/PDF sur une période
- [ ] Alerte email/Slack à 80% et 100% du budget (SMTP + webhook Slack)

### Semaine 6 — Packaging
`docker-compose up` et ça tourne dans le SI du client en 10 minutes.

- [ ] Variables d'env documentées dans `.env.example`
- [ ] Script de migration SQL au démarrage automatique
- [ ] README en français avec instructions de démarrage en 5 minutes
- [ ] Guide de configuration providers (OpenAI, Anthropic, Mistral, vLLM)
- [ ] Test de déploiement from scratch sur machine vierge

---

## Modèle de données (PostgreSQL)

```sql
-- Organisations
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Équipes
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id),
    name TEXT NOT NULL,
    budget_eur NUMERIC(10,4) DEFAULT 0,
    budget_period TEXT DEFAULT 'monthly',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Clés API virtuelles
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id),
    key_hash TEXT NOT NULL UNIQUE,   -- SHA-256 de la clé, jamais la clé en clair
    key_prefix TEXT NOT NULL,        -- "gw_sk_abc..." pour affichage
    provider TEXT NOT NULL,          -- openai | anthropic | mistral | vllm
    provider_key_encrypted TEXT,     -- Clé provider chiffrée (AES-256)
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    revoked_at TIMESTAMPTZ
);

-- Logs de requêtes
CREATE TABLE request_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_key_id UUID REFERENCES api_keys(id),
    team_id UUID REFERENCES teams(id),
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    tokens_input INTEGER DEFAULT 0,
    tokens_output INTEGER DEFAULT 0,
    cost_eur NUMERIC(10,6) DEFAULT 0,
    latency_ms INTEGER,
    status TEXT NOT NULL,            -- success | error | blocked
    http_status INTEGER,
    error_message TEXT,
    integrity_hash TEXT NOT NULL,    -- SHA-256 du log pour immuabilité
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index pour les requêtes fréquentes
CREATE INDEX idx_logs_team_date ON request_logs(team_id, created_at DESC);
CREATE INDEX idx_logs_created ON request_logs(created_at DESC);

-- Dépenses mensuelles par équipe (vue matérialisée)
CREATE TABLE monthly_spend (
    team_id UUID REFERENCES teams(id),
    year_month TEXT NOT NULL,        -- "2026-05"
    total_tokens_input BIGINT DEFAULT 0,
    total_tokens_output BIGINT DEFAULT 0,
    total_cost_eur NUMERIC(10,4) DEFAULT 0,
    request_count INTEGER DEFAULT 0,
    PRIMARY KEY (team_id, year_month)
);
```

---

## Conventions de code

**Nommage :**
- Variables et fonctions : `snake_case`
- Classes : `PascalCase`
- Constantes : `UPPER_SNAKE_CASE`
- Fichiers : `snake_case.py`

**Fonctions :**
```python
# Toujours typé
async def forward_request(
    request: ChatCompletionRequest,
    api_key: APIKey,
    team: Team,
) -> ChatCompletionResponse:
    """
    Forward la requête vers le provider configuré.
    Lève ProviderError si le provider est indisponible.
    Lève BudgetExceededError si le budget est dépassé.
    """
    ...
```

**Gestion d'erreurs :**
```python
# Toujours des exceptions métier explicites, jamais de raise Exception générique
class BudgetExceededError(Exception):
    def __init__(self, team_id: str, current_spend: float, budget: float):
        self.team_id = team_id
        self.current_spend = current_spend
        self.budget = budget

class ProviderError(Exception):
    def __init__(self, provider: str, status_code: int, message: str):
        ...
```

**Configuration :**
```python
# config.py — tout via env vars, jamais de valeur en dur
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    redis_url: str = "redis://localhost:6379"
    encryption_key: str          # AES-256 pour chiffrer les clés provider
    smtp_host: str = ""
    smtp_port: int = 587
    alert_from_email: str = ""
    
    class Config:
        env_file = ".env"
```

---

## Règles de sécurité non négociables

1. **Jamais de clé provider en clair en BDD.** Toujours chiffré AES-256.
2. **Jamais de clé API en clair en BDD.** Toujours SHA-256 hashé.
3. **Jamais de secrets dans le code.** Toujours via variables d'environnement.
4. **Jamais de contenu de requête loggé par défaut.** Seulement les métadonnées.
5. **Toujours valider l'authentification avant tout traitement.**
6. **Rate limiting sur les endpoints d'auth** (max 10 tentatives/minute par IP).

---

## Comment on travaille ensemble

**Au début de chaque session :**
- Paul indique sur quel module ou feature on travaille
- Demander si du contexte supplémentaire est nécessaire avant de coder
- Valider l'approche ensemble avant d'écrire du code

**Pendant le développement :**
- Coder une chose à la fois, pas tout un module d'un coup
- Après chaque fonction ou classe, montrer ce qui a été fait avant de continuer
- Si un problème de design est détecté, le signaler avant de coder autour
- Ne pas ajouter de feature hors sprint sans le signaler explicitement

**Ce qu'on évite :**
- Du code de 500 lignes sorti d'un coup sans validation intermédiaire
- Des abstractions prématurées ("on pourrait faire un plugin system pour...")
- Des dépendances ajoutées sans discussion
- Du code qui marche mais que Paul ne comprend pas

**Format de réponse préféré :**
1. L'approche en 3-4 lignes
2. Le code, fichier par fichier
3. Les tests associés
4. Ce qu'on fait ensuite

---

## Commandes utiles

```bash
# Démarrer en local (proxy + postgres)
docker-compose up -d

# Dashboard en dev (hot reload)
uvicorn dashboard.main:app --reload --port 3000

# Tests
pytest dashboard/tests/ -v

# Vérifier la santé du proxy
curl http://localhost:8000/health

# Tester le proxy (appel via clé virtuelle)
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer gw_sk_xxx" \
  -d '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "test"}]}'
```

---

## Ce qu'on ne fait PAS en sprint 1

- Pas de code proxy — LiteLLM le fait, on le configure
- Pas de frontend React/Next.js — Jinja2 server-side suffit pour des tableaux
- Pas de semantic caching
- Pas de PII detection
- Pas de SSO / OAuth
- Pas de multi-tenant avancé
- Pas de Kubernetes
- Pas d'IA dans le dashboard
- Pas de pricing dynamique
- Pas d'API de management programmatique complète

Ces features existent — elles sont dans le sprint 3. Pour l'instant on ship LiteLLM configuré + un dashboard de gouvernance lisible par un DAF + les champs AI Act. C'est tout.
