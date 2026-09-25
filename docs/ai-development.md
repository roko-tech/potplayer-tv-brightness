# AI-assisted development

AI can accelerate reading, implementation, tests, review, and documentation, but it does not own product intent, authority, or accountability. Treat AI output like a fast untrusted contribution: constrain it, inspect it, and verify the resulting behavior.

## Repository instruction strategy

- Keep durable repository-wide rules in root [AGENTS.md](../AGENTS.md).
- Add narrower instructions close to a subsystem only for real local commands, contracts, or safety constraints.
- Keep rules concise, outcome-based, and current. Put deterministic formatting/lint behavior in CI rather than spending model context on it.
- In code-review rules, describe the consequential behavior to flag and the safe path or exception.
- Verify instruction discovery in the intended AI tool after adding nested overrides.

## Workflow for an AI-assisted change

1. Provide the issue, acceptance criteria, relevant paths, constraints, and allowed side effects.
2. Require the agent to read code, tests, current docs, ADRs, and working-tree state before changing anything.
3. Ask it to surface assumptions and define verifiable success criteria.
4. For bugs, reproduce or establish concrete evidence before editing.
5. Keep implementation surgical; inspect every diff and dependency change.
6. Run deterministic checks and realistic behavior validation. Review artifacts and logs, not only the agent's summary.
7. Require a handoff that separates verified facts, inference, limitations, and untested surfaces.
8. Retain the decision and evidence in normal project artifacts—not raw hidden reasoning.

Use a fresh task/context when goals materially change. Long chats accumulate stale assumptions and make scope control harder.

## Authority and data boundaries

- Never place secrets, production records, private customer data, unreleased source outside its approved environment, or licensed material into an unapproved model/tool.
- Grant the minimum filesystem, network, account, and repository permissions needed for the task.
- Require explicit human authorization for destructive operations, production changes, migrations, releases, purchases, external communication, and other consequential side effects.
- Review generated shell commands and workflows for expansion, broad paths, credential exposure, and unsafe external input.
- AI review supplements CI, threat modeling, branch protection, and accountable human approval.

## Building AI features into the product

When the product itself uses a model, document and test:

- the user outcome and why a non-AI approach is insufficient;
- model/provider/version selection, prompt/tool/schema versioning, and change control;
- approved input data, retention, residency, and redaction;
- structured output validation and authorization after the model—not delegated to it;
- prompt injection, tool abuse, data exfiltration, unsafe content, and denial/cost scenarios;
- deterministic fallback, abstention, human review, cancellation, and idempotent side effects;
- versioned representative and adversarial eval sets with protected held-out cases;
- quality thresholds by segment, including false-positive/negative costs;
- latency, token/cost budgets, rate limits, monitoring, drift, rollback, and provider outage behavior.

Never use an LLM judgment as the sole control for access, payment, deletion, legal/medical/safety-critical action, or another high-consequence decision. Put deterministic policy and accountable approval around it.

Official Codex guidance used by this starter is linked in [references.md](references.md).
