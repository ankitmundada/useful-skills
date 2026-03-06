---
name: atlassian-cli
description: Interact with Jira and Confluence using the acli command. Use when managing Jira work items (create, search, comment, transition, link), working with sprints/boards/filters, or reading/creating Confluence pages, spaces, and blog posts.
---

# Atlassian CLI (acli)

## Jira

### Search

```bash
acli jira workitem search --jql "project = <PROJECT> AND assignee = currentUser() AND resolution = Unresolved"
acli jira workitem search --jql "project = <PROJECT>" --fields "key,status,summary"
acli jira workitem search --jql "project = <PROJECT>" --limit 50 --paginate
acli jira workitem search --jql "project = <PROJECT>" --count
```

**Common JQL patterns**

```sql
project = <PROJECT> AND assignee = currentUser() AND resolution = Unresolved
project = <PROJECT> AND status = '<status-name>'
project = <PROJECT> AND statusCategory = 'In Progress'
project = <PROJECT> AND updated >= -7d ORDER BY updated DESC
project = <PROJECT> AND Sprint = '<sprint-name>'
```

JQL notes: use single quotes for values with spaces; prefer `NOT status = 'Done'` over `!=`; functions: `currentUser()`, `startOfDay()`, `endOfWeek()`

### View

```bash
acli jira workitem view <KEY>
acli jira workitem view <KEY> --fields "summary,description,status,comment"
acli jira workitem view <KEY> --fields "*all" --json
```

`--fields` values: `*all`, `*navigable`, or `-fieldname` to exclude

### Create

```bash
acli jira workitem create --summary "New Task" --project "TEAM" --type "Task"
acli jira workitem create --from-file workitem.txt --project PROJ --type Bug --assignee user@example.com --label "bug,cli"
acli jira workitem create --from-json workitem.json
acli jira workitem create --generate-json   # outputs a template JSON to fill in
```

`--assignee`: email address, `@me`, or `default`; `--type`: Epic, Story, Task, Bug, etc.

### Edit

```bash
acli jira workitem edit --key <KEY> --summary "New title"
acli jira workitem edit --key <KEY> --assignee "user@example.com"
acli jira workitem edit --key <KEY> --remove-assignee
acli jira workitem edit --key <KEY> --labels "bug,urgent" --remove-labels "wontfix"
acli jira workitem edit --key <KEY> --description-file desc.txt
acli jira workitem edit --jql "project = <PROJECT> AND labels = old" --labels "new" --yes
acli jira workitem edit --generate-json   # outputs a template JSON
```

### Comment

```bash
acli jira workitem comment create --key <KEY> --body "Comment text"
acli jira workitem comment create --key <KEY> --body-file comment.txt   # plain text or ADF JSON
acli jira workitem comment create --jql "project = <PROJECT> AND labels = needs-review" --body "Reviewed"
acli jira workitem comment list --key <KEY>
acli jira workitem comment create --key <KEY> --edit-last --body "Updated comment"
```

Jira Cloud uses ADF for rich formatting. See [adf-reference.md](adf-reference.md) for ADF JSON examples and acli limitations.

### Transition

```bash
acli jira workitem transition --key <KEY> --status "Done"
acli jira workitem transition --key "<KEY1>,<KEY2>" --status "<status>"
acli jira workitem transition --jql "project = <PROJECT> AND labels = ready" --status "Done" --yes
acli jira workitem transition --filter <FILTER-ID> --status "Done"
```

### Other Work Item Commands

```bash
# Attachments
acli jira workitem attachment list --key <KEY>
acli jira workitem attachment delete --key <KEY> --attachment-id <ID>

# Links
acli jira workitem link create --key <KEY> --link-type "blocks" --outward-key <OTHER-KEY>
acli jira workitem link list-types

# Watchers
acli jira workitem watcher add --key <KEY> --user "user@example.com"
acli jira workitem watcher remove --key <KEY> --user "user@example.com"

# Lifecycle
acli jira workitem clone --key <KEY>
acli jira workitem archive --key <KEY>
acli jira workitem unarchive --key <KEY>
acli jira workitem delete --key <KEY>
```

### Project

```bash
acli jira project list --recent
acli jira project view --key <PROJECT> --json
```

### Board

```bash
acli jira board search --name "My Board" --type scrum --project <PROJECT> --json
acli jira board get --id <BOARD-ID>
acli jira board list-projects --id <BOARD-ID>
acli jira board list-sprints --id <BOARD-ID> --state active --json
```

`--type` values: `scrum`, `kanban`, `simple`; `--state` values: `active`, `closed`, `future`

### Sprint

```bash
acli jira sprint view --id <SPRINT-ID> --json
acli jira sprint list-workitems --sprint <SPRINT-ID> --board <BOARD-ID>
acli jira sprint list-workitems --sprint <SPRINT-ID> --board <BOARD-ID> --jql "assignee = currentUser()" --fields "key,summary,status"
```

### Filter

```bash
acli jira filter list --my
acli jira filter list --favourite
acli jira filter search --owner user@example.com --name "report" --json
acli jira filter search --paginate --csv
acli jira filter get --id <FILTER-ID>
```

### Dashboard

```bash
acli jira dashboard search --json
```

### Field (Custom Fields)

```bash
acli jira field create ...
acli jira field delete ...          # moves to trash
acli jira field cancel-delete ...   # restores from trash
```

---

## Confluence

### Page

```bash
acli confluence page view --id <PAGE-ID>
acli confluence page view --id <PAGE-ID> --body-format storage --json
acli confluence page view --id <PAGE-ID> --include-labels --include-direct-children
acli confluence page view --id <PAGE-ID> --version <N>
```

`--body-format`: `storage`, `atlas_doc_format`, `view`

Include flags: `--include-labels`, `--include-direct-children`, `--include-version`, `--include-versions`, `--include-collaborators`, `--include-likes`, `--include-properties`

### Space

```bash
acli confluence space list
acli confluence space list --type personal --status archived --json
acli confluence space list --keys "SPACE1,SPACE2"

acli confluence space view --id <SPACE-ID> --include-all
acli confluence space view --id <SPACE-ID> --labels --permissions --json

acli confluence space create --key SPACEKEY --name "Space Name" --description "..." --private
acli confluence space archive --key <SPACE-KEY>
acli confluence space restore --key <SPACE-KEY>
```

`--type`: `global`, `personal`; `--status`: `current`, `archived`

### Blog

```bash
acli confluence blog list --space-id <SPACE-ID> --title "Release Notes" --limit 25 --json
acli confluence blog view --id <BLOG-ID> --body-format storage --json
acli confluence blog create --space-id <SPACE-ID> --title "Title" --body "<p>Content</p>"
acli confluence blog create --space-id <SPACE-ID> --title "Draft" --status draft --from-file blog.html
acli confluence blog create --generate-json   # outputs a template JSON
```

`--status`: `current` (published), `draft`

---

## Common Flags

| Flag | Short | Scope |
|------|-------|-------|
| `--key` | `-k` | Work item key(s), comma-separated |
| `--jql` | `-j` | JQL query string |
| `--filter` | | Saved filter ID |
| `--fields` | `-f` | Fields to include in output |
| `--limit` | `-l` | Maximum results |
| `--paginate` | | Fetch all pages of results |
| `--json` | | JSON output |
| `--csv` | | CSV output |
| `--web` | `-w` | Open in browser |
| `--yes` | `-y` | Skip confirmation prompts |
| `--ignore-errors` | | Continue on partial failures |

---

## Workflow Patterns

### Batch operations

```bash
# Comment on multiple work items
acli jira workitem comment create --key "<KEY1>,<KEY2>,<KEY3>" --body "Batch update"

# Transition via JQL
acli jira workitem transition --jql "project = <PROJECT> AND labels = ready" --status "Done" --yes

# Bulk label update
acli jira workitem edit --jql "project = <PROJECT> AND labels = old" --labels "new" --yes
```

### Sprint planning

```bash
# Find active sprint
acli jira board list-sprints --id <BOARD-ID> --state active --json

# List work items in sprint
acli jira sprint list-workitems --sprint <SPRINT-ID> --board <BOARD-ID> --fields "key,summary,assignee,status"
```
