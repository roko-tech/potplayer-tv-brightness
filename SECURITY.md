# Security policy

## Supported versions

Only the latest release and the current default branch receive security fixes.

## Report a vulnerability

Do not open a public issue containing vulnerability details, credentials, a TV pairing key, private data, or an exploit. Report privately through GitHub: the repository's **Security** tab, then **Report a vulnerability**. The maintainer, @rokogan, aims to acknowledge within a week.

Include the affected commit, prerequisites, reproduction steps, impact, and any safe proof of concept. Do not access data that is not yours, disrupt service, persist access, or publish details before the maintainer has had a reasonable opportunity to respond.

## Maintainer response

Maintainers should acknowledge receipt, preserve evidence, validate the report sceptically, assess affected versions, coordinate a fix and disclosure plan, and credit the reporter if requested. Security fixes require regression tests and a review of whether the root cause exists elsewhere.

See the [threat model](docs/security/threat-model.md) and [secure development guide](docs/security/secure-development.md) for project controls.
