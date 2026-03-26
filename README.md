# FactSet Analyst Agent (Google Native A2A)

Welcome to the definitive **FactSet Market Context Protocol (MCP)** integration for Google Cloud! 

This repository allows you to quickly deploy a "Middleman Proxy" (an Agent-to-Agent or A2A framework) onto Google Cloud Run. This proxy directly bridges the **Google Vertex AI Gemini Enterprise API** to the **FactSet Financial Data APIs** without timing out on large financial queries!

## What is this? (Explain like I'm 5) 🧠
Vertex AI is extremely smart, but it doesn't natively speak "FactSet." Furthermore, Enterprise APIs require knowing precisely *who* is asking the question (User Identity). 

This codebase builds an invisible, native helper robot on **Google Cloud Run**. 
When you ask Gemini a question, Vertex securely hands your Identity Token to our helper robot. Our robot turns around, takes your Token, unlocks FactSet's vault, pulls the data, and writes out a beautiful summary sent straight back to your Gemini window! 

Learn more about this "walkie-talkie" architecture here: **[Read the Architecture ELI5 Guide](./docs/architecture.md)**!

## Documentation Directory 📚

We have structured the documentation to guide you from understanding what an A2A proxy does all the way to actively debugging Cloud Run logs:

1. **[Architecture & Diagram (Start Here!)](./docs/architecture.md)**
   A simple visually mapped guide explaining what an A2A Proxy is and how it solves Identity and Timeout issues between FactSet and Google.
2. **[Infrastructure & Deployment](./docs/deployment.md)**
   Walks you step-by-step through customizing your `.env` abstractions and explains how our Bash shell scripts magically connect Vertex AI to Cloud Run endpoints automatically.
3. **[Execution Debugging & Tracing](./docs/debugging.md)**
   Explains rigorously how to observe raw Cloud Run logs from inside your own GCP container, helping you debug missing APIs or 409 Authorization errors.

## Quickstart Deployment 🚀

To rapidly deploy this repository to your own Google Cloud:

1. Duplicate `.env.example` into `.env` and fill all missing secrets (Client IDs).
2. Configure your isolated `AGENT_SERVICE_NAME` naming conventions.
3. Simply execute the automation script on your terminal:

```bash
# Standup the entire Cloud Run proxy natively and register your Agent:
bash ./deploy_and_register.sh
```

**Testing your agent:** Go into your Vertex UI workspace and explicitly ask: _"What were the largest M&A acquisitions executed by TSLA over the last 15 years?"_ The FactSet MCP will trigger automatically!
