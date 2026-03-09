---
name: project-management-atlassian
description: "Foundational guide for AI agents to work effectively in Jira and Confluence via the Atlassian MCP Server. Use this skill whenever the user asks you to interact with Jira or Confluence — creating issues, searching with JQL, transitioning tickets, managing sprints, triaging bugs, generating reports, bulk-creating issues from notes, writing or reading Confluence pages, or any read/write operation. Also trigger when the user mentions Jira project keys (like PROJ-123), asks about sprint status, backlogs, epics, or references Atlassian MCP. Even if the user just says 'check my tickets', 'what's in my backlog', 'create a task for X', or 'write up a doc for this', use this skill."
---

# Jira + Confluence Agent Skill

Foundational knowledge for AI agents working with Jira and Confluence. Covers how Jira's pieces fit together, decision patterns for common tasks, JQL, and the Jira+Confluence philosophy.

**Relationship with Atlassian's official skills:** Atlassian publishes task-specific workflow skills (triage, status reports, spec-to-backlog, etc.) that automate common multi-step jobs. This skill is the foundation layer underneath — it teaches how Jira works, how to approach tasks, and how to write queries. When an official Atlassian skill exists for a task, prefer it. When it doesn't, or when you need general Jira fluency, use this skill. See "Official Atlassian Skills" at the end for the full list.

---

## How Jira's Pieces Fit Together

Understanding the hierarchy is essential. Get this wrong and everything downstream — sprint planning, reporting, backlog grooming — falls apart.

### The Hierarchy

```
Initiative (optional, via Jira Plans)
  └── Epic          — a feature or body of work, spans multiple sprints
        └── Story   — a user-facing outcome, completable in one sprint
        └── Task    — internal work (refactors, infra, tooling)
        └── Bug     — something broken that needs fixing
              └── Sub-task (optional) — a checklist item within a story/task/bug
```

### Opinionated Rules

**Epics are features, not categories.** "Authentication System" is a good epic. "Backend Work" is not — that's a component or label. An epic should have a clear definition of done: when all its stories are shipped, the feature is complete.

**Stories describe outcomes, not implementation.** "As a user, I can reset my password via email" is a story. "Add POST /reset-password endpoint" is a task or sub-task. If your stories read like technical specs, they're too granular.

**Tasks are for work that doesn't face the user.** CI/CD pipeline improvements, database migrations, dependency upgrades, tech debt payoff. These still belong in sprints and still need estimation.

**Bugs are for broken behavior, not missing features.** "Login button returns 500" is a bug. "We need a login button" is a story. Mislabeling creates noisy reports.

**Sub-tasks are optional and often overused.** If a story needs 8 sub-tasks, it's probably two stories. Use sub-tasks sparingly — for genuine checklists where each step needs independent tracking, not as a substitute for breaking stories down properly.

### Sprints

A sprint is a fixed time-box (typically 1–2 weeks) where the team commits to completing a set of issues. Key principles:

- **A sprint has a goal**, not just a pile of tickets. The goal is a sentence: "Users can complete the checkout flow end-to-end."
- **Stories should fit within one sprint.** If a story can't be finished in a single sprint, it's too big — split it.
- **Don't stuff sprints.** Unfinished work carries over and demoralizes. Aim for 80% capacity to leave room for surprises.
- **The backlog is the queue, not the sprint.** The backlog holds everything that's been groomed and prioritized. The sprint holds only what's committed for this time-box.

### How It All Connects

```
Backlog (prioritized queue)
  ├── Epic A: "User Authentication"
  │     ├── Story: "User can sign up with email"        ← Sprint 4
  │     ├── Story: "User can log in with password"       ← Sprint 4
  │     ├── Story: "User can reset password"             ← Sprint 5 (planned)
  │     └── Task: "Set up auth middleware"               ← Sprint 4
  ├── Epic B: "Payment Processing"
  │     ├── Story: "User can add a credit card"          ← Sprint 5 (planned)
  │     └── Bug: "Stripe webhook fails on refunds"       ← Sprint 4 (hotfix)
  └── Unepiced items
        └── Task: "Upgrade Node.js to v22"               ← Backlog (not yet planned)
```

The backlog feeds sprints. Epics give structure across sprints. Stories/tasks/bugs are the actual work units.

---

## Searching: JQL for Jira, CQL for Confluence

Use the right query language for each product. If a user asks a broad question that could span both, run one JQL search and one CQL search, then combine results. For CQL patterns, see the [Advanced Reference](./references/advanced-jira-reference.md) §4.

### Essential JQL

These patterns cover the vast majority of real-world queries.

```
# My open issues
assignee = currentUser() AND status != Done

# Bugs from the last 7 days
project = "PROJ" AND type = Bug AND created >= -7d

# High-priority items in the current sprint
project = "PROJ" AND priority in (High, Highest) AND sprint in openSprints()

# Text search
project = "PROJ" AND text ~ "payment error"

# Recently updated
updated >= -24h ORDER BY updated DESC

# Overdue
project = "PROJ" AND due < now() AND status != Done

# Unassigned backlog items
project = "PROJ" AND assignee is EMPTY AND sprint is EMPTY AND status = "To Do"

# Everything in an epic
"Epic Link" = PROJ-100

# What shipped this week
project = "PROJ" AND status changed to Done AFTER startOfWeek()
```

**Syntax reminders:** Quote values with spaces. Key operators: `=`, `!=`, `~` (contains), `in`, `not in`, `>=`, `<=`, `is EMPTY`, `is not EMPTY`. Key functions: `currentUser()`, `openSprints()`, `startOfDay()`, `startOfWeek()`, `now()`.

**If JQL doesn't work:** Check that field names are exact (custom fields use `cf[10001]` syntax). Always quote string values. The `sprint` field only exists in Scrum projects with a board configured. For advanced JQL patterns (date functions, sprint queries, status-change tracking, link-based queries), see the [Advanced Reference](./references/advanced-jira-reference.md) §1.

---

## Decision Patterns

These are the thinking patterns for common tasks — which operations to chain and in what order. The MCP connection already tells you what tools exist; this section tells you *when and why* to use them.

### Creating Issues

Never guess project keys, issue types, or required fields. Discover them.

1. If the project is unclear, list visible projects and pick from context.
2. Get issue types for the project. This tells you what types exist (Story, Bug, Task, Epic) and their IDs.
3. Get required fields for the project+type combo. Some projects require priority, components, or custom fields beyond a summary.
4. If assigning, look up the person's account ID by name or email. Never hardcode account IDs.
5. Create the issue with all required fields populated.

**For bulk creation** (e.g., from meeting notes or a spec): do steps 2–3 once, then loop step 5. Don't re-fetch metadata per issue. For pagination on large result sets and custom field value formats, see the [Advanced Reference](./references/advanced-jira-reference.md) §5–6.

### Transitioning Issues

Jira workflows are custom per project. Never assume a transition name exists.

1. Get available transitions for the issue to see what moves are valid from its current status.
2. Match the user's intent to a transition name. If ambiguous, present the options.
3. Execute the transition using the transition **ID** (not name).
4. Add a comment explaining the transition if it's meaningful for audit.

### Understanding Fields by Inspecting Existing Issues

**When you're unsure how a field works — especially custom fields, sprint fields, or the parent/epic link — the most reliable approach is to fetch an existing issue that already has it set and examine the response.** This is faster and more accurate than guessing from metadata alone.

For example, if you need to set the Sprint field on a new issue but aren't sure of the format, find an issue already in a sprint (`sprint in openSprints()`) and inspect how the sprint value appears. You'll see whether it expects an ID, a name, or an object. The same applies to epic links (some instances use `customfield_10014`, others use the `parent` field), story points, and any other custom field.

Make this a habit: **when a field write fails or you're unsure of the format, read an issue that has it right.**

---

## Jira + Confluence: The Combination

Jira tracks **what** and **when**. Confluence tracks **why** and **how**. Use them together:

| Content | Where it lives | Why |
|---|---|---|
| Requirements, specs, design docs | Confluence | Long-form, collaborative, versioned |
| Architecture decisions (ADRs) | Confluence | Persistent reference with context |
| Sprint goals and retrospectives | Confluence | Narrative that doesn't fit in a ticket |
| Meeting notes and action items | Confluence (notes) → Jira (tickets) | Notes capture context; tickets capture commitments |
| Individual work items | Jira | Trackable, assignable, sprintable |
| Bug reports and triage decisions | Jira | Status-driven workflow |
| Release notes | Confluence (generated from Jira) | Aggregated view for stakeholders |

**Practical pattern:** When creating issues from a spec, read the Confluence page, extract action items, then create Jira issues for each. Add the Confluence page link to each issue's description so developers can trace back to the "why."

---

## Workflows

### Workflows covered by official Atlassian skills

For these tasks, **prefer the official Atlassian skill if available**. If not installed, use the fallback guidance.

**Bug triage** → prefer `triage-issue` skill.
Fallback: Read the bug → search for duplicates with `text ~` → set priority/labels/assignee → comment with reasoning.

**Create tickets from meeting notes** → prefer `capture-tasks-from-meeting-notes` skill.
Fallback: Extract action items → look up assignee account IDs → create issues (discover project metadata first per "Creating Issues" above).

**Convert a spec into a backlog** → prefer `spec-to-backlog` skill.
Fallback: Read the Confluence page → create an Epic → create implementation tickets linked to the Epic.

**Generate a status report** → prefer `generate-status-report` skill.
Fallback: Search issues by status/priority → summarize into categories → optionally publish to Confluence.

**Search company knowledge** → prefer `search-company-knowledge` skill.
Fallback: Run JQL and CQL searches in parallel, then synthesize results.

### Workflows without official Atlassian skills

**Daily stand-up summary:**
```
1. Search — completed yesterday:
   assignee = currentUser() AND status changed to Done AFTER startOfDay("-1d")
2. Search — in progress:
   assignee = currentUser() AND sprint in openSprints() AND status != Done
3. Summarize: done, in-progress, and any blockers.
```

**Sprint report:**
```
1. Completed: sprint = "Sprint 12" AND status = Done
2. Carry-overs: sprint = "Sprint 12" AND status != Done
3. Calculate completion rate.
4. Optionally create a Confluence page with the formatted report.
```

**Move an issue and reassign:**
```
1. Look up the person's account ID.
2. Get available transitions → find the target.
3. Execute transition.
4. Update the assignee.
5. Comment to document the change.
```

---

## Instance Memory: What to Cache Across Sessions

Every Jira instance has constants that never change (or change very rarely). Discovering them costs API calls and tokens every time. **After your first session with an instance, save these to your persistent memory or AGENTS.md** so you never have to look them up again:

```
## Jira Instance Constants
- cloudId: <from getAccessibleAtlassianResources or first API response>
- site: <e.g., yourteam.atlassian.net>
- project key: <e.g., PROJ>
- board ID: <from board config>
- active sprint ID: <update when sprints change>
- issue type IDs: Story=10001, Task=10002, Bug=10003, Epic=10004 (varies by instance)
- key custom fields:
  - Sprint: customfield_10020 (write as integer ID, not name)
  - Epic Link: customfield_10014 (some instances use `parent` instead)
  - Story Points: customfield_10016
- transition IDs: Done=51, In Progress=31, To Do=21, Backlog=11 (varies by workflow)
```

**What to cache:** cloudId, site URL, project key(s), board ID, issue type IDs, custom field mappings (especially Sprint, Epic Link, Story Points), and transition IDs.

**What not to cache:** Sprint IDs (these change every sprint cycle — re-discover with `openSprints()`), assignee account IDs (people join and leave), issue counts or statuses (always query live).

**How to discover these:** On first use, create one test issue or fetch an existing well-populated issue and inspect the response. The field IDs, transition IDs, and custom field mappings will all be visible. Then save them.

---

## Practical Tips and Pitfalls

**Always leave a comment when modifying issues.** Especially when triaging, reassigning, or transitioning. Silent changes erode trust. A one-line comment explaining "why" makes agent-driven changes transparent.

**Don't over-create issues.** If a user says "create a task to fix the login bug," that's one issue, not three. Resist the urge to decompose prematurely — let the developer decide if sub-tasks are needed.

**Cache metadata within a session.** Project lists, issue type configs, and field metadata rarely change. Call them once and reuse. Better yet, save them to instance memory (see above).

**Prefer narrow JQL.** A query returning 5 results is better than one returning 200 that you then filter. Push all filtering into JQL.

**Always set result limits.** Use `maxResults: 10` (or `limit: 10` for CQL) on every search call. Default to 10. Only increase if you genuinely need more results — and even then, cap it. Large result sets waste tokens, slow responses, and rarely add value. If you need to process many issues, paginate deliberately rather than pulling everything at once.

**Confirm destructive actions.** Before bulk-transitioning, deleting, or making sweeping edits, show the user what you plan to do and ask for approval.

**Use labels and components, not just epics.** Epics are for feature-level grouping. Labels are for cross-cutting concerns ("tech-debt", "security", "performance"). Components are for system areas ("backend", "iOS", "infra"). They serve different purposes — use them that way.

**Link issues to Confluence pages.** When a story originates from a spec, put the Confluence link in the description. When a sprint ends, write the retro in Confluence and link it. The connection between "what" and "why" is where teams lose context — don't let that happen.

**Inspect before you write.** When you're unsure how a field should be formatted, fetch an existing issue that has it set correctly and mirror the structure. This is the fastest way to learn any instance's quirks.

---

## Error Quick Reference

| Error | Fix |
|---|---|
| JQL syntax error | Check field names; quote values with spaces |
| Cannot create issue | Get field metadata — you're missing a required field |
| Transition not available | Get transitions for the issue — it's not in the expected status |
| 403 Forbidden | User doesn't have permission for this project/action |
| Rate limited | Back off, batch operations, cache metadata |
| Field format wrong | Inspect an existing issue that has the field set correctly |

---

## Official Atlassian Skills

Atlassian publishes these task-specific workflow skills as part of the [atlassian-mcp-server](https://github.com/atlassian/atlassian-mcp-server/tree/main/skills) repo (also available as the Atlassian plugin in the Cursor marketplace). If installed in your environment, prefer them for matching tasks. If not available, fall back to the guidance in this skill.

| Skill | What it does | When to prefer it |
|---|---|---|
| `triage-issue` | Searches for duplicates, checks fix history, creates or updates bug reports | User reports a bug, pastes an error, or asks to triage |
| `capture-tasks-from-meeting-notes` | Extracts action items, resolves assignees, creates Jira tasks | User shares meeting notes and wants tasks created |
| `spec-to-backlog` | Reads a Confluence spec, creates an Epic and linked implementation tickets | User wants to turn a spec/requirements doc into tickets |
| `generate-status-report` | Queries Jira, categorizes by status/priority, publishes to Confluence | User asks for a project status report or weekly summary |
| `search-company-knowledge` | Searches Confluence + Jira in parallel, returns cited answers | User asks about internal processes, systems, or terminology |

**These skills and this skill are complementary.** This skill provides Jira/Confluence literacy — hierarchy, decision patterns, JQL, sprint discipline, the Jira+Confluence philosophy. The official skills provide optimized automation for specific jobs. Use both: this skill for general fluency, official skills for the workflows they cover.

---

## Reference Files

For advanced JQL (date functions, sprint queries, status-change tracking, link-based queries), multi-step workflow recipes (release notes, dependency analysis, stale issue cleanup, velocity, workload distribution), CQL for Confluence, custom field handling, pagination, and a complete field name table:

→ **[Advanced Jira Reference](./references/advanced-jira-reference.md)**
