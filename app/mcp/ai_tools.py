"""AI-powered tools for MCP agent - optional LLM integration."""

import logging
from typing import Any, Dict, Optional
import httpx
import json

from app.mcp.config import mcp_settings

logger = logging.getLogger(__name__)


class AIAssistant:
    """AI assistant for enhanced MCP operations."""
    
    def __init__(self):
        """Initialize AI assistant with configured LLM."""
        self.enabled = mcp_settings.mcp_enable_ai_tools
        
        # Determine which LLM to use
        if mcp_settings.openai_api_key:
            self.provider = "openai"
            self.api_key = mcp_settings.openai_api_key
            self.model = mcp_settings.openai_model
            self.base_url = mcp_settings.openai_base_url or "https://api.openai.com/v1"
        elif mcp_settings.anthropic_api_key:
            self.provider = "anthropic"
            self.api_key = mcp_settings.anthropic_api_key
            self.model = mcp_settings.anthropic_model
            self.base_url = "https://api.anthropic.com/v1"
        elif mcp_settings.azure_openai_api_key:
            self.provider = "azure"
            self.api_key = mcp_settings.azure_openai_api_key
            self.endpoint = mcp_settings.azure_openai_endpoint
            self.deployment = mcp_settings.azure_openai_deployment
        else:
            self.provider = "local"
            self.base_url = mcp_settings.local_llm_base_url
            self.model = mcp_settings.local_llm_model
    
    async def analyze_query(self, query: str) -> Dict[str, Any]:
        """Use AI to analyze and optimize a database query.
        
        Args:
            query: SQL query to analyze
            
        Returns:
            Analysis results with suggestions
        """
        if not self.enabled:
            return {"error": "AI tools are disabled"}
        
        prompt = f"""
        Analyze this SQL query and provide optimization suggestions:
        
        {query}
        
        Provide:
        1. Query explanation
        2. Potential performance issues
        3. Optimization suggestions
        4. Security concerns
        """
        
        try:
            response = await self._call_llm(prompt)
            return {
                "success": True,
                "analysis": response,
                "original_query": query
            }
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return {"error": str(e)}
    
    async def generate_report(self, data: Dict[str, Any]) -> str:
        """Use AI to generate a natural language report from data.
        
        Args:
            data: Structured data to convert to report
            
        Returns:
            Natural language report
        """
        if not self.enabled:
            return "AI report generation is disabled"
        
        prompt = f"""
        Generate a professional summary report from this data:
        
        {json.dumps(data, indent=2, default=str)}
        
        The report should be:
        1. Clear and concise
        2. Highlight key metrics
        3. Identify trends or issues
        4. Provide actionable insights
        """
        
        try:
            return await self._call_llm(prompt)
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return f"Failed to generate report: {e}"
    
    async def suggest_next_actions(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI to suggest next actions based on current context.
        
        Args:
            context: Current system state and recent operations
            
        Returns:
            Suggested actions with reasoning
        """
        if not self.enabled:
            return {"suggestions": []}
        
        prompt = f"""
        Based on the current project management context:
        
        {json.dumps(context, indent=2, default=str)}
        
        Suggest the next 3-5 most important actions to take.
        For each action, provide:
        1. Action description
        2. Why it's important
        3. Expected impact
        4. MCP tool to use
        """
        
        try:
            response = await self._call_llm(prompt)
            return {
                "success": True,
                "suggestions": response
            }
        except Exception as e:
            logger.error(f"Action suggestion failed: {e}")
            return {"error": str(e)}
    
    async def _call_llm(self, prompt: str) -> str:
        """Call the configured LLM with a prompt.
        
        Args:
            prompt: The prompt to send
            
        Returns:
            LLM response text
        """
        if self.provider == "openai":
            return await self._call_openai(prompt)
        elif self.provider == "anthropic":
            return await self._call_anthropic(prompt)
        elif self.provider == "azure":
            return await self._call_azure(prompt)
        elif self.provider == "local":
            return await self._call_local(prompt)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are an AI assistant for a project management system."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    async def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic Claude API."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 1000
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]
    
    async def _call_azure(self, prompt: str) -> str:
        """Call Azure OpenAI Service."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.endpoint}/openai/deployments/{self.deployment}/chat/completions?api-version={mcp_settings.azure_openai_api_version}",
                headers={
                    "api-key": self.api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "messages": [
                        {"role": "system", "content": "You are an AI assistant for a project management system."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    async def _call_local(self, prompt: str) -> str:
        """Call local LLM (Ollama, LlamaCpp, etc.)."""
        async with httpx.AsyncClient() as client:
            # Ollama API format
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")


# Singleton instance
ai_assistant = AIAssistant()