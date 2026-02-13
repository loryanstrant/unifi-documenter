"""
AI integration module for analyzing UniFi backup data
"""
import json
import logging
import requests
from typing import Dict, List, Optional, Union
from abc import ABC, abstractmethod

from .config import Config

logger = logging.getLogger('unifi_documenter')

class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    @abstractmethod
    def generate_completion(self, prompt: str, max_tokens: int = 4000) -> Optional[str]:
        """Generate a completion from the AI provider"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the AI provider is available"""
        pass

class OpenAIProvider(AIProvider):
    """OpenAI API provider"""
    
    def __init__(self, config: Config):
        self.config = config
        self.api_key = config.AI_API_KEY if config.AI_API_KEY else None  # Convert empty string to None
        self.api_url = config.AI_API_URL
        self.model = config.AI_MODEL
        
        # Import openai here to avoid issues if not installed
        try:
            import openai
            # OpenAI client accepts None for api_key
            self.client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.api_url
            )
        except ImportError as e:
            logger.error(f"OpenAI package not installed: {str(e)}")
            logger.error("Install with: pip install openai")
            self.client = None
    
    def generate_completion(self, prompt: str, max_tokens: int = 4000) -> Optional[str]:
        """Generate completion using OpenAI API"""
        if not self.client:
            return None
            
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert network administrator and documentation specialist. Analyze the provided UniFi configuration data and create clear, comprehensive documentation."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.1
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            logger.error(f"API URL: {self.api_url}")
            logger.error(f"Model: {self.model}")
            logger.error(f"Error type: {type(e).__name__}")
            return None
    
    def is_available(self) -> bool:
        """Check if OpenAI provider is available"""
        # API key is now optional, only check if client is initialized
        available = self.client is not None
        if not available:
            logger.debug("OpenAI provider unavailable: Client not initialized")
        return available

class AzureOpenAIProvider(AIProvider):
    """Azure OpenAI provider"""
    
    def __init__(self, config: Config):
        self.config = config
        self.api_key = config.AI_API_KEY if config.AI_API_KEY else None  # Convert empty string to None
        self.endpoint = config.AZURE_OPENAI_ENDPOINT
        self.deployment = config.AZURE_OPENAI_DEPLOYMENT
        self.api_version = config.AZURE_OPENAI_API_VERSION
        
        try:
            import openai
            # Azure OpenAI client accepts None for api_key
            self.client = openai.AzureOpenAI(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.endpoint
            )
        except ImportError as e:
            logger.error(f"OpenAI package not installed: {str(e)}")
            logger.error("Install with: pip install openai")
            self.client = None
    
    def generate_completion(self, prompt: str, max_tokens: int = 4000) -> Optional[str]:
        """Generate completion using Azure OpenAI API"""
        if not self.client:
            return None
            
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": "You are an expert network administrator and documentation specialist. Analyze the provided UniFi configuration data and create clear, comprehensive documentation."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.1
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Azure OpenAI API error: {str(e)}")
            logger.error(f"Azure Endpoint: {self.endpoint}")
            logger.error(f"Deployment: {self.deployment}")
            logger.error(f"API Version: {self.api_version}")
            logger.error(f"Error type: {type(e).__name__}")
            return None
    
    def is_available(self) -> bool:
        """Check if Azure OpenAI provider is available"""
        # API key is now optional, only check client, endpoint, and deployment
        available = self.client is not None and all([self.endpoint, self.deployment])
        if not available:
            if self.client is None:
                logger.debug("Azure OpenAI provider unavailable: Client not initialized")
            elif not self.endpoint:
                logger.debug("Azure OpenAI provider unavailable: Endpoint not configured")
            elif not self.deployment:
                logger.debug("Azure OpenAI provider unavailable: Deployment not configured")
        return available

class OllamaProvider(AIProvider):
    """Ollama local AI provider"""
    
    def __init__(self, config: Config):
        self.config = config
        self.url = config.OLLAMA_URL
        self.model = config.OLLAMA_MODEL
    
    def generate_completion(self, prompt: str, max_tokens: int = 4000) -> Optional[str]:
        """Generate completion using Ollama API"""
        try:
            response = requests.post(
                f"{self.url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": f"You are an expert network administrator and documentation specialist. Analyze the provided UniFi configuration data and create clear, comprehensive documentation.\n\nUser: {prompt}",
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.1
                    }
                },
                timeout=300  # 5 minute timeout for generation
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '')
            else:
                logger.error(f"Ollama API error - Status: {response.status_code}")
                logger.error(f"Ollama URL: {self.url}/api/generate")
                logger.error(f"Model: {self.model}")
                logger.error(f"Response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Ollama API error: {str(e)}")
            logger.error(f"Ollama URL: {self.url}")
            logger.error(f"Model: {self.model}")
            logger.error(f"Error type: {type(e).__name__}")
            return None
    
    def is_available(self) -> bool:
        """Check if Ollama provider is available"""
        try:
            response = requests.get(f"{self.url}/api/tags", timeout=10)
            if response.status_code == 200:
                return True
            else:
                logger.debug(f"Ollama provider unavailable: HTTP {response.status_code} from {self.url}/api/tags")
                return False
        except requests.exceptions.ConnectionError as e:
            logger.debug(f"Ollama provider unavailable: Connection error to {self.url} - {str(e)}")
            return False
        except requests.exceptions.Timeout:
            logger.debug(f"Ollama provider unavailable: Timeout connecting to {self.url}")
            return False
        except Exception as e:
            logger.debug(f"Ollama provider unavailable: {type(e).__name__} - {str(e)}")
            return False

class CustomProvider(AIProvider):
    """Custom AI provider for other OpenAI-compatible APIs"""
    
    def __init__(self, config: Config):
        self.config = config
        self.api_key = config.AI_API_KEY if config.AI_API_KEY else None  # Convert empty string to None
        self.api_url = config.AI_API_URL
        self.model = config.AI_MODEL
    
    def generate_completion(self, prompt: str, max_tokens: int = 4000) -> Optional[str]:
        """Generate completion using custom OpenAI-compatible API"""
        try:
            headers = {
                "Content-Type": "application/json"
            }
            
            # Only add Authorization header if API key is provided
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are an expert network administrator and documentation specialist. Analyze the provided UniFi configuration data and create clear, comprehensive documentation."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.1
            }
            
            response = requests.post(
                f"{self.api_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=300
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                logger.error(f"Custom API error - Status: {response.status_code}")
                logger.error(f"API URL: {self.api_url}/chat/completions")
                logger.error(f"Model: {self.model}")
                logger.error(f"Response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Custom API error: {str(e)}")
            logger.error(f"API URL: {self.api_url}")
            logger.error(f"Model: {self.model}")
            logger.error(f"Error type: {type(e).__name__}")
            return None
    
    def is_available(self) -> bool:
        """Check if custom provider is available"""
        # API key is now optional, only check if URL is configured
        available = bool(self.api_url)
        if not available:
            logger.debug("Custom provider unavailable: API URL not configured")
        return available

class AIManager:
    """Manages AI providers and handles AI-related operations"""
    
    def __init__(self, config: Config):
        self.config = config
        self.provider = self._create_provider()
    
    def _create_provider(self) -> Optional[AIProvider]:
        """Create the appropriate AI provider based on configuration"""
        provider_type = self.config.AI_PROVIDER.lower()
        
        providers = {
            'openai': OpenAIProvider,
            'azure-openai': AzureOpenAIProvider,
            'ollama': OllamaProvider,
            'custom': CustomProvider
        }
        
        provider_class = providers.get(provider_type)
        if not provider_class:
            logger.error(f"Unknown AI provider: {provider_type}")
            logger.error(f"Valid providers: {', '.join(providers.keys())}")
            logger.error(f"Check AI_PROVIDER environment variable")
            return None
        
        provider = provider_class(self.config)
        
        if not provider.is_available():
            logger.error(f"AI provider '{provider_type}' is not available")
            logger.error(f"Configuration check failed - review the debug logs above for specific missing configuration")
            
            # Provide specific configuration hints based on provider type
            if provider_type == 'openai':
                logger.error(f"Required: AI_API_URL (current: {self.config.AI_API_URL}), AI_MODEL (current: {self.config.AI_MODEL})")
                logger.error(f"Optional: AI_API_KEY (configured: {'Yes' if self.config.AI_API_KEY else 'No'})")
            elif provider_type == 'azure-openai':
                logger.error(f"Required: AZURE_OPENAI_ENDPOINT (current: {self.config.AZURE_OPENAI_ENDPOINT}), AZURE_OPENAI_DEPLOYMENT (current: {self.config.AZURE_OPENAI_DEPLOYMENT})")
                logger.error(f"Optional: AI_API_KEY (configured: {'Yes' if self.config.AI_API_KEY else 'No'})")
            elif provider_type == 'ollama':
                logger.error(f"Required: OLLAMA_URL (current: {self.config.OLLAMA_URL}), OLLAMA_MODEL (current: {self.config.OLLAMA_MODEL})")
                logger.error(f"Ensure Ollama is running and accessible at the configured URL")
            elif provider_type == 'custom':
                logger.error(f"Required: AI_API_URL (current: {self.config.AI_API_URL}), AI_MODEL (current: {self.config.AI_MODEL})")
                logger.error(f"Optional: AI_API_KEY (configured: {'Yes' if self.config.AI_API_KEY else 'No'})")
                logger.error(f"Ensure the custom API endpoint is OpenAI-compatible and accessible")
            
            return None
        
        logger.info(f"Initialized AI provider: {provider_type}")
        return provider
    
    def is_available(self) -> bool:
        """Check if AI manager is ready to use"""
        available = self.provider is not None and self.provider.is_available()
        if not available:
            if self.provider is None:
                logger.debug("AI manager unavailable: No provider initialized")
            elif not self.provider.is_available():
                logger.debug(f"AI manager unavailable: Provider '{self.config.AI_PROVIDER}' is not available")
        return available
    
    def generate_documentation(self, data: Union[str, Dict], context: str = "") -> Optional[str]:
        """Generate documentation for the provided data"""
        if not self.is_available():
            logger.error("AI provider not available")
            return None
        
        try:
            # Convert data to string if it's a dict
            if isinstance(data, dict):
                data_str = json.dumps(data, indent=2)
            else:
                data_str = str(data)
            
            # Calculate the token budget for input data.
            # Rough estimate: 1 token ≈ 4 characters.
            chars_per_token = 4
            max_completion_tokens = self.config.AI_MAX_TOKENS
            context_window = self.config.AI_CONTEXT_WINDOW

            # Reserve tokens for: system message (~37 tok) + prompt
            # template (~100 tok) + context string + completion output.
            system_msg_tokens = 40
            template_tokens = 120
            context_tokens = len(context) // chars_per_token + 1
            overhead_tokens = system_msg_tokens + template_tokens + context_tokens
            available_data_tokens = context_window - max_completion_tokens - overhead_tokens
            if available_data_tokens < 0:
                available_data_tokens = 0
            max_data_chars = available_data_tokens * chars_per_token

            # Also honor the legacy MAX_DOCUMENT_SIZE setting
            max_data_chars = min(max_data_chars, self.config.MAX_DOCUMENT_SIZE)

            if len(data_str) > max_data_chars:
                data_str = data_str[:max_data_chars] + "\n... (truncated)"
                logger.warning(
                    f"Data truncated to {max_data_chars} characters "
                    f"(context_window={context_window}, max_tokens={max_completion_tokens})"
                )
            
            prompt = self._create_documentation_prompt(data_str, context)
            return self.provider.generate_completion(prompt, max_tokens=max_completion_tokens)
            
        except Exception as e:
            logger.error(f"Documentation generation failed: {str(e)}")
            return None
    
    def _create_documentation_prompt(self, data: str, context: str) -> str:
        """Create a comprehensive prompt for documentation generation"""
        return f"""
Please analyze the following UniFi configuration data and create comprehensive markdown documentation. 
The documentation should be suitable for both human readers and RAG (Retrieval-Augmented Generation) systems.

Context: {context if context else "General UniFi configuration analysis"}

Requirements:
1. Create clear, structured markdown with appropriate headers
2. Explain the purpose and function of each configuration element
3. Include security implications where relevant
4. Use tables for structured data when appropriate
5. Add troubleshooting tips if applicable
6. Make it searchable with good keywords and descriptions
7. Focus on practical information that would be useful for network administration

Configuration Data:
```json
{data}
```

Please provide the analysis in markdown format:
"""

    def analyze_configuration_type(self, data: Dict) -> str:
        """Analyze what type of UniFi configuration this data represents"""
        if not self.is_available():
            return "Unknown"
        
        try:
            # Limit the data snippet to fit within the context window.
            chars_per_token = 4
            # This is a lightweight call — reserve only 50 tokens for output.
            type_max_tokens = 50
            overhead_tokens = 80  # system + prompt template
            available_tokens = self.config.AI_CONTEXT_WINDOW - type_max_tokens - overhead_tokens
            max_chars = max(available_tokens * chars_per_token, 200)
            data_snippet = json.dumps(data, indent=2)[:max_chars]

            prompt = f"""
Analyze this UniFi configuration data and identify what type of configuration it represents.
Respond with just the category name (e.g., "Access Point", "Network Settings", "Security Policy", "User Management", etc.)

Data: {data_snippet}
"""
            result = self.provider.generate_completion(prompt, max_tokens=type_max_tokens)
            return result.strip() if result else "Unknown"
            
        except Exception as e:
            logger.error(f"Configuration type analysis failed: {str(e)}")
            return "Unknown"