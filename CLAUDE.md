# CLAUDE.md — Gateway IA Gouvernance EU

## Contexte du projet

Tu travailles sur **un gateway IA de gouvernance** destiné aux entreprises françaises et européennes.

Le produit est un **proxy transparent** qui s'intercale entre les applications d'une organisation et ses LLMs (APIs externes comme OpenAI, Anthropic, Mistral — et modèles internes self-hosted via vLLM ou Ollama).

L'objectif : donner aux équipes DSI, DAF et DPO une visibilité totale sur leur consommation LLM, des contrôles budgétaires automatiques, et une traçabilité conforme à l'AI Act européen.

**Positionnement :** l'alternative européenne à Portkey/LiteLLM — hébergé en France, conforme AI Act, avec des interfaces pensées pour les décideurs non-techniques.

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
Backend    : Python 3.11+ / FastAPI
Proxy core : LiteLLM (fork ou wrapper — à décider ensemble)
Base de données : PostgreSQL (asyncpg)
Cache      : Redis (optionnel, sprint 2)
Auth       : JWT + clés API virtuelles (HMAC SHA-256)
Infra      : Docker + Docker Compose
Hébergement: Scaleway Paris (région fr-par-1)
Monitoring : Prometheus + Grafana (sprint 2)
Frontend   : Next.js 14 + Tailwind CSS (sprint 2)
Tests      : pytest + httpx (async)
```

**Pourquoi ces choix :**
- FastAPI : async natif, typage fort, OpenAPI auto-généré, standard industrie
- LiteLLM : supporte 200+ providers, format OpenAI-compatible, MIT license
- PostgreSQL : robuste, jsonb pour les logs flexibles, requêtes analytiques performantes
- Docker Compose : déployable n'importe où, reproductible, simple à maintenir

---

## Architecture du projet

```
gateway/
├── main.py                  # Entrypoint FastAPI
├── config.py                # Config via env vars (pydantic-settings)
├── database.py              # Connexion PostgreSQL (asyncpg pool)
│
├── routers/
│   ├── proxy.py             # Routes proxy LLM (/v1/chat/completions, etc.)
│   ├── auth.py              # Gestion clés API virtuelles
│   ├── budget.py            # Budget caps et alertes
│   └── logs.py              # Consultation et export des logs
│
├── services/
│   ├── proxy_service.py     # Logique forwarding vers providers
│   ├── token_counter.py     # Comptage tokens précis
│   ├── cost_calculator.py   # Calcul coût en temps réel
│   ├── budget_service.py    # Vérification et enforcement budgets
│   └── log_service.py       # Écriture logs immuables
│
├── models/
│   ├── api_key.py           # Modèle clé API virtuelle
│   ├── request_log.py       # Modèle log de requête
│   ├── budget.py            # Modèle budget par équipe
│   └── team.py              # Modèle équipe/organisation
│
├── middleware/
│   ├── auth_middleware.py   # Validation clé API sur chaque requête
│   ├── budget_middleware.py # Vérification budget avant forwarding
│   └── log_middleware.py    # Logging automatique après chaque requête
│
├── migrations/              # SQL migrations (pas d'ORM, SQL pur)
│   ├── 001_initial.sql
│   └── 002_budgets.sql
│
└── tests/
    ├── test_proxy.py
    ├── test_budget.py
    └── test_logs.py
```

---

## Sprint 1 — MVP (objectif : 6 semaines)

**Ce qu'on build dans ce sprint, rien de plus.**

### Module 1 — Gateway proxy (semaines 1-2)
- [ ] Endpoint `/v1/chat/completions` compatible OpenAI SDK
- [ ] Support providers : OpenAI, Anthropic, Mistral (API), vLLM (local)
- [ ] Forwarding de la requête vers le bon provider
- [ ] Streaming support (Server-Sent Events)
- [ ] Gestion des erreurs provider avec message clair
- [ ] Overhead cible : < 10ms hors latence provider

### Module 2 — Auth et clés API (semaine 2)
- [ ] Génération de clés API virtuelles (`gw_sk_...`)
- [ ] Stockage sécurisé en BDD (hash SHA-256, jamais en clair)
- [ ] Révocation instantanée d'une clé
- [ ] Association clé → équipe → provider réel
- [ ] Middleware d'authentification sur toutes les routes proxy

### Module 3 — Logging (semaines 2-3)
- [ ] Log structuré à chaque requête : `{id, timestamp, api_key_id, team_id, provider, model, tokens_input, tokens_output, cost_eur, latency_ms, status, http_status}`
- [ ] Écriture async en BDD (ne bloque pas la réponse)
- [ ] Hash d'intégrité sur chaque log (SHA-256 du contenu)
- [ ] Endpoint GET `/logs` avec filtres (équipe, date, modèle)
- [ ] Export CSV des logs

### Module 4 — Comptage tokens et coûts (semaine 3)
- [ ] Comptage tokens précis par provider (tiktoken pour OpenAI, tokenizer Mistral, etc.)
- [ ] Table de pricing par modèle maintenue en config YAML
- [ ] Calcul coût en euros à chaque requête
- [ ] Mise à jour facile du pricing sans redéploiement

### Module 5 — Budget caps (semaines 3-4)
- [ ] Budget mensuel configurable par équipe (en euros)
- [ ] Vérification du budget **avant** chaque forwarding
- [ ] Blocage avec HTTP 429 + message clair si budget dépassé
- [ ] Alerte email à 80% et 100% du budget (SMTP simple)
- [ ] Reset automatique du budget le 1er du mois

### Module 6 — Dashboard minimal (semaines 4-6)
- [ ] Page d'overview : tokens totaux, coût total du mois, nb requêtes
- [ ] Vue par équipe : consommation, budget restant, top modèles
- [ ] Tableau des derniers logs avec filtres
- [ ] Aucun graphique complexe en sprint 1 — tableaux seulement
- [ ] Auth basique (login/password pour l'admin)

### Infra sprint 1
- [ ] Docker Compose (gateway + postgres + redis optionnel)
- [ ] Variables d'env via `.env` (jamais de secrets en dur)
- [ ] Script de migration SQL au démarrage
- [ ] Health check endpoint `/health`
- [ ] README complet avec instructions de démarrage en 5 minutes

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
# Démarrer en local
docker-compose up -d
uvicorn gateway.main:app --reload --port 8000

# Tests
pytest tests/ -v

# Migration BDD
python -m gateway.migrations.run

# Vérifier la santé
curl http://localhost:8000/health
```

---

## Ce qu'on ne fait PAS en sprint 1

- Pas de frontend complexe (tableaux HTML suffisent)
- Pas de semantic caching
- Pas de PII detection
- Pas de SSO / OAuth
- Pas de multi-tenant avancé
- Pas de Kubernetes
- Pas d'IA dans le dashboard
- Pas de pricing dynamique
- Pas d'API de management programmatique complète

Ces features existent — elles sont dans le sprint 3. Pour l'instant on ship un proxy qui fonctionne, qui logge, et qui bloque les dépassements de budget. C'est tout.
