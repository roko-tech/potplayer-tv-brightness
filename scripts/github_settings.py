#!/usr/bin/env python3
"""Check, or apply with --apply, the baseline GitHub settings for a repository.

Requires an authenticated `gh` CLI with admin access to the repository.
Visibility and topics are only checked: change them deliberately by hand.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys


REPOSITORY_SETTINGS = {
    "private": True,
    "has_issues": True,
    "has_projects": False,
    "has_wiki": False,
    "allow_squash_merge": True,
    "allow_merge_commit": False,
    "allow_rebase_merge": False,
    "allow_update_branch": True,
    "delete_branch_on_merge": True,
}
ACTIONS_SETTINGS = {
    "actions_enabled": True,
    "allowed_actions": "selected",
    "sha_pinning_required": True,
    "github_owned_allowed": True,
    "verified_allowed": False,
    "default_workflow_permissions": "read",
    "can_approve_pull_request_reviews": False,
}
SECURITY_SETTINGS = {
    "vulnerability_alerts": True,
    "automated_security_fixes": True,
}
EXPECTED = REPOSITORY_SETTINGS | ACTIONS_SETTINGS | SECURITY_SETTINGS

# Keep in sync with docs/github-governance.md and the issue forms.
LABELS = (
    "type: bug",
    "type: feature",
    "type: architecture",
    "status: triage",
    "status: blocked",
    "priority: p0",
    "priority: p1",
    "priority: p2",
    "priority: p3",
    "risk: high",
)
GITHUB_DEFAULT_LABELS = (
    "bug",
    "documentation",
    "duplicate",
    "enhancement",
    "good first issue",
    "help wanted",
    "invalid",
    "question",
    "wontfix",
)
VULNERABILITY_ALERTS_QUERY = (
    "query($owner: String!, $name: String!) "
    "{ repository(owner: $owner, name: $name) "
    "{ hasVulnerabilityAlertsEnabled } }"
)


def gh(*args: str, stdin: str | None = None) -> str:
    return subprocess.run(
        ["gh", *args],
        input=stdin,
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        check=True,
    ).stdout


def gh_json(*args: str) -> object:
    return json.loads(gh(*args))


def read_state(repo: str) -> dict[str, object]:
    owner, name = repo.split("/")
    repository = gh_json("api", f"repos/{repo}")
    actions = gh_json("api", f"repos/{repo}/actions/permissions")
    selected = (
        gh_json("api", f"repos/{repo}/actions/permissions/selected-actions")
        if actions["allowed_actions"] == "selected"
        else {}
    )
    workflow = gh_json("api", f"repos/{repo}/actions/permissions/workflow")
    alerts = gh(
        "api",
        "graphql",
        "-f",
        f"owner={owner}",
        "-f",
        f"name={name}",
        "-f",
        f"query={VULNERABILITY_ALERTS_QUERY}",
        "--jq",
        ".data.repository.hasVulnerabilityAlertsEnabled",
    ).strip()
    fixes = gh_json("api", f"repos/{repo}/automated-security-fixes")
    labels = gh_json(
        "label", "list", "--repo", repo, "--limit", "500", "--json", "name"
    )

    return {
        **{key: repository.get(key) for key in REPOSITORY_SETTINGS},
        "actions_enabled": actions["enabled"],
        "allowed_actions": actions["allowed_actions"],
        "sha_pinning_required": actions.get("sha_pinning_required"),
        "github_owned_allowed": selected.get("github_owned_allowed"),
        "verified_allowed": selected.get("verified_allowed"),
        "patterns_allowed": selected.get("patterns_allowed", []),
        "default_workflow_permissions": workflow[
            "default_workflow_permissions"
        ],
        "can_approve_pull_request_reviews": workflow[
            "can_approve_pull_request_reviews"
        ],
        "vulnerability_alerts": alerts == "true",
        "automated_security_fixes": fixes["enabled"],
        "labels": [label["name"] for label in labels],
        "topics": repository.get("topics", []),
    }


def find_drift(state: dict[str, object]) -> list[str]:
    drift = [
        f"{key}: expected {expected!r}, found {state.get(key)!r}"
        for key, expected in EXPECTED.items()
        if state.get(key) != expected
    ]
    labels = state["labels"]
    drift += [
        f"missing label: {label}" for label in LABELS if label not in labels
    ]
    drift += [
        f"GitHub default label present: {label}"
        for label in GITHUB_DEFAULT_LABELS
        if label in labels
    ]
    if not state["topics"]:
        drift.append(
            "no repository topics (set project-specific topics by hand)"
        )
    return drift


def label_in_use(repo: str, label: str) -> bool:
    count = gh(
        "api",
        "--method",
        "GET",
        "search/issues",
        "-f",
        f'q=repo:{repo} label:"{label}"',
        "--jq",
        ".total_count",
    )
    return int(count) > 0


def apply(repo: str, state: dict[str, object]) -> None:
    repository_changes = {
        key: value
        for key, value in REPOSITORY_SETTINGS.items()
        if key != "private"
    }
    gh(
        "api",
        "--method",
        "PATCH",
        f"repos/{repo}",
        "--input",
        "-",
        stdin=json.dumps(repository_changes),
    )
    gh(
        "api",
        "--method",
        "PUT",
        f"repos/{repo}/actions/permissions",
        "--input",
        "-",
        stdin=json.dumps(
            {
                "enabled": True,
                "allowed_actions": "selected",
                "sha_pinning_required": True,
            }
        ),
    )
    # Preserve any narrowly reviewed third-party action patterns.
    gh(
        "api",
        "--method",
        "PUT",
        f"repos/{repo}/actions/permissions/selected-actions",
        "--input",
        "-",
        stdin=json.dumps(
            {
                "github_owned_allowed": True,
                "verified_allowed": False,
                "patterns_allowed": state["patterns_allowed"],
            }
        ),
    )
    gh(
        "api",
        "--method",
        "PUT",
        f"repos/{repo}/actions/permissions/workflow",
        "--input",
        "-",
        stdin=json.dumps(
            {
                "default_workflow_permissions": "read",
                "can_approve_pull_request_reviews": False,
            }
        ),
    )
    gh("api", "--method", "PUT", f"repos/{repo}/vulnerability-alerts")
    gh("api", "--method", "PUT", f"repos/{repo}/automated-security-fixes")

    for label in LABELS:
        if label not in state["labels"]:
            gh("label", "create", label, "--repo", repo)
    for label in GITHUB_DEFAULT_LABELS:
        if label in state["labels"] and not label_in_use(repo, label):
            gh("label", "delete", label, "--repo", repo, "--yes")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        help="OWNER/NAME (defaults to the current directory's repository)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="apply the baseline, then read every setting back",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo = (
        args.repo
        or gh(
            "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"
        ).strip()
    )

    state = read_state(repo)
    if args.apply:
        apply(repo, state)
        state = read_state(repo)

    drift = find_drift(state)
    if drift:
        print(f"{repo}: {len(drift)} setting(s) differ from the baseline:")
        for item in drift:
            print(f"- {item}")
        return 1
    print(f"{repo}: GitHub settings match the baseline.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
