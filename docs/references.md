# Research references

These primary or canonical sources informed the starter. Links were reviewed on 2026-08-20; re-check versioned standards and platform capabilities when making a consequential decision.

## Architecture and documentation

- [C4 model](https://c4model.com/) — layered system diagrams and audience-appropriate abstraction.
- [Documenting architecture decisions](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions) — the original lightweight ADR approach.
- [Diátaxis](https://diataxis.fr/) — separating tutorials, how-to guides, reference, and explanation by user need.

## Delivery and GitHub

- [GitHub flow](https://docs.github.com/en/get-started/using-github/github-flow) — branch-based collaboration around pull requests.
- [About repository rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets) — enforceable branch/tag governance and plan availability.
- [Secure use of GitHub Actions](https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions) — least privilege, third-party action pinning, and untrusted input guidance.
- [Workflow permission syntax](https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions#permissions) — explicit `GITHUB_TOKEN` permissions.
- [Dependabot configuration](https://docs.github.com/en/code-security/dependabot/working-with-dependabot/dependabot-options-reference) — supported update configuration.

## Security and reliability

- [NIST Secure Software Development Framework](https://csrc.nist.gov/pubs/sp/800/218/final) — organization-level secure development practices.
- [OWASP Application Security Verification Standard](https://owasp.org/www-project-application-security-verification-standard/) — testable application-security requirements.
- [OWASP Software Assurance Maturity Model](https://owaspsamm.org/) — risk-based secure development improvement.
- [Google SRE: Implementing SLOs](https://sre.google/workbook/implementing-slos/) — user-centered service indicators, objectives, and error budgets.
- [DORA metrics](https://dora.dev/guides/dora-metrics/) — delivery and operational performance measures used as improvement signals.

## LG TV integration

- [LG webOS TV user guide (2022 models)](https://kr.eguide.lgappstv.com/manual/w22_mr15/w22_eu05/eng.html) — menu paths for the network settings (the TV's IP address) and external device connections; no LG Connect Apps switch on these models.
- [Home Assistant: LG webOS TV](https://www.home-assistant.io/integrations/webostv/) — older models need LG Connect Apps turned on under the TV's network settings; SSAP uses TCP ports 3000 and 3001.
- [lgtv2](https://github.com/hobbyquaker/lgtv2) — source of `pairing.json`, the signed manifest that grants `WRITE_SETTINGS` (MIT).
- [aiowebostv issue #728](https://github.com/home-assistant-libs/aiowebostv/issues/728) — `WRITE_SETTINGS` is granted per connection by the signed manifest sent at pairing, not by the client key; some firmware now rejects that certificate as blacklisted.
- [lg_webos_brightness_adjustment](https://github.com/zedr32/lg_webos_brightness_adjustment) — on a C6 with firmware 43.21.60 the direct brightness write returns 401; it switches to the luna notification-alert method (ADR-0002's fallback).
- [LG Developer Mode app](https://webostv.developer.lge.com/develop/getting-started/developer-mode-app) — Developer Mode is for installing and testing apps under development and needs an LG developer account; turning it off uninstalls those apps. This app uses none of it.

## Packaging

- [PyInstaller manual](https://pyinstaller.org/en/stable/) — one-file builds, spec files, and the license exception that allows bundling apps under any license.

## Releasing a Windows exe

Reviewed 2026-09-27 for the first release.

- [Immutable releases are generally available](https://github.blog/changelog/2025-10-28-immutable-releases-are-now-generally-available/) — locked tags and assets with a signed release attestation; publish from a draft with the assets attached.
- [Artifact attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations) — build provenance from GitHub Actions, verifiable with `gh attestation verify`; the next step once CI can run.
- [Code signing options for Windows apps](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options) — certificate types and SmartScreen reputation.
- [SignPath Foundation](https://signpath.io/solutions/open-source-community) — free code signing for open-source projects built in CI; the certificate names SignPath Foundation as publisher.
- [Azure Artifact Signing](https://azure.microsoft.com/en-us/products/artifact-signing) — about $10 a month; open to individual developers only in the US and Canada.
- [Antivirus false positives with PyInstaller](https://www.pythonguis.com/faq/problems-with-antivirus-software-and-pyinstaller/) — avoid UPX, prefer signing, and report false positives to the vendor.
- [Building PyInstaller's bootloader](https://pyinstaller.org/en/stable/bootloader-building.html) — compiling the launcher from source, which `packaging\build.cmd` does; it halved this app's VirusTotal detections.
- [LGPL and GPL compliance with PyInstaller](https://velovix.github.io/post/lgpl-gpl-license-compliance-with-pyinstaller/) — why a public source and build recipe matter for bundled LGPL libraries.

## AI-assisted engineering

- [OpenAI: Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md) — layered repository guidance and discovery.
- [OpenAI: Review GitHub pull requests with Codex](https://learn.chatgpt.com/docs/third-party/github) — repository-specific review rules and the boundary between AI review and deterministic controls.
