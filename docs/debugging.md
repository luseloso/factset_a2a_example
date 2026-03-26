# FactSet Agent Debugging Guide

Because the FactSet native agent intercepts complex A2A streaming payloads and binds them to remote Identity-Aware contexts, diagnosing issues can be intricate. This guide maps out precisely how to observe the payload event streams and troubleshoot Vertex Agent Builder edge cases.

## Core Traceability

When you deploy a change to the native proxy, debugging begins deeply at the container level by querying the underlying Starlette router traffic mapping the Python AnyIO environment.

### 1. View Proxy Event Streams
The absolute authoritative source of truth indicating whether Vertex Agent Builder is successfully forwarding HTTP payloads to the FactSet A2A proxy is the Cloud Run execution trace:
```bash
# Authenticate against Google Cloud metrics
source .env

# Tail the last 50 execution sequences of the native container
gcloud run services logs read factset-native-agent --project=$GOOGLE_CLOUD_PROJECT --region=$GOOGLE_CLOUD_LOCATION --limit=50
```

* **Happy Path**: You should see the `INFO:main:==> Injected Vertex OAuth Token...` immediately followed by `INFO:httpx:HTTP Request: POST https://mcp.factset.com/content/v1/ "HTTP/1.1 200 OK"`.
* **Silence**: If there is no activity logged but the Vertex UI hangs, the agent is either not published cleanly, or the explicit `.well-known/agent.json` routing configuration inside Vertex AI is disconnected. Re-run `bash deploy_and_register.sh` to forcefully sync the metadata pointer!

## Common Failure Signatures

### 1. `Failed to create MCP session: TaskGroup`
This error occurs instantaneously in Vertex when the `mcp-python-sdk` tries to bootstrap the connection to FactSet but fundamentally rejects the handshake (generating a `401 Unauthorized` HTML payload).
* **Cause**: The Vertex UI inherently failed to secure the external OAuth scope prior to requesting FactSet execution, resulting in empty or `MISSING_TOKEN` proxy injection contexts across `gemini_agent.py`.
* **Fix**: Ensure your IAM configuration in Google Cloud correctly binds the identity scope, and that the `AuthorizationContextMiddleware` in `main.py` is accurately extracting `request.headers.get("Authorization")`.

### 2. `Malformed function call: from ... import ...`
This extremely misleading Vertex UI error literally means Gemini completely hallucinated the REST payload constraints and chose to execute dynamic code (typically Python) instead of passing raw JSON. 
* **Cause**: The FactSet endpoint schema is missing, poorly typed (flattened), or requires iterative math. `gemini-2.5-flash` natively shifts toward Python interpretation logic if it senses looping required (e.g., aggregating 20 years of M&A data via 1-year deltas).
* **Fix**: Force restrictive `NO PYTHON` exclusion markers into the `gemini_agent.py` Persona instruction, and demand valid string arrays mapping specifically to the single Tool function call.

### 3. The Silent Hang (Vertex Proxy Timeouts)
If Vertex Agent Builder submits a request, spins aggressively, and 15 seconds later abruptly hangs silently without printing text, your infrastructure has experienced a proxy starvation timeout.
* **Cause**: Your backend FactSet queries blocked the Cloud Run Event loop longer than Google's explicit Server-Sent Events HTTP buffer allowance. 
* **Fix**: Do NOT build custom `FastAPI` logic proxies! Rely strictly upon compiling `A2aStarletteApplication` provided natively by `google-adk`, which inherently guarantees proper keep-alive buffering back to the UI!
