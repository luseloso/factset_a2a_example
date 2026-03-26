# FactSet Analyst Agent (Native ADK)

This repository contains the definitive, highly optimized codebase for integrating FactSet's Market Context Protocol (MCP) securely into the **Google Vertex AI Gemini Enterprise** workspace via a remote Agent-to-Agent (A2A) Cloud Run proxy.

Unlike traditional custom FastAPI proxy implementations, this system is explicitly architected around the official **Agent Development Kit (ADK)** by Google. It securely and statelessly manages Identity-Aware User Tokens (`sf_token_var`) directly inside a fast-fail proxy boundary to prevent Server-Sent Event (SSE) freezing timeouts.

## Deep Dive Documentation

To understand the core structural mechanisms enabling this Enterprise integration, please review the highly detailed architectural breakdown documents generated dynamically inside the [`/docs/`](./docs/) repository folder:

1. **[Architecture Guidelines](./docs/architecture.md)**
   Delves into the complex backend logic explaining how the ADK A2A event stream acts as a native buffer, effectively halting Vertex UI proxy timeouts for quantitative data queries exceeding >20 seconds. It explicitly maps out the `NO PYTHON` hallucination constraints inside the LLM tool schemas.
   
2. **[Infrastructure Components](./docs/deployment.md)**
   Walks you step-by-step through configuring your `Google Cloud Project` identity bindings, and explicitly unpackages the unique 2-step registration dependency orchestrating Cloud Run URLs seamlessly into Gemini Agent Builder.
   
3. **[Execution Debugging & Tracing](./docs/debugging.md)**
   Explains rigorously how to observe the raw Cloud Run event stream outputs to perfectly verify authentication hooks, mitigate `Malformed function call` payload anomalies, and successfully trace TaskGroup exceptions natively mapping back to Gemini.

## Quickstart

If you possess a `.env` file correctly mapping your `GOOGLE_CLOUD_PROJECT` identifier and your Vertex `GEMINI_ENTERPRISE_APP_ID`:

```bash
# Standup entire Cloud Run proxy natively and register your Agent:
bash ./deploy_and_register.sh
```

**Testing your agent:** Provide dynamic queries such as _"What were the largest M&A acquisitions executed by TSLA over the last 15 years?"_ natively inside your Vertex Workspace UI to trigger FactSet quantitative extraction!
