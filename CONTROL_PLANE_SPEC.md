# AgentLoopGuard Control Plane Architecture & API Specification

**Document Version**: 1.0.0  
**Specification Date**: 2026-07-24  
**Status**: Approved Architecture & API Specification (ALG-027)  
**Target Implementation**: Phase 2 Commercial SaaS Control Plane  

---

## 1. Executive Summary & System Overview

The **AgentLoopGuard Control Plane** provides a centralized, cloud-hosted management tier for multi-agent enterprise deployments. While the open-source AgentLoopGuard Python SDK executes zero-dependency, local circuit-breaking in client runtimes, the Control Plane enables organization-wide governance, centralized FinOps budget management, real-time incident alerting, and compliance audit vaulting.

```
+-------------------------------------------------------------------------+
|                        AgentLoopGuard Client SDK                        |
|   (Local Circuit-Breaker: Python / LangChain / CrewAI / AutoGen / etc.) |
+-------------------------------------------------------------------------+
       |                                      ^
       | 1. Async Step & Detection Push       | 2. Dynamic Policy Sync (Polling)
       v                                      |
+-------------------------------------------------------------------------+
|                      AgentLoopGuard Control Plane                       |
|                                                                         |
|  +---------------------+   +-------------------+   +-----------------+  |
|  | Policy Sync Server  |   | FinOps Aggregator |   | Alert Webhooks  |  |
|  +---------------------+   +-------------------+   +-----------------+  |
|  | Audit Vault Storage |   | Hosted Dashboard  |   | Security Engine |  |
|  +---------------------+   +-------------------+   +-----------------+  |
+-------------------------------------------------------------------------+
       |                                      |
       v                                      v
+-----------------------+          +-----------------------+
| Immutable Audit Vault |          | External Destinations |
| (S3/GCS + WORM Hashing|          | (Slack, PagerDuty)    |
+-----------------------+          +-----------------------+
```

### Key Pillars
1. **Centralized Policy Sync Protocol**: Remotely manage detector thresholds, budget caps, and model policies across hundreds of distributed agents without redeploying code.
2. **Multi-Agent FinOps Aggregator**: Aggregate token consumption and financial spend across teams, projects, and LLM providers with hard/soft budget enforcement.
3. **Managed Webhook Dispatcher**: Trigger real-time notifications to Slack, PagerDuty, Datadog, or custom HTTP endpoints upon loop or budget breaches.
4. **Immutable Audit Vault**: Cryptographically chain and persist step events and detection logs for compliance (SOC 2, ISO 27001, HIPAA).

---

## 2. Centralized Policy Sync Protocol

The SDK periodically polls the Control Plane for policy updates or receives pushed rules via WebSocket. Remote policies override local default thresholds while preserving local fail-safe execution.

### Policy Synchronization Flow
- **SDK Startup**: Client initializes `RemotePolicyProvider(api_key="...", policy_id="pol_123", sync_interval_sec=60)`.
- **Cache Strategy**: Local policy file (`.agentloopguard/policy_cache.json`) ensures offline resilience if Control Plane is unreachable.
- **ETag Validation**: `If-None-Match` header minimizes network overhead; `304 Not Modified` returns immediately.

### Policy Data Schema (`PolicyRuleSet`)
```json
{
  "schema_version": 1,
  "policy_id": "pol_enterprise_prod_01",
  "organization_id": "org_velro_9921",
  "updated_at": "2026-07-24T18:00:00Z",
  "rules": {
    "budget": {
      "max_iterations": 25,
      "max_cost_usd": 50.0,
      "max_tokens": 500000,
      "max_duration_seconds": 300,
      "unknown_model_policy": "fail_closed"
    },
    "detectors": {
      "exact_repeat": {
        "enabled": true,
        "max_repeats": 3
      },
      "lexical_similarity": {
        "enabled": true,
        "similarity_threshold": 0.85,
        "history_window": 5
      },
      "cost_velocity": {
        "enabled": true,
        "max_cost_velocity_usd_per_min": 5.0,
        "window_size_seconds": 60
      },
      "oscillation": {
        "enabled": true,
        "cycle_length": 2,
        "min_repeats": 2
      }
    },
    "alert_mode": "raise"
  }
}
```

---

## 3. Multi-Agent FinOps Budget Aggregator API

The FinOps API aggregates step events across distributed worker nodes to track organizational spend against global budgets in real time.

### Real-Time Budget Evaluation
- **Global Budget Hierarchy**: `Organization` ➔ `Department/Team` ➔ `Project` ➔ `Agent Session`.
- **Soft Cap Action**: Triggers warning webhooks when spend reaches 80% of budget.
- **Hard Cap Action**: Returns `RECOMMEND_KILL` signal in policy responses, signaling local guards to halt agent execution.

### Ingestion Payload (`POST /v1/telemetry/steps`)
SDK sends batches of `StepEvent` objects asynchronously in background threads.

```json
{
  "organization_id": "org_velro_9921",
  "project_id": "proj_customer_support",
  "environment": "production",
  "steps": [
    {
      "schema_version": 1,
      "session_id": "b0b92248-9fdc-438b-82b5-cc311b458462",
      "timestamp": 1784897948.981,
      "model": "gpt-4o",
      "input_tokens": 450,
      "output_tokens": 120,
      "cost_usd": 0.00285,
      "cost_source": "builtin_snapshot_20260721",
      "tool_name": "db_query",
      "tool_args": {"query": "SELECT * FROM orders;"},
      "output": "10 rows returned"
    }
  ]
}
```

---

## 4. Alert Webhooks & Event Delivery Schema

When an agent loop or budget overrun occurs, the Control Plane generates signed webhooks to external notification targets.

### Webhook Event Payload Schema (`agentloopguard.detection.v1`)
```json
{
  "event_id": "evt_99182a7b21",
  "event_type": "detection.loop_trapped",
  "timestamp": "2026-07-24T20:10:00Z",
  "organization_id": "org_velro_9921",
  "project_id": "proj_customer_support",
  "session_id": "b0b92248-9fdc-438b-82b5-cc311b458462",
  "detection": {
    "schema_version": 1,
    "detector_id": "cost_velocity",
    "detector_name": "CostVelocityDetector",
    "confidence": 1.0,
    "description": "Cost velocity 12.50 USD/min exceeds threshold of 5.00 USD/min.",
    "measured_values": {
      "measured_velocity_usd_per_min": 12.5,
      "threshold_usd_per_min": 5.0
    },
    "recommended_action": "stop",
    "pattern_details": {
      "window_seconds": 60,
      "recent_cost_usd": 0.258
    }
  },
  "action_taken": "session_terminated"
}
```

### Security & Signature Verification
Every outgoing webhook includes headers for payload integrity:
- `X-AgentLoopGuard-Signature`: `t=1784897948,v1=9f8a...` (HMAC-SHA256 signature calculated over `timestamp + "." + payload` using the shared webhook secret).

---

## 5. Immutable Audit Vault Data Model

The Audit Vault retains cryptographic event logs for legal compliance and post-incident investigation.

### Hash-Chaining Data Structure
Each audit entry contains a cryptographic hash computed from:
$$\text{Hash}_n = \text{SHA-256}(\text{Hash}_{n-1} \parallel \text{Timestamp}_n \parallel \text{Payload}_n)$$

```json
{
  "audit_id": "aud_01827491",
  "sequence_number": 10482,
  "prev_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "current_hash": "8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4",
  "organization_id": "org_velro_9921",
  "session_id": "b0b92248-9fdc-438b-82b5-cc311b458462",
  "event_type": "detection_event",
  "timestamp": "2026-07-24T20:10:00Z",
  "payload": {
    "detector_name": "CostVelocityDetector",
    "action": "stop"
  }
}
```

---

## 6. OpenAPI 3.0 REST Specification

Below is the formal OpenAPI 3.0 YAML specification for the core Control Plane REST endpoints.

```yaml
openapi: 3.0.3
info:
  title: AgentLoopGuard Control Plane API
  version: 1.0.0
  description: Centralized policy, FinOps budget aggregation, webhooks, and audit APIs for AgentLoopGuard.
paths:
  /v1/policies/{policy_id}:
    get:
      summary: Fetch remote policy configuration
      operationId: getPolicy
      parameters:
        - name: policy_id
          in: path
          required: true
          schema:
            type: string
        - name: If-None-Match
          in: header
          required: false
          schema:
            type: string
      responses:
        '200':
          description: Policy configuration retrieved
          headers:
            ETag:
              schema:
                type: string
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PolicyRuleSet'
        '304':
          description: Policy not modified since last poll

  /v1/telemetry/steps:
    post:
      summary: Batch ingest step events from SDK clients
      operationId: ingestStepEvents
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/StepBatchPayload'
      responses:
        '202':
          description: Batch accepted for asynchronous processing
          content:
            application/json:
              schema:
                type: object
                properties:
                  accepted_steps:
                    type: integer
                  budget_status:
                    type: string
                    enum: [ok, warning, limit_exceeded]

  /v1/finops/budgets/{organization_id}:
    get:
      summary: Get organization budget summary
      operationId: getBudgetSummary
      parameters:
        - name: organization_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Budget and spend summary
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BudgetSummary'

  /v1/audit/search:
    post:
      summary: Query immutable audit vault
      operationId: queryAuditVault
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                organization_id:
                  type: string
                session_id:
                  type: string
                start_time:
                  type: string
                  format: date-time
                end_time:
                  type: string
                  format: date-time
      responses:
        '200':
          description: Matching audit vault records
          content:
            application/json:
              schema:
                type: object
                properties:
                  records:
                    type: array
                    items:
                      $ref: '#/components/schemas/AuditRecord'

components:
  schemas:
    PolicyRuleSet:
      type: object
      properties:
        schema_version:
          type: integer
        policy_id:
          type: string
        updated_at:
          type: string
        rules:
          type: object

    StepBatchPayload:
      type: object
      properties:
        organization_id:
          type: string
        project_id:
          type: string
        environment:
          type: string
        steps:
          type: array
          items:
            type: object

    BudgetSummary:
      type: object
      properties:
        organization_id:
          type: string
        current_spend_usd:
          type: number
        allocated_budget_usd:
          type: number
        period:
          type: string

    AuditRecord:
      type: object
      properties:
        audit_id:
          type: string
        sequence_number:
          type: integer
        prev_hash:
          type: string
        current_hash:
          type: string
        timestamp:
          type: string
```

---

## 7. Next Steps & Implementation Roadmap

1. **ALG-028 (Phase 2 SDK Client Integration)**: Implement optional `RemotePolicyProvider` and `WebhookExporter` inside `src/agentloopguard/client/` using Python stdlib / non-blocking network calls without adding required external dependencies.
2. **Control Plane Infrastructure Setup**: Deploy policy sync server, FinOps aggregator worker, and PostgreSQL/S3 audit store.
