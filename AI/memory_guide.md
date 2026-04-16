# 🧠 AI Memory Guide — Miracle Coins / CoinSync Pro

This document explains **how the AI agent MUST use memory** while working on Miracle Coins.  
Memory = small JSON files the agent **reads first** and **updates last** so work stays consistent across tasks, branches, and agents.

---

## 0) Folder Layout

All memory lives under `/AI/memory/coinsync/`:

/AI/memory/coinsync/
system/
state.json # Global runtime facts: ports, env flags, DB names, channels enabled
decisions.json # Architectural + product decisions (with date & rationale)
issues.json # Known problems, mitigations, follow-ups
features/
pricing.json # Facts & rules for the pricing subsystem
marketplaces.json # Channel mappings (Shopify/eBay), webhooks, metafields
images.json # File-server usage, auto-square rules, style constraints
sales.json # Sales tracking, revenue forecasting, multi-channel metrics
inventory.json # Advanced inventory management, bulk operations, individual tracking
alerts.json # Real-time alert system, customizable thresholds, notifications
collections.json # Collections management (replaces categories), metadata, pricing strategy
tasks/
log.jsonl # Append-only per-task memory entries (chronological)

yaml
Copy code

> Create additional feature files as needed (e.g., `inventory.json`, `orders.json`).

---

## 1) Golden Rules

1. **Always read memory before doing anything.**  
   - Load `system/state.json`, `system/decisions.json`, and the relevant `features/*.json`.  
2. **Never overwrite; append or merge.**  
   - Prefer additive updates; include timestamps.  
3. **No secrets in memory.**  
   - Use environment variables for keys/tokens.  
4. **Keep memory human-auditable.**  
   - Small JSON files, comments in the PR, and clear diffs.  
5. **Single source of truth.**  
   - If a fact conflicts, `system/state.json` wins for environment/runtime;  
     `system/decisions.json` wins for policy/architecture choices.

---

## 2) JSON Schemas

### 2.1 `system/state.json`
Stores *current* environment/flags the agent must respect.
```json
{
  "project": "Miracle Coins — CoinSync Pro",
  "env": {
    "backend_port": 13000,
    "frontend_port": 8100,
    "postgres": {
      "db_name": "miracle-coins",
      "port": 5432
    },
    "redis": true,
    "goldapi_key": "configured",
    "shopify_domain": "miracle-coins.com",
    "shopify_api_key": "configured"
  },
  "auth": {
    "provider": "stream-lineai",
    "admin_only": true
  },
  "channels": {
    "shopify": { "enabled": true, "domain": "miracle-coins.com", "api_scopes": "configured" },
    "ebay":    { "enabled": false },
    "etsy":    { "enabled": false },
    "tiktok":  { "enabled": false }
  },
  "ai_services": {
    "pricing_agent": { "enabled": true, "goldapi_integration": true, "scam_detection": true },
    "spot_price_service": { "enabled": true, "source": "goldapi" },
    "market_scraper_service": { "enabled": true },
    "shopify_pricing_service": { "enabled": true }
  },
  "style": { "theme": "black_gold" },
  "last_updated": "2025-01-27T10:30:00Z"
}
2.2 system/decisions.json
Permanent decisions with rationale and timestamp.

json
Copy code
[
  {
    "id": "pricing-base-from-entry",
    "title": "Use entry melt as base for default pricing",
    "rationale": "Owner wants stability vs daily spot swings.",
    "status": "approved",
    "decided_at": "2025-10-17",
    "impacts": ["pricing_engine", "reprice_job"]
  },
  {
    "id": "auth-admin-only",
    "title": "Admins only in UI & API",
    "rationale": "Internal tool, customers exist in shared auth.",
    "status": "approved",
    "decided_at": "2025-10-17",
    "impacts": ["routes", "frontend-guards"]
  }
]
2.3 system/issues.json
Known problems, mitigations, owners.

json
Copy code
[
  {
    "id": "shopify-webhook-retries",
    "summary": "Occasional webhook timeouts from Shopify",
    "status": "open",
    "mitigation": "Idempotent handlers + retry with backoff",
    "owner": "BackendAI",
    "updated_at": "2025-10-17T04:12:00Z"
  }
]
2.4 features/*.json
Feature-specific rules and mappings.

features/pricing.json

json
Copy code
{
  "default_multiplier": 1.5,
  "base_from_entry": false,
  "override_allowed": true,
  "spot_refresh_cron": "hourly",
  "inputs": {
    "spot_provider": "goldapi",
    "market_refs": ["ebay", "apmex", "jm_bullion", "sd_bullion"]
  },
  "outputs": {
    "computed_price_field": "computed_price",
    "threshold_notify_delta": 0.03
  },
  "scam_detection": {
    "enabled": true,
    "confidence_threshold": 0.7,
    "scam_threshold": 0.8
  },
  "last_updated": "2025-01-27T10:30:00Z"
}
features/marketplaces.json

json
Copy code
{
  "shopify": {
    "enabled": true,
    "domain": "miracle-coins.com",
    "metafields_namespace": "coins",
    "required_scopes": ["read_products","write_products","read_inventory","write_inventory","read_orders","write_orders","read_customers","read_price_rules","write_price_rules","read_reports","read_webhooks","write_webhooks"],
    "webhooks": ["order-created"],
    "api_version": "2023-10"
  },
  "ebay": {
    "enabled": false,
    "defaults_ready": false
  },
  "last_updated": "2025-01-27T10:30:00Z"
}
features/images.json

json
Copy code
{
  "file_server": "https://file-server.stream-lineai.com",
  "auto_square": true,
  "background": "black",
  "accent": "gold",
  "optimize": true,
  "sort_primary_first": true,
  "last_updated": "2025-01-27T10:30:00Z"
}
2.5 tasks/log.jsonl (append-only)
Chronological log of memory-relevant actions.

json
Copy code
{"ts":"2025-10-17T04:12:00Z","task_id":"MC-PRC-001","summary":"Added pricing_agent backend files","impacts":["pricing.json"],"branch":"feature/pricing-agent-backend"}
{"ts":"2025-10-17T05:05:00Z","task_id":"MC-INV-002","summary":"Inventory CRUD routes created","impacts":["inventory.json"],"branch":"feature/inventory-crud"}
3) Agent Workflow (MUST Follow)
Before coding (READ):

Read system/state.json → respect ports, DB name, flags.

Read system/decisions.json → do not contradict approved decisions.

Read relevant features/*.json → adopt rules/mappings.

While coding (USE):
4. If a rule is missing/ambiguous, propose a new decision object and proceed conservatively.
5. Never store secrets in memory; reference .env fields.
6. Keep code aligned with state.json (ports, enabled channels, admin-only).

After coding (WRITE):
7. Update relevant features/*.json last_updated if you changed behavior.
8. If you made a durable choice → append to system/decisions.json with status:"proposed" or approved if told.
9. Append a line to tasks/log.jsonl summarizing what changed (one line JSON).

On conflicts:
10. If two files disagree, prefer:
- Environment/runtime → system/state.json
- Policy/architecture → system/decisions.json
- Otherwise, open a new issue in system/issues.json and continue with safest assumption.

4) When to Update Memory
Update memory when you:

Change an endpoint, schema, job cadence, or external mapping.

Add or deprecate feature flags (e.g., enabling eBay).

Add a new invariant ("all images must be auto-squared").

Resolve or log a known issue.

**Comprehensive Implementation Updates:**
- Update feature files when implementing new modules (sales, inventory, financial, alerts)
- Add new API endpoints to relevant feature configurations
- Update business rules and profit margin strategies
- Document new UI/UX patterns and component structures
- Track implementation progress in task logs

Do not update memory for:

Minor refactors with no behavioral change.

Secrets, tokens, or transient dev notes.

5) Examples
5.1 Add a New Decision
Append to system/decisions.json:

json
Copy code
{
  "id": "market-reprice-threshold",
  "title": "Reprice only when delta >= 3%",
  "rationale": "Reduce churn in Shopify updates.",
  "status": "approved",
  "decided_at": "2025-10-17",
  "impacts": ["pricing_engine","shopify_sync"]
}
5.2 Enable eBay (later)
Edit features/marketplaces.json:

json
Copy code
{
  "shopify": { "...": "..." },
  "ebay": {
    "enabled": true,
    "defaults_ready": true
  },
  "last_updated": "2025-11-02T10:15:00Z"
}
Append to tasks/log.jsonl:

json
Copy code
{"ts":"2025-11-02T10:15:00Z","task_id":"MC-MKT-010","summary":"Enabled eBay channel; defaults set","impacts":["marketplaces.json"],"branch":"feature/ebay-sync"}
6) Git & PR Etiquette
Memory changes go in the same PR as code when tightly coupled.

Commit message should include a [memory] tag, e.g.:

pgsql
Copy code
feat(pricing): add hourly spot sync [memory: pricing.json, state.json]
Keep diffs small; JSON formatted & valid.

7) Validations & Guards
On CI, run a memory linter (optional) that checks:

Valid JSON

Required keys present (last_updated)

No secrets detected (simple regex heuristic)

8) Quick Checklist (per task)
 Read state.json + decisions.json + relevant features/*.json

 Conform code to memory (ports, flags, rules)

 Propose/update decisions if needed

 Append to tasks/log.jsonl

 No secrets added to memory

9) FAQ
Q: What if I need a new feature file?
A: Create it under features/ with a minimal JSON and add last_updated.

Q: What if a decision is wrong?
A: Add a new decision entry with status:"proposed" + rationale. Do not mutate historical entries.

Q: Can I store large payloads?
A: No. Keep memory small and factual; use docs or DB migrations for heavy data.

