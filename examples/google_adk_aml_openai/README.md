# Google ADK AML OpenAI Reference

This is a production-shaped reference example, not a full AML platform. It shows
how a Google ADK 1.x-style AML agent can expose source-visible controls that an
assurance skill can inspect and test.

## Layout

- `agent.py`: thin ADK discovery entrypoint that exposes `root_agent`.
- `adk_aml_openai/agent.py`: root-agent construction.
- `adk_aml_openai/config.py`: model, runtime, and control thresholds.
- `adk_aml_openai/schemas.py`: typed tool request models.
- `adk_aml_openai/tools.py`: ADK tools for evidence retrieval and regulated action preparation.
- `adk_aml_openai/callbacks.py`: ADK guardrail callbacks.
- `adk_aml_openai/policies.py`: reusable authorization, redaction, grounding, injection, and handoff policies.
- `adk_aml_openai/governance.py`: source-visible model-risk and NFR governance evidence.
- `adk_aml_openai/assurance/eval_adapter.py`: deterministic golden-data adapter.
- `adk_aml_openai/api/server.py`: optional FastAPI `/invoke` wrapper.
- `adk_aml_openai/adapters/http_adapter.py`: CLI adapter for the HTTP wrapper.

The root-level `server.py`, `eval_adapter.py`, and `http_adapter.py` files are
compatibility shims for the existing smoke-test commands.
