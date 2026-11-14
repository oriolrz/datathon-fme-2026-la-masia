"""Assegura dependències locals completes i importació en un procés aïllat."""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.package import ROOT, build_archive, local_dependencies, validate_archive

OFFICIAL = Path(os.environ.get("UPC_OFFICIAL_ROOT", str(ROOT.parent / "paquet_participants_datathon_upc")))


class PackageTests(unittest.TestCase):
    def test_deterministic_archive_with_complete_runtime_and_official_checker(self):
        with tempfile.TemporaryDirectory() as directory:
            first, second = Path(directory) / "first.zip", Path(directory) / "second.zip"
            build_archive(ROOT, first)
            build_archive(ROOT, second)
            self.assertEqual(hashlib.sha256(first.read_bytes()).hexdigest(), hashlib.sha256(second.read_bytes()).hexdigest())
            with zipfile.ZipFile(first) as archive:
                self.assertEqual(set(archive.namelist()), {"agent.py", "src/__init__.py", "src/safety.py", "src/fallback.py"})
                target = Path(directory) / "isolated"
                archive.extractall(target)
            # Sense site-packages ni cwd del repo: el lliurable funciona amb stdlib.
            code = (
                "import sys; sys.path.insert(0, '.'); from agent import BatteryAgent; "
                "import json; print(json.dumps(BatteryAgent().act({'soc_kwh': 0.0})))"
            )
            smoke = subprocess.run([sys.executable, "-I", "-S", "-B", "-c", code], cwd=target,
                                   capture_output=True, text=True, timeout=60)
            self.assertEqual(smoke.returncode, 0, smoke.stdout + smoke.stderr)
            self.assertEqual(json.loads(smoke.stdout), 0.0)
            result = validate_archive(first, OFFICIAL / "starter_kit/check_submission.py")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_local_dependency_rejected_and_recursive_imports_included(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            (root / "src/__init__.py").write_text("", encoding="utf-8")
            (root / "agent.py").write_text("from src.missing import choose_action\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "absent"):
                local_dependencies(root)
            (root / "src/missing.py").write_text("from .helper import action\n", encoding="utf-8")
            (root / "src/helper.py").write_text("action = 0.0\n", encoding="utf-8")
            self.assertEqual({str(path.as_posix()) for path in local_dependencies(root)},
                             {"agent.py", "src/__init__.py", "src/missing.py", "src/helper.py"})


if __name__ == "__main__":
    unittest.main()
