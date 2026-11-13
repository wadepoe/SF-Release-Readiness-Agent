---
name: change-classification
description: Rules for classifying each required SuccessFactors configuration change as low-risk (auto-applicable) or requires-human-approval
---

# Change Classification Skill

Use this skill after the impact assessment is complete and you have a list of change items that affect the current tenant. Classify each item before presenting the change plan to the admin.

## Classification Rules

### Low-Risk (Auto-Applicable After Confirmation)

A change is LOW-RISK if ALL of the following are true:
- It affects only display labels, translatable text, picklist value labels, or UI theme settings
- It does not modify any access control, permission rule, or data visibility setting
- It does not change any workflow routing or approval step configuration
- It does not alter the structure or fields of any MDF object
- It does not affect integration endpoints, API configurations, or authentication settings
- Reversing the change would have no impact on data integrity

**Examples of low-risk changes:**
- Updating a picklist value label (e.g. renaming "Active" to "Active Employee")
- Updating a Foundation Object text/label (e.g. renaming a department display name)
- Changing a UI theme colour or font setting
- Adding a translation for an existing UI label
- Updating custom navigation link labels

### Requires Human Approval

A change REQUIRES APPROVAL if ANY of the following is true:
- It modifies a Role-Based Permission role, permission group, or access rule
- It changes who can see or edit any data field or UI section
- It alters the routing, steps, or conditions of any workflow or approval process
- It changes the structure, fields, or relationships of any MDF object
- It affects integration configurations, API endpoints, or authentication/SSO settings
- It removes or deprecates a feature that is currently active in this tenant
- It changes any business rule condition or action
- Its impact on the tenant cannot be fully assessed from the release note alone (review_required = true)
- The classification is uncertain for any reason

**Escalation rule**: When in doubt, always classify as REQUIRES APPROVAL. Never apply the benefit of the doubt to a change that could affect access, data, or process flow.

## Output Format

For each change item, annotate with:
```
classification: low-risk | requires-approval
rationale: <one sentence explaining why this classification was assigned>
```

## Summary Output

After classifying all items, produce a summary:
- **Low-risk changes**: <count> items — these can be applied automatically after your confirmation
- **Requires-approval changes**: <count> items — these will require your manual action; the agent will provide step-by-step guidance
- **Not applicable to this tenant**: <count> items (from the impact assessment)

Present this summary clearly to the admin before asking for confirmation to proceed.
