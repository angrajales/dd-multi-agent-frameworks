# dd-multi-agent-frameworks
Exploration of different multi agent frameworks


# SetUp

## Prerequisites

- [https://www.python.org/downloads/](Python3.10)
- [https://docs.astral.sh/uv/](uv)
- Preconfigure an Azure OpenAI account (https://azure.microsoft.com/es-es/products/ai-services/openai-service) or a OpenAI api key

## Local setup

```bash
# For this setup, it's highly recommended to use GitBash for windows or bash in linux.
git clone https://github.com/angrajales/dd-multi-agent-frameworks.git
cd dd-multi-agent-frameworks
uv venv
uv sync
mkdir -p .local # or equivalent in windows
# For Azure OpenAI
export AZURE_API_KEY="<YOUR_KEY>" # Or equivalent in windows
export AZURE_API_BASE="<YOUR_ENDPOINT>" # Or equivalent in windows
export AZURE_API_VERSION="<VERSION>" # See https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models?tabs=global-standard%2Cstandard-chat-completions # Or equivalent in windows
cat<<EOF>.local/model_config.yaml
provider: autogen_ext.models.openai.AzureOpenAIChatCompletionClient
config:
    model: gpt-4o
    azure_endpoint: https://{your-custom-endpoint}.openai.azure.com/
    azure_deployment: {your-azure-deployment}
    api_version: {your-api-version}
    api_key: REPLACE_WITH_YOUR_API_KEY
EOF
# For openai
cat<<EOF>.local/model_config.yaml
provider: autogen_ext.models.openai.OpenAIChatCompletionClient
config:
  model: gpt-4o
  api_key: REPLACE_WITH_YOUR_API_KEY
EOF

# Running the application
## Running the autogen example
PYTHONPATH="$(pwd)" python samples/autogen/app_team.py
## Runnin the adk example
PYTHONPATH="$(pwd)" python samples/adk_sample/agent.py
```