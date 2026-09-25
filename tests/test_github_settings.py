from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest import mock

from scripts import github_settings


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def compliant_state() -> dict[str, object]:
    return {
        **github_settings.EXPECTED,
        "patterns_allowed": [],
        "labels": list(github_settings.LABELS),
        "topics": ["example"],
    }


class GitHubSettingsTests(unittest.TestCase):
    def test_compliant_state_has_no_drift(self) -> None:
        self.assertEqual([], github_settings.find_drift(compliant_state()))

    def test_drift_is_reported(self) -> None:
        state = compliant_state()
        state.update(
            allowed_actions="all",
            sha_pinning_required=False,
            github_owned_allowed=None,
            labels=["bug", *github_settings.LABELS[1:]],
            topics=[],
        )

        self.assertEqual(
            [
                "allowed_actions: expected 'selected', found 'all'",
                "sha_pinning_required: expected True, found False",
                "github_owned_allowed: expected True, found None",
                "missing label: type: bug",
                "GitHub default label present: bug",
                "no repository topics (set project-specific topics by hand)",
            ],
            github_settings.find_drift(state),
        )

    def test_apply_preserves_action_patterns_and_used_default_labels(
        self,
    ) -> None:
        calls: list[tuple[tuple[str, ...], str | None]] = []

        def fake_gh(*args: str, stdin: str | None = None) -> str:
            calls.append((args, stdin))
            if "search/issues" in args:
                return (
                    "2" if any('label:"bug"' in arg for arg in args) else "0"
                )
            return ""

        state = compliant_state()
        state.update(
            patterns_allowed=["example/action@*"],
            labels=["bug", "wontfix", *github_settings.LABELS[1:]],
        )
        with mock.patch.object(github_settings, "gh", fake_gh):
            github_settings.apply("owner/repo", state)

        selected = next(
            json.loads(stdin)
            for args, stdin in calls
            if any(arg.endswith("/selected-actions") for arg in args)
        )
        self.assertEqual(["example/action@*"], selected["patterns_allowed"])
        commands = [args for args, _ in calls if args[0] == "label"]
        self.assertEqual(
            [
                ("label", "create", "type: bug", "--repo", "owner/repo"),
                (
                    "label",
                    "delete",
                    "wontfix",
                    "--repo",
                    "owner/repo",
                    "--yes",
                ),
            ],
            commands,
        )

    def test_labels_match_governance_documentation(self) -> None:
        governance = (
            REPOSITORY_ROOT / "docs" / "github-governance.md"
        ).read_text(encoding="utf-8")
        for label in github_settings.LABELS:
            self.assertIn(f"`{label}`", governance)


if __name__ == "__main__":
    unittest.main()
