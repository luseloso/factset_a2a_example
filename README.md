# FactSet Analyst Agent (Native Vertex A2A)

**Created by [Luis Lopez](https://github.com/luseloso)**

A sophisticated multi-agent protocol leveraging Google's **Agent Development Kit (ADK)** to securely proxy and execute high-latency financial queries against **FactSet's Market Context Platform (MCP)** directly from the Gemini Enterprise Workspace.

The **FactSet Native A2A Agent** resolves strict Identity-Aware proxy timeouts by seamlessly streaming Google Vertex OAuth tokens through a stateless Cloud Run container. It is designed to evaluate, map, and execute enterprise-grade quantitative market queries without triggering hidden Vertex AI execution timeouts.

1. **Intercept Vertex AI OAuth Tokens statelessly** via `AuthorizationContextMiddleware`.
2. **Transform LLM queries into strict JSON constraints** using bounded tool architectures.
3. **Execute REST calls against FactSet** and stream the compiled evaluation inherently backward to the end user.

This project is built directly on the **Google Agent Development Kit (ADK)** for scalable, production-ready agent orchestration.

- 🏦 **Enterprise Identity Mapping**: Dynamically proxies the active Vertex UI user directly into FactSet API spaces.
- ⚡ **Timeout Mitigation**: Uses the native `A2aStarletteApplication` to serialize long-running event loops and prevent UI UI silent disconnects.
- 🛑 **Hallucination Blocking**: Explicitly mapped schemas and `NO PYTHON` protocols prevent the Gemini LLM from breaking external endpoints with looping logic.
- 🔒 **Secure Extensibility**: Air-gapped secret management explicitly ignoring tracking configurations for clean customer git hand-offs.
- 🚀 **Built on Google ADK**: Fully compliant production API orchestration template.

---

```
factset_a2a_example/
├── README.md                          # Project documentation
├── requirements.txt                   # Python dependencies
├── deploy_and_register.sh             # Cloud Run & Vertex Builder Orchestrator
├── register_agent.sh                  # Vertex AI Registry Hook (Standalone)
├── .env.example                       # Deployment Secret Template
├── config.json.example                # OAuth CCA Template
│
├── main.py                            # Cloud Run Container Entrypoint (Proxy)
├── gemini_agent.py                    # FactSet Agent Definition & System Prompts
├── auth_context.py                    # AnyIO Token Context Isolator
│
└── docs/                              # Deep-Dive Documentation
    ├── architecture.md                # A2A Sequence / Mermaid Maps
    ├── deployment.md                  # Infrastructure Constraints (409 Handling)
    └── debugging.md                   # Tracing SDK errors and Proxy drops
```

| File | Purpose |
|------|---------|
| **gemini_agent.py** | Defines the core `FactSet` persona, restricts tool schemas, and assigns the custom `patched_get_tools()` token hooks. |
| **main.py** | Intercepts inbound webhooks, extracts Identity Tokens, and starts the `ADK A2A` API server frame. |
| **auth_context.py** | Maintains strict token boundary isolations per request to prevent cross-contamination. |
| **deploy_and_register.sh**| Dynamically parses `.env`, patches Cloud Run containers, and injects the FactSet Agent schema into Vertex AI seamlessly. |

---

The system relies on a continuous Server-Sent Event proxy utilizing native ADK interceptors:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Vertex Agent Builder                         │
│               (Gemini Enterprise Workspace UI)                  │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │   Cloud Run Proxy    │
            │  (factset-native-v1) │
            │                      │
            │ Engine: Google ADK   │
            │ Middleware: AnyIO    │
            └──────────┬───────────┘
                       │
                       │ Forward Identity & Payload JSON
                       ▼
            ┌──────────────────────┐
            │   FactSet (MCP)      │
            │  (Target System)     │
            │                      │
            │ Action: GET / M&A    │
            │ Bearer: User Context │
            └──────────┬───────────┘
                       │
                       │ Return quantitative JSON string
                       ▼
            ┌──────────────────────┐
            │   Gemini 2.5 Flash   │
            │  (Output Synthesis)  │
            └──────────┬───────────┘
                       │
                       │ Markdown Event Stream
                       ▼
            ┌──────────────────────┐
            │ Vertex User UI       │
            └──────────────────────┘
```

---

### FactSet_MergersAcquisitions
Executes multi-year corporate action aggregations (e.g. Tesla Acquisitions between 2010 and 2025). Restricted forcefully against runtime script execution to ensure the Vertex AI backend handles JSON schema properly without `Malformed function call` errors.

### FactSet_Ownership
Retrieves institutional shareholder data dynamically mapped via secure bearer Identity validations.

The complete workflow follows this sequence:

```
START
  │
  ├─► User Input: M&A Quantitative Request
  │
  ├─► STAGE 1: Cloud Run Webhook Interception
  │   └─► Input: Bearer Token mapped from HTTP Header
  │   └─► Output: Saved to asynchronous ContextVar
  │
  ├─► STAGE 2: ADK Schema Construction
  │   └─► Model analyzes Tools and explicitly skips Python Code Execution
  │   └─► Generates raw Schema JSON
  │
  ├─► STAGE 3: Tool Invocation
  │   └─► System grabs FaceSet token from ContextVar
  │   └─► Output: 200 OK Financial Body
  │
  └─► Output: Final Agent Report inside Vertex!
END
```

---

- MacOS or Linux Environment
- Python 3.14 (managed via `uv`)
- Valid Google Cloud Platform configuration (`gcloud auth login`)
- FactSet Institutional Client Secret keys.

---

## 📦 Configuration

Before starting, map your local environment files natively so the Bash wrappers securely build the Agent variables for you:

```bash
# Rename the template and fill out your local API variables
cp .env.example .env

# Verify these core abstraction strings match your enterprise
AGENT_SERVICE_NAME="factset-native-proxy-v1"
AGENT_AUTH_ID="factset-oauth-v1"
AGENT_DISPLAY_NAME="FactSet Analyst"
```

---

## 🚀 Deployment Operations

Execute the full build script. It will dynamically scrape your `.env`, construct the `gcloud run` instance sequentially, and `POST` your Agent JSON layout straight into your Vertex AI interface:

```bash
bash ./deploy_and_register.sh
```

**Testing the Protocol:** Simply query your new Assistant locally in Vertex: *“What is the biggest acquisition from Google in the past year?”*

*(View our [Development Architectures](./docs/architecture.md) or [Proxy Debugging Matrix](./docs/debugging.md) for more details).*

---

## 🤝 Contributing
Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/factset-pipeline`)
3. Commit changes (`git commit -m 'Add new FactSet MCP Tool'`)
4. Push to branch (`git push origin feature/factset-pipeline`)
5. Open a Pull Request

---

## 📚 References
- [Google Agent Development Kit (ADK)](https://developers.google.com/google-developers/documentation)
- [FactSet Developer Portal](https://developer.factset.com/)
- [Gemini Enterprise API](https://ai.google.dev/)
