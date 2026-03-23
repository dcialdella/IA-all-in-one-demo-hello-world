"""
Ollama Tools Hook - Tools that interact with Ollama

Provides:
- Code generation
- Text completion
- Embeddings
- Model information
- Chat with specific context
"""

import json
import os
from typing import Optional, List, Dict, Any
try:
    import httpx
except ImportError:
    import subprocess
    subprocess.check_call([subprocess.sys.executable, "-m", "pip", "install", "httpx", "-q"])
    import httpx


OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")


class OllamaToolsHook:
    """Tools that interact with Ollama LLM."""
    
    def __init__(self):
        self.default_model = "llama3.1"
    
    def run(self, tool: str = None, **kwargs) -> dict:
        """
        Execute an Ollama tool.
        
        Args:
            tool: "generate", "chat", "embeddings", "models", "pull", "info"
        
        Returns:
            dict with result
        """
        tools = {
            "generate": self.generate,
            "chat": self.chat,
            "embeddings": self.embeddings,
            "models": self.list_models,
            "pull": self.pull_model,
            "info": self.model_info,
            "tags": self.list_models,
        }
        
        if tool is None:
            return {"available_tools": list(tools.keys())}
        
        if tool not in tools:
            return {"error": f"Unknown tool: {tool}", "available": list(tools.keys())}
        
        return tools[tool](**kwargs)
    
    def generate(self, prompt: str, model: str = None, system: str = None, **kwargs) -> dict:
        """
        Generate text using Ollama.
        
        Args:
            prompt: Input prompt
            model: Model name (default: llama3.1)
            system: System prompt
            **kwargs: Additional options (temperature, max_tokens, etc.)
        
        Returns:
            dict with generated text
        """
        model = model or self.default_model
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
        
        if system:
            payload["system"] = system
        
        payload.update({k: v for k, v in kwargs.items() if v is not None})
        
        try:
            response = httpx.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=120)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "model": model,
                    "prompt": prompt,
                    "response": data.get("response", ""),
                    "context": data.get("context"),
                    "total_duration": data.get("total_duration"),
                    "eval_count": data.get("eval_count"),
                }
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        except httpx.ConnectError:
            return {"error": "Cannot connect to Ollama. Make sure Ollama is running."}
        except Exception as e:
            return {"error": str(e)}
    
    def chat(self, messages: List[Dict[str, str]], model: str = None, **kwargs) -> dict:
        """
        Chat with Ollama using message format.
        
        Args:
            messages: List of message dicts with "role" and "content"
            model: Model name
            **kwargs: Additional options
        
        Returns:
            dict with response
        """
        model = model or self.default_model
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
        }
        
        payload.update({k: v for k, v in kwargs.items() if v is not None})
        
        try:
            response = httpx.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=120)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "model": model,
                    "message": data.get("message", {}),
                    "done": data.get("done"),
                }
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"error": str(e)}
    
    def embeddings(self, prompt: str, model: str = "nomic-embed-text:latest", **kwargs) -> dict:
        """
        Generate embeddings for a prompt.
        
        Args:
            prompt: Text to embed
            model: Embedding model
        
        Returns:
            dict with embeddings
        """
        payload = {
            "model": model,
            "prompt": prompt,
        }
        
        try:
            response = httpx.post(f"{OLLAMA_URL}/api/embeddings", json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "model": model,
                    "embedding": data.get("embedding", [])[:10],  # First 10 dims for display
                    "embedding_dimensions": len(data.get("embedding", [])),
                }
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"error": str(e)}
    
    def list_models(self, **kwargs) -> dict:
        """List available models."""
        try:
            response = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                return {
                    "models": [m["name"] for m in models],
                    "count": len(models),
                }
            else:
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def pull_model(self, model: str, **kwargs) -> dict:
        """
        Pull a model from Ollama registry.
        
        Args:
            model: Model name to pull
        """
        try:
            response = httpx.post(
                f"{OLLAMA_URL}/api/pull",
                json={"name": model},
                timeout=0,  # No timeout for large downloads
            )
            
            if response.status_code == 200:
                return {"success": True, "model": model, "message": "Pull complete"}
            else:
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def model_info(self, model: str = None, **kwargs) -> dict:
        """Get information about a model."""
        model = model or self.default_model
        
        try:
            response = httpx.post(
                f"{OLLAMA_URL}/api/show",
                json={"name": model},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def translate(self, text: str, source_lang: str = "auto", target_lang: str = "english", **kwargs) -> dict:
        """
        Translate text using Ollama.
        
        Args:
            text: Text to translate
            source_lang: Source language
            target_lang: Target language
        """
        system = f"""You are a professional translator. Translate the following text 
from {source_lang} to {target_lang}. Only provide the translation, nothing else."""
        
        return self.generate(prompt=text, system=system, **kwargs)
    
    def summarize(self, text: str, max_length: int = 100, **kwargs) -> dict:
        """
        Summarize text using Ollama.
        """
        system = f"""Summarize the following text in no more than {max_length} words.
Provide a concise summary that captures the main points."""
        
        return self.generate(prompt=text, system=system, **kwargs)
    
    def explain_code(self, code: str, language: str = "python", **kwargs) -> dict:
        """
        Explain code using Ollama.
        """
        system = """You are a code explainer. Explain what the following code does
in a clear, concise manner. Break down each section and explain its purpose."""
        
        return self.generate(prompt=f"Language: {language}\n\nCode:\n{code}", system=system, **kwargs)
    
    def help(self) -> str:
        return """
Ollama Tools Hook
=================
Usage: /hook ollama_tools tool="generate" prompt="Hello world"

Tools:
- generate: Generate text from prompt
- chat: Chat with message history
- embeddings: Generate text embeddings
- models: List available models
- pull: Pull a new model
- info: Get model information

Special functions:
- translate: Translate text between languages
- summarize: Summarize long text
- explain_code: Explain what code does

Examples:
  /hook ollama_tools tool="generate" prompt="Write a Python function"
  /hook ollama_tools tool="translate" text="Hola mundo" target_lang="english"
  /hook ollama_tools tool="embeddings" prompt="Hello world"
  /hook ollama_tools tool="models"
"""


if __name__ == "__main__":
    hook = OllamaToolsHook()
    
    result = hook.list_models()
    print(json.dumps(result, indent=2))
