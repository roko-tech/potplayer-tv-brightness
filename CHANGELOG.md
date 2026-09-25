# Changelog

All notable changes to this project are documented here. Follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and use semantic versioning when the project exposes a versioned public contract.

## [Unreleased]

### Added

- Initial project governance, documentation, AI instructions, GitHub workflows, and repository validation.
- `scripts/github_settings.py` to check or apply the repository, label, Actions, and Dependabot baseline.

### Changed

- CI cancels superseded runs only for pull requests, so every commit pushed to `main` keeps its own result.
- The no-AI-co-author-trailer rule now covers every AI tool, not only Codex.

### Fixed

- `scripts/verify.py` skips files ignored by `.gitignore`, such as dependencies and build or scratch output.
- `scripts/verify.py` no longer requires the default ADR-0001 filename, and `PROJECT_SETUP.md` no longer says the file may be removed.
