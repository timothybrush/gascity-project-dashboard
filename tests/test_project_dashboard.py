import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import project_dashboard


class ProjectDashboardTests(unittest.TestCase):
    def snapshot(self, date: str, stars: int, ci_rate: float | None) -> dict:
        return {
            "schema_version": project_dashboard.SCHEMA_VERSION,
            "snapshot_date": date,
            "generated_at": f"{date}T06:00:00Z",
            "repository": "gastownhall/gascity",
            "latest_release": {"tag": "v1.2.3", "age_days": 5, "downloads": 10},
            "workflow_latest": [],
            "ci_main_recent_runs": [
                {
                    "sha_short": "abc12345",
                    "conclusion": "success",
                    "duration_minutes": 9.5,
                    "updated_at": f"{date}T06:10:00Z",
                    "html_url": "https://example.test/run",
                }
            ],
            "top_referrers": [],
            "top_paths": [],
            "metrics": {
                "github_stars": {"value": stars, "unit": "count"},
                "traffic_views_14d_uniques": {"value": stars + 10, "unit": "visitors"},
                "traffic_clones_14d_uniques": {"value": stars + 2, "unit": "cloners"},
                "release_downloads_total": {"value": stars * 2, "unit": "downloads"},
                "ci_success_rate_7d": {"value": ci_rate, "unit": "percent"},
                "ci_main_commits_checked_7d": {"value": 10, "unit": "commits"},
                "ci_main_failed_commits_7d": {"value": 1, "unit": "commits"},
                "ci_main_median_duration_minutes_7d": {"value": 9.5, "unit": "minutes"},
                "ci_main_p90_duration_minutes_7d": {"value": 15.0, "unit": "minutes"},
                "ttfr_median_hours_30d": {"value": 24, "unit": "hours"},
                "community_profile_score": {"value": 87, "unit": "percent"},
            },
        }

    def test_upsert_replaces_same_snapshot_date(self) -> None:
        old = self.snapshot("2026-05-17", 100, 90)
        replacement = self.snapshot("2026-05-17", 125, 95)
        new = self.snapshot("2026-05-24", 130, 92)

        snapshots = project_dashboard.upsert_snapshot([old, new], replacement)

        self.assertEqual([item["snapshot_date"] for item in snapshots], ["2026-05-17", "2026-05-24"])
        self.assertEqual(project_dashboard.metric_value(snapshots[0], "github_stars"), 125)

    def test_snapshot_file_round_trips_jsonl_sorted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "snapshots.jsonl"
            snapshots = [
                self.snapshot("2026-05-24", 130, 92),
                self.snapshot("2026-05-17", 125, 95),
            ]

            project_dashboard.write_snapshots(path, snapshots)
            loaded = project_dashboard.load_snapshots(path)

            self.assertEqual([item["snapshot_date"] for item in loaded], ["2026-05-17", "2026-05-24"])
            for line in path.read_text(encoding="utf-8").splitlines():
                self.assertIsInstance(json.loads(line), dict)

    def test_render_dashboard_includes_trends_and_status(self) -> None:
        snapshots = [
            self.snapshot("2026-05-17", 100, 80),
            self.snapshot("2026-05-24", 130, 92),
        ]

        rendered = project_dashboard.render_dashboard(snapshots)

        self.assertIn("# Project Dashboard", rendered)
        self.assertIn("Executive Signals", rendered)
        self.assertIn("CI success rate, 7d", rendered)
        self.assertIn("Recent Main CI Results", rendered)
        self.assertIn("Metric Reference", rendered)
        self.assertIn("How it is collected", rendered)
        self.assertIn("Healthy", rendered)
        self.assertIn("+12", rendered)

    def test_value_series_ignores_older_metric_sources(self) -> None:
        old = self.snapshot("2026-05-17", 100, 80)
        old["metrics"]["ci_success_rate_7d"]["source"] = "old source"
        new = self.snapshot("2026-05-24", 130, 92)
        new["metrics"]["ci_success_rate_7d"]["source"] = "new source"

        self.assertEqual(project_dashboard.value_series([old, new], "ci_success_rate_7d"), [92])

    def test_metric_reference_covers_collected_metrics(self) -> None:
        missing = set(project_dashboard.COLLECTED_METRIC_KEYS) - set(project_dashboard.METRIC_DEFINITIONS)
        self.assertEqual(missing, set())

    def test_status_thresholds_handle_missing_values(self) -> None:
        self.assertEqual(project_dashboard.status_for("ci_success_rate_7d", None), "No data")
        self.assertEqual(project_dashboard.status_for("ci_success_rate_7d", 70), "Needs attention")
        self.assertEqual(project_dashboard.status_for("ttfr_median_hours_30d", 24), "Healthy")


if __name__ == "__main__":
    unittest.main()
