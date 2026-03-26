# FactSet Agent Infrastructure & Deployment Overviews

Because Vertex AI strictly expects stable JSON Server payloads mapping directly to Google Cloud proxy APIs, you must deploy FactSet as the "Agent to Agent" (A2A) remote host. This requires explicit deployment methodologies inside a Cloud Run runtime Docker container.

## 1. Cloud Run A2A Infrastructure

The agent natively listens for Webhooks by running Google's core Agent Development Kit backend. The runtime is orchestrated perfectly via the following container `Dockerfile`:
```docker
FROM python:3.14-slim AS builder

RUN pip install uv
COPY . /app
WORKDIR /app
RUN uv venv && uv pip sync requirements.txt

# The absolute critical piece here is --a2a flag!
# It executes the remote SSE proxy.
CMD ["/app/.venv/bin/uv", "run", "adk", "api_server", "--a2a", "--module", "gemini_agent", "--port", "8080"]
```
Because of Identity-Aware mechanisms, the Cloud Run instance **MUST** be deployed exposing HTTPS (`--allow-unauthenticated`), but rely strictly on the `Authorization` headers passed gracefully by Vertex Agent builder.

## 2. Setting Up the `.env` Vault

Before deploying to Google Cloud Run, verify you have a strict `.env` located locally mirroring your exact Cloud GCP parameters:
```bash
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GEMINI_ENTERPRISE_APP_ID=agentspace_xxxxxx  # Specific Vertex AI Reasoning Engine Host
MODEL=gemini-2.5-flash
```

## 3. The Deployment Two-Step Circularity

Because the Vertex Agent Builder console absolutely requires a fully structural remote `.well-known/agent.json` description tag of your `FactSet Agent v7`, you cannot register your agent to the console *until* Cloud Run goes online. Conversely, Cloud Run isn't useful until the console forwards routing traffic!

We bypassed this with `deploy_and_register.sh`:
1. **Infrastructure Standup**: 
First, the script violently builds the ADK `Dockerfile` via `gcloud builds submit` and attaches it globally to Cloud Run. It immediately pulls the final `--format="value(status.url)"`.
2. **Server-Side Authorization Hook**:
Because you are accessing Vertex natively, the script creates a dedicated `AGENT_AUTH_ID` configuration directly connecting FactSet backend tokens into Google's IAM suite.

> [!WARNING] **Breaking Deployment Constraints (409 Conflict)**
> Google's Vertex API pipeline does **not** support `POST` upserts for Identity mappings! If an `AGENT_AUTH_ID` is already registered inside the target GCP environment, attempting to execute the deployment script will result in a fatal `409 Conflict` bypass. If you ever fundamentally rotate your `CLIENT_SECRET` in `.env`, you **MUST** increment your `AGENT_AUTH_ID` (e.g., `factset-oauth-v2`) prior to deploying, otherwise the Google engine will simply ignore the new secret!

3. **Agent Registration Patching**:
The script extracts the Cloud Run URL and dynamically patches the complex `a2aAgentDefinition` JSON mapping inside bash! It sets `credentials: Bearer <TOKEN>`, thereby overriding Google's API natively! 
Finally, the script forces an `HTTP POST` into `v1alpha/projects/$GOOGLE_CLOUD_PROJECT/locations/global/collections/.../agents` creating the `FactSet Agent v7` seamlessly in your Enterprise UI!
