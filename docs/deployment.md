# Infrastructure & Deployment

**FactSet Agent Automation Pipelines**

Because the Vertex Agent Builder console absolutely requires a fully structural remote `.well-known/agent.json` description tag natively pointing to your active proxy host, you cannot register your agent to the GCP console *until* Cloud Run goes online. Conversely, Cloud Run isn't useful until the console explicitly forwards routing traffic!

We bypass this two-step "Chicken or the Egg" anomaly via our strict automation shells natively embedded inside `deploy_and_register.sh`.

---

## 📦 Automation Workflows

```
START
  │
  ├─► STAGE 1: Dynamic Parameter Injection
  │   └─► System parses `.env` explicitly mapping GCP Identity.
  │   └─► Resolves Abstract `AGENT_SERVICE_NAME` namespaces.
  │
  ├─► STAGE 2: Pipeline Standup (Cloud Run)
  │   └─► Executes `gcloud run deploy` via `uv` Builder Container.
  │   └─► Generates raw Target HTTPS URL natively.
  │
  ├─► STAGE 3: Server-Side Authorization Patch
  │   └─► Connects Google Cloud endpoints into FactSet OpenID structures.
  │   └─► Binds explicitly into: `AGENT_AUTH_ID`
  │
  └─► STAGE 4: Gemini Enterprise Enrollment
      └─► Patches local Schema configurations onto the generated URL host!
      └─► Forces Registration via standard POST pipelines!
END
```

---

## ⚙️ Setting Up Your Blueprints

Before executing automated infrastructure pushes to Google Cloud Run, seamlessly build your exact organizational targets globally via the generated template matrix.

```bash
# Clone the secure template into local environments natively
cp .env.example .env
```

| Environment Key | Core Purpose | Example Namespace |
|-----------------|--------------|-------------------|
| `AGENT_SERVICE_NAME` | The absolute Cloud Run namespace path containing your ADK. | `factset-native-proxy-v1` |
| `AGENT_AUTH_ID` | The Vertex Agent Authorization Registry pointer. | `factset-oauth-v1` |
| `AGENT_DISPLAY_NAME` | The visible Agent Card natively displayed to Enterprise Users. | `FactSet Institutional` |


---

> [!WARNING] **Breaking Deployment Constraints (409 Conflict)**
> Google's Vertex API pipeline does **not** support `POST` upserts for Identity mappings! If an `AGENT_AUTH_ID` is strictly already registered inside the target GCP environment, attempting to execute the deployment sequence will fatally throw an unhandled `409 Conflict`. 
>
> If you ever deliberately execute a **Secret Rotation Password Patch** manually inside `.env`, you **MUST** physically increment your `AGENT_AUTH_ID` (e.g., `factset-oauth-v2`) prior to deploying, or the engine will inherently reject your new access blocks!
