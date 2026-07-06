# Evidence Schema

Emit exactly one evidence file per audit, named `agent_control_audit_evidence.jsonl` unless the user requests a different path. Use JSON Lines: one finding record per line.

## Record Schema

```json
{
  "schema_version": "1.0",
  "audit_id": "aca-<date>-<short-hash>",
  "finding_id": "ACA-001",
  "target": {
    "repo": "<path>",
    "entrypoint": "<path>",
    "commit": "<commit-or-null>"
  },
  "control": {
    "id": "C005",
    "name": "Human Approval Gate",
    "type": "approval_gate"
  },
  "requirement": {
    "id": "FIN-001",
    "text": "<author requirement text>",
    "source": "author_policy"
  },
  "status": "missing",
  "severity": "blocker",
  "location": "<file:line or null>",
  "detection_method": "static_openai_agents_sdk_adapter",
  "evidence": ["<short evidence snippets or symbol names>"],
  "adequacy": "<why this is or is not enough>",
  "recommendation": "<minimal fix>",
  "eval_evidence": {
    "suite": null,
    "dataset_hash": null,
    "runner": null,
    "metrics": null,
    "thresholds": null,
    "passed": null
  },
  "coverage": {
    "static_only": true,
    "blind_spots": ["<blind spot relevant to this finding>"]
  },
  "confidence": "high",
  "record_hash": "sha256:<hex>",
  "signature": null,
  "signature_algorithm": null,
  "signed_by": null,
  "signed_at": null
}
```

## Hashing

1. Build the record with `record_hash`, `signature`, `signature_algorithm`, `signed_by`, and `signed_at` set to `null`.
2. Canonicalize as UTF-8 JSON with sorted keys and no insignificant whitespace.
3. Compute SHA-256 over the canonical bytes.
4. Set `record_hash` to `sha256:<hex>`.
5. Optional signing fields are additive and must not change any other schema shape.

## Constraints

- Do not create separate schemas for signed and unsigned evidence.
- Do not include unverifiable external controls as present. Use `out_of_scope`.
- Every finding must trace to at least one requirement or adapter stop condition.
- Keep quotes short; prefer file paths, symbol names, line numbers, and paraphrased evidence.
