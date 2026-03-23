"""
OpenCode Chat Hooks - Programmable hooks for automated activities

This module provides hooks that can be triggered by specific events
or commands in the chat interface.
"""

from .web_search import WebSearchHook
from .code_analysis import CodeAnalysisHook
from .notification import NotificationHook
from .ollama_tools import OllamaToolsHook
from .souls import SOULS2Hook
from .meeting_assistant import MeetingAssistantHook
from .access_control import AccessControlHook
from .email_hook import EmailHook

__all__ = [
    "WebSearchHook",
    "CodeAnalysisHook",
    "NotificationHook",
    "OllamaToolsHook",
    "SOULSHook",
    "MeetingAssistantHook",
    "AccessControlHook",
    "EmailHook",
    "HookManager",
]


class HookManager:
    def __init__(self):
        self.hooks: dict[str, callable] = {}
        self.register_default_hooks()
    
    def register_default_hooks(self):
        self.register("web_search", WebSearchHook())
        self.register("code_analysis", CodeAnalysisHook())
        self.register("notification", NotificationHook())
        self.register("ollama_tools", OllamaToolsHook())
        self.register("souls", SOULS2Hook())
        self.register("meeting", MeetingAssistantHook())
        self.register("access", AccessControlHook())
        self.register("email", EmailHook())
    
    def register(self, name: str, hook: callable):
        self.hooks[name] = hook
    
    def execute(self, hook_name: str, **kwargs):
        if hook_name in self.hooks:
            return self.hooks[hook_name].run(**kwargs)
        return {"error": f"Hook '{hook_name}' not found"}
    
    def list_hooks(self):
        return list(self.hooks.keys())
    
    def get_hook_info(self, name: str):
        if name in self.hooks:
            hook = self.hooks[name]
            return {
                "name": name,
                "description": hook.__doc__ or "No description",
                "methods": dir(hook) if hasattr(hook, '__class__') else []
            }
        return None


class BaseHook:
    def run(self, **kwargs):
        raise NotImplementedError
    
    def help(self) -> str:
        return "Base hook - override in subclass"
