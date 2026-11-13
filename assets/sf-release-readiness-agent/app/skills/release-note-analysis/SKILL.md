---
name: release-note-analysis
description: Instructions for parsing and interpreting SAP SuccessFactors What's New Viewer release notes and mapping change items to configuration areas
---

# Release Note Analysis Skill

Use this skill when the user provides SAP SuccessFactors release note content (pasted text, uploaded document, or URL) and asks you to analyse what changes are required.

## Step 1: Ingest Release Note Content

Accept the release notes in one of these forms:
- **Pasted text**: the user pastes content directly into the conversation
- **Uploaded document**: a PDF or plain text file attached to the conversation
- **URL**: the user provides a link to the SF What's New Viewer; fetch the page content using available tools

If the source is a URL, attempt to retrieve the content. If retrieval fails, inform the user and ask them to paste the content directly.

## Step 2: Extract Change Items

For each item in the release notes, extract and record:
- **Module**: the SF module or product area (e.g. Employee Central, Recruiting, Performance & Goals, Platform, Onboarding)
- **Feature area**: the specific feature within the module (e.g. Role-Based Permissions, Business Rules, Picklists, Workflows)
- **Change type**: one of — New Feature, Changed Behaviour, Deprecation, Removed Feature, Configuration Required, Optional Action
- **Description**: a concise plain-language summary of what changed (1–2 sentences)
- **Action required**: Yes / No / Optional — whether the admin must take action before the release

## Step 3: Map to Configuration Domains

Map each change item to one or more of the following SuccessFactors configuration domains:

| Domain | Examples |
|---|---|
| Role-Based Permissions (RBP) | Permission roles, permission groups, access rules |
| Picklists & Foundation Objects | Picklist values, labels, FOJobFunction, FODepartment, FOCostCenter |
| Business Rules | Rule engine configurations, condition-action rules |
| Workflows & Approvals | Approval workflow routing, step configurations |
| MDF Objects & Custom Fields | Metadata Framework objects, custom field definitions |
| Platform & UI | UI themes, custom navigation, translations, SSO, Single Sign-On settings |
| User Management | User account settings, user data fields, password policies |
| Integration | Integration Center flows, API configurations |
| Other | Anything that does not fit the above |

A single change item may map to multiple domains.

## Step 4: Flag Ambiguous Items

If a change item's impact on the tenant's configuration cannot be determined from the release note text alone (e.g. "behaviour may change depending on your configuration"), flag it as:
- `review-required: true`
- Add a note explaining what is ambiguous and what the admin should check

Never assume a change does or does not apply — when in doubt, flag for review.

## Step 5: Produce Structured Output

Return a structured list of change items with the following fields per item:
```
- id: <sequential number>
  module: <SF module>
  feature_area: <feature area>
  change_type: <New Feature | Changed Behaviour | Deprecation | Removed Feature | Configuration Required | Optional Action>
  description: <plain-language summary>
  action_required: <Yes | No | Optional>
  configuration_domains: [<domain1>, <domain2>]
  review_required: <true | false>
  review_note: <explanation if review_required is true>
```

After producing this list, confirm to the admin:
- Total number of change items identified
- Count by module
- Count of items where action_required = Yes
- Count of items flagged as review_required
