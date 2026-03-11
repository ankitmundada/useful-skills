---
name: atlassian-cli
description: "Interact with Jira and Confluence using the open-source atlassian-cli tool. Use this skill whenever the user asks you to interact with Jira or Confluence — creating issues, searching with JQL, transitioning tickets, managing sprints, triaging bugs, generating reports, bulk-creating issues from notes, writing or reading Confluence pages, spaces, and blog posts. Also trigger when the user mentions Jira project keys (like PROJ-123), asks about sprint status, backlogs, epics, or references atlassian-cli. Even if the user just says 'check my tickets', 'what's in my backlog', 'create a task for X', or 'write up a doc for this', use this skill."
---

# atlassian-cli — Agent Skill

Use the open-source `atlassian-cli` tool for all Jira and Confluence operations. It talks directly to Atlassian Cloud REST APIs and produces compact, predictable output well suited for AI agent workflows.

**Install:** `pip install cli-atlassian` (or `pipx install cli-atlassian` or `brew install ankitmundada/tap/atlassian-cli`).

**Setup:** `atlassian-cli auth login` — prompts for site URL, email, and API token. Create a token at https://id.atlassian.com/manage/api-tokens.

**Verify:** `atlassian-cli auth status`

---

## How Jira's Pieces Fit Together

Understanding the hierarchy is essential. Get this wrong and everything downstream — sprint planning, reporting, backlog grooming — falls apart.

```
Initiative (optional, via Jira Plans)
  └── Epic       — a feature, not a category. Has a definition of done.
        ├── Story    — user-facing outcome. Must fit in one sprint.
        ├── Task     — internal work (infra, refactors). Still needs estimation.
        └── Bug      — broken behavior, not a missing feature.
              └── Sub-task (optional) — use sparingly. 8 sub-tasks = 2 stories.
```

**Key judgment calls:** "Authentication System" is a good epic; "Backend Work" is not (use a component or label). "User can reset password" is a story; "Add POST /reset-password" is a task. "Login returns 500" is a bug; "We need login" is a story.

### Sprints

A sprint is a 1–2 week time-box. Stories should fit within one sprint — if they can't, split them. Don't stuff sprints past ~80% capacity. The sprint has a **goal** (a sentence, not a pile of tickets). The backlog is the prioritized queue that feeds sprints; the sprint holds only what's committed.

---

## Jira Commands

### Search

```bash
atlassian-cli jira issue search --jql "<JQL>" --limit 10
atlassian-cli jira issue search --jql "<JQL>" --fields "key,summary,status" --limit 10
atlassian-cli jira issue search --jql "<JQL>" --count            # just the count
atlassian-cli jira issue search --jql "<JQL>" --output json      # JSON output
atlassian-cli jira issue search --jql "<JQL>" --output csv       # CSV output
```

**Always set `--limit`.** Default is 10. Only increase when you genuinely need more. Use `--count` first if unsure how large the result set is.

### View

```bash
atlassian-cli jira issue view PROJ-123
atlassian-cli jira issue view PROJ-123 --fields "summary,description,status,comment"
atlassian-cli jira issue view PROJ-123 --output json
```

### Create

```bash
atlassian-cli jira issue create --project PROJ --type Task --summary "Title"
atlassian-cli jira issue create --project PROJ --type Story --summary "Title" --assignee "@me" --labels "frontend,urgent"
atlassian-cli jira issue create --project PROJ --type Story --summary "Title" --description "Details here" --priority "High"
atlassian-cli jira issue create --project PROJ --type Sub-task --summary "Sub-task" --parent PROJ-100
atlassian-cli jira issue create --from-json issue.json
```

`--assignee`: email address or `@me`. `--type`: Epic, Story, Task, Bug, Sub-task, etc. `--description`: issue body text. `--priority`: High, Highest, Medium, Low, Lowest.

### Edit

```bash
atlassian-cli jira issue edit PROJ-123 --summary "New title"
atlassian-cli jira issue edit PROJ-123 --assignee "user@example.com"
atlassian-cli jira issue edit PROJ-123 --unassign
atlassian-cli jira issue edit PROJ-123 --labels "bug,urgent"
atlassian-cli jira issue edit PROJ-123 --priority "High"
atlassian-cli jira issue edit PROJ-123 --from-json updates.json
```

### Assign

```bash
atlassian-cli jira issue assign PROJ-123 --user "@me"
atlassian-cli jira issue assign PROJ-123 --user "user@example.com"
atlassian-cli jira issue assign PROJ-123 --unassign
```

### Transition

```bash
atlassian-cli jira issue transition PROJ-123 --status "Done"
atlassian-cli jira issue transition PROJ-123 --status "In Progress"
```

The tool finds the right transition automatically from the status name. If the transition is invalid, it shows available options.

### Delete

```bash
atlassian-cli jira issue delete PROJ-123
atlassian-cli jira issue delete PROJ-123 --yes   # skip confirmation
```

### Comment

```bash
atlassian-cli jira issue comment add PROJ-123 --body "Comment text"
atlassian-cli jira issue comment add PROJ-123 --body-file comment.txt
atlassian-cli jira issue comment list PROJ-123 --limit 5
atlassian-cli jira issue comment edit PROJ-123 --id <COMMENT-ID> --body "Updated"
atlassian-cli jira issue comment delete PROJ-123 --id <COMMENT-ID>
```

For rich formatting, use ADF JSON in the body. See [adf-reference.md](adf-reference.md).

### Links

```bash
atlassian-cli jira issue link add PROJ-123 --target PROJ-456 --type "Blocks"
atlassian-cli jira issue link list PROJ-123
atlassian-cli jira issue link types
```

### Project

```bash
atlassian-cli jira project list
atlassian-cli jira project list --recent 5
atlassian-cli jira project view PROJ --output json
```

### Board

```bash
atlassian-cli jira board list --project PROJ
atlassian-cli jira board list --type scrum --name "My Board" --output json
atlassian-cli jira board view 42
atlassian-cli jira board sprints 42 --state active
atlassian-cli jira board sprints 42 --state "active,future"
```

`--type`: `scrum`, `kanban`, `simple`. `--state`: `active`, `closed`, `future` (comma-separated).

### Sprint

```bash
atlassian-cli jira sprint view 100
atlassian-cli jira sprint issues 100 --jql "assignee = currentUser()" --limit 20
atlassian-cli jira sprint create --board 42 --name "Sprint 5" --start 2026-03-15 --end 2026-03-29 --goal "Ship auth"
atlassian-cli jira sprint update 100 --state active      # start sprint
atlassian-cli jira sprint update 100 --state closed       # close sprint
atlassian-cli jira sprint update 100 --name "Sprint 5 - Extended" --end 2026-04-05
atlassian-cli jira sprint delete 100
atlassian-cli jira sprint move 100 --keys "PROJ-1,PROJ-2,PROJ-3"   # move issues into sprint
```

---

## JQL Reference

### Essential Patterns

```sql
-- My open work
assignee = currentUser() AND resolution = Unresolved

-- Bugs from the last 7 days
project = "PROJ" AND type = Bug AND created >= -7d

-- High-priority in current sprint
project = "PROJ" AND priority in (High, Highest) AND sprint in openSprints()

-- Text search
project = "PROJ" AND text ~ "payment error"

-- Recently updated
updated >= -24h ORDER BY updated DESC

-- Overdue
project = "PROJ" AND due < now() AND status != Done

-- Unassigned backlog items
project = "PROJ" AND assignee is EMPTY AND sprint is EMPTY AND status = "To Do"

-- Everything in an epic
"Epic Link" = PROJ-100

-- What shipped this week
project = "PROJ" AND status changed to Done AFTER startOfWeek()

-- Items by status category
project = "PROJ" AND statusCategory = 'In Progress'
```

### Syntax Reminders

- Quote values with spaces: `status = 'In Progress'`
- Key operators: `=`, `!=`, `~` (contains), `in`, `not in`, `>=`, `<=`, `is EMPTY`, `is not EMPTY`
- Key functions: `currentUser()`, `openSprints()`, `closedSprints()`, `startOfDay()`, `startOfWeek()`, `endOfMonth()`, `now()`
- Relative dates: `-7d`, `-24h`, `-30d`
- `statusCategory` values: `'To Do'`, `'In Progress'`, `'Done'`

### Advanced JQL

See [advanced-jql-reference.md](references/advanced-jql-reference.md) for date functions, sprint queries, status-change tracking, link-based queries, and complex combinations.

---

## Confluence Commands

### Page

```bash
atlassian-cli confluence page view <PAGE-ID>
atlassian-cli confluence page view <PAGE-ID> --body-format storage --output json
atlassian-cli confluence page create --space <SPACE-ID> --title "Title" --body "h1. Title\n\nContent here."
atlassian-cli confluence page create --space <SPACE-ID> --title "Title" --body-file page.wiki
atlassian-cli confluence page edit <PAGE-ID> --title "New Title" --body "h1. Updated\n\nNew content."
atlassian-cli confluence page search --cql "space = 'ENG' AND title = 'Design Doc'" --limit 10
```

**Body format for writing (`--format`):** `wiki` (default), `storage` (XHTML), `atlas_doc_format` (ADF JSON). Wiki is compact and preferred for LLM-generated content.

**Body format for reading (`--body-format`):** `markdown` (default — fetches rendered HTML and converts to clean Markdown), `storage` (raw XHTML), `view` (rendered HTML), `atlas_doc_format` (ADF JSON — very verbose, avoid).

**Wiki markup quick reference:**
```
h1. Heading 1    h2. Heading 2
*bold*   _italic_   +underline+   -strikethrough-
[link text|https://example.com]
* bullet item    # numbered item
||Col1||Col2||   |cell1|cell2|
{code:language=python}
code here
{code}
{note}important{note}   {warning}dangerous{warning}   {tip}helpful{tip}
```

### Space

```bash
atlassian-cli confluence space list
atlassian-cli confluence space list --type personal --status archived --output json
atlassian-cli confluence space view <SPACE-ID>
atlassian-cli confluence space create --key NEWSPACE --name "Space Name" --description "..."
```

`--type`: `global`, `personal`. `--status`: `current`, `archived`.

### Blog

```bash
atlassian-cli confluence blog list --space <SPACE-ID> --title "Release" --limit 10
atlassian-cli confluence blog view <BLOG-ID> --output json
atlassian-cli confluence blog create --space <SPACE-ID> --title "Title" --body "h1. Title\n\nContent here."
atlassian-cli confluence blog create --space <SPACE-ID> --title "Draft" --status draft --body-file post.wiki
```

`--status`: `current` (published), `draft`. `--format`: `wiki` (default), `storage`, `atlas_doc_format`.

---

## Common Options

All commands support:

| Option      | Short | Purpose                                      |
| ----------- | ----- | -------------------------------------------- |
| `--output`  | `-o`  | `table` (default), `json`, or `csv`          |
| `--profile` | `-p`  | Select auth profile (default: `default`)     |
| `--limit`   | `-l`  | Max results (for list/search commands)       |
| `--yes`     | `-y`  | Skip confirmation (for destructive commands) |

---

## Decision Patterns

### Querying: Zoom In, Don't Dump

**Start broad and shallow, then drill into detail.** When a user asks "where are we on the project?", don't pull every issue — that's a firehose. Instead:

1. **Start at epic level:** `--jql "project = PROJ AND type = Epic"` with `--limit 10`.
2. **Summarize from that.** Report epics and their statuses. This often answers the question.
3. **Drill in only if asked:** `--jql "'Epic Link' = PROJ-100 AND status != Done"`.

Always start with the smallest query that answers the question.

### Creating Issues

1. If the project key is unclear, run `atlassian-cli jira project list --recent 5` to discover it.
2. For assigning: use email address or `@me` for self-assignment.
3. Always provide `--project`, `--type`, and `--summary` at minimum.

### Transitioning Issues

The tool uses the status **name** directly — no need to look up transition IDs. Just use `--status "Done"`. If the name doesn't match, the tool shows available options.

### Understanding Fields by Inspecting Existing Issues

When you're unsure how a field works — especially custom fields — fetch an existing issue:

```bash
atlassian-cli jira issue view PROJ-123 --output json
```

Inspect the response to see field formats, custom field keys, and value structures.

---

## Workflow Recipes

### Daily Stand-up Summary

```bash
# Done yesterday
atlassian-cli jira issue search --jql "assignee = currentUser() AND status changed to Done AFTER startOfDay('-1d')" --limit 20

# In progress
atlassian-cli jira issue search --jql "assignee = currentUser() AND sprint in openSprints() AND statusCategory = 'In Progress'" --limit 20
```

Summarize: done, in-progress, and any blockers.

### Sprint Report

```bash
# Completed
atlassian-cli jira issue search --jql "sprint = '<Sprint Name>' AND status = Done" --limit 50

# Carry-overs
atlassian-cli jira issue search --jql "sprint = '<Sprint Name>' AND status != Done" --limit 50
```

### Bug Triage

```bash
# Read the bug
atlassian-cli jira issue view PROJ-456

# Search for duplicates
atlassian-cli jira issue search --jql "project = PROJ AND type = Bug AND text ~ '<keywords>'" --limit 5

# Triage: set priority and assignee
atlassian-cli jira issue edit PROJ-456 --labels "triaged,p1" --priority "High"
atlassian-cli jira issue assign PROJ-456 --user "dev@example.com"
atlassian-cli jira issue comment add PROJ-456 --body "Triaged: P1. No duplicates found."
```

### Sprint Management

```bash
# Create a new sprint
atlassian-cli jira sprint create --board 42 --name "Sprint 5" --start 2026-03-15 --end 2026-03-29 --goal "Complete auth flow"

# Start the sprint
atlassian-cli jira sprint update 100 --state active

# Move issues into sprint
atlassian-cli jira sprint move 100 --keys "PROJ-1,PROJ-2,PROJ-3"

# Close the sprint
atlassian-cli jira sprint update 100 --state closed
```

### Move and Reassign

```bash
atlassian-cli jira issue transition PROJ-123 --status "In Progress"
atlassian-cli jira issue assign PROJ-123 --user "new-owner@example.com"
atlassian-cli jira issue comment add PROJ-123 --body "Reassigned to new-owner for sprint 5."
```

### Publish Release Notes to Confluence

```bash
# Gather shipped items
atlassian-cli jira issue search --jql "project = PROJ AND fixVersion = 'v2.5' AND status = Done" --output json > shipped.json

# Create a blog post in wiki format (default)
atlassian-cli confluence blog create --space <SPACE-ID> --title "Release Notes — v2.5" --body-file release-notes.wiki
```

---

## Jira + Confluence: The Combination

Jira tracks **what** and **when**. Confluence tracks **why** and **how**.

| Content                          | Where                               | Why                                                |
| -------------------------------- | ----------------------------------- | -------------------------------------------------- |
| Requirements, specs, design docs | Confluence                          | Long-form, collaborative, versioned                |
| Sprint goals and retrospectives  | Confluence                          | Narrative that doesn't fit in a ticket             |
| Meeting notes → action items     | Confluence (notes) → Jira (tickets) | Notes capture context; tickets capture commitments |
| Individual work items            | Jira                                | Trackable, assignable, sprintable                  |
| Bug reports and triage           | Jira                                | Status-driven workflow                             |
| Release notes                    | Confluence (generated from Jira)    | Aggregated view for stakeholders                   |

---

## Auth & Profiles

```bash
# Set up a profile
atlassian-cli auth login --profile prod --site https://team.atlassian.net --email you@company.com --token <TOKEN>

# Check status
atlassian-cli auth status

# Use a specific profile
atlassian-cli jira issue search --jql "..." --profile prod

# Environment variable override
export ATLASSIAN_API_TOKEN=your-token-here
```

Config is stored at `~/.config/atlassian-cli/config.json`. The `ATLASSIAN_API_TOKEN` env var overrides stored tokens.

---

## Instance Memory: What to Cache Across Sessions

After your first session with an instance, save these constants to persistent memory so you never rediscover them:

```
## Jira Instance Constants
- site: <e.g., yourteam.atlassian.net>
- project key(s): <e.g., PROJ, TEAM>
- board ID: <from board list>
- space ID(s): <for Confluence spaces>
```

**What to cache:** site URL, project keys, board IDs, Confluence space IDs.

**What not to cache:** Sprint IDs (change every cycle — rediscover with `board sprints --state active`), issue counts or statuses (always query live).

---

## Practical Tips

**Always leave a comment when modifying issues.** Especially when triaging, reassigning, or transitioning. Silent changes erode trust.

**Always set `--limit`.** Default to 10. Use `--count` first if unsure about result set size.

**Use `--output json` for structured data processing.** Use default (table) output for human-readable summaries. Use `--output csv` for export.

**Confirm destructive actions.** Before bulk-transitioning, deleting, or making sweeping edits, show the user what you plan to do and ask for approval.

**Use labels and components, not just epics.** Epics are for feature-level grouping. Labels are for cross-cutting concerns ("tech-debt", "security"). Components are for system areas ("backend", "iOS").

---

## Error Quick Reference

| Error                    | Fix                                                                           |
| ------------------------ | ----------------------------------------------------------------------------- |
| `No profiles configured` | Run `atlassian-cli auth login`                                                |
| `No API token`           | Set `ATLASSIAN_API_TOKEN` or re-login                                         |
| JQL syntax error         | Check field names; quote values with spaces                                   |
| Transition not available | The issue isn't in a status that allows that transition; view the issue first |
| 403 Forbidden            | User lacks permission for this project/action                                 |
| 404 Not Found            | Check the issue key or page/space ID                                          |

---

## Reference Files

- **[ADF Reference](adf-reference.md)** — Atlassian Document Format examples for rich text in comments and descriptions
- **[Advanced JQL Reference](references/advanced-jql-reference.md)** — Date functions, sprint queries, status-change tracking, link-based queries
