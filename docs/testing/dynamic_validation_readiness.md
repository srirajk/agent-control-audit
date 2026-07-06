# Dynamic Validation Readiness

This note summarizes the secrets, service connections, and local runtime setup needed to move from static audit evidence to live eval evidence for the current finance proof targets.

Do not put secrets in chat, committed files, normalized datasets, generated eval suites, reports, or logs. Use process environment variables, local ignored `.env` files, workspace settings, or the target repo's documented secret mechanism.

## Shared Requirements

| Layer | Needed | Notes |
|---|---|---|
| Eval judge | `OPENAI_API_KEY` | Enough for DeepEval LLM-as-judge metrics, toxicity/jailbreak grading, answer quality, and OpenAI-based sample agents. |
| DeepEval cloud, optional | `CONFIDENT_API_KEY` | Only needed if publishing eval runs/traces to Confident AI. Local DeepEval runs do not require it. |
| Target invocation | One of HTTP, MCP stdio, SDK command, or repo CLI | The skill can evaluate a target only after there is a stable way to invoke it per golden case. |
| Golden data | JSONL, JSON, CSV, or XLSX from client | The skill normalizes this internally and flags missing assertions/client input. |
| Network | Outbound access to model/provider/tool APIs | Live evals can fail because the target agent's tools cannot reach external services. |
| Dependency install | `pip`, `uv`, `npm`, Docker, or repo-specific installer | Static audit does not need dependency install; dynamic runs usually do. |

## Target Matrix

| Target | Minimal live-demo secrets | Additional connections for full proof | Demo readiness |
|---|---|---|---|
| Generated/mock OpenAI agent | `OPENAI_API_KEY` | None | Best first smoke test for our DeepEval flow. |
| `TauricResearch/TradingAgents` | `OPENAI_API_KEY` if using OpenAI provider | Optional: `ALPHA_VANTAGE_API_KEY`, `FRED_API_KEY`, provider keys for Anthropic/Gemini/etc., Azure/AWS/Ollama/OpenAI-compatible endpoints | Strong local demo candidate. Can run with OpenAI plus mostly public/keyless data paths; richer macro/vendor coverage needs extra keys. |
| `vals-ai/finance-agent-v2` | `OPENAI_API_KEY`, `TAVILY_API_KEY`, `SEC_EDGAR_API_KEY`, `PRICING_DATA_API_KEY` | Optional LLM provider keys: `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `ETC_API_KEY`; Vals platform access and suite IDs for official benchmark runs | Strong financial research benchmark, but not OpenAI-only if all tools are enabled. |
| `microsoft/FinanceBenchmark` | `OPENAI_API_KEY` for evaluation/judge | ERP slice needs `ERP_MCP_TOKEN`, Dynamics 365 Finance sandbox, MCP server config, Azure login or `AZ_USERNAME`/`AZ_PASSWORD`/`AZ_TENANT_ID`; optional `ERP_BLOCKED_AZ_USER` guard | Excellent governance story, but full ERP proof is enterprise-plumbing-heavy. |
| `Lormyn/aml-agent-adk` | Not OpenAI-first; needs Google/Vertex setup | `GOOGLE_GENAI_USE_VERTEXAI`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, `GOOGLE_CLOUD_STAGING_BUCKET`, `MCP_URL`, optional `AGENT_ENGINE_ID`, optional telemetry flags; BigQuery dataset, Cloud Run MCP Toolbox, GCP ADC/service auth, IAM | Best AML story, but requires GCP, BigQuery, MCP Toolbox, and ADK runtime. |
| `aifinlab/FinVault` | Usually Qwen/OpenAI-compatible model config, depending selected agent | `QWEN_LOCAL_BASE_URL`, `QWEN_LOCAL_MODEL_NAME`, `QWEN_LOCAL_API_KEY`; optional safeguard keys `LLAMA_GUARD_API_KEY`, `LLAMA_GUARD_API_URL`, optional Hugging Face endpoint/cache for local guard models | Great safety benchmark, but needs benchmark-runner mapping and model-provider configuration. |
| `eddyzzl/marvis-risk-agent` | None for deterministic/local workflow; LLM features need OpenAI-compatible profile | Workspace `settings/llm.json` or UI config with API base URL, model name, and API key/env reference; optional `MARVIS_LOCAL_TOKEN`, `MARVIS_ALLOW_REMOTE_READ`, `MARVIS_TRUSTED_PROXY_HOSTS`; optional Java for PMML | Strong NFR/governance UI candidate. LLM validation is workspace-profile based, not a simple global env-only flow. |

## Recommended Proof Order

1. Prove our DeepEval generation and runner against the mock OpenAI/sample agent with only `OPENAI_API_KEY`.
2. Run a small dynamic eval on `TradingAgents` with OpenAI as the provider and one low-risk ticker/date scenario.
3. Run `finance-agent-v2` only after adding Tavily, SEC API, and Tiingo pricing keys, or restrict the tool set to the keys available.
4. Use `FinanceBenchmark` for the governance story; treat ERP QA as pending until Dynamics 365 plus MCP token are available.
5. Use `aml-agent-adk` for the AML showcase only when GCP Vertex, BigQuery, Cloud Run MCP Toolbox, and IAM are configured.
6. Use MARVIS for local credit-risk workflow/NFR review; configure its LLM profile through workspace settings if agentic explanation paths are needed.

## What One OpenAI Key Proves

One OpenAI key is sufficient to prove the evaluator side: DeepEval LLM-as-judge, safety grading, toxicity/jailbreak grading, output quality scoring, and OpenAI-based demo agents. It is not sufficient to prove target-agent tools that call Google Cloud, Microsoft Dynamics, Tavily, SEC API, Tiingo, Alpha Vantage, FRED, local Qwen, or custom MCP servers.

