import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scope_check.py"
SPEC = importlib.util.spec_from_file_location("scope_check", SCRIPT)
scope_check = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = scope_check
SPEC.loader.exec_module(scope_check)


POLICY = {
    "allowed_paths": ["src/main/java/**", "src/test/java/**"],
    "approval_required_paths": [".github/**", "build.gradle"],
    "prohibited_paths": ["src/main/resources/db/migration/**", "**/*secret*"],
    "planned_files": ["src/main/java/App.java", "src/test/java/AppTest.java"],
    "allow_deletions": False,
    "allow_untracked": False,
    "allow_binary": False,
    "allow_symlinks": False,
}


class ScopeEvaluationTest(unittest.TestCase):
    def reasons(self, change):
        return {item["reason"] for item in scope_check.evaluate_changes([change], POLICY)}

    def test_allows_planned_source_change(self):
        self.assertEqual(set(), self.reasons(scope_check.Change("M", "src/main/java/App.java")))

    def test_allows_planned_test_change(self):
        self.assertEqual(set(), self.reasons(scope_check.Change("M", "src/test/java/AppTest.java")))

    def test_blocks_workflow_change(self):
        reasons = self.reasons(scope_check.Change("M", ".github/workflows/ci.yml"))
        self.assertIn("additional_approval_required", reasons)
        self.assertIn("outside_allowed_paths", reasons)

    def test_blocks_dependency_change(self):
        self.assertIn(
            "additional_approval_required", self.reasons(scope_check.Change("M", "build.gradle"))
        )

    def test_blocks_migration_change(self):
        self.assertIn(
            "prohibited_path",
            self.reasons(scope_check.Change("A", "src/main/resources/db/migration/V2__change.sql")),
        )

    def test_blocks_deletion(self):
        self.assertIn(
            "deletion_not_allowed", self.reasons(scope_check.Change("D", "src/main/java/App.java"))
        )

    def test_blocks_rename_and_checks_old_path(self):
        reasons = self.reasons(
            scope_check.Change("R100", "src/main/java/App.java", ".github/workflows/old.yml")
        )
        self.assertIn("rename_or_copy_not_allowed", reasons)
        self.assertIn("additional_approval_required", reasons)

    def test_blocks_untracked(self):
        self.assertIn(
            "untracked_not_allowed",
            self.reasons(scope_check.Change("?", "src/main/java/App.java", untracked=True)),
        )

    def test_blocks_binary(self):
        self.assertIn(
            "binary_not_allowed",
            self.reasons(scope_check.Change("M", "src/main/java/App.java", binary=True)),
        )

    def test_blocks_symlink(self):
        self.assertIn(
            "symlink_not_allowed",
            self.reasons(scope_check.Change("M", "src/main/java/App.java", symlink=True)),
        )

    def test_blocks_path_outside_allowlist(self):
        self.assertIn("outside_allowed_paths", self.reasons(scope_check.Change("M", "README.md")))

    def test_rejects_path_traversal(self):
        with self.assertRaises(ValueError):
            scope_check.normalize_path("../outside.txt")


class GitParsingIntegrationTest(unittest.TestCase):
    def git(self, repo, *args):
        subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)

    def test_collects_rename_and_untracked_file(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            self.git(repo, "init", "-b", "main")
            self.git(repo, "config", "user.name", "Scope Test")
            self.git(repo, "config", "user.email", "scope@example.invalid")
            (repo / "src/main/java").mkdir(parents=True)
            original = repo / "src/main/java/App.java"
            original.write_text("class App {}\n", encoding="utf-8")
            self.git(repo, "add", ".")
            self.git(repo, "commit", "-m", "baseline")
            base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
            self.git(repo, "mv", "src/main/java/App.java", "src/main/java/Renamed.java")
            self.git(repo, "commit", "-m", "rename")
            (repo / "src/test/java").mkdir(parents=True)
            (repo / "src/test/java/AppTest.java").write_text("class AppTest {}\n", encoding="utf-8")

            changes = scope_check.collect_changes(repo, base)

            self.assertTrue(any(change.status.startswith("R") for change in changes))
            self.assertTrue(any(change.untracked for change in changes))


if __name__ == "__main__":
    unittest.main()
