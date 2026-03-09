# Advanced Jira MCP Reference

Supplementary reference for the jira-mcp-agent skill. Load this file when you need deeper JQL patterns, multi-step workflow recipes, or Jira Service Management operations.

---

## Table of Contents

1. Advanced JQL Patterns
2. Multi-Step Workflow Recipes
3. Jira Service Management (JSM) Tools
4. CQL Patterns for Confluence Search
5. Custom Field Handling
6. Pagination and Large Result Sets
7. Common Jira Field Names

---

## 1. Advanced JQL Patterns

### Relative Date Functions

```
# Issues created this week
created >= startOfWeek()

# Issues updated in the last 3 days
updated >= -3d

# Issues due before end of month
due <= endOfMonth()

# Issues resolved between specific dates
resolved >= "2026-01-01" AND resolved <= "2026-03-31"

# Issues created in the last 2 hours
created >= -2h
```

### Sprint-Based Queries

```
# All issues in any open sprint
sprint in openSprints()

# Issues in a specific sprint by name
sprint = "Sprint 2026-Q1-3"

# Carry-over: unresolved issues from closed sprints
sprint in closedSprints() AND resolution = Unresolved

# Issues not yet in any sprint (backlog)
sprint is EMPTY AND status = "To Do"
```

### Group and Team Queries

```
# Issues assigned to members of a group
assignee in membersOf("engineering-team")

# Issues reported by a specific user
reporter = "5a1234bc5678de9012f34567"

# Unassigned issues in a specific project
project = "PROJ" AND assignee is EMPTY

# Issues watched by current user
watcher = currentUser()
```

### Status Change Queries

```
# Issues that moved to "In Review" today
status changed to "In Review" AFTER startOfDay()

# Issues that were "In Progress" at some point in the last week
status was "In Progress" DURING (startOfWeek(), now())

# Issues that have been in current status for more than 5 days
status changed BEFORE -5d AND status != Done

# Issues transitioned by a specific user
status changed BY "5a1234bc5678de9012f34567"
```

### Component and Label Filtering

```
# Issues with a specific component
component = "Backend API"

# Issues with multiple labels (AND)
labels = "performance" AND labels = "p0"

# Issues with any of these labels (OR)
labels in ("critical", "security", "data-loss")

# Issues without any label
labels is EMPTY
```

### Link-Based Queries

```
# Issues that block other issues
issueLinkType = "blocks"

# Issues linked to a specific epic
"Epic Link" = PROJ-100

# Issues with sub-tasks
issueFunction in hasSubtasks()

# Parent epic of child issues
issueFunction in epicsOf("project = PROJ AND type = Bug")
```

Note: `issueFunction` requires the ScriptRunner or similar plugin. Not available by default.

### Combining Complex Clauses

```
# High-priority bugs in active sprint, unresolved, created in last 30 days
project = "PROJ"
  AND type = Bug
  AND priority in (High, Highest)
  AND sprint in openSprints()
  AND resolution = Unresolved
  AND created >= -30d
  ORDER BY priority DESC, created ASC
```

---

## 2. Multi-Step Workflow Recipes

### Recipe: Automated Release Notes

```
Step 1: searchJiraIssuesUsingJql
  JQL: project = "PROJ" AND fixVersion = "v2.5.0" AND status = Done
       ORDER BY type ASC, priority DESC

Step 2: Group results by issue type (Features, Bugs, Improvements)

Step 3: createConfluencePage
  Title: "Release Notes — v2.5.0"
  Body: Formatted markdown with grouped issues, keys, and summaries

Step 4: addCommentToJiraIssue (on each resolved issue)
  Comment: "Included in release notes: [link to Confluence page]"
```

### Recipe: Dependency Analysis

```
Step 1: getJiraIssue for the target issue (e.g., PROJ-200)

Step 2: Check issueLinks in the response for:
  - "blocks" relationships (this issue blocks others)
  - "is blocked by" relationships (this issue is blocked)

Step 3: For each linked issue, getJiraIssue to check its status

Step 4: Build a dependency summary:
  - Blockers: list issues blocking PROJ-200
  - Downstream: list issues that PROJ-200 blocks
  - Status of each: are blockers resolved or still open?
```

### Recipe: Stale Issue Cleanup

```
Step 1: searchJiraIssuesUsingJql
  JQL: project = "PROJ" AND status = "To Do" AND updated <= -90d
       ORDER BY updated ASC

Step 2: For each stale issue, present to user:
  - Key, summary, last updated date, reporter

Step 3: With user approval:
  a. addCommentToJiraIssue: "This issue has been inactive for 90+ days. Closing as stale."
  b. getTransitionsForJiraIssue → find "Close" or "Won't Do" transition
  c. transitionJiraIssue to close it
```

### Recipe: Sprint Velocity Calculation

```
Step 1: searchJiraIssuesUsingJql
  JQL: sprint = "Sprint 12" AND status = Done

Step 2: Sum the story points (check field: story_points or customfield_XXXXX)

Step 3: searchJiraIssuesUsingJql
  JQL: sprint = "Sprint 12" AND status != Done

Step 4: Sum incomplete story points

Step 5: Report:
  - Completed points: X
  - Carry-over points: Y
  - Velocity: X points / sprint duration
  - Completion rate: X / (X + Y) * 100%
```

### Recipe: Workload Distribution Analysis

```
Step 1: searchJiraIssuesUsingJql
  JQL: project = "PROJ" AND sprint in openSprints() AND status != Done

Step 2: Group by assignee, count issues per person

Step 3: Flag imbalances:
  - Overloaded: assignees with > 2x average issue count
  - Underloaded: assignees with 0 or very few issues
  - Unassigned: issues with no assignee

Step 4: Present distribution summary to user
```

---

## 3. Jira Service Management (JSM) Tools

JSM tools require API token authentication (not OAuth). They must be explicitly enabled by an organization admin.

### Available Tools

| Tool | Description |
|---|---|
| `getJsmOpsAlerts` | Query alerts by ID, alias, or search. Filter by time window. |
| `updateJsmOpsAlert` | Acknowledge, unacknowledge, close, or escalate an alert. |
| `getJsmOpsScheduleInfo` | List on-call schedules. Get current or next on-call responders. |
| `getJsmOpsTeamInfo` | List operations teams. View escalation policies and roles. |

### Common JSM Workflows

**Who's on call right now?**
```
1. getJsmOpsScheduleInfo — query current on-call for a schedule
2. Present responder name and schedule details
```

**Acknowledge an active alert:**
```
1. getJsmOpsAlerts — search for the alert by keyword or alias
2. updateJsmOpsAlert — set action to "acknowledge"
3. Optionally add a note explaining the acknowledgment
```

**Escalate an unresolved alert:**
```
1. getJsmOpsAlerts — find the alert
2. getJsmOpsTeamInfo — check escalation policy
3. updateJsmOpsAlert — set action to "escalate"
```

---

## 4. CQL Patterns for Confluence Search

CQL (Confluence Query Language) is used with `searchConfluenceUsingCql`.

```
# Search by title
title = "Sprint Retrospective Q1"

# Full text search
text ~ "deployment checklist"

# Pages in a specific space
space = "ENG" AND type = "page"

# Pages modified in the last 7 days
lastModified >= now("-7d")

# Pages created by a specific user
creator = "5a1234bc5678de9012f34567"

# Pages with a specific label
label = "architecture-decision"

# Combine: recent meeting notes in a space
space = "TEAM" AND label = "meeting-notes" AND lastModified >= now("-30d")
```

---

## 5. Custom Field Handling

Jira projects often have custom fields. They appear in API responses as `customfield_10001`, `customfield_10042`, etc.

### Discovering Custom Fields

When you call `getJiraIssueTypeMetaWithFields`, the response includes all fields (standard and custom) with:
- `fieldId` — the customfield ID
- `name` — the human-readable name (e.g., "Story Points", "Team")
- `required` — whether it's mandatory for issue creation
- `schema` — the data type (string, number, array, option)

### Using Custom Fields in JQL

```
# Custom field by name (if indexed for JQL)
"Story Points" >= 5

# Custom field by ID
cf[10042] = "Platform Team"
```

### Setting Custom Fields on Create/Edit

Pass custom field values in the `createJiraIssue` or `editJiraIssue` call using the `customfield_XXXXX` key. The value format depends on the field type:

- **Text**: `"customfield_10001": "some value"`
- **Number**: `"customfield_10002": 8`
- **Select (single)**: `"customfield_10003": { "value": "Option A" }`
- **Select (multi)**: `"customfield_10004": [{ "value": "A" }, { "value": "B" }]`
- **User**: `"customfield_10005": { "accountId": "5a1234..." }`

---

## 6. Pagination and Large Result Sets

`searchJiraIssuesUsingJql` returns paginated results. By default, you get the first page. If the total exceeds the page size:

1. Check `total` in the response to see how many issues match.
2. Use `startAt` and `maxResults` parameters in subsequent calls.
3. Iterate until you've retrieved all results.

**Guidance**: Prefer narrow JQL queries that return small result sets. If you need to process hundreds of issues, consider whether the query can be tightened, or process results in batches and summarize progressively.

---

## 7. Common Jira Field Names

These are the standard field names used in JQL and API payloads. Custom fields will vary by instance.

| Field | JQL Name | API Field |
|---|---|---|
| Summary | `summary` | `summary` |
| Description | `description` | `description` |
| Status | `status` | `status` |
| Assignee | `assignee` | `assignee` |
| Reporter | `reporter` | `reporter` |
| Priority | `priority` | `priority` |
| Issue Type | `type` or `issuetype` | `issuetype` |
| Project | `project` | `project` |
| Labels | `labels` | `labels` |
| Components | `component` | `components` |
| Fix Version | `fixVersion` | `fixVersions` |
| Affects Version | `affectedVersion` | `versions` |
| Sprint | `sprint` | `sprint` |
| Epic Link | `"Epic Link"` | `customfield_10014` (varies) |
| Story Points | `"Story Points"` | `customfield_10016` (varies) |
| Created | `created` | `created` |
| Updated | `updated` | `updated` |
| Resolved | `resolved` | `resolutiondate` |
| Due Date | `due` | `duedate` |
| Resolution | `resolution` | `resolution` |
