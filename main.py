import logging
import os
import json
import uvicorn
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory import InMemoryMemoryService

from a2a.server.apps.jsonrpc.starlette_app import A2AStarletteApplication
from google.adk.a2a.executor.a2a_agent_executor import A2aAgentExecutor
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard

from gemini_agent import GeminiAgent
from auth_context import sf_token_var

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Auth Interceptor ---
# We use this tiny middleware solely to grab the Vertex AI Bearer token
# and inject it into the async context variable so the FactSet MCPToolset
# can blindly inherit it downstream without needing complex router hacks.
class AuthorizationContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"==> INCOMING A2A REQUEST: {request.method} {request.url.path}")
        
        # Log all headers cleanly to see exactly what Identity-Aware Proxy or Vertex is injecting
        for name, value in request.headers.items():
            secure_val = value if name.lower() != "authorization" else f"{value[:15]}... [REDACTED]"
            logger.info(f"    HEADER {name}: {secure_val}")
            
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            logger.info(f"==> Injected Vertex OAuth Token into context var for FactSet!")
            sf_token_var.set(token)
        else:
            logger.warning("No valid Bearer token found in request. FactSet MCP will fail if called.")
            sf_token_var.set("MISSING_TOKEN")
            
        return await call_next(request)


app = FastAPI(title="FactSet Native A2A Agent Server")
app.add_middleware(AuthorizationContextMiddleware)


# Initialize the agent instance (tools are initialized on-demand natively)
root_agent = GeminiAgent(require_auth=False)

# Recreate the exact discovery agent card automatically
server_url = "https://factset-native-agent-4bz26qs7xq-uc.a.run.app"
agent_card = root_agent.create_agent_card(agent_url=server_url)

# Utilize the absolute official ADK Google Native A2A Executor
runner = Runner(
    app_name=root_agent.name,
    agent=root_agent,
    session_service=InMemorySessionService(),
    artifact_service=InMemoryArtifactService(),
    memory_service=InMemoryMemoryService(),
)

agent_executor = A2aAgentExecutor(runner=runner)

request_handler = DefaultRequestHandler(
    agent_executor=agent_executor,
    task_store=InMemoryTaskStore(),
)

a2a_app = A2AStarletteApplication(
    agent_card=agent_card,
    http_handler=request_handler,
)

# FactSet A2A is mounted securely to the root
app.mount("/", app=a2a_app.build())

if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=8080)
