# FactSet Native ADK Context Architecture

This document maps out the internal structural design of the FactSet Gemini Enterprise integration, focusing entirely on how the Google Agent Development Kit (ADK) interfaces with Vertex AI without breaking Server-Sent Events (SSE) constraints.

## 1. Native A2A Wrapper vs Legacy Webhooks

In experimental proxy designs, mapping the LLM to the Vertex proxy meant manually instantiating `agent_executor.py` middleware loops to reconstruct A2A payloads. Because manual loops frequently misalign with internal Vertex serialization rules (such as placing final chat responses into disjoint `TaskStatusUpdateEvent` structures instead of mapping them identically to structural stream artifacts), Vertex Agent Builder natively "froze" or "hung."

**Solution:** The system now entirely relies on the Google ADK's native `A2aStarletteApplication`. The native engine binds inherently to Gemini's internal byte-stream, ensuring that long-running operations (>20 seconds) from quantitative FactSet endpoints properly buffer the socket instead of timing out silently.

## 2. Stateless OAuth 2.0 Injection Protocol

A massive bottleneck of standard ADK Python implementations is that agents and `MCPToolset` tools statically compile and spin up exactly once during the global container boot cycle. Vertex AI passes dynamic, per-request `Authorization` Bearer Tokens in the HTTP headers representing the actively logged-in enterprise user.

If the container compiles statically, you cannot hard-code a static token. 

### Core Workflow:

1. **The Fast-Fail Middleware**:
The `main.py` Starlette router runs an overriding class called `AuthorizationContextMiddleware`. The literal microsecond a webhook arrives, this middleware parses the `Authorization` header and assigns the actual 30-minute transient Bearer Token into an asynchronous `ContextVar` (`sf_token_var`).
2. **Context Persistence**:
Because AnyIO task execution perfectly maintains context boundaries, the static `gemini_agent.py` was structurally modified so that its `patched_get_tools()` hook fires. This hook looks at the memory context, pulls the user's explicit token out, and assigns it instantly to the `_mcp_session_manager._connection_params.headers` before invoking the REST payload!

## 3. Tool Calling vs Python Code Hallucinations

When Vertex AI Agent Builder queries tools with heavily flattened OpenAPI schemas, it naturally struggles to resolve parameter constraints. By default, Gemini 2.5 Flash engines use **Code Execution** plugins dynamically.

If a user asked "Who did TSLA acquire over the last 15 years", the LLM would see the `FactSet_MergersAcquisitions` JSON tool mapping `startDate` as a generic string and natively bypass JSON completely by writing a 20-line standalone Python loop logic script directly inside the A2A endpoint payload to execute `timedelta(days=364)` calculations! Vertex inherently crashes attempting to parse raw Python out of a REST argument array (`Malformed function call`).

To secure this architecture:
* Gemini 2.5 Flash is strictly restricted within the Persona to absolutely rely on native JSON execution. 
* A structural `NO PYTHON` exclusion string prevents proxy bypass instructions natively.
