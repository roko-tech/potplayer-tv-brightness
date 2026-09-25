from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts import verify


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class RepositoryVerificationTests(unittest.TestCase):
    def test_repository_contract_passes(self) -> None:
        self.assertEqual([], verify.validate(REPOSITORY_ROOT))

    def test_missing_required_file_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            errors = verify.check_required_files(root, ("README.md",))

        self.assertEqual(["missing required file: README.md"], errors)

    def test_broken_relative_markdown_link_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "README.md").write_text(
                "[Missing](docs/missing.md)\n", encoding="utf-8"
            )
            errors = verify.check_markdown_links(root)

        self.assertEqual(
            ["README.md: broken local link: docs/missing.md"], errors
        )

    def test_git_ignored_files_are_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
            (root / ".gitignore").write_text(
                "node_modules/\n", encoding="utf-8"
            )
            dependency = root / "node_modules" / "package"
            dependency.mkdir(parents=True)
            (dependency / "README.md").write_text(
                "[Missing](missing.md)  ", encoding="utf-8"
            )
            (root / "notes.md").write_text(
                "[Missing](missing.md)\n", encoding="utf-8"
            )
            errors = verify.check_text_hygiene(root)
            errors += verify.check_markdown_links(root)

        self.assertEqual(["notes.md: broken local link: missing.md"], errors)

    def test_text_hygiene_reports_trailing_whitespace_and_blank_eof(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "README.md").write_text("Heading  \n\n", encoding="utf-8")
            errors = verify.check_text_hygiene(root)

        self.assertEqual(
            [
                "README.md: extra blank line at end of file",
                "README.md:1: trailing whitespace",
            ],
            errors,
        )

    def test_unpinned_external_action_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            workflow_root = root / ".github" / "workflows"
            workflow_root.mkdir(parents=True)
            (workflow_root / "ci.yml").write_text(
                "permissions:\n"
                "  contents: read\n"
                "jobs:\n"
                "  validate:\n"
                "    steps:\n"
                "      - uses: actions/checkout@v7\n",
                encoding="utf-8",
            )
            errors = verify.check_action_pins(root)

        self.assertEqual(
            [
                ".github/workflows/ci.yml: "
                "actions/checkout@v7 is not pinned to a full commit SHA"
            ],
            errors,
        )

    def test_ruleset_requires_core_protections(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            ruleset_root = root / ".github" / "rulesets"
            ruleset_root.mkdir(parents=True)
            (ruleset_root / "main.json").write_text(
                json.dumps(
                    {
                        "target": "branch",
                        "enforcement": "active",
                        "rules": [{"type": "deletion"}],
                    }
                ),
                encoding="utf-8",
            )
            errors = verify.check_ruleset(root)

        self.assertEqual(1, len(errors))
        self.assertIn("missing rules", errors[0])
        self.assertIn("required_status_checks", errors[0])


if __name__ == "__main__":
    unittest.main()
