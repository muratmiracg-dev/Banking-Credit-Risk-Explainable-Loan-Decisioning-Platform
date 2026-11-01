from __future__ import annotations

import contextlib
import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from credit_risk import cli


class CliTests(unittest.TestCase):
    def test_defaults(self) -> None:
        args = cli.build_parser().parse_args([])
        self.assertEqual(args.root, ".")
        self.assertEqual(args.config, "config/project.yaml")

    def test_main_runs_pipeline_and_prints_compact_manifest(self) -> None:
        manifest = {
            "pipeline_status": "PASS",
            "generated_artifacts": ["a", "b"],
            "executive_summary": {"oot_gini": 0.47},
        }
        out = io.StringIO()
        with (
            patch.object(cli, "run_pipeline", return_value=manifest) as run,
            contextlib.redirect_stdout(out),
        ):
            cli.main(["--root", "project-root", "--config", "custom.yaml"])
        run.assert_called_once_with(Path("project-root"), "custom.yaml")
        printed = json.loads(out.getvalue())
        self.assertEqual(printed["pipeline_status"], "PASS")
        self.assertEqual(printed["generated_artifact_count"], 2)
        self.assertEqual(printed["executive_summary"], {"oot_gini": 0.47})


if __name__ == "__main__":
    unittest.main()
