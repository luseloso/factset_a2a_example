# Execution Debugging & Tracing

**Diagnosing the ADK Proxy Telemetry**

Because the native Agent fundamentally sits between two wildly complex structural systems (The Gemini Vertex Pipeline and the external FactSet Financial REST Framework), identifying root-cause errors is completely reliant upon tracing execution schemas accurately!

---

## 🔍 Core Traceability Matrices

When deploying changes directly against the proxy, telemetry observation is inherently analyzed natively on Cloud Run servers:

```bash
# Synthesize dynamic environment limits via source
source .env

# Target the active payload execution streams directly out of Starlette Webhooks natively
gcloud run services logs read "$AGENT_SERVICE_NAME" --project=$GOOGLE_CLOUD_PROJECT --region=$GOOGLE_CLOUD_LOCATION --limit=50
```

- ✅ **Successful Path**: Logs will natively emit `INFO:main:==> Injected Vertex OAuth Token...` immediately followed linearly by `INFO:httpx:HTTP Request: POST https://mcp.factset.com/content/v1/ "HTTP/1.1 200 OK"`.
- ❌ **Total Silence**: If there is zero payload activity logged but the Vertex UI completely hangs, the `.well-known/agent.json` routing layer inside the UI SDK is absolutely disconnected. **Fix**: Re-instantiate `bash deploy_and_register.sh` to forcefully update the proxy URLs natively.

---

## 💣 Identifying Terminal Edge Cases

### 1. `Failed to create MCP session: TaskGroup`
Triggers instantly when the Vertex Python backend SDK attempts to explicitly bootstrap REST channels against FactSet but generates a catastrophic `401 Unauthorized` token block natively.
- **Root Cause**: Vertex Agent Builder never originally challenged the external user to complete the OAuth UI signin sequence! As a result, Cloud Run evaluates empty Bearer payloads instantly.
- **The Fix**: Validate your IAM Configuration inside Google's Identity console to guarantee explicit target authorization mappings.

### 2. `Malformed function call: from ... import ...`
An incredibly misleading Vertex execution proxy error which literally dictates: Gemini explicitly decided your Schema parameters were too complex to solve strictly via valid `JSON` elements, so it radically generated a pure **Python executable block** natively designed to calculate your query via loops! 
- **Root Cause**: Flattened schema arrays mapping 20+ years of target variables strictly crash model logic templates safely over to internal code generators natively!
- **The Fix**: Absolutely ban Python evaluation parameters directly inside the foundational `Instructions` persona architecture natively!

### 3. The "Silent 15-Second Proxy Hang"
Vertex inherently halts requests manually, spins statically, and 15 seconds subsequently dumps the conversation completely.
- **Root Cause**: The custom FactSet HTTP pipelines mathematically starved the basic Cloud Run Event loop longer than Google considers stable natively via standard Webhooks! 
- **The Fix**: Entirely rely structurally upon the exact `ADK A2aStarletteApplication` protocol designed uniquely to keep remote API tunnels buffer-active!
