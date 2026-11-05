from __future__ import annotations

import gzip
import importlib.util
import json
import tempfile
import unittest
import warnings
from pathlib import Path

import joblib
import sklearn
from sklearn.exceptions import InconsistentVersionWarning

ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "compare_artifacts", ROOT / "scripts/compare_artifacts.py"
)
compare_artifacts = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(compare_artifacts)


def _write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if relative.endswith(".gz"):
        path.write_bytes(gzip.compress(text.encode("utf-8")))
    else:
        path.write_text(text, encoding="utf-8")


class CompareArtifactsTests(unittest.TestCase):
    def _run(self, committed: dict[str, str], regenerated: dict[str, str]) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            for relative, text in committed.items():
                _write(base / "old", relative, text)
            for relative, text in regenerated.items():
                _write(base / "new", relative, text)
            (base / "new").mkdir(exist_ok=True)
            return compare_artifacts.compare_trees(base / "old", base / "new")

    def test_floating_point_noise_is_accepted(self) -> None:
        problems = self._run(
            {
                "m.csv": "model,brier\nlr,0.12581623994232974\n",
                "s.json": json.dumps({"err": 2.6645e-15, "n": 3, "ok": True}),
                "d.csv.gz": "id,p\n1,0.1\n",
            },
            {
                "m.csv": "model,brier\nlr,0.12581623994233\n",
                "s.json": json.dumps({"err": 1.7763e-15, "n": 3, "ok": True}),
                "d.csv.gz": "id,p\n1,0.1000000000000001\n",
            },
        )
        self.assertEqual(problems, [])

    def test_model_drift_is_rejected(self) -> None:
        # Real drift seen when scikit-learn 1.9 replaced 1.8: HGB ROC AUC moved.
        problems = self._run(
            {"m.csv": "model,roc_auc\nhgb,0.7250907946160521\n"},
            {"m.csv": "model,roc_auc\nhgb,0.7237350179285774\n"},
        )
        self.assertEqual(len(problems), 1)
        self.assertIn("roc_auc", problems[0])

    def test_text_json_and_structure_changes_are_rejected(self) -> None:
        problems = self._run(
            {
                "a.csv": "model,status\nlr,CHAMPION\n",
                "b.json": json.dumps({"status": "PASS", "items": [1, 2]}),
                "c.csv": "x\n1\n",
                "gone.json": "{}",
            },
            {
                "a.csv": "model,status\nlr,CHALLENGER\n",
                "b.json": json.dumps({"status": "FAIL", "items": [1]}),
                "c.csv": "x\n1\n2\n",
            },
        )
        joined = "\n".join(problems)
        self.assertIn("a.csv: column 'status'", joined)
        self.assertIn("b.json: $.items: length 2 != 1", joined)
        self.assertIn("b.json: $.status", joined)
        self.assertIn("c.csv: row count 1 != 2", joined)
        self.assertIn("gone.json: missing after regeneration", joined)

    def test_main_exit_codes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            _write(base / "old", "x.json", '{"v": 1.0}')
            _write(base / "new", "x.json", '{"v": 1.0}')
            self.assertEqual(compare_artifacts.main([str(base / "old"), str(base / "new")]), 0)
            _write(base / "new", "x.json", '{"v": 1.5}')
            self.assertEqual(compare_artifacts.main([str(base / "old"), str(base / "new")]), 1)
            empty = base / "empty"
            empty.mkdir()
            self.assertEqual(compare_artifacts.main([str(empty), str(base / "new")]), 1)


class ModelArtifactVersionTests(unittest.TestCase):
    def test_committed_model_matches_installed_scikit_learn(self) -> None:
        """Pickles are not portable across scikit-learn versions (see requirements.txt)."""
        for name in ("champion_logistic_pipeline.joblib", "linear_shap_state.joblib"):
            path = ROOT / "artifacts/model" / name
            with warnings.catch_warnings():
                warnings.simplefilter("error", InconsistentVersionWarning)
                try:
                    joblib.load(path)
                except InconsistentVersionWarning as exc:  # pragma: no cover - failure path
                    self.fail(
                        f"{name} was pickled with scikit-learn {exc.original_sklearn_version}, "
                        f"installed {sklearn.__version__}; install requirements.txt pins"
                    )


if __name__ == "__main__":
    unittest.main()
