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

## AI-assisted engineering

- [OpenAI: Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md) — layered repository guidance and discovery.
- [OpenAI: Review GitHub pull requests with Codex](https://learn.chatgpt.com/docs/third-party/github) — repository-specific review rules and the boundary between AI review and deterministic controls.
