import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("release_builder", ROOT / "scripts/build_release.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleaseTests(unittest.TestCase):
    def test_private_context_and_history_are_excluded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source"
            root.mkdir()
            for name in release.FILES:
                (root / name).write_text("fixture\n")
            for name in [".git/config", "project-context/handoff.md", "economicreasoning/private.txt",
                         "artifacts/private.py", ".env", ".tools/tool.py", "examples/.env",
                         "src/theorydebugger.egg-info/SOURCES.txt"]:
                p = root / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text("must not ship")
            (root / "examples/One.lean").write_text("example : True := True.intro\n")
            output = Path(directory) / "release.zip"
            release.build(output, root)
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                expected = {"TheoryDebugger/" + name for name in release.FILES}
                expected |= {"TheoryDebugger/examples/One.lean", "TheoryDebugger/RELEASE-MANIFEST.json"}
                self.assertEqual(names, expected)
                manifest = json.loads(archive.read("TheoryDebugger/RELEASE-MANIFEST.json"))
                self.assertEqual(set(manifest), release.FILES | {"examples/One.lean"})
            with self.assertRaises(FileExistsError): release.build(output, root)

    def test_release_inputs_have_no_reference_or_build_roots(self):
        files = [p.relative_to(ROOT).parts for p in release.source_files()]
        forbidden = {".git", ".lake", ".tools", "artifacts", "project-context", "economicreasoning"}
        self.assertTrue(files)
        self.assertFalse(any(set(parts) & forbidden for parts in files))

    def test_case_collisions_rejected_before_archiving(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "release.zip"
            # Model both directory spellings even on a case-insensitive host.
            files = [root / "Example/a.py", root / "example/b.py"]
            with patch.object(release, "source_files", return_value=files):
                with self.assertRaisesRegex(ValueError, "Case-colliding"):
                    release.build(output, root)
            self.assertFalse(output.exists())


if __name__ == "__main__": unittest.main()
