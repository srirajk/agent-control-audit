# Financial AML Domain Profile

## Identity

- `domain_id`: `financial_aml`
- Domain name: Financial crime and AML investigation assistance
- Business line or sub-business line: AML alert investigation, case analysis, due diligence, SAR/RFI/client-exit support
- Owner: To be supplied by user/team
- Reviewer/approver: To be supplied by user/team
- Version: Draft
- Reviewed date: To be supplied by user/team

## Intended Use

Assist analysts with AML investigation tasks such as alert triage, evidence gathering, party due diligence, case narrative drafting, RFI/SAR/client-exit recommendation support, and analyst-facing summaries.

## Prohibited Use

The agent must not autonomously file a SAR, close a case, recommend client exit as final action, contact a customer about an investigation, mutate a case-management record, or disclose AML investigation status without approved human review.

## User Personas

- AML analyst.
- Investigator.
- Quality control reviewer.
- Case manager.
- Model-risk or compliance reviewer.

## Harm Surfaces

- SAR filing or SAR narrative finalization.
- Alert or case closure.
- Client exit recommendation.
- Customer tipping-off.
- Sensitive customer/account/transaction data.
- Sanctions, adverse media, and KYC grounding.
- Wrong entity/counterparty resolution.
- Prompt injection from adverse media, uploaded documents, retrieved web pages, or tool output.
- Overblocking benign analyst workflows.
- Missing or stale source evidence.

## Required Human Approval Gates

- Approve selected transactions and derived parties before due diligence.
- Approve party summaries and evidence before case analysis.
- Approve case analysis and recommendation before SAR/RFI/client-exit/post-disposition action.
- Approve any write-back to a case-management system.

## Required Evidence Standard

Material allegations must cite approved evidence IDs, such as KYC, transaction, sanctions, adverse-media, policy, or case-management records. If evidence is insufficient, the agent should say so and request analyst review rather than fabricate a conclusion.

## Accepted Exclusions

If the agent cannot execute case closure, SAR filing, customer contact, payment movement, or case-management write-back, the team may mark those side-effect controls as out of scope only when source code, configuration, or deployment evidence proves the capability is absent.
