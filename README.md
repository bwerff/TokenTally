# TokenTally

**AI-Usage Meter & Billing Gateway – Product Requirements Document (PRD)**
*Last updated: 24 May 2025*

TokenTally is a drop-in gateway that meters AI usage across multiple providers
and turns it into clean invoices. The sections below outline our mission, key
goals, measurable success metrics, detailed functional requirements and the
phased delivery plan.

---

### 1  |  Mission

Finance leaders are sick of reconciling five-and-six-figure “mystery bills” from OpenAI, Anthropic, GPU hosts and half-a-dozen home-rolled models. Devs keep switching models, prompts retry, and nobody can prove which customer or feature burned the budget. Existing FinOps suites watch VMs and S3 buckets, not tokens and context windows.
**We’ll plant ourselves directly in the request path, meter every token/second, stamp it with price, and push an itemised invoice into Stripe (or NetSuite, Chargebee, etc.). Once we’re the first hop, ripping us out hurts—exactly how Plaid got sticky.**

---

### 2  |  Goals & Non-Goals

|                                                                              | In scope | Out of scope                                                       |
| ---------------------------------------------------------------------------- | -------- | ------------------------------------------------------------------ |
| **Multi-vendor LLM gateway** (OpenAI, Anthropic, Cohere, local Ollama)       | ✅        | ❌ proprietary optimisation of prompt quality                       |
| **Deterministic metering** (tokens, GPU-seconds, embeddings, vector queries) | ✅        | ❌ tracking generic AWS/GCP costs (Cloudability already does it)    |
| **Usage-based invoicing via Stripe Billing API**                             | ✅        | ❌ building our own payment processor                               |
| **Real-time cost dashboards + alerts**                                       | ✅        | ❌ fancy BI (we export to Snowflake; Tableau is customers’ problem) |
| **SOC 2 / GDPR / AI Act logging**                                            | ✅        | ❌ HIPAA BAA phase 1 (consider later)                               |

---

### 3  |  Success Metrics

* < 100 ms added P95 latency to any request routed through the gateway
* Token counts match vendor invoices **±0.1 %** on audit sample
* 90 % of invoices auto-reconciled by finance without spreadsheet surgery
* Net retention > 140 % at twelve months (gateway lock-in effect)

---

### 4  |  Stakeholders

* **GM / Product** – owns roadmap, pricing, GTM
* **Engineering Lead** – delivery, tech choices, SRE
* **Finance Controller** (design partner) – validates metering accuracy
* **CISO** – security, compliance, vendor reviews
* **Customer Success** – onboarding, issue triage

---

### 5  |  Personas & top-priority use-cases

| Persona                       | “Job to be done”                                             | Example trigger                               |
| ----------------------------- | ------------------------------------------------------------ | --------------------------------------------- |
| **AI SaaS founder**           | Bill end-customers for actual LLM usage instead of guesswork | Switching from \$49/seat to per-token tiers   |
| **Enterprise FinOps analyst** | Allocate LLM spend to each BU / cost centre                  | CFO asks why corporate-chatbot budget blew up |
| **Open-source model host**    | Add usage-based billing without building payments stack      | Launching hosted Mistral-7B endpoint          |

*If a requirement doesn’t unblock one of these three, punt it.*

---

### 6  |  User stories (MVP scope)

| ID        | Story                                                                                                                            | Acceptance criteria                                                            |
| --------- | -------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| **US-01** | As a developer, I hit a single `/v1/chat/completions` proxy and set a header `X-LLM-Provider: openai`.                           | 200 OK, same latency ±10 ms vs direct call; response body untouched.           |
| **US-02** | As finance, I download a CSV of usage by `customer_id`, `feature`, `provider`, `model`, `tokens`, `cost` for any date range.     | CSV matches Stripe invoice lines exactly.                                      |
| **US-03** | As an admin, I create a per-model markup rule (e.g., `GPT-4o => +20 %`).                                                         | Subsequent usage events reflect new price; historical data frozen.             |
| **US-04** | As an ops engineer, I set a monthly budget alert at \$10 k.                                                                      | Slack notification fires within 60 s of threshold.                             |
| **US-05** | As legal, I view a 12-month immutable audit log (hash-chained) of every prompt’s token count, but **never** see raw prompt text. | SHA-256 hashes stored; GDPR “right to be forgotten” deletes hashes on request. |

---

### 7  |  Functional Requirements

1. **Gateway Edge**

   * Global POPs via Cloudflare Workers or Fastly Compute\@Edge.
   * Pass-through TLS, preserves vendor-specific headers.
   * Enforces concurrency & rate limits configurable per API key.

2. **Metering Engine**

   * Language-specific tokenisers (tiktoken, Anthropic tokenizer, BytePairLite).
   * Deterministic counting regardless of streaming or retries.
   * Token counters for OpenAI, Anthropic and local models.
   * GPU-minute parser for local models using Nvidia DCGM metrics.

3. **Usage Ledger**

   * Append-only table in ClickHouse (partition by day).
   * Schema: `event_id, ts, customer_id, provider, model, metric_type, units, unit_cost_usd`.
   * Outbox stream → Kafka → Stripe Billing API nightly.
   * Python helpers in `token_tally.usage_ledger` implement this schema and
     emit each event to Kafka when recorded.

4. **Pricing & Markup Rules**

   * CRUD via REST endpoints and a simple Admin UI.
   * Versioned; effective-date field prevents silent retroactive changes.
   * Supports FX conversion with daily ECB spot rates, with optional intraday feed.


5. **Invoice Service**

   * Maps ledger rows → Stripe metered-usage line items.
   * Consolidates into unified invoice per billing cycle, supports credit notes.

6. **Alerting & Forecast**

   * Time-series forecast (ARIMA baseline) computed hourly.
   * Webhook & Slack integration.
   * `python -m token_tally.budget_alert ledger.db https://hook` can be run
     hourly via cron to notify when a customer exceeds their monthly budget.
   * Hard-stop capability (`HTTP 429`) if customer hits credit limit.
   * `python -m token_tally.commitment_manager analyze ledger.db` suggests
     reserved-capacity commitments from historical usage.

7. **Admin Portal** (Next.js + tRPC)

   * Org/user management, SSO (SAML 2.0, Google).
   * Usage explorer with filters.
   * Audit-trail viewer (read-only).

8. **SDKs** (Typescript, Python, Go)

   * Drop-in replacements mirroring OpenAI/Anthropic client signatures.
   * Auto-retry w/ exponential back-off; surfaces gateway-specific errors.

9. **Compliance Pack**

   * SOC 2 roadmap published; see "SOC 2 & Data Residency" below.
   * Data residency: US or EU-managed clusters, or self-host via Helm.
   * Private-cloud (Helm chart) for Enterprise tier (see `helm/token-tally`).
   * `python -m token_tally.soc2_monitor audit.db http://localhost:8000/health`
     can be run every 5 minutes via cron to verify audit-log integrity and
     service health.


---

### 8  |  Non-functional requirements

| Category                 | Requirement                                                                    |
| ------------------------ | ------------------------------------------------------------------------------ |
| **Performance**          | +< 100 ms P95 latency; 10 K rps single-tenant, burst 100 K rps multi-tenant.   |
| **Reliability**          | 99.95 % monthly availability SLA; dual-region write-ahead log.                 |
| **Security**             | TLS 1.3 everywhere; zero raw-prompt retention; field-level encryption at rest. |
| **Scalability**          | Linear horizontal scale; ClickHouse cluster auto-rebalance.                    |
| **Observability**        | Prometheus metrics, OpenTelemetry traces exported to Grafana Cloud.            |
| **Internationalisation** | UI strings externalised; initial languages EN + FR.                            |
| **Accessibility**        | WCAG 2.1 AA for Admin Portal.                                                  |

---

### 9  |  Data flows & object model (high-level)

```
Client SDK
   │  JSON request
   ▼
Gateway Edge  ──► Provider API (OpenAI, etc.)
   │ TL;DR fields: api_key, provider, model, tokens_prompt_est
   ▼
Metering Engine  ──► (enriched event) ──► Kafka "usage_events"
                                       └─► ClickHouse ledger
                                       └─► Dead-letter topic (parse errors)
Billing Service ◄─┘ nightly query
   │  POST /v1/usage_records (Stripe)
   ▼
Stripe Invoice → Customer
```

---

### 10  |  Integrations

| System                         | Direction | Purpose                                                             |
| ------------------------------ | --------- | ------------------------------------------------------------------- |
| **Stripe Billing**             | Outbound  | Create metered-usage line items, handle webhooks for payment status |
| **QuickBooks / NetSuite** (v2) | Outbound  | Push GL entries for closed invoices                                 |
| **Slack / Teams**              | Outbound  | Cost alerts                                                         |
| **Snowflake / BigQuery**       | Outbound  | Live usage replica for advanced BI                                  |

The `token_tally.export.bigquery_export` CLI pushes usage events to BigQuery.

---

### 11  |  Phased Delivery Plan

| Phase                            | Target                     | Must-have deliverables                                                                       |
| -------------------------------- | -------------------------- | -------------------------------------------------------------------------------------------- |
| **0** – Prototype (4 wks)        | Dogfood only               | Gateway passthrough, ClickHouse ledger, manual CSV export                                    |
| **1** – MVP Beta (8 wks after 0) | 3 design partners          | Token-accurate meter, Stripe invoices, Slack alerts, basic Admin UI, SOC 2 roadmap published |
| **2** – GA Cloud (Q4 2025)       | Open signup                | Multi-region edge, SSO, mark-up rules, forecasts, SDKs                                       |
| **3** – Enterprise (Q1 2026)     | On-prem Helm, Private Link | Audit log viewer, EU residency, Type II SOC 2, charge-back by BU                             |
| **4** – Optimizer (Q2 2026)      | Revenue upsell             | Smart routing / spot-GPU arbitrage, commitment-manager advisor                               |

---

### 12  |  Key risks & blunt mitigations

| Risk                                                          | Brutal reality check                       | Mitigation                                                                              |
| ------------------------------------------------------------- | ------------------------------------------ | --------------------------------------------------------------------------------------- |
| **Vendor lockout** (OpenAI launches own multi-vendor billing) | They might—BigCo loves subsuming partners. | Ship now, own the integration. Double-down on *cross-vendor* analytics they can’t do.   |
| **Latency tax kills adoption**                                | 150 ms extra = angry devs.                 | Use edge compute, pre-warm sessions, optimise tokenisers in Rust.                       |
| **Tokeniser drift** (new model, new rules)                    | Counting wrong = refund headache.          | Versioned tokeniser registry, nightly diff vs vendor counts; alert on >0.05 % variance. |
| **Stripe dependency** outage                                  | If Stripe dies, invoices stall.            | Pluggable billing adapters; queue events until PSP recovers.                            |
| **Data privacy blow-up**                                      | Prompt data might carry PII.               | Never store prompt; only counts + hashes. Enterprise can self-host.                     |

---

### 13  |  Open questions

1. Should we expose a *write-your-own-pricing* DSL at launch or hard-code JSON rules?
2. Will ClickHouse satisfy multi-tenant EU residency, or do we need isolated clusters per customer?
3. What’s the minimum viable approach to FX rates—daily ECB feed or intraday?
4. Can we skip SOC 2 auditors until post-MVP without losing Enterprise design partners?
5. Do we include a basic cost optimisation router in MVP, or treat that as paid add-on?

---

### 14  |  Next-step action items (owner → deadline)

| Action                                             | Owner    | Due         |
| -------------------------------------------------- | -------- | ----------- |
| Conduct 20 customer discovery calls ([script](docs/customer_discovery_calls.md)) | Product  | 14 Jun 2025 |
| Fork Portkey, bolt ClickHouse & Stripe hook (PoC)  | Eng Lead | 05 Jun 2025 |
| Draft security architecture doc for SOC readiness  | CISO     | 28 Jun 2025 |
| Prepare one-pager + deck for \$1.5 M pre-seed      | GM       | 21 Jun 2025 |
| Line up design-partner LOIs (3 SaaS, 2 Enterprise) | Sales    | 30 Jun 2025 |

---
**Bottom line:** This gateway solves a *real*, boring accounting problem nobody wants to touch. Nail deterministic metering, stay invisible in the hot path, and invoice cleanly—everything else is a feature-creep distraction.

## SOC 2 & Data Residency

### SOC 2 roadmap

| Milestone                     | Target    |
| ----------------------------- | --------- |
| Policies & risk assessment    | Aug 2025  |
| Type I audit                  | Q1 2026   |
| Continuous monitoring in place| Q2 2026   |
| Type II report                | Q4 2026   |

### Data residency options

TokenTally runs in US-East by default. Enterprise customers may pin all data processing to the EU region or deploy the gateway inside their own Kubernetes clusters using the Helm chart under `helm/token-tally`.

## Frontend
A Next.js + tRPC admin portal lives in `frontend/`. Run `npm install` in that
folder and `npm run dev` to start it locally. The portal uses NextAuth for SSO
(Google or any SAML 2.0 provider). Set the following variables to enable each
provider:

- `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` – Google sign-in
- `SAML_ENTRYPOINT`, `SAML_ISSUER` and `SAML_CERT` – generic SAML provider

The frontend exposes tRPC endpoints for usage data and an audit log, shown in
the Usage and Audit sections of the UI.

## Client SDKs
Lightweight SDK wrappers live in `clients/` for TypeScript, Python and Go. Each
offers a `get_usage()` helper that mirrors the REST endpoint used by the portal.

## Payout helper
Use `PayoutService` to record payouts in `ledger.db` and read their status:

```python
from token_tally import PayoutService

svc = PayoutService()
svc.record_payout("p1", "user42", 1000, "USD")
status = svc.get_status("p1")
```

## Stripe webhook server
Run `token_tally.stripe_webhook` to listen for Stripe events. It validates the
`Stripe-Signature` header and writes invoice or payout statuses to `ledger.db`.

```bash
python -m token_tally.stripe_webhook whsec_test --db-path ledger.db --port 9000
```

Configure Stripe to send webhooks to `http://localhost:9000/webhook`.

## Upgrading
If you are migrating from a previous version of TokenTally, the ledger schema
now includes a `business_unit` column on both the `usage_events` and `invoices`
tables. Existing databases can be updated with:

```sql
ALTER TABLE usage_events ADD COLUMN business_unit TEXT NOT NULL DEFAULT '';
ALTER TABLE invoices ADD COLUMN business_unit TEXT NOT NULL DEFAULT '';
```


## Pricing DSL
TokenTally includes a small DSL for pricing rules. Each file contains one or more blocks of the form:

```
rule "<id>" {
    provider = "<llm provider>"
    model    = "<model name>"
    markup   = <decimal markup>
    effective_date = "YYYY-MM-DD"
}
```

Compile a rules file into the SQLite store used by the gateway:

```bash
python -m token_tally.pricing_dsl path/to/rules.tally
```

See [docs/pricing_dsl.md](docs/pricing_dsl.md) for the full DSL reference.
## Pre-seed pitch deck
The slide outline for our $1.5 M raise lives in [`docs/preseed_pitch_deck/outline.md`](docs/preseed_pitch_deck/outline.md).

