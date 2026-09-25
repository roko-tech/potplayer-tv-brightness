#!/usr/bin/env python3
"""Validate the stack-independent contract provided by this template."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from fnmatch import fnmatch
from pathlib import Path
from urllib.parse import unquote, urlsplit


REQUIRED_PATHS = (
    ".editorconfig",
    ".env.example",
    ".gitattributes",
    ".github/CODEOWNERS",
    ".github/ISSUE_TEMPLATE/architecture.yml",
    ".github/ISSUE_TEMPLATE/bug.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/ISSUE_TEMPLATE/feature.yml",
    ".github/dependabot.yml",
    ".github/pull_request_template.md",
    ".github/rulesets/main.json",
    ".github/workflows/ci.yml",
    ".gitignore",
    "AGENTS.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "PROJECT_SETUP.md",
    "README.md",
    "SECURITY.md",
    "docs/README.md",
    "docs/ai-development.md",
    "docs/architecture/decisions/0000-template.md",
    "docs/architecture/decisions/README.md",
    "docs/architecture/overview.md",
    "docs/design/README.md",
    "docs/design/rfc-template.md",
    "docs/documentation-policy.md",
    "docs/feature-lifecycle.md",
    "docs/github-governance.md",
    "docs/operations/backup-restore.md",
    "docs/operations/postmortem-template.md",
    "docs/operations/runbook.md",
    "docs/operations/slo.md",
    "docs/product/brief.md",
    "docs/project-lifecycle.md",
    "docs/references.md",
    "docs/release-checklist.md",
    "docs/security/secure-development.md",
    "docs/security/threat-model.md",
    "docs/testing.md",
    "docs/user/README.md",
    "scripts/github_settings.py",
    "scripts/verify.py",
    "tests/test_github_settings.py",
    "tests/test_verify.py",
)

MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\n]+)\)")
ACTION_USE = re.compile(
    r"^\s*(?:-\s*)?uses:\s*([^@\s]+)@([^\s#]+)", re.MULTILINE
)
FULL_COMMIT_SHA = re.compile(r"^[0-9a-fA-F]{40}$")
ADR_NAME = re.compile(r"^(\d{4})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
TEXT_FILE_NAMES = {
    ".editorconfig",
    ".env.example",
    ".gitattributes",
    ".gitignore",
}
TEXT_FILE_SUFFIXES = {
    ".bat",
    ".cfg",
    ".cmd",
    ".css",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".ps1",
    ".py",
    ".scss",
    ".sh",
    ".sql",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}


def repository_files(root: Path, pattern: str = "*") -> list[Path]:
    """Return matching files that Git does not ignore.

    Inside a Git work tree this lists tracked and untracked files while
    honoring .gitignore, so dependency, build, and scratch output is skipped.
    Outside one it walks the directory, excluding only Git's own metadata.
    """

    directories = (root, *root.parents)
    if any((directory / ".git").exists() for directory in directories):
        command = "git ls-files -z --cached --others --exclude-standard"
        listed = subprocess.run(
            command.split(),
            cwd=root,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.decode("utf-8")
        candidates = (root / name for name in listed.split("\0") if name)
    else:
        candidates = (
            path
            for path in root.rglob("*")
            if ".git" not in path.relative_to(root).parts
        )
    return sorted(
        path
        for path in candidates
        if path.is_file() and fnmatch(path.name, pattern)
    )


def check_required_files(
    root: Path, required_paths: tuple[str, ...] = REQUIRED_PATHS
) -> list[str]:
    errors: list[str] = []
    for relative in required_paths:
        path = root / relative
        if not path.is_file():
            errors.append(f"missing required file: {relative}")
        elif path.stat().st_size == 0:
            errors.append(f"required file is empty: {relative}")
    return errors


def check_text_hygiene(root: Path) -> list[str]:
    errors: list[str] = []
    candidates = [
        path
        for path in repository_files(root)
        if path.name in TEXT_FILE_NAMES
        or path.suffix.lower() in TEXT_FILE_SUFFIXES
    ]

    for path in candidates:
        relative = path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"{relative}: expected UTF-8 text")
            continue

        if text and not text.endswith("\n"):
            errors.append(f"{relative}: missing final newline")
        if text.endswith("\n\n") or text.endswith("\r\n\r\n"):
            errors.append(f"{relative}: extra blank line at end of file")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if line.endswith((" ", "\t")):
                errors.append(f"{relative}:{line_number}: trailing whitespace")
    return errors


def _link_destination(raw_destination: str) -> str:
    destination = raw_destination.strip()
    if destination.startswith("<") and ">" in destination:
        return destination[1 : destination.index(">")]
    return destination.split(maxsplit=1)[0]


def check_markdown_links(root: Path) -> list[str]:
    errors: list[str] = []
    root = root.resolve()

    for document in repository_files(root, "*.md"):
        text = document.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK.finditer(text):
            destination = _link_destination(match.group(1))
            if not destination or destination.startswith("#"):
                continue

            parsed = urlsplit(destination)
            if parsed.scheme or parsed.netloc:
                continue
            if destination.startswith("/"):
                relative_document = document.relative_to(root).as_posix()
                errors.append(
                    f"{relative_document}: root-relative link is not portable: {destination}"
                )
                continue

            local_part = unquote(destination.split("#", 1)[0].split("?", 1)[0])
            if not local_part:
                continue

            target = (document.parent / local_part).resolve()
            try:
                target.relative_to(root)
            except ValueError:
                relative_document = document.relative_to(root).as_posix()
                errors.append(
                    f"{relative_document}: link escapes repository: {destination}"
                )
                continue

            if not target.exists():
                relative_document = document.relative_to(root).as_posix()
                errors.append(
                    f"{relative_document}: broken local link: {destination}"
                )
    return errors


def check_action_pins(root: Path) -> list[str]:
    errors: list[str] = []
    workflow_root = root / ".github" / "workflows"
    workflows = sorted(workflow_root.glob("*.yml")) + sorted(
        workflow_root.glob("*.yaml")
    )

    for workflow in workflows:
        relative = workflow.relative_to(root).as_posix()
        text = workflow.read_text(encoding="utf-8")

        if re.search(r"^\s*pull_request_target\s*:", text, re.MULTILINE):
            errors.append(
                f"{relative}: pull_request_target requires an explicit security review"
            )
        if not re.search(r"^permissions\s*:", text, re.MULTILINE):
            errors.append(f"{relative}: workflow permissions are not explicit")

        for action, revision in ACTION_USE.findall(text):
            if action.startswith("./") or action.startswith("docker://"):
                continue
            if not FULL_COMMIT_SHA.fullmatch(revision):
                errors.append(
                    f"{relative}: {action}@{revision} is not pinned to a full commit SHA"
                )
    return errors


def check_adrs(root: Path) -> list[str]:
    errors: list[str] = []
    decision_root = root / "docs" / "architecture" / "decisions"
    seen_numbers: dict[str, str] = {}

    for path in sorted(decision_root.glob("*.md")):
        if path.name in {"README.md", "0000-template.md"}:
            continue
        match = ADR_NAME.fullmatch(path.name)
        if not match:
            errors.append(
                "docs/architecture/decisions/"
                f"{path.name}: expected NNNN-lowercase-slug.md"
            )
            continue
        number = match.group(1)
        if number in seen_numbers:
            errors.append(
                f"duplicate ADR number {number}: {seen_numbers[number]} and {path.name}"
            )
        seen_numbers[number] = path.name
    return errors


def check_ruleset(root: Path) -> list[str]:
    path = root / ".github" / "rulesets" / "main.json"
    if not path.is_file():
        return []

    relative = path.relative_to(root).as_posix()
    try:
        ruleset = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"{relative}: invalid JSON: {error}"]

    errors: list[str] = []
    if ruleset.get("target") != "branch":
        errors.append(f"{relative}: target must be branch")
    if ruleset.get("enforcement") != "active":
        errors.append(f"{relative}: enforcement must be active")

    rules = ruleset.get("rules")
    if not isinstance(rules, list):
        return errors + [f"{relative}: rules must be an array"]

    types = {rule.get("type") for rule in rules if isinstance(rule, dict)}
    required_types = {
        "deletion",
        "non_fast_forward",
        "pull_request",
        "required_linear_history",
        "required_status_checks",
    }
    missing = sorted(required_types - types)
    if missing:
        errors.append(f"{relative}: missing rules: {', '.join(missing)}")
    return errors


def validate(root: Path) -> list[str]:
    root = root.resolve()
    checks = (
        check_required_files,
        check_text_hygiene,
        check_markdown_links,
        check_action_pins,
        check_adrs,
        check_ruleset,
    )
    errors: list[str] = []
    for check in checks:
        errors.extend(check(root))
    return errors


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (defaults to the parent of scripts/)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve()
    errors = validate(root)
    if errors:
        print(f"Repository contract failed with {len(errors)} error(s):")
        for error in errors:
            print(f"- {error}")
        return 1

    markdown_count = len(repository_files(root, "*.md"))
    workflow_count = len(repository_files(root / ".github" / "workflows", "*.yml"))
    adr_count = len(
        [
            path
            for path in (root / "docs" / "architecture" / "decisions").glob(
                "[0-9][0-9][0-9][0-9]-*.md"
            )
            if path.name != "0000-template.md"
        ]
    )
    print(
        "Repository contract valid: "
        f"{markdown_count} Markdown files, {adr_count} ADR(s), "
        f"{workflow_count} workflow(s)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
