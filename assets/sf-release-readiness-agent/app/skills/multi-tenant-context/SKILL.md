---
name: multi-tenant-context
description: Rules for managing context isolation across multiple SuccessFactors tenant environments
---

# Multi-Tenant Context Skill

Use this skill before any operation that queries or modifies a specific SuccessFactors tenant. This skill ensures that tenant contexts are never mixed and that the admin always knows which tenant is being acted upon.

## Step 1: Confirm the Active Tenant

Before querying or modifying any tenant configuration:
1. Identify the current active tenant from the conversation context
2. Confirm the tenant with the admin using their preferred alias (e.g. "ClientA", "ACME Corp") — never refer to raw tenant IDs or hostnames in responses
3. If no tenant has been selected yet, ask: "Which tenant would you like to work with? Please select from the tenants you have registered."

## Step 2: Tenant Registration (Session Start)

At the start of each release readiness session, prompt the admin to register their tenants:
- Ask for each tenant: alias (user-friendly name), tenant URL/host, and a credential reference (vault key or identifier — never the raw credential itself)
- Store the tenant list in the session context as: `{ alias, host, credential_ref }`
- Confirm the registered tenants back to the admin before proceeding

## Step 3: Context Isolation Rules

ALWAYS enforce the following:
- Never use credentials from tenant A when making API calls for tenant B
- Never include configuration data from tenant A in the impact report for tenant B
- Never mix change logs across tenants — each tenant has its own independent change log for this session
- If the admin switches tenant mid-conversation (e.g. "now let's look at ClientB"), explicitly acknowledge the switch and confirm the new active tenant before proceeding

## Step 4: Tenant-Switching

When the admin requests a switch to a different tenant:
1. Confirm: "Switching context to [TenantAlias]. All subsequent queries and changes will apply to this tenant."
2. Clear any tenant-specific working state from the previous tenant (impact report, change plan, pending changes)
3. Do NOT carry over unconfirmed changes from the previous tenant

## Step 5: Pre-Action Confirmation

Before applying any change, always re-confirm the target tenant explicitly:
- State: "I am about to apply [N] low-risk changes to tenant [TenantAlias]. Please confirm to proceed."
- Never apply changes to a tenant without this explicit confirmation in the current conversation turn.

## Error Handling

- If a credential reference cannot be resolved for a tenant, inform the admin and do not proceed with that tenant
- If an API call fails for a tenant, record the failure and continue with the next tenant if the admin has requested batch processing
- Never attempt to guess or substitute credentials for a failed tenant
