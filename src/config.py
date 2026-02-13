"""
Configuration management for UniFi Documenter
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    """Configuration class for UniFi Documenter"""
    
    # Schedule Configuration
    SCHEDULE_FREQUENCY = os.getenv('SCHEDULE_FREQUENCY', 'daily')  # daily, weekly, monthly
    SCHEDULE_TIME = os.getenv('SCHEDULE_TIME', '02:00')  # HH:MM format
    SCHEDULE_DAY = int(os.getenv('SCHEDULE_DAY', '1'))  # Day for weekly/monthly
    TIMEZONE = os.getenv('TIMEZONE', 'UTC')
    
    # UDM Configuration
    UDM_IP = os.getenv('UDM_IP', '192.168.1.1')
    UDM_ROOT_PASSWORD = os.getenv('UDM_ROOT_PASSWORD', '')
    REMOTE_BACKUP_DIR = os.getenv('REMOTE_BACKUP_DIR', '/usr/lib/unifi/data/backup/autobackup')
    
    # AI Configuration
    AI_PROVIDER = os.getenv('AI_PROVIDER', 'openai')  # openai, ollama, azure-openai, custom
    AI_API_URL = os.getenv('AI_API_URL', 'https://api.openai.com/v1')
    AI_API_KEY = os.getenv('AI_API_KEY', '')
    AI_MODEL = os.getenv('AI_MODEL', 'gpt-4o-mini')
    AI_CONTEXT_WINDOW = int(os.getenv('AI_CONTEXT_WINDOW', '128000'))  # Total token window for the model
    AI_MAX_TOKENS = int(os.getenv('AI_MAX_TOKENS', '4000'))  # Max tokens for completion/output
    AI_COOLDOWN_SECONDS = float(os.getenv('AI_COOLDOWN_SECONDS', '0'))  # Delay between LLM calls to reduce VRAM pressure
    
    # Ollama Configuration
    OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3')
    
    # Embedding / RAG Configuration
    EMBEDDING_ENABLED = os.getenv('EMBEDDING_ENABLED', 'true').lower() == 'true'
    EMBEDDING_PROVIDER = os.getenv('EMBEDDING_PROVIDER', 'ollama')  # ollama, openai, custom
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'nomic-embed-text')
    EMBEDDING_CONTEXT_WINDOW = int(os.getenv('EMBEDDING_CONTEXT_WINDOW', '8192'))  # Max token context for embedding model
    QDRANT_URL = os.getenv('QDRANT_URL', 'http://localhost:6333')
    EMBEDDING_COLLECTION = os.getenv('EMBEDDING_COLLECTION', 'unifi_configs')
    EMBEDDING_TOP_K = int(os.getenv('EMBEDDING_TOP_K', '5'))
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT', '')
    AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-01')
    AZURE_OPENAI_DEPLOYMENT = os.getenv('AZURE_OPENAI_DEPLOYMENT', '')
    
    # Output Configuration
    OUTPUT_FORMAT = os.getenv('OUTPUT_FORMAT', 'html')  # html, markdown, json, both
    WEB_ENABLED = os.getenv('WEB_ENABLED', 'true').lower() == 'true'
    WEB_PORT = int(os.getenv('WEB_PORT', '8080'))
    MAX_DOCUMENT_SIZE = int(os.getenv('MAX_DOCUMENT_SIZE', '2000000'))  # 2MB for batch processing
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', '20'))  # Number of documents to process per AI call
    INCLUDE_RAW_DATA = os.getenv('INCLUDE_RAW_DATA', 'false').lower() == 'true'
    
    # Paths
    OUTPUT_DIR = '/app/output'
    CONFIG_DIR = '/app/config'
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration values"""
        required_fields = {
            'UDM_IP': cls.UDM_IP,
            'UDM_ROOT_PASSWORD': cls.UDM_ROOT_PASSWORD,
        }
        
        # Validate AI configuration based on provider (API keys are now optional)
        if cls.AI_PROVIDER == 'azure-openai':
            # Azure still requires endpoint and deployment, but API key is optional
            required_fields.update({
                'AZURE_OPENAI_ENDPOINT': cls.AZURE_OPENAI_ENDPOINT,
                'AZURE_OPENAI_DEPLOYMENT': cls.AZURE_OPENAI_DEPLOYMENT,
            })
        elif cls.AI_PROVIDER == 'ollama':
            required_fields['OLLAMA_URL'] = cls.OLLAMA_URL
        # OpenAI and custom providers don't require any additional fields now
        # API keys are optional for all providers
        
        missing_fields = [field for field, value in required_fields.items() if not value]
        
        if missing_fields:
            raise ValueError(f"Missing required configuration: {', '.join(missing_fields)}")
        
        return True