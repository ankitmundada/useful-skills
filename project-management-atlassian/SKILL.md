---
name: project-management-atlassian
description: "Guide for AI agents to work effectively in Jira and Confluence via the Atlassian MCP Server. Use this skill whenever the user asks you to interact with Jira or Confluence — creating issues, searching with JQL, transitioning tickets, managing sprints, triaging bugs, generating reports, bulk-creating issues from notes, writing or reading Confluence pages, or any read/write operation. Also trigger when the user mentions Jira project keys (like PROJ-123), asks about sprint status, backlogs, epics, or references Atlassian MCP. Even if the user just says 'check my tickets', 'what's in my backlog', 'create a task for X', or 'write up a doc for this', use this skill."
---

# Jira + Confluence Agent Skill

How to use Jira and Confluence effectively as an AI agent. This covers the mental model for how Jira's pieces fit together, which tools to reach for, how to write good JQL, and practical workflow patterns.

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

## Tool Selection

Pick the right tool on the first call.

### Jira Tools

| What you need to do | Tool |
|---|---|
| Find issues by criteria | `searchJiraIssuesUsingJql` |
| Get a specific issue's details | `getJiraIssue` |
| Create a new issue | `createJiraIssue` |
| Update issue fields | `editJiraIssue` |
| Move issue to a new status | `transitionJiraIssue` (call `getTransitionsForJiraIssue` first) |
| Add a comment | `addCommentToJiraIssue` |
| Log time | `addWorklogToJiraIssue` |
| List projects | `getVisibleJiraProjects` |
| Get issue types for a project | `getJiraProjectIssueTypesMetadata` |
| Get required fields for creation | `getJiraIssueTypeMetaWithFields` |
| Find a user's account ID | `lookupJiraAccountId` |
| Get remote links on an issue | `getJiraIssueRemoteIssueLinks` |

### Confluence Tools

| What you need to do | Tool |
|---|---|
| Create a page | `createConfluencePage` |
| Read a page | `getConfluencePage` |
| Update a page | `updateConfluencePage` |
| Search pages with CQL | `searchConfluenceUsingCql` |
| List spaces | `getConfluenceSpaces` |
| List pages in a space | `getPagesInConfluenceSpace` |
| Get child pages | `getConfluencePageDescendants` |
| Get page comments | `getConfluencePageFooterComments` |
| Add a comment to a page | `createConfluenceFooterComment` |

### Searching: JQL for Jira, CQL for Confluence

There is no cross-product natural-language search on the free tier. Use the right query language for each product:

- **Jira** → `searchJiraIssuesUsingJql` with JQL (see Essential JQL below)
- **Confluence** → `searchConfluenceUsingCql` with CQL (see the advanced reference for CQL patterns)

If the user asks a broad question that could span both, run one JQL search and one CQL search, then combine the results.

---

## Essential JQL

These patterns cover the vast majority of real-world agent queries.

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

**If JQL doesn't work:** Check that field names are exact (custom fields use `cf[10001]` syntax). Always quote string values. The `sprint` field only exists in Scrum projects with a board configured.

---

## Creating Issues

Never guess project keys, issue types, or required fields. Discover them.

1. **Identify the project.** If unclear, call `getVisibleJiraProjects` and pick from context.
2. **Get issue types.** Call `getJiraProjectIssueTypesMetadata` with the project key. This tells you what types exist (Story, Bug, Task, Epic) and their IDs.
3. **Get required fields.** Call `getJiraIssueTypeMetaWithFields` with the project key and issue type ID. Some projects require priority, components, or custom fields beyond just a summary.
4. **Resolve people.** If assigning, call `lookupJiraAccountId` with a name or email. Never hardcode account IDs.
5. **Create.** Call `createJiraIssue` with all required fields.

**For bulk creation** (e.g., from meeting notes or a spec): do steps 2–3 once, then loop step 5 for each item. Don't re-fetch metadata per issue.

---

## Transitioning Issues

Jira workflows are custom per project. Never assume a transition name exists.

1. Call `getTransitionsForJiraIssue` to see what transitions are available from the issue's current status.
2. Match the user's intent to a transition name. If ambiguous, present the options.
3. Call `transitionJiraIssue` with the transition **ID** (not name).
4. Add a comment explaining the transition if it's meaningful for the team's audit trail.

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

**Practical pattern:** When creating issues from a spec, use `getConfluencePage` to read the spec, extract action items, then `createJiraIssue` for each. Add the Confluence page link to each issue's description so developers can trace back to the "why."

**Sprint reports:** After analyzing sprint data via JQL, call `createConfluencePage` to persist the summary as a team-visible document rather than just printing it in chat.

---

## Common Workflows

### Daily Stand-up Summary
```
1. searchJiraIssuesUsingJql — what I completed yesterday:
   assignee = currentUser() AND status changed to Done AFTER startOfDay("-1d")
2. searchJiraIssuesUsingJql — what's in progress:
   assignee = currentUser() AND sprint in openSprints() AND status != Done
3. Summarize: done, in-progress, and any blockers.
```

### Sprint Report
```
1. Search for completed items: sprint = "Sprint 12" AND status = Done
2. Search for carry-overs: sprint = "Sprint 12" AND status != Done
3. Calculate completion rate.
4. Optionally createConfluencePage with the formatted report.
```

### Bug Triage
```
1. getJiraIssue — read the bug details.
2. Analyze: determine appropriate priority, component, assignee.
3. editJiraIssue — set priority, labels, assignee.
4. addCommentToJiraIssue — explain triage reasoning (builds trust, creates audit trail).
5. transitionJiraIssue if it needs to move to a specific status.
```

### Create Tickets from Meeting Notes
```
1. getVisibleJiraProjects → confirm target project.
2. getJiraProjectIssueTypesMetadata → get type IDs.
3. getJiraIssueTypeMetaWithFields → know required fields.
4. For each action item: createJiraIssue.
5. Report created ticket keys back to the user.
```

### Move an Issue and Reassign
```
1. lookupJiraAccountId with the person's name → get account ID.
2. getTransitionsForJiraIssue → find the target transition.
3. transitionJiraIssue.
4. editJiraIssue to update the assignee.
5. addCommentToJiraIssue to document the change.
```

---

## Practical Tips and Pitfalls

**Always leave a comment when modifying issues.** Especially when triaging, reassigning, or transitioning. Silent changes erode trust. A one-line comment explaining "why" makes agent-driven changes transparent.

**Don't over-create issues.** If a user says "create a task to fix the login bug," that's one issue, not three. Resist the urge to decompose prematurely — let the developer decide if sub-tasks are needed.

**Cache metadata within a session.** `getVisibleJiraProjects`, `getJiraProjectIssueTypesMetadata`, and `getJiraIssueTypeMetaWithFields` return data that rarely changes. Call them once and reuse.

**Prefer narrow JQL.** A query returning 5 results is better than one returning 200 that you then filter. Push all filtering into JQL.

**Confirm destructive actions.** Before bulk-transitioning, deleting, or making sweeping edits, show the user what you plan to do and ask for approval.

**Use labels and components, not just epics.** Epics are for feature-level grouping. Labels are for cross-cutting concerns ("tech-debt", "security", "performance"). Components are for system areas ("backend", "iOS", "infra"). They serve different purposes — use them that way.

**Link issues to Confluence pages.** When a story originates from a spec, put the Confluence link in the description. When a sprint ends, write the retro in Confluence and link it. The connection between "what" and "why" is where teams lose context — don't let that happen.

---

## Error Quick Reference

| Error | Fix |
|---|---|
| JQL syntax error | Check field names; quote values with spaces |
| Cannot create issue | Call `getJiraIssueTypeMetaWithFields` — you're missing a required field |
| Transition not available | Call `getTransitionsForJiraIssue` — issue isn't in the right status |
| 403 Forbidden | User doesn't have permission for this project/action |
| Rate limited | Back off, batch operations, cache metadata |

---

## Reference Files

For advanced JQL patterns (date functions, sprint queries, status change tracking, link-based queries), multi-step workflow recipes (release notes generation, dependency analysis, stale issue cleanup, velocity calculation, workload distribution), JSM operations, CQL for Confluence, custom field handling, and a complete field name table:

→ **[Advanced Jira Reference](./references/advanced-jira-reference.md)**
