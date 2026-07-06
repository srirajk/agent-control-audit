"""ADK discovery entrypoint.

Keep this file at the example root because ADK project discovery conventionally
looks for an `agent.py` that exposes `root_agent`. The implementation lives in
the `adk_aml_openai` package.
"""

try:
    from .adk_aml_openai.agent import root_agent
except ImportError:  # pragma: no cover - ADK direct-folder discovery path
    from adk_aml_openai.agent import root_agent

__all__ = ["root_agent"]
