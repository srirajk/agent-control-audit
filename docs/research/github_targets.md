# External Validation Targets

Use these repositories to prove the skill against real financial agent shapes. Clone into `external_repos/` or another temporary workspace, run `agent-control-audit/scripts/static_audit.py` from the repository root, then have Codex perform the adapter-specific review. Do not treat README claims as control evidence unless source/config proves them.

## Priority Targets

### Google ADK Antom Payment Agent

- URL: `https://github.com/google/adk-samples/tree/main/python/agents/antom-payment`
- Why it matters: payment session creation, payment details, cancellation, refunds, merchant credentials, MCP tools.
- Expected current outcome: router detects Google ADK and runs framework-aware source discovery; reviewer must dynamically prove ADK callback/plugin order, tool confirmation, auth, deployed session state, and workflow semantics.
- Future adapter should test: tool authorization, approval before payment/refund, semantic argument validation, transaction limits, secret handling, audit logging, rate/cost bounds, timeout/fallback, jailbreak resistance.

### virattt/financial-agent

- URL: `https://github.com/virattt/financial-agent`
- Why it matters: LangChain/FastAPI stock-analysis agent with price/news/financial data, metrics, DCF valuation, and disclaimer language.
- Expected current outcome: router detects LangChain and runs framework-aware source discovery; reviewer must dynamically prove middleware ordering, callbacks, tool binding, retrieval chains, and deployment configuration.
- Future adapter should test: financial recommendation output validation, grounding, disclaimer adequacy, data-source scope, prompt injection through data/news, rate limits, evals.

### gsaini/financial-research-analyst-agent

- URL: `https://github.com/gsaini/financial-research-analyst-agent`
- Why it matters: multi-agent financial research system with RAG, many analysis tools, reports, API/UI/deployment, and security claims.
- Expected current outcome: router detects LangChain and runs framework-aware source discovery, or routes to LangGraph when explicit graph constructs are present.
- Future adapter should test: multi-agent authority, handoff provenance, RAG grounding, report output validation, operational NFRs, eval/reproducibility claims.

### nolancacheux/Rag-Equity-Research-Agent

- URL: `https://github.com/nolancacheux/Rag-Equity-Research-Agent`
- Why it matters: LangGraph equity research with SEC filings, hybrid RAG, external data, Reddit/news, Telegram/API deployment.
- Expected current outcome: router detects LangGraph and runs framework-aware source discovery; reviewer must dynamically prove graph transitions, interrupts, checkpointers, stores, and bypass paths.
- Future adapter should test: graph routing, state/checkpoints, retrieval scope, indirect prompt injection, external delivery controls, observability, rate/cost boundaries, eval gates.

### AI4Finance-Foundation/FinRobot

- URL: `https://github.com/AI4Finance-Foundation/FinRobot`
- Why it matters: open-source financial AI agent platform with specialized finance agents and toolchains.
- Expected current outcome: router may detect framework-specific or custom agent patterns depending on package version; use it to test whether the static discovery needs broader non-LangChain/non-ADK framework signals.
- Future adapter should test: report grounding, tool access, data provenance, analyst-facing output controls, multi-agent authority, and eval dataset compatibility.

## Expansion Backlog By Business Line

Use these after the priority targets to prove that the skill is not just an AML or stock-research auditor. Prefer cloning a small number from different business lines over cloning many similar stock-analysis demos.

## Deep-Search Standouts: Platform, Benchmark, And Multi-Domain Repos

These are the strongest follow-up candidates from a deeper search because one repo can exercise many assurance dimensions.

- `https://github.com/aifinlab/FinVault`
  - Why it matters: benchmark for financial-agent safety in execution-grounded environments, with sandbox code, datasets, and scenario-specific tools/states/checks.
  - Coverage: 31 scenarios across credit/lending, insurance, securities/investment, payments/settlement, compliance/AML, and risk management.
  - What it stresses: tool-aware safety, attack/benign parity, over-refusal, execution outcomes, sandbox vulnerability checks, jailbreak/prompt-injection families, and release integrity checks.
  - Priority: highest. This is the best single repo for proving the skill is broader than AML or stock research.
- `https://github.com/vals-ai/finance-agent-v2`
  - Why it matters: Finance Agent Benchmark v2 evaluates tool-using financial research agents over web search, SEC EDGAR, HTML parsing, stored information, and price history.
  - Coverage: public-company research, financial statements, SEC filings, equity/ETF/crypto/FX price history.
  - What it stresses: tool-calling evidence, financial QA grounding, benchmark reproducibility, model/provider comparison, logs, and eval integration.
- `https://github.com/vals-ai/finance-agent`
  - Why it matters: original Finance Agent Benchmark with web search, EDGAR search, HTML parsing, and information retrieval.
  - Coverage: companies, financial statements, and SEC filings.
  - What it stresses: financial RAG, source grounding, tool logs, model eval harnesses, and benchmark portability.
- `https://github.com/microsoft/FinanceBenchmark`
  - Why it matters: benchmark for Finance Agent in M365 Copilot, including financial obligations research, financial performance research, and business brief generation.
  - Coverage: AP/AR and ERP queries through MCP/Dynamics 365, public-company performance research, and business briefs.
  - What it stresses: MCP tool authorization, ERP data access, rubric-grounded LLM judging, internal-vs-public data boundaries, and provider comparison.
- `https://github.com/TauricResearch/TradingAgents`
  - Why it matters: high-signal multi-agent trading framework with analyst, researcher, trader, risk management, and portfolio manager roles.
  - Coverage: fundamentals, sentiment, news, technical analysis, debate, risk management, portfolio approval, simulated exchange execution, decision logs, and LangGraph checkpointing.
  - What it stresses: multi-agent authority boundaries, final trade approval, risk-team escalation, execution-adjacent controls, persistent memory, reproducibility, market-data grounding, and no-advice boundary.
- `https://github.com/eddyzzl/marvis-risk-agent`
  - Why it matters: local-first credit-risk workbench for validation, data processing, feature analysis, modeling, strategy, monitoring, portfolio, limit/pricing, and vintage workflows.
  - Coverage: credit model development, validation, scoring, monitoring, strategy, portfolio analysis, limit/pricing, and auditable workflow execution.
  - What it stresses: model governance, independent validation, data lineage, drift/outcome monitoring, explainability, audit history, human-in-the-loop gates, and local-first evidence handling.
- `https://github.com/Lormyn/aml-agent-adk`
  - Why it matters: Google ADK AML analyst assistant with BigQuery, MCP Toolbox, Agent Engine deployment, SAR generation, memory, and A2A support.
  - Coverage: alert triage, user profile lookup, transaction tracing, high-risk alerts, SAR report drafting, MCP tools, BigQuery data, Agent Engine memory, and A2A discovery.
  - What it stresses: ADK adapter quality, AML-specific controls, SAR approval, MCP authorization, BigQuery data minimization, A2A handoff provenance, and deployment/runtime blind spots.

### Capital Markets, Research, And Wealth Advice

- `https://github.com/ZhiweiChen-coder/OpenAshare`
  - Why it matters: AI-powered China A-share stock analysis with agent orchestration, memory, investment recommendations, holdings, and market/news tracking.
  - What it stresses: recommendation validation, advice disclaimers, market-data freshness, memory minimization, source attribution, suitability boundaries.
- `https://github.com/Frida7771/QuantBrains`
  - Why it matters: LangGraph financial analyst with stock data, SEC 10-K analysis, FastAPI, React, FAISS, Yahoo Finance, and LangSmith.
  - What it stresses: SEC/filing RAG grounding, citation validation, LangGraph routing, LangSmith evidence, output validation.
- `https://github.com/benstaf/ipoagent`
  - Why it matters: IPO due-diligence benchmark/agent for S-1 filing analysis and rubric generation.
  - What it stresses: long-document retrieval, due-diligence factuality, rubric/eval quality, hallucination controls, investment-banking research boundaries.
- `https://github.com/MoazIrfan/Personal-Finance-Coach-AI-Agent`
  - Why it matters: consumer-facing personal finance coach with expense/spending workflows.
  - What it stresses: regulated advice boundaries, customer-data minimization, PII redaction, toxicity/abuse safety, benign false-positive evals.

### Trading, Market Signals, And Execution-Adjacent Workflows

- `https://github.com/IvanWng97/TradingAgents-Telegram`
  - Why it matters: Telegram wrapper for TradingAgents with watchlists, parallel multi-ticker analysis, cancellation, and reports.
  - What it stresses: customer-facing bot safety, trading-signal disclaimers, prompt injection through chat, report provenance, cancellation semantics.
- `https://github.com/cy-Yin/TradingAgents-CN-lite`
  - Why it matters: LangGraph multi-agent trading analysis for A-share, HK, and US markets.
  - What it stresses: multi-agent authority, market-data provenance, region-specific market assumptions, investment recommendation controls.
- `https://github.com/ronitg1/alpha-terminal`
  - Why it matters: retail-investor dashboard with AI agent panels, stock scoring, and options backtesting.
  - What it stresses: options-risk disclosures, backtest reproducibility, no-execution boundary, recommendation calibration, rate/cost controls.
- `https://github.com/Vigneshmaradiya/ai-agent-comparison`
  - Why it matters: same stock-analysis workflow implemented across CrewAI, LangGraph, and AutoGen.
  - What it stresses: adapter coverage gaps, cross-framework evidence consistency, multi-agent routing, possible future AutoGen/CrewAI adapters.

### Credit, Lending, And Underwriting

- `https://github.com/SayamAlt/AI-Credit-Underwriting-Engine-using-FastMCP-LangGraph`
  - Why it matters: LangGraph and FastMCP credit underwriting with specialized agents, fraud/risk evaluation, explainable decisions, and LangSmith tracing.
  - What it stresses: fair-lending controls, explainability/reason codes, adverse-action boundaries, MCP tool authorization, credit-policy traceability.
- `https://github.com/aayushpandey01/Credit-Risk-Agent`
  - Why it matters: autonomous credit-risk monitoring with probability-of-default, early-warning signals, portfolio drift, and LLM reasoning.
  - What it stresses: drift/outcome monitoring, model governance, benchmark/backtesting, data lineage, portfolio-risk explanations.
- `https://github.com/AdityaC-07/BTECH-LY-Project-Loanease`
  - Why it matters: loan-origination agent system with KYC verification, underwriting, loan recommendation/negotiation, XGBoost risk scoring, SHAP, OCR, and WhatsApp.
  - What it stresses: KYC handling, fair lending, explainability, customer communications, OCR data quality, human approval for offers/negotiation.

### AML, KYC, Fraud, Sanctions, And Financial Crime

- `https://github.com/techgirldiaries/theia`
  - Why it matters: agentic fraud intelligence platform with multi-agent collaboration, RAG, risk scoring, AML/KYC compliance, and financial-crime detection.
  - What it stresses: AML typology coverage, KYC evidence handling, sanctions screening, adverse-media grounding, case-management audit trails.
- `https://github.com/Jackson-Cai-ctrl/finguard-ai`
  - Why it matters: financial risk-control multi-agent system for AML/KYC compliance.
  - What it stresses: SAR/escalation approval, false-positive handling, investigator explanations, sanctions/PEP data scope, evidence retention.
- `https://github.com/Souptik96/riskos-aml-intelligence`
  - Why it matters: multi-agent AI for fraud detection, credit risk, KYC identity verification, and sanctions screening.
  - What it stresses: cross-domain financial-crime controls, sub-100ms latency claims, model/data provenance, operational NFRs.
- `https://github.com/yichenC1c/SAGE`
  - Why it matters: LLM-driven self-reflective multi-agent fraud detection framework from recent research.
  - What it stresses: fraud-specific eval metrics, class imbalance, reward design, per-decision explanations, benchmark reproducibility.
- `https://github.com/msy0513/UniDetect`
  - Why it matters: LLM-driven fraud detection across heterogeneous blockchains and DeFi transaction graphs.
  - What it stresses: crypto/DeFi fraud, transaction-graph evidence, cross-chain generalization, grounding over generated transaction summaries.
- `https://github.com/Nolpak14/getregdata`
  - Why it matters: business-registry data skills for KYC/AML, beneficial ownership, compliance, credit risk, and government-data lookup.
  - What it stresses: tool authorization, jurisdictional data provenance, entity resolution, beneficial-owner data minimization, KYC data-source freshness.

### Payments And Merchant Workflows

- `https://github.com/google/adk-samples/tree/main/python/agents/antom-payment`
  - Why it matters: already-prioritized Google ADK payment sample with merchant/payment/refund-like surfaces.
  - What it stresses: ADK tool confirmation, payment/refund approval, credential scoping, side-effect limits, idempotency, audit logging.

### Insurance

Open-source insurance-agent repos are thinner than trading, credit, and AML. Keep searching here, but do not force weak repos into the proof matrix. Useful target qualities are submission intake, policy comparison, claims triage, underwriting referral, loss-history extraction, and human approval before coverage/claim decisions.

## Acceptance Criteria

- Empty repo stops as `no agent found`.
- Supported detected frameworks run static first-pass discovery; ambiguous framework repos stop as `framework undetermined`.
- OpenAI fixture produces hashable findings matching `tests/fixtures/planted_gaps.md`.
- External finance repos exercise at least one of: payment/refund tools, RAG, multi-agent orchestration, customer-facing output, external API deployment, or eval/security claims.
