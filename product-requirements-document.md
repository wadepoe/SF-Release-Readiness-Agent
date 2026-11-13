# Product Requirements Document (PRD)

**Title:** SF Release Readiness Agent  
**Date:** 2026-11-13  
**Owner:** SuccessFactors System Administrator / HR IT Team  
**Solution Category:** AI Agent

---

## Product Purpose & Value Proposition

**Elevator Pitch:**  
SuccessFactors administrators managing multiple client tenants spend more than a week per release cycle manually reviewing release notes, assessing configuration impacts, and applying changes. This agent automates that entire process — reading the release notes, querying each tenant's live configuration, generating an impact report, and applying low-risk changes automatically while routing higher-risk ones for human approval.

**Business Need:**  
SAP SuccessFactors releases updates twice per year (H1 and H2), each requiring administrators to review hundreds of changes, assess which affect their specific tenant configurations, and manually apply required updates. With more than three client tenants to manage, this work multiplies to consume more than a week of skilled admin time per cycle — time that is otherwise error-prone, repetitive, and leaves tenants vulnerable to post-release incidents caused by missed changes.

**Expected Value:**  
- Reduce pre-release review and preparation time from > 1 week to a fraction of that effort
- Cut post-release configuration incidents by 50%+
- Free admin capacity for higher-value configuration, optimization, and client advisory work

**Product Objectives (Prioritized):**
1. Accurately interpret SAP SuccessFactors release notes and map them to specific configuration impacts per tenant
2. Enable autonomous application of low-risk changes (e.g. picklist labels, text updates) after human confirmation
3. Support multi-tenant environments with clear context separation and per-tenant change plans
4. Provide a complete, auditable change log for every release cycle

---

## Business Metrics

| Metric | Baseline | Target | Timeline | Process / Capability | Source |
|--------|----------|--------|----------|----------------------|--------|
| Time spent on pre-release review per cycle | > 1 week | TBD (to be refined after pilot) | Per release cycle | SF Release Readiness Management | user |
| Post-release configuration incidents | — | Reduce by 50%+ | Per release | SF Configuration Change Management | user |
| Admin time freed for higher-value tasks | — | Measurable reduction after first 3 releases | 3 release cycles | SF Admin Productivity | user |

---

## User Profiles & Personas

### Primary Persona: Alex — SuccessFactors System Administrator

Alex is a 34-year-old SuccessFactors system administrator working for an HR consultancy that manages SuccessFactors environments for more than three client organisations. Each SAP release cycle, Alex spends the better part of two weeks reading through release notes, cross-referencing each client's configuration, documenting what needs to change, and manually applying updates — often late at night to avoid disrupting users. Alex is technically proficient, familiar with SuccessFactors OData APIs, and deeply frustrated by how repetitive and error-prone this process is. Alex's biggest fear is missing a change that causes a post-release incident for a client.

**Goals:**
- Know exactly what needs to change in each tenant before the release goes live
- Apply routine changes quickly and with confidence, without manual repetition
- Have a defensible audit trail of every change made per release

**Key Tasks:**
- Upload or link to the SF What's New Viewer for the upcoming release
- Review the agent's impact report per tenant
- Confirm the change plan and let the agent apply low-risk changes
- Review remaining flagged items and apply them manually with agent guidance

### Secondary Persona: Jordan — HR IT Consultant / Technical Consultant

Jordan is a senior HR IT consultant who oversees configuration strategy across multiple client accounts. Jordan doesn't do the hands-on admin work but needs confidence that release readiness is being handled correctly before go-live. Jordan reviews the change summary, checks risk classifications, and gives sign-off before any changes are applied.

**Goals:**
- Understand the scope and risk of each release across all managed tenants
- Ensure no high-risk changes are applied without explicit approval
- Have visibility into what was changed and why, for client reporting

---

## Goals and Non-Goals

### Goals (In Scope)

- Ingest and interpret SAP SuccessFactors What's New Viewer release notes (via document upload or URL)
- Query live SF tenant configuration via available OData APIs (Role-Based Permissions, Generic Objects, User Management, Common Platform)
- Produce a structured per-tenant impact assessment report for each upcoming release
- Classify required changes as low-risk (auto-applicable) or requires-human-approval
- Present a change plan to the admin and apply low-risk changes upon confirmation
- Support multi-tenant environments (3+ tenants) with isolated context per tenant
- Maintain an auditable change log per tenant per release cycle
- Provide guidance and manual action lists for changes the agent cannot apply automatically

### Non-Goals (Out of Scope)

- Direct access to SAP SuccessFactors Provisioning settings (not available via OData API)
- Integration with SAP Cloud ALM (not connected in current landscape)
- Automated regression testing or functional testing after changes are applied
- Management of SuccessFactors integrations (Integration Center flows, middleware)
- Support for non-SuccessFactors SAP systems (e.g. S/4HANA, Concur)

---

## Requirements

### Must-Have Requirements

**R1: Release Note Ingestion**

- **Problem to Solve**: Admins manually read through lengthy SAP release notes to find relevant items — a time-consuming and error-prone process.
- **User Story**: As Alex, I need to provide the upcoming release notes to the agent so that it can analyse them on my behalf without me reading every item manually.
- **Acceptance Criteria**:
  - Given a release note document (PDF, URL, or pasted text), when the agent receives it, then it parses and indexes all change items with their module, feature area, and impact type.
  - Given the ingested content, the agent can answer specific questions about what changed in a given feature area.
- **Maps to Objective**: Objective 1
- **Priority Rank**: 1

**R2: Per-Tenant Impact Assessment**

- **Problem to Solve**: Not every release note item affects every tenant — admins must manually cross-reference release notes with each tenant's specific configuration, multiplied across all tenants.
- **User Story**: As Alex, I need the agent to query each of my tenants and identify which release note items actually affect their configuration, so I get a targeted list rather than reviewing everything.
- **Acceptance Criteria**:
  - Given ingested release notes and credentials for a tenant, when the agent runs an assessment, then it queries the tenant's live configuration via the SF OData APIs and returns a list of impacted configuration areas.
  - The impact report is scoped per tenant and clearly indicates which items are affected and which are not applicable.
- **Maps to Objective**: Objectives 1 & 3
- **Priority Rank**: 2

**R3: Change Classification**

- **Problem to Solve**: Admins must decide which changes are safe to apply immediately and which require careful review — this judgement currently relies on experience and is inconsistently applied.
- **User Story**: As Alex, I need the agent to classify each required change as low-risk or requires-approval, so I know what I can action quickly and what needs more careful consideration.
- **Acceptance Criteria**:
  - Given an impact report, the agent categorises each change item as: (a) low-risk / auto-applicable, or (b) requires human approval, with a clear rationale for each classification.
  - Low-risk changes include but are not limited to: picklist label updates, translatable text changes, UI theme adjustments.
  - Requires-approval changes include: permission role modifications, workflow changes, MDF object structural changes.
- **Maps to Objective**: Objectives 1 & 2
- **Priority Rank**: 3

**R4: Human-Confirmed Change Application**

- **Problem to Solve**: Admins need to trust that the agent will not make changes without their knowledge, but they also want to avoid repeating the same routine changes manually.
- **User Story**: As Alex, I need to review and confirm the change plan before anything is applied, so I remain in control while still benefiting from automation.
- **Acceptance Criteria**:
  - Given a classified change plan, the agent presents a summary to the admin and waits for explicit confirmation before applying any changes.
  - Upon confirmation, the agent applies only the low-risk changes via SF OData APIs and reports success or failure for each.
  - No changes are applied to any tenant without explicit admin confirmation in that session.
- **Maps to Objective**: Objective 2
- **Priority Rank**: 4

**R5: Multi-Tenant Support**

- **Problem to Solve**: Admins manage more than three tenants; each has its own credentials and configuration state that must never be mixed.
- **User Story**: As Alex, I need the agent to manage multiple SF tenant environments separately, so I can run assessments and apply changes per tenant without risking cross-tenant data exposure.
- **Acceptance Criteria**:
  - The agent maintains separate credential contexts per tenant and never shares data between tenants in a single session.
  - The admin can select which tenant(s) to assess and/or apply changes to.
  - Change logs are stored and retrievable per tenant.
- **Maps to Objective**: Objective 3
- **Priority Rank**: 5

**R6: Auditable Change Log**

- **Problem to Solve**: Admins and their clients need a record of what was changed, when, and by whom for compliance and incident investigation purposes.
- **User Story**: As Jordan, I need a complete log of every change the agent applied per tenant per release cycle, so I can report to clients and investigate any issues.
- **Acceptance Criteria**:
  - Every change applied by the agent is recorded with: timestamp, tenant ID, change type, before/after values, and confirmation by whom.
  - The change log is accessible to the admin after the session and exportable (e.g. as structured text or JSON).
- **Maps to Objective**: Objective 4
- **Priority Rank**: 6

**R7: Manual Action Guidance**

- **Problem to Solve**: Some required changes cannot be applied via API (e.g. provisioning settings). Admins need clear, targeted guidance for these.
- **User Story**: As Alex, I need the agent to give me step-by-step guidance for changes it cannot apply automatically, so I can complete the release preparation efficiently.
- **Acceptance Criteria**:
  - For each change classified as requires-approval or not-auto-applicable, the agent provides a plain-language description of what needs to be done and where in the SF UI.
  - The guidance is tenant-specific, referencing the actual configuration values where relevant.
- **Maps to Objective**: Objective 1
- **Priority Rank**: 7

---

## Solution Architecture

**Architecture Overview:**  
A pro-code Python AI agent built on the A2A protocol, deployed on SAP BTP. The agent uses LLM-based reasoning to interpret release notes and match them to live configuration data retrieved from SAP SuccessFactors via OData APIs. Custom MCP translation files are generated from the SF OData API specifications to enable structured tool calls from the agent into each tenant's SF environment.

**Key Components:**

- **SF Release Readiness Agent (Python, A2A)**: Core reasoning engine — interprets release notes, runs impact assessment, classifies changes, manages conversation flow, applies changes
- **MCP Translation Layer**: Custom MCP servers generated from SF OData API specs (Role-Based Permissions, Generic Objects, User Management, Common Platform) enabling structured API calls per tenant
- **Multi-Tenant Credential Manager**: Secure storage and context isolation for per-tenant SF credentials
- **Change Log Store**: Persistent, per-tenant record of all changes applied per release cycle

**Integration Points:**

- SAP SuccessFactors OData APIs (per tenant): read configuration state, write low-risk changes — `PLTRoleBasedPermissions`, `PLTGenericObjects`, `FoundationPlatformPLT`, `PLTUserManagement`
- SF What's New Viewer: input source for release notes (document upload or HTTP fetch)

---

### Agent Extensibility & Instrumentation

**Agent Extensibility:**
- The agent is designed with extension points to support future capability additions, such as: additional SF module coverage (Recruiting, LMS, Succession), integration with SAP Cloud ALM when available, automated post-change validation checks, and scheduled (pre-release) assessment runs.
- Tool integrations (MCP servers) are modular — new SF API areas can be added as additional MCP tools without restructuring the core agent.

**Business Step Instrumentation:**
- All five key business milestones (see Milestones section) must emit structured log statements for observability.
- Log pattern: `[MILESTONE_ID].[achieved|missed]: [description]`
- Instrumentation enables monitoring of agent behaviour in production and supports debugging of incomplete or failed release cycles.

---

### Automation & Agent Behaviour

**Automation Level:** Hybrid (LLM reasoning + human-in-the-loop approval gate)

**Actions the agent performs without human approval:**
- Parsing and indexing release note content
- Querying SF tenant configuration via OData APIs (read-only)
- Generating impact assessment reports
- Classifying changes as low-risk vs. requires-approval
- Presenting the change plan to the admin

**Actions that require human review or approval:**
- Applying any configuration change to a tenant (even low-risk changes require explicit confirmation before execution)
- Selecting which tenants to include in an assessment run

**Model or engine used:** LLM via SAP Generative AI Hub (GPT-4o class model)

**Knowledge & data sources accessed:**

- SF What's New Viewer release notes (provided by admin per release cycle)
- Live SF tenant configuration (queried via OData APIs at assessment time)
- Agent's own change log (for audit and context across sessions)

**Tools or connectors invoked:**

- `PLTRoleBasedPermissions` MCP tool: read and assess permission role configurations (read/write — write gated by human confirmation)
- `PLTGenericObjects` MCP tool: read and update picklists and foundation objects (read/write — write gated by confirmation)
- `FoundationPlatformPLT` MCP tool: read platform and common configuration (read-only in assessment; selected writes gated)
- `PLTUserManagement` MCP tool: read user configuration state (read-only)

**Guardrails & fail-safes:**

- No change is applied to any tenant without explicit admin confirmation in the active session
- Changes classified as requires-approval are never auto-applied, even if confirmed in bulk
- If an API call fails during change application, the agent halts remaining changes, reports the error, and does not partially apply a dependent change set
- Agent never stores or logs full credential secrets; tenant credential references use secure vault identifiers only
- If release note content cannot be confidently parsed, the agent flags ambiguous items for human review rather than guessing

---

## Milestones

### M1: Release Notes Ingested

- **Description**: The agent has successfully received and parsed the SF What's New Viewer content for the upcoming release cycle.
- **Achieved when**: Release note content is indexed and the agent can answer questions about specific change items and their feature areas.
- **Log on achievement**: `M1.achieved: release notes ingested and indexed for release [release-version], [N] change items identified`
- **Log on miss**: `M1.missed: release note ingestion did not complete — content unavailable or unparseable`

### M2: Impact Assessment Complete

- **Description**: The agent has queried the target tenant's live configuration and produced a structured impact report identifying which release items affect that tenant.
- **Achieved when**: A per-tenant impact report is generated listing all affected configuration areas with their current state.
- **Log on achievement**: `M2.achieved: impact assessment complete for tenant [tenant-id], [N] impacted areas identified`
- **Log on miss**: `M2.missed: impact assessment did not complete for tenant [tenant-id] — API query failed or timed out`

### M3: Change Plan Generated

- **Description**: All impacted items have been classified as low-risk (auto-applicable) or requires-human-approval, and the plan has been presented to the admin.
- **Achieved when**: The agent has presented a complete, classified change plan and is awaiting admin confirmation.
- **Log on achievement**: `M3.achieved: change plan generated for tenant [tenant-id] — [N] low-risk, [M] requires-approval`
- **Log on miss**: `M3.missed: change plan generation incomplete for tenant [tenant-id]`

### M4: Low-Risk Changes Applied

- **Description**: The admin has confirmed the change plan and the agent has successfully applied all low-risk changes to the target tenant.
- **Achieved when**: All low-risk changes have been applied via SF OData APIs and confirmed with success responses; any failures are recorded.
- **Log on achievement**: `M4.achieved: [N] low-risk changes applied to tenant [tenant-id], [F] failures recorded`
- **Log on miss**: `M4.missed: change application aborted for tenant [tenant-id] — confirmation not received or API error`

### M5: Review & Sign-Off

- **Description**: The admin has reviewed the full change log and the remaining manual action list has been delivered.
- **Achieved when**: The change log is finalised and the manual action guidance for requires-approval items has been presented to the admin.
- **Log on achievement**: `M5.achieved: release readiness cycle complete for tenant [tenant-id], change log finalised`
- **Log on miss**: `M5.missed: review cycle did not complete for tenant [tenant-id]`

---

## Risks, Assumptions, and Dependencies

### Risks

- **API coverage gaps**: Not all SF configuration areas are accessible via OData APIs — provisioning settings and some advanced rule types must remain manual. The agent will flag these clearly rather than silently skipping them.
- **SAP Cloud ALM not connected**: Structured IT change governance and cross-system audit trails are unavailable. The agent maintains its own change log as a mitigation, but this does not replace ALM-grade traceability.
- **Multi-tenant credential security**: Managing secrets for 3+ tenants introduces credential exposure risk. A secrets vault approach (e.g. SAP Credential Store) is required from the start.
- **LLM interpretation accuracy**: Release note language can be ambiguous. The agent must be tuned to flag uncertainty rather than make incorrect impact assessments.

### Assumptions

- SF What's New Viewer content is available as a document or accessible URL that the admin can provide per release cycle.
- Each managed tenant has an API user with sufficient permissions for the OData APIs listed in the integration points.
- The admin confirms changes explicitly — the agent will not apply changes based on implicit or ambiguous approval.

### Dependencies

- SAP SuccessFactors OData APIs: `PLTRoleBasedPermissions`, `PLTGenericObjects`, `FoundationPlatformPLT`, `PLTUserManagement` — all available in the landscape.
- SAP Generative AI Hub: LLM inference endpoint required for release note interpretation and impact reasoning.
- SAP BTP Credential Store or equivalent: secure storage for per-tenant SF API credentials.

---

## Appendix

### Glossary

- **What's New Viewer**: SAP's official portal listing all changes in each SuccessFactors release, filterable by module and release version.
- **Low-risk change**: A configuration update that affects display labels, translatable text, picklist values, or UI themes — changes that do not alter business logic, permissions, or data structure.
- **Requires-approval change**: A configuration update that affects permissions, workflow routing, data object structure, or integration behaviour — changes that carry material risk if applied incorrectly.
- **Multi-tenant**: The management of more than one distinct SAP SuccessFactors instance, each belonging to a different client organisation with separate credentials and configuration state.
- **A2A protocol**: Agent-to-Agent protocol used by SAP Joule Studio runtime agents for structured agent communication and extensibility.
- **MCP (Model Context Protocol)**: A protocol that allows AI agents to call structured tools (APIs) in a standardised way. Used here to wrap SF OData APIs as agent-callable tools.

### References

- SAP SuccessFactors Role-Based Permissions API: `sap.sf:apiResource:PLTRoleBasedPermissions:v1`
- SAP SuccessFactors Generic Objects API: `sap.sf:apiResource:PLTGenericObjects:v1`
- SAP SuccessFactors Common Platform API: `sap.sf:apiResource:FoundationPlatformPLT:v1`
- SAP SuccessFactors User Management API: `sap.sf:apiResource:PLTUserManagement:v1`
- SAP SuccessFactors What's New Viewer: https://help.sap.com/whats-new/cf0cb2cb149647329b5d02aa96303f56
