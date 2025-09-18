# Example configurations for different use cases

## Minimal OpenAI Setup
```bash
UDM_IP=192.168.1.1
UDM_ROOT_PASSWORD=your_password
AI_PROVIDER=openai
AI_API_KEY=sk-your-openai-key
SCHEDULE_FREQUENCY=daily
SCHEDULE_TIME=02:00
```

## Weekly Documentation with Azure OpenAI
```bash
UDM_IP=192.168.1.1
UDM_ROOT_PASSWORD=your_password
AI_PROVIDER=azure-openai
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4
AI_API_KEY=your_azure_key
SCHEDULE_FREQUENCY=weekly
SCHEDULE_DAY=1
SCHEDULE_TIME=03:00
TIMEZONE=America/New_York
```

## Local Processing with Ollama
```bash
UDM_IP=192.168.1.1
UDM_ROOT_PASSWORD=your_password
AI_PROVIDER=ollama
OLLAMA_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama3
SCHEDULE_FREQUENCY=daily
SCHEDULE_TIME=01:00
OUTPUT_FORMAT=both
INCLUDE_RAW_DATA=true
```

## Monthly Comprehensive Analysis
```bash
UDM_IP=192.168.1.1
UDM_ROOT_PASSWORD=your_password
AI_PROVIDER=openai
AI_API_KEY=sk-your-openai-key
AI_MODEL=gpt-4-turbo-preview
SCHEDULE_FREQUENCY=monthly
SCHEDULE_DAY=1
SCHEDULE_TIME=01:00
MAX_DOCUMENT_SIZE=100000
OUTPUT_FORMAT=both
INCLUDE_RAW_DATA=true
```

## Development/Testing Setup
```bash
UDM_IP=192.168.1.1
UDM_ROOT_PASSWORD=your_password
AI_PROVIDER=openai
AI_API_KEY=sk-your-openai-key
RUN_MODE=once
OUTPUT_FORMAT=markdown
```