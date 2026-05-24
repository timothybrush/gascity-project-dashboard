# Gas City Project Dashboard

This repository stores the public weekly metric snapshots and dashboard
automation for `gastownhall/gascity`.

The workflow in `.github/workflows/project-dashboard.yml` runs weekly, collects
GitHub repository health metrics, appends or replaces the current weekly row in
`data/gascity/snapshots.jsonl`, renders `dashboard/Project-Dashboard.md`, and
publishes that rendered Markdown to:

https://github.com/gastownhall/gascity/wiki/Project-Dashboard

## Repository Layout

| Path | Purpose |
|---|---|
| `scripts/project_dashboard.py` | Collector and Markdown renderer. |
| `tests/test_project_dashboard.py` | Unit tests for snapshot handling, trends, and metric reference coverage. |
| `data/gascity/snapshots.jsonl` | Versioned weekly raw snapshots, one JSON object per line. |
| `dashboard/Project-Dashboard.md` | Rendered dashboard preview committed with each snapshot. |
| `.github/workflows/project-dashboard.yml` | Scheduled collector and wiki publisher. |

## Configuration

The workflow defaults to collecting `gastownhall/gascity` and publishing to the
`gastownhall/gascity` wiki.

Optional repository variables:

| Variable | Default | Purpose |
|---|---|---|
| `TARGET_REPOSITORY` | `gastownhall/gascity` | Repository to collect metrics for. |
| `WIKI_REPOSITORY` | `gastownhall/gascity` | Repository whose wiki receives `Project-Dashboard.md`. |

Recommended secrets:

| Secret | Purpose |
|---|---|
| `METRICS_COLLECTION_TOKEN` | Token with access to target repository traffic, Actions, security, issue, PR, and wiki APIs. |
| `METRICS_WIKI_TOKEN` | Optional separate token for wiki writes. Falls back to `METRICS_COLLECTION_TOKEN`. |

## Local Use

Render from existing snapshots:

```bash
python3 scripts/project_dashboard.py render \
  --snapshot-file data/gascity/snapshots.jsonl \
  --output dashboard/Project-Dashboard.md
```

Collect a live snapshot:

```bash
GITHUB_TOKEN="$(gh auth token)" python3 scripts/project_dashboard.py collect \
  --repo gastownhall/gascity \
  --repo-root /path/to/gascity \
  --snapshot-file data/gascity/snapshots.jsonl \
  --output dashboard/Project-Dashboard.md
```

Run tests:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_project_dashboard.py
```
