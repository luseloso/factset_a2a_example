#!/bin/bash
set -e

# Load environment variables
if [ -f .env ]; then
  set -a
  source .env
  set +a
else
  echo ".env file not found!"
  exit 1
fi

PROJECT_ID=${GOOGLE_CLOUD_PROJECT}
REGION=${GOOGLE_CLOUD_LOCATION}
PROJECT_NUMBER=${GOOGLE_CLOUD_PROJECT_NUMBER}
SERVICE_NAME=${AGENT_SERVICE_NAME:-"factset-native-agent"}
ENGINE_ID=${GEMINI_ENTERPRISE_APP_ID}
AUTH_ID=${AGENT_AUTH_ID:-"factset-oauth-native-v1"}
NAME_DESC=${AGENT_DISPLAY_NAME:-"FactSet Agent v7"}
echo "====================================================="
echo "1. Deploying FactSet Agent to Cloud Run..."
echo "====================================================="
gcloud run deploy "$SERVICE_NAME" \
  --source . \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --allow-unauthenticated \
  --quiet || { echo "Deployment failed on Cloud Run step."; exit 1; }

# Get the service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --project="$PROJECT_ID" --region="$REGION" --format='value(status.url)')
echo "Service URL obtained: $SERVICE_URL"

echo "====================================================="
echo "2. Registering Server-Side OAuth2 Authorization..."
echo "====================================================="
OAUTH_AUTH_URI="https://auth.factset.com/as/authorization.oauth2?response_type=code&client_id=${CLIENT_ID}&redirect_uri=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Foauth-redirect&scope=mcp"

# Register the authorization resource
curl -s -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  "https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/global/authorizations?authorizationId=${AUTH_ID}" \
  -d '{
    "name": "projects/'"${PROJECT_ID}"'/locations/global/authorizations/'"${AUTH_ID}"'",
    "serverSideOauth2": {
      "clientId": "'"${CLIENT_ID}"'",
      "clientSecret": "'"${CLIENT_SECRET}"'",
      "authorizationUri": "'"${OAUTH_AUTH_URI}"'",
      "tokenUri": "'"${TOKEN_URI}"'"
    }
  }' > /dev/null || true
echo && echo "Authorization registered."

echo "====================================================="
echo "3. Registering Agent to Gemini Enterprise..."
echo "====================================================="

AUTH_RESOURCE_PATH="projects/${PROJECT_NUMBER}/locations/global/authorizations/${AUTH_ID}"

# Construct JSON Payload using jq to safely encode variables
PAYLOAD=$(jq -n \
  --arg displayName "$NAME_DESC" \
  --arg description "FactSet Financial Assistant" \
  --arg url "$SERVICE_URL" \
  --arg authId "$AUTH_RESOURCE_PATH" \
  '{
    "displayName": $displayName,
    "description": $description,
    "a2aAgentDefinition": {
      "jsonAgentCard": ({
        "provider": {
          "url": $url,
          "organization": "FactSet"
        },
        "url": $url,
        "name": $displayName,
        "description": $description,
        "version": "1.0.0",
        "protocolVersion": "0.3.0",
        "capabilities": {},
        "skills": [
          {
            "id": "chat",
            "name": "Chat Skill",
            "description": "Chat with the FactSet agent to retrieve financial data.",
            "tags": ["chat"],
            "examples": ["What is the current stock price of Apple?"]
          }
        ],
        "defaultInputModes": ["text"],
        "defaultOutputModes": ["text"],
        "authentication": {
          "schemes": "Authorization",
          "credentials": "Bearer <TOKEN>"
        }
      } | tojson)
    },
    "authorizationConfig": {
      "agentAuthorization": $authId
    }
  }')

curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  -H "x-goog-user-project: ${PROJECT_ID}" \
  "https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_NUMBER}/locations/global/collections/default_collection/engines/${ENGINE_ID}/assistants/default_assistant/agents" \
  -d "$PAYLOAD"

echo && echo "Agent fully registered to Agentspace!"
