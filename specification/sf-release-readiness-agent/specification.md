# Specification: sf-release-readiness-agent

> **Guidelines**: Read all applicable guidelines before executing ANY tasks below:
> - [guidelines.md](../guidelines.md) — Universal execution rules
> - [guidelines-agent.md](../guidelines-agent.md) — Universal agent patterns
> - [guidelines-agent-python.md](../guidelines-agent-python.md) — Python implementation details
> - [guidelines-agent-skills.md](../guidelines-agent-skills.md) — Runtime skills patterns
> - [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) — MCP integration patterns

---

## Basic Setup

- [x] Read `product-requirements-document.md` and `intent.md` for full context before implementing anything
- [x] Bootstrap agent code in `assets/sf-release-readiness-agent/` using the `sap-agent-bootstrap` instructions (invoke from inside `assets/sf-release-readiness-agent/`, use copy commands — do NOT create files manually)
- [x] Install dependencies, validate the agent starts and responds at `/.well-known/agent.json`

---

## Runtime Skills

- [x] Create `assets/sf-release-readiness-agent/app/skills/release-note-analysis/SKILL.md` with:
  - YAML frontmatter: `name: release-note-analysis`, `description: Instructions for parsing and interpreting SAP SuccessFactors What's New Viewer release notes and mapping change items to configuration areas`
  - Body: Step-by-step instructions for:
    1. Extracting individual change items from release note content (module, feature area, change type, description)
    2. Mapping each change item to a SuccessFactors configuration domain (RBP, Picklists, Foundation Objects, User Management, Platform)
    3. Flagging ambiguous items as requiring human review rather than making assumptions
    4. Producing a structured list of change items per configuration domain

- [x] Create `assets/sf-release-readiness-agent/app/skills/change-classification/SKILL.md` with:
  - YAML frontmatter: `name: change-classification`, `description: Rules for classifying each required SuccessFactors configuration change as low-risk (auto-applicable) or requires-human-approval`
  - Body:
    1. **Low-risk criteria** (auto-applicable after confirmation): picklist label/value updates, translatable text changes, UI theme configuration, custom navigation label changes
    2. **Requires-approval criteria**: Role-Based Permission role or group changes, workflow routing changes, MDF object structural changes, integration-related configuration, any change that affects user access or data visibility
    3. **Escalation rule**: when classification is uncertain, always default to requires-approval
    4. Output format: each change item annotated with `classification: low-risk | requires-approval` and `rationale: <reason>`

- [x] Create `assets/sf-release-readiness-agent/app/skills/multi-tenant-context/SKILL.md` with:
  - YAML frontmatter: `name: multi-tenant-context`, `description: Rules for managing context isolation across multiple SuccessFactors tenant environments`
  - Body:
    1. Always confirm which tenant is in scope before querying or modifying any configuration
    2. Never mix API credentials or results across tenants in the same conversation turn
    3. Refer to each tenant by a user-defined alias (e.g. client name) rather than raw tenant IDs when communicating with the admin
    4. Before applying any change, re-confirm the target tenant explicitly

---

## Project-Specific Tasks

### R1: Release Note Ingestion

- [x] Add system prompt section instructing the agent to accept release note content in these forms:
  - Pasted text (inline in conversation)
  - Uploaded document (PDF or plain text)
  - URL to the SF What's New Viewer (agent fetches via HTTP if URL is provided)
- [x] Implement ingestion logic in the agent: when release notes are provided, invoke the `release-note-analysis` runtime skill to parse and index change items
- [x] Agent must confirm to the admin how many change items were identified and across which SF modules/feature areas after ingestion

### R2: Per-Tenant Impact Assessment

- [x] Add system prompt section instructing the agent to:
  - Accept a target tenant identifier (alias or tenant ID) from the admin
  - Query the tenant's live configuration using the available MCP tools (RBP, Generic Objects, Foundation Platform, User Management)
  - Cross-reference indexed release note change items against the queried configuration to identify which items actually affect this tenant
- [x] Agent must produce a structured impact report per tenant:
  - List of affected configuration areas with current configuration state
  - List of release note items that are NOT applicable to this tenant (with brief reason)
- [x] Implement support for running the assessment across multiple tenants sequentially, presenting a separate report per tenant

### R3: Change Classification

- [x] After generating the impact report for a tenant, invoke the `change-classification` runtime skill to classify each impacted item
- [x] Agent must present the classified change plan to the admin as a structured summary:
  - Section 1: Low-risk changes (list with rationale, count)
  - Section 2: Requires-approval changes (list with rationale, count)
  - Section 3: Not applicable (count only)
- [x] Agent must wait for admin acknowledgement before proceeding to change application

### R4: Human-Confirmed Change Application

- [x] Implement an explicit confirmation gate: the agent MUST NOT apply any change until the admin explicitly confirms in the conversation (e.g. "confirm", "apply", "proceed")
- [x] After confirmation, the agent applies ONLY low-risk changes via the MCP tools:
  - Picklist label/value updates → via Generic Objects MCP tools
  - Foundation Object text updates → via Foundation Platform MCP tools
  - Custom navigation label changes → via Foundation Platform MCP tools
- [x] After each change is applied, the agent records the result (success/failure) in the session change log
- [x] If any change application fails, the agent halts remaining changes, reports the failure, and does NOT continue applying dependent changes
- [x] Requires-approval changes are NEVER applied automatically — agent produces manual action guidance only (see R7)

### R5: Multi-Tenant Support

- [x] At session start, the agent asks the admin to register the tenants in scope for this release cycle (alias, tenant host/URL, credential reference)
- [x] All API calls via MCP tools are made with the correct per-tenant credentials — never shared across tenants
- [x] The agent maintains a separate change log per tenant within the session
- [x] The admin can switch between tenants using natural language (e.g. "now assess tenant ClientB")
- [x] The `multi-tenant-context` runtime skill is invoked before every tenant-scoped operation

### R6: Auditable Change Log

- [x] At the end of each tenant's change application, the agent produces a final change log as a structured text block containing:
  - Release cycle identifier (e.g. "H1 2026")
  - Tenant alias
  - Timestamp (UTC) of each change applied
  - Change type
  - Before value / after value (where applicable)
  - Confirmed by (admin confirmation statement)
  - Result (success / failure)
- [x] The agent presents the change log to the admin and explicitly offers to export it (copy-paste as JSON or plain text)

### R7: Manual Action Guidance

- [x] For each change classified as requires-approval or not-auto-applicable, the agent generates a manual action guide containing:
  - Plain-language description of what needs to change
  - The exact location in the SF admin UI (menu path / screen name)
  - The current value (from the live configuration query) and the expected target value (from the release note)
  - Risk level and reason for manual-only classification
- [x] The manual action guide is presented to the admin as a numbered checklist at the end of the session
- [x] The guide is tenant-specific (referencing actual values from that tenant's configuration)

---

## System Prompt Requirements

- [x] Add to agent system prompt:
  - "IMPORTANT: You MUST use tools to retrieve live data. Never fabricate, guess, or invent SuccessFactors configuration values. Relay tool errors verbatim without adding suggestions."
  - "When calling tools that support pagination, always set the page size parameter (top, limit, etc.) to a maximum of 100 items to prevent context overflow. Inform the user when this limit is applied."
  - "Never apply any configuration change to a SuccessFactors tenant without receiving explicit confirmation from the admin in the current conversation turn."
  - "Never mix credentials, configuration data, or change logs across different tenant environments."
  - "If you are uncertain whether a release note item applies to the current tenant, flag it as 'requires review' rather than making an assumption."
  - "Use the `release-note-analysis` skill when parsing release notes, the `change-classification` skill when classifying changes, and the `multi-tenant-context` skill before any tenant-scoped operation."

---

## Business Instrumentation

- [x] Add milestone instrumentation using `instrumentation.log_milestone` and named OpenTelemetry spans:

  | Milestone | Log on achievement | Log on miss |
  |---|---|---|
  | M1: Release Notes Ingested | `M1.achieved: release notes ingested and indexed for release [release-version], [N] change items identified` | `M1.missed: release note ingestion did not complete — content unavailable or unparseable` |
  | M2: Impact Assessment Complete | `M2.achieved: impact assessment complete for tenant [tenant-id], [N] impacted areas identified` | `M2.missed: impact assessment did not complete for tenant [tenant-id] — API query failed or timed out` |
  | M3: Change Plan Generated | `M3.achieved: change plan generated for tenant [tenant-id] — [N] low-risk, [M] requires-approval` | `M3.missed: change plan generation incomplete for tenant [tenant-id]` |
  | M4: Low-Risk Changes Applied | `M4.achieved: [N] low-risk changes applied to tenant [tenant-id], [F] failures recorded` | `M4.missed: change application aborted for tenant [tenant-id] — confirmation not received or API error` |
  | M5: Review & Sign-Off | `M5.achieved: release readiness cycle complete for tenant [tenant-id], change log finalised` | `M5.missed: review cycle did not complete for tenant [tenant-id]` |

- [x] Verify `bootstrap(app)` is called after `app = server.build()` in `main.py`

---

## MCP Tool Integration

> Read [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) for complete MCP integration patterns.

- [x] Verify `specification/sf-release-readiness-agent/api-specs/` contains all four downloaded API spec files:
  - `PLTRoleBasedPermissions.edmx` (34 KB) — Role-Based Permissions
  - `PLTGenericObjects.edmx` (67 KB) — Generic Objects / Picklists
  - `FoundationPlatformPLT.edmx` (213 KB) — Common Platform APIs
  - `PLTUserManagement.edmx` (93 KB) — User Management
- [x] Invoke the `mcp-translation-file` skill for each of the four API spec files (one MCP server per API)
- [x] Invoke `setup-solution` to create and register MCP server assets for all four translation files
- [x] Verify the agent's `AgentExecutor` loads tools via `mcp_providers.agw.get_mcp_tools()` — do NOT add direct HTTP clients or custom tool files
- [x] Add all four MCP server dependencies to `asset.yaml` under `requires` using the exact ORD IDs from the generated `asset.yaml` files (Path A — do NOT invent or guess ORD IDs)
- [x] After MCP translation and setup-solution complete, generate `mcp-mock.json` using the `mcp-mock-config` skill

**MCP API scope definitions (for mcp-translation-file pruning):**

```
MCP API: sap.sf:apiResource:PLTRoleBasedPermissions:v1
MCP tool scope: read-only
Resources in scope: PermissionRole, PermissionRoleGroup, PermissionCategory

MCP API: sap.sf:apiResource:PLTGenericObjects:v1
MCP tool scope: read-write
Resources in scope: PicklistV2, PicklistValueV2, FOJobFunction, FODepartment, FOBusinessUnit, FOCostCenter

MCP API: sap.sf:apiResource:FoundationPlatformPLT:v1
MCP tool scope: read-write
Resources in scope: PickListValueV2, CustomNavigation, ThemeV2, TranslationLocale

MCP API: sap.sf:apiResource:PLTUserManagement:v1
MCP tool scope: read-only
Resources in scope: User, PerGlobalInfo, PerEmail
```

---

## Testing

- [x] `conftest.py` only sets `IBD_TESTING=true`
- [x] Write one integration test that exercises the end-to-end agent flow:
  - Input: sample release note content (fixture text) + a mock tenant context
  - Expected: agent produces an impact report, classifies changes, presents a change plan, and (after mock confirmation) applies low-risk changes
  - All MCP tools and LLM calls mocked; test must run offline
- [x] Write unit tests for:
  - Release note ingestion (R1): verify change items are correctly parsed and counted
  - Change classification (R3): verify low-risk vs. requires-approval rules are applied correctly for representative examples
  - Confirmation gate (R4): verify no changes are applied before explicit confirmation
  - Tenant context isolation (R5): verify different tenant aliases produce isolated change logs
- [x] Run `pytest` from `assets/sf-release-readiness-agent/` (no args) — if coverage < 70%, add tests until threshold met
- [x] Run `pytest` again from `assets/sf-release-readiness-agent/` (no args) to generate final `test_report.json`
- [x] Verify `test_report.json` exists in `assets/sf-release-readiness-agent/`
