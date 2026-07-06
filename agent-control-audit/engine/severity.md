# Severity Rules

Rank findings by user harm, regulatory or policy importance from the regime file, autonomy, exploitability, and whether the control can block before harm occurs.

## Severity Levels

- `blocker`: Ship must be blocked. A missing, weak, or misconfigured control can enable irreversible financial action, unauthorized account/data access, unsupported eligibility decisions, or uncontrolled multi-agent delegation in a financial workflow.
- `high`: Hold until fixed or formally accepted. A control gap can produce materially misleading financial output, sensitive data exposure, ungrounded regulated communication, or incomplete auditability for important workflows.
- `medium`: Fix before broad rollout. A gap weakens defense in depth, reduces traceability, or affects lower-risk/internal-only behavior.
- `low`: Improve when practical. A gap is narrow, mostly cosmetic, or has strong compensating evidence in code.

## Status Effects

- `missing`: use the requirement severity floor, then raise for autonomy and side effects.
- `weak`: normally one level below missing unless the weakness removes the blocking path for a high-impact action.
- `misconfigured`: same as missing when the control is attached to the wrong boundary; otherwise same as weak.
- `out_of_scope`: use at least medium. Raise to high or blocker when the repository delegates a required control to external infrastructure without evidence and the harm surface is high.
- `not_checked`: use medium by default. Raise when the unchecked adapter area is exactly where the risky behavior lives.
- `present`: no finding unless adequacy notes reveal residual risk that should be separately reported.

## Escalation Rules

Escalate to `blocker` when any of these are true:

- A money-moving, account-changing, trade/execution, credit/eligibility, or externally notifying tool lacks authorization, semantic argument validation, approval, or audit logging.
- A jailbreak or prompt-injection path can bypass approval, authorization, retrieval scope, data redaction, or handoff authority for a high-impact financial surface.
- A multi-agent handoff can transfer customer financial data or action authority without a destination boundary and input filtering.
- The framework is detected but the matching adapter is not implemented for the codebase under audit.
- Framework signals conflict and the audit would otherwise guess.

Escalate to `high` when any of these are true:

- Financial-facing output lacks validation against unsupported claims, missing caveats, or ungrounded recommendations.
- Retrieval is used for financial answers without source allowlisting or grounding validation.
- Sensitive financial data can enter prompts, tools, logs, memory, or handoffs without minimization or redaction.
- A customer-facing or retrieval-connected financial agent lacks prompt-injection/jailbreak controls.
- A high-risk financial agent lacks eval regression gates for jailbreaks, data leakage, grounding failures, and tool misuse.
- Audit logging exists only as local prints, comments, or non-durable messages.

Keep as `medium` when:

- The affected path is internal-only, reversible, and has no sensitive data or side effects.
- The control is present but incomplete in a way that limits coverage rather than removing it.
- The pass cannot inspect runtime/deployment evidence but the code clearly contains a hook for that control.
- Customer-facing toxicity, rate/cost, timeout/fallback, or observability controls are absent but the agent has no side effects and does not process customer financial data.

Use `low` only for narrow evidence-quality problems that do not change the verdict.

## Verdict Mapping

- `block`: one or more blocker findings, or no safe framework route.
- `hold`: no blockers, but one or more high findings.
- `ship_with_conditions`: no blockers/highs, but medium findings need tracked fixes or explicit risk acceptance.
- `ship`: no blocker/high/medium findings and all required controls are present or justified out of scope with evidence.

Risk tier:

- `critical`: any blocker on a high-impact financial surface.
- `elevated`: high findings or multiple medium findings across different control classes.
- `moderate`: only medium findings on constrained/internal paths.
- `low`: only low findings or clean audit.
