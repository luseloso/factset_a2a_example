import os
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPServerParams
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse
from a2a.types import AgentCard, AgentCapabilities, AgentSkill

# Import our async context variable
from auth_context import sf_token_var

# --- 1. CONFIGURATION ---

MODEL_ID = os.environ.get("MODEL", "gemini-2.5-pro")
FACTSET_MCP_URL = "https://mcp.factset.com/content/v1/"


# --- 2. CALLBACK IMPLEMENTATION ---

def before_agent_callback(callback_context: CallbackContext) -> None:
    """Callback before each agent call to initialize state."""
    if not callback_context.state:
        callback_context.state = {}
    callback_context.state['step'] = 0

def create_after_model_callback(agent_name: str):
    """Factory to create an after_model_callback that correctly captures the agent's name."""
    def after_model_callback(
        callback_context: CallbackContext, llm_response: LlmResponse
    ) -> None:
        state = callback_context.state
        llm_response.custom_metadata = {
            'function_call_id': 'FunctionCallId_{}'.format(state.get('step', 0)),
            'agent_name': agent_name,
        }
        state['step'] = state.get('step', 0) + 1
    return after_model_callback


# --- 3. DEFINE AGENT INSTRUCTIONS ---

factset_analyst_instructions = """
# System Instructions: FactSet Financial Analyst

## Role & Objective
You are an highly capable Financial Analyst powered by Gemini and FactSet. Your primary objective is to process natural language financial queries and retrieve accurate market, company, and quantitative data from the FactSet MCP server.

## Data Access & Tool Usage
You are equipped with direct access to FactSet Terminal Data via the MCP Server.
* **REST/JSON strictly:** You MUST use the native Google Vertex JSON Function Calling framework to invoke tools! 
* **NO PYTHON:** Do NEVER write, inject, or execute Python scripts. You are NOT in a localized coding environment! You MUST bind your arguments natively to the exact JSON schema provided by the tool.
* **Date Handling:** If you need iterative dates for M&A data, do NOT write loops. Make ONE single tool execution with a wide 5-10 year static string span (e.g., startDate="2015-01-01", endDate="2025-01-01").
* **Mandatory Tool Usage:** Whenever a user asks about financial data, stock quotes, market indicators, or economic figures, you MUST natively execute the JSON tools to retrieve accurate data. Never guess or hallucinate financial information.

## Output & Formatting Guidelines
1. **Leverage Tables:** You must use structured Markdown tables whenever possible to present stock prices, comparative metrics, or historical data.
2. **Synthesize & Advise:** Do not simply regurgitate raw tool output. Analyze the data you retrieve from FactSet and synthesize it into clear, strategic, and actionable insights for the user.
3. **Professional Tone:** Always maintain a professional, objectivity-focused, and highly helpful tone suited for a fast-paced financial research environment.
4. **Graceful Error Handling:** If a tool call fails, experiences a timeout, or returns no data, inform the user gracefully without exposing raw technical errors. Suggest alternative ways to assist or offer a revised query.
"""


# --- 4. CREATE THE MAIN AGENT ---

import copy
import asyncio

# --- FactSet Specific Schema Patches ---
def apply_factset_patches():
    print("LOADING FLATENING + TYPING PATCH...")

    def flatten_schema_property(prop_name, prop_def):
        if not isinstance(prop_def, dict):
            return

        complex_keys = ["anyOf", "oneOf", "allOf"]
        found_complex = next((k for k in complex_keys if k in prop_def), None)

        if found_complex:
            options = prop_def[found_complex]
            is_array = False
            
            if isinstance(options, list):
                for opt in options:
                    if isinstance(opt, dict):
                        t = opt.get("type")
                        if t == "array": is_array = True
            
            del prop_def[found_complex]

            if is_array:
                prop_def["type"] = "array"
                if "items" not in prop_def:
                    prop_def["items"] = {"type": "string"}

        # Handle OpenAPI 3.1 arrays of types: e.g. ["string", "null"]
        if "type" in prop_def and isinstance(prop_def["type"], list):
            valid_types = [x for x in prop_def["type"] if x != "null"]
            prop_def["type"] = valid_types[0] if valid_types else "string"

        # Infer foundational types BEFORE enforcing string fallback
        if "type" not in prop_def or not isinstance(prop_def.get("type"), str):
            if "properties" in prop_def:
                prop_def["type"] = "object"
            elif "items" in prop_def:
                prop_def["type"] = "array"
            else:
                prop_def["type"] = "string"

        t = prop_def.get("type")
        if t == "null":
             prop_def["type"] = "string"

        # Unconditionally recurse structures (depth-first traversal into properties/items)
        if "items" in prop_def:
            items = prop_def.get("items")
            if not isinstance(items, dict):
                prop_def["items"] = {"type": "string"}
            flatten_schema_property(f"{prop_name}.items", prop_def["items"])
            
        if "properties" in prop_def:
            for k, v in list(prop_def["properties"].items()):
                if not isinstance(v, dict):
                    prop_def["properties"][k] = {"type": "string", "description": str(v)}
                flatten_schema_property(f"{prop_name}.{k}", prop_def["properties"][k])

    # We patch the MCPToolset to flatten tool input schemas
    from google.adk.tools.mcp_tool import MCPToolset

    # Save original get_tools
    original_get_tools = MCPToolset.get_tools

    async def patched_get_tools(self, readonly_context=None):
        # Dynamically inject the contextually resolved OAuth token right before SDK executes
        from auth_context import sf_token_var
        t = sf_token_var.get()
        if t and t != "MISSING_TOKEN":
            if hasattr(self, "_mcp_session_manager") and hasattr(self._mcp_session_manager, "_connection_params"):
                self._mcp_session_manager._connection_params.headers = {"Authorization": f"Bearer {t}"}
            elif hasattr(self, "connection_params"):
                self.connection_params.headers = {"Authorization": f"Bearer {t}"}
        
        tools = await original_get_tools(self, readonly_context)
        print(f"Patched get_tools called! Found {len(tools)} tools.", flush=True)
        
        for tool in tools:
            # Modern versions of ADK renamed the Pydantic model property
            has_new = hasattr(tool, "_mcp_tool")
            has_old = hasattr(tool, "mcp_tool")
            
            if has_new or has_old: 
                raw_tool = tool._mcp_tool if has_new else tool.mcp_tool
                
                # Extract original schema dictionary natively or via Pydantic model dump
                current_schema = getattr(raw_tool, "inputSchema", {})
                if hasattr(current_schema, "model_dump"): schema_dict = current_schema.model_dump()
                elif hasattr(current_schema, "dict"): schema_dict = current_schema.dict()
                else: schema_dict = current_schema

                if isinstance(schema_dict, dict):
                    import copy
                    new_schema = copy.deepcopy(schema_dict)
                    
                    # Ensure top-level is an object
                    if new_schema.get("type") not in ("object", "OBJECT"):
                        new_schema["type"] = "object"
                        
                    properties = new_schema.get("properties", {})
                    for k, v in list(properties.items()):
                        if not isinstance(v, dict):
                            properties[k] = {"type": "string", "description": str(v)}
                        flatten_schema_property(k, properties[k])
                    
                    # Pydantic v2 "frozen" tools completely ignore `__dict__` hacks during model_dump!
                    # We must natively rebuild the tool class parameters and overwrite the instance attribute!
                    try:
                        raw_tool_data = getattr(raw_tool, "model_dump", getattr(raw_tool, "dict", lambda: raw_tool.__dict__))()
                        raw_tool_data["inputSchema"] = new_schema
                        raw_tool_class = raw_tool.__class__
                        rebuilt_tool = raw_tool_class(**raw_tool_data)
                        
                        if has_new:
                            tool._mcp_tool = rebuilt_tool
                        else:
                            tool.mcp_tool = rebuilt_tool
                    except Exception as e:
                        # Fallback for dynamic types or highly restricted setups
                        print(f"Rebuild failed for {getattr(raw_tool, 'name', 'tool')}: {e}", flush=True)
                        try:
                            raw_tool.inputSchema = new_schema
                        except Exception:
                            raw_tool.__dict__["inputSchema"] = new_schema
        return tools

    MCPToolset.get_tools = patched_get_tools
    print("MCPToolset patched with flattening support for FactSet.")

apply_factset_patches()


class GeminiAgent(LlmAgent):
    """The root FactSet Analyst agent powered by Gemini that delegates to FactSet MCP."""
    
    name: str = "factset_analyst_agent"
    description: str = "An intelligent FactSet Analyst Agent powered by Gemini and FactSet MCP."

    def __init__(self, require_auth: bool = True, token: str = None, **kwargs):
        active_tools = []
        
        # 3. Configure the MCP Toolset natively
        from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPServerParams
        factset_mcp_tools = MCPToolset(
            connection_params=StreamableHTTPServerParams(
                url=FACTSET_MCP_URL,
                headers={}
            )
        )
        active_tools.append(factset_mcp_tools)
        
        # 4. Initialize the ADK LlmAgent
        super().__init__(
            model=MODEL_ID,
            instruction=factset_analyst_instructions,
            tools=active_tools,
            before_agent_callback=before_agent_callback,
            after_model_callback=create_after_model_callback(agent_name="GeminiAgent"),
            **kwargs,
        )
    def create_agent_card(self, agent_url: str) -> "AgentCard":
        return AgentCard(
            name=self.name,
            description=self.description,
            url=agent_url,
            version="1.0.0",
            defaultInputModes=["text/plain"],
            defaultOutputModes=["text/plain"],
            capabilities=AgentCapabilities(streaming=True),
            skills=[
                AgentSkill(
                    id="factset_charting",
                    name="FactSet Charting",
                    description="Interact with FactSet Terminal Data via MCP.",
                    tags=["factset", "finance", "mcp"],
                    examples=[
                        "What is the current stock price of Apple?",
                        "Chart the historical price of Tesla."
                    ]
                )
            ]
        )