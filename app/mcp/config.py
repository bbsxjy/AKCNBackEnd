"""MCP Agent configuration settings."""

import os
from typing import Optional
from pydantic import BaseSettings, Field


class MCPSettings(BaseSettings):
    """MCP Agent configuration.
    
    These settings are for when YOUR app needs to call OTHER AI services.
    The MCP server itself doesn't need API keys - it's called BY AI clients.
    """
    
    # OpenAI Configuration (if you want the MCP agent to call OpenAI)
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4-turbo-preview", env="OPENAI_MODEL")
    openai_base_url: Optional[str] = Field(None, env="OPENAI_BASE_URL")
    
    # Anthropic Configuration (if you want the MCP agent to call Claude API)
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    anthropic_model: str = Field("claude-3-opus-20240229", env="ANTHROPIC_MODEL")
    
    # Azure OpenAI Configuration
    azure_openai_api_key: Optional[str] = Field(None, env="AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: Optional[str] = Field(None, env="AZURE_OPENAI_ENDPOINT")
    azure_openai_deployment: Optional[str] = Field(None, env="AZURE_OPENAI_DEPLOYMENT")
    azure_openai_api_version: str = Field("2024-02-15-preview", env="AZURE_OPENAI_API_VERSION")
    
    # Local LLM Configuration (Ollama, LlamaCpp, etc.)
    local_llm_base_url: Optional[str] = Field("http://localhost:11434", env="LOCAL_LLM_BASE_URL")
    local_llm_model: str = Field("llama2", env="LOCAL_LLM_MODEL")
    
    # MCP Server Settings
    mcp_server_name: str = Field("AKCN MCP Agent", env="MCP_SERVER_NAME")
    mcp_server_version: str = Field("1.0.0", env="MCP_SERVER_VERSION")
    mcp_enable_ai_tools: bool = Field(False, env="MCP_ENABLE_AI_TOOLS")
    
    # Security
    mcp_allowed_operations: list = Field(
        default_factory=lambda: ["read", "write", "execute"],
        env="MCP_ALLOWED_OPERATIONS"
    )
    mcp_max_query_limit: int = Field(1000, env="MCP_MAX_QUERY_LIMIT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


mcp_settings = MCPSettings()