"""AI-powered tools for MCP agent - optional LLM integration."""

import logging
import asyncio
from typing import Any, Dict, Optional, Callable
import httpx
import json

from app.mcp.config import mcp_settings

logger = logging.getLogger(__name__)


def sanitize_data_for_jinja2(data: Any) -> str:
    """
    Convert data to a string format that won't break Jinja2 templates.

    Avoids issues with LM Studio's Jinja2 template parsing by converting
    structured data to a simple key-value text format.

    Args:
        data: Data to sanitize (dict, list, or simple type)

    Returns:
        Safe string representation
    """
    try:
        # Convert dict/list to simple text format instead of JSON
        # This avoids ALL Jinja2 delimiter conflicts
        if isinstance(data, dict):
            lines = []
            for key, value in list(data.items())[:20]:  # Limit to 20 items
                # Recursively sanitize nested structures
                if isinstance(value, (dict, list)):
                    value_str = str(value)[:100]  # Truncate nested structures
                else:
                    value_str = str(value)
                lines.append(f"  {key}: {value_str}")
            result = "\n".join(lines)
        elif isinstance(data, list):
            result = "\n".join(f"  - {str(item)[:100]}" for item in data[:20])
        else:
            result = str(data)[:1000]

        # Final safety check - remove any remaining template-like patterns
        result = result.replace("{%", "").replace("%}", "")
        result = result.replace("{{", "").replace("}}", "")
        result = result.replace("{#", "").replace("#}", "")

        return result if result else "(no data)"
    except Exception as e:
        logger.warning(f"Failed to sanitize data: {e}")
        return "(data unavailable)"


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

        # Retry configuration
        self.max_retries = 3
        self.base_delay = 1.0  # seconds

    async def _retry_with_backoff(self, func: Callable, *args, **kwargs) -> Any:
        """
        Retry a function with exponential backoff for rate limit errors.

        Args:
            func: Async function to retry
            *args, **kwargs: Arguments to pass to the function

        Returns:
            Function result

        Raises:
            Last exception if all retries fail
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except httpx.HTTPStatusError as e:
                last_exception = e

                # Check if it's a rate limit error (429)
                if e.response.status_code == 429:
                    if attempt < self.max_retries - 1:
                        # Calculate exponential backoff delay
                        delay = self.base_delay * (2 ** attempt)

                        # Add jitter to avoid thundering herd
                        import random
                        jitter = random.uniform(0, 0.1 * delay)
                        total_delay = delay + jitter

                        logger.warning(
                            f"Rate limit (429) encountered on attempt {attempt + 1}/{self.max_retries}. "
                            f"Retrying in {total_delay:.2f}s..."
                        )
                        await asyncio.sleep(total_delay)
                        continue
                    else:
                        logger.error(f"Rate limit (429) - max retries ({self.max_retries}) exceeded")
                        raise
                else:
                    # Non-429 error, raise immediately
                    raise
            except Exception as e:
                # Other exceptions, raise immediately
                raise

        # If we get here, all retries failed
        if last_exception:
            raise last_exception
        raise RuntimeError("Retry loop completed without success or exception")

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

        # Sanitize data to avoid Jinja2 template parsing issues
        safe_data = sanitize_data_for_jinja2(data)

        prompt = f"""
        Generate a professional summary report from this data:

        {safe_data}

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

        # Sanitize data to avoid Jinja2 template parsing issues
        safe_context = sanitize_data_for_jinja2(context)

        prompt = f"""
        Based on the current project management context:

        {safe_context}

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

    async def _call_llm_stream(self, prompt: str):
        """Call the configured LLM with streaming support.

        Args:
            prompt: The prompt to send

        Yields:
            String chunks as they are generated
        """
        if self.provider == "openai":
            async for chunk in self._call_openai_stream(prompt):
                yield chunk
        elif self.provider == "anthropic":
            async for chunk in self._call_anthropic_stream(prompt):
                yield chunk
        elif self.provider == "azure":
            async for chunk in self._call_azure_stream(prompt):
                yield chunk
        elif self.provider == "local":
            async for chunk in self._call_local_stream(prompt):
                yield chunk
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API with retry logic."""
        return await self._retry_with_backoff(self._do_openai_call, prompt)

    async def _do_openai_call(self, prompt: str) -> str:
        """Internal method to call OpenAI API (used by retry logic)."""
        # Use longer timeout for local LLMs like LM Studio
        timeout = httpx.Timeout(120.0, connect=10.0)

        # Check if we should use completion API (for LM Studio Jinja2 issues)
        use_completion = mcp_settings.use_completion_api

        if use_completion:
            # Use /completions endpoint (bypasses chat template)
            endpoint = f"{self.base_url}/completions"
            system_msg = "You are an AI assistant for a project management system. Answer in Chinese (中文).\n\n"
            request_data = {
                "model": self.model,
                "prompt": system_msg + prompt,
                "temperature": 0.7,
                "max_tokens": 2000
            }
        else:
            # Use /chat/completions endpoint (default)
            endpoint = f"{self.base_url}/chat/completions"
            request_data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are an AI assistant for a project management system. Answer in Chinese (中文)."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 2000
            }

        # Log detailed request information
        logger.info(f"=== AI Request (Non-Streaming) ===")
        logger.info(f"URL: {endpoint}")
        logger.info(f"Model: {self.model}")
        logger.info(f"API Type: {'Completion' if use_completion else 'Chat'}")
        logger.info(f"Request body:")
        logger.info(json.dumps(request_data, indent=2, ensure_ascii=False))
        logger.info(f"=== End Request ===")

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                endpoint,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=request_data
            )
            response.raise_for_status()
            data = response.json()

            # Extract content based on API type
            if use_completion:
                content = data["choices"][0]["text"]
            else:
                content = data["choices"][0]["message"]["content"]

            logger.info(f"=== AI Response ===")
            logger.info(f"Status: {response.status_code}")
            logger.info(f"Content: {content[:200]}...")
            logger.info(f"=== End Response ===")

            return content
    
    async def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic Claude API."""
        timeout = httpx.Timeout(120.0, connect=10.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
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
                    "max_tokens": 2000
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]
    
    async def _call_azure(self, prompt: str) -> str:
        """Call Azure OpenAI Service."""
        timeout = httpx.Timeout(120.0, connect=10.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
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
                    "max_tokens": 2000
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    async def _call_local(self, prompt: str) -> str:
        """Call local LLM (Ollama, LlamaCpp, etc.)."""
        timeout = httpx.Timeout(120.0, connect=10.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            # Ollama API format
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")

    # ================== Streaming Methods ==================

    async def _call_openai_stream(self, prompt: str):
        """Call OpenAI API with streaming (works with LM Studio too)."""
        timeout = httpx.Timeout(120.0, connect=10.0)

        # Check if we should use completion API (for LM Studio Jinja2 issues)
        use_completion = mcp_settings.use_completion_api

        if use_completion:
            # Use /completions endpoint (bypasses chat template)
            endpoint = f"{self.base_url}/completions"
            system_msg = "You are an AI assistant for a project management system. Answer in Chinese (中文).\n\n"
            request_data = {
                "model": self.model,
                "prompt": system_msg + prompt,
                "temperature": 0.7,
                "max_tokens": 2000,
                "stream": True
            }
        else:
            # Use /chat/completions endpoint (default)
            endpoint = f"{self.base_url}/chat/completions"
            request_data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are an AI assistant for a project management system. Answer in Chinese (中文)."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 2000,
                "stream": True
            }

        # Log detailed request information
        logger.info(f"=== AI Request (Streaming) ===")
        logger.info(f"URL: {endpoint}")
        logger.info(f"Model: {self.model}")
        logger.info(f"API Type: {'Completion' if use_completion else 'Chat'}")
        logger.info(f"Request body:")
        logger.info(json.dumps(request_data, indent=2, ensure_ascii=False))
        logger.info(f"=== End Request ===")

        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST",
                endpoint,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=request_data
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                if use_completion:
                                    # Completion API format
                                    content = data["choices"][0].get("text", "")
                                else:
                                    # Chat API format
                                    delta = data["choices"][0].get("delta", {})
                                    content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue

    async def _call_anthropic_stream(self, prompt: str):
        """Call Anthropic Claude API with streaming."""
        timeout = httpx.Timeout(120.0, connect=10.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 2000,
                    "stream": True
                }
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        try:
                            data = json.loads(data_str)
                            if data.get("type") == "content_block_delta":
                                content = data.get("delta", {}).get("text", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue

    async def _call_azure_stream(self, prompt: str):
        """Call Azure OpenAI with streaming."""
        timeout = httpx.Timeout(120.0, connect=10.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST",
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
                    "max_tokens": 2000,
                    "stream": True
                }
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue

    async def _call_local_stream(self, prompt: str):
        """Call local LLM with streaming (Ollama)."""
        timeout = httpx.Timeout(120.0, connect=10.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": True
                }
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    try:
                        data = json.loads(line)
                        content = data.get("response", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue


# Singleton instance
ai_assistant = AIAssistant()