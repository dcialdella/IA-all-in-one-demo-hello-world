"""
OpenCode Chat Interface - Interactive LLM Chat with Agents, Skills and Hooks

A chat interface that connects to local Ollama LLM and allows
selecting different agents, skills and hooks for specialized interactions.
"""

import json
import os
import sys
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    import httpx
except ImportError:
    print("Installing httpx...")
    os.system(f"{sys.executable} -m pip install httpx -q")
    import httpx

BASE_DIR = Path(__file__).parent.parent
OLLAMA_URL = "http://localhost:11434"
CONFIG_FILE = BASE_DIR / ".opencode_chat_config.json"

try:
    from hooks import HookManager, WebSearchHook, CodeAnalysisHook, NotificationHook, OllamaToolsHook
except ImportError:
    from src.hooks import HookManager, WebSearchHook, CodeAnalysisHook, NotificationHook, OllamaToolsHook


@dataclass
class Agent:
    name: str
    description: str
    system_prompt: str
    tools: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return f"{self.name}: {self.description}"


@dataclass
class Skill:
    name: str
    description: str
    content: str

    def __str__(self) -> str:
        return f"{self.name}: {self.description}"


class OpenCodeChat:
    def __init__(self):
        self.ollama_url = OLLAMA_URL
        self.model = "llama3.1"
        self.conversation_history: list[dict] = []
        self.agents: dict[str, Agent] = {}
        self.skills: dict[str, Skill] = {}
        self.current_agent: Optional[Agent] = None
        self.current_skill: Optional[Skill] = None
        self.available_models: list[str] = []
        self.hook_manager = HookManager()
        self.meeting_assistant = None
        self.email_hook = None
        self.load_config()
        self.load_agents_and_skills()

    def load_config(self):
        try:
            if CONFIG_FILE.exists():
                config = json.loads(CONFIG_FILE.read_text())
                self.model = config.get("model", "llama3.1")
        except:
            pass

    def save_config(self):
        try:
            CONFIG_FILE.write_text(json.dumps({"model": self.model}, indent=2))
        except:
            pass

    def load_agents_and_skills(self):
        opencode_dir = BASE_DIR / ".opencode"
        
        agents_dir = opencode_dir / "agents"
        if agents_dir.exists():
            for agent_file in agents_dir.glob("*.md"):
                agent = self._parse_agent_file(agent_file)
                if agent:
                    self.agents[agent.name] = agent

        skills_dir = opencode_dir / "skills"
        if skills_dir.exists():
            for skill_dir in skills_dir.glob("*/SKILL.md"):
                skill = self._parse_skill_file(skill_dir)
                if skill:
                    self.skills[skill.name] = skill

    def _parse_agent_file(self, path: Path) -> Optional[Agent]:
        try:
            content = path.read_text()
            lines = content.split("\n")
            
            name = path.stem
            description = ""
            system_prompt = ""
            in_frontmatter = False
            in_prompt = False
            
            for i, line in enumerate(lines):
                if line.strip() == "---":
                    if not in_frontmatter:
                        in_frontmatter = True
                    else:
                        in_frontmatter = False
                        in_prompt = True
                    continue
                
                if in_frontmatter:
                    if line.startswith("description:"):
                        description = line.replace("description:", "").strip()
                
                if in_prompt and not in_frontmatter:
                    system_prompt += line + "\n"
            
            if not system_prompt:
                system_prompt = content
                
            return Agent(name=name, description=description, system_prompt=system_prompt.strip())
        except Exception as e:
            print(f"Error parsing agent {path}: {e}")
            return None

    def _parse_skill_file(self, path: Path) -> Optional[Skill]:
        try:
            content = path.read_text()
            lines = content.split("\n")
            
            name = path.parent.name
            description = ""
            
            for line in lines:
                if line.startswith("description:"):
                    description = line.replace("description:", "").strip()
                    break
            
            return Skill(name=name, description=description, content=content)
        except Exception as e:
            print(f"Error parsing skill {path}: {e}")
            return None

    def check_ollama_connection(self) -> bool:
        try:
            response = httpx.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

    def list_models(self) -> list[str]:
        try:
            response = httpx.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.available_models = [m["name"] for m in data.get("models", [])]
                return self.available_models
        except:
            pass
        return []

    def set_model(self, model: str):
        if model in self.available_models:
            self.model = model
            self.save_config()
            print(f"Model changed to: {self.model}")
        else:
            print(f"Model '{model}' not available")

    def select_model_interactive(self):
        print("\n" + "="*60)
        print("  SELECT LLM MODEL")
        print("="*60)
        
        models = self.list_models()
        
        if not models:
            print("\n⚠️  No models found!")
            print("   Make sure Ollama is running: ollama serve")
            print("   Or pull a model: ollama pull llama3.1")
            print(f"\n   Using default model: {self.model}\n")
            return
        
        print("\nAvailable models:\n")
        for i, model in enumerate(models, 1):
            marker = " ← current" if model == self.model else ""
            print(f"  [{i}] {model}{marker}")
        
        print(f"\n  [0] Skip - Use current ({self.model})")
        print()
        
        while True:
            try:
                choice = input(f"Select model (1-{len(models)}) or 0 to skip: ").strip()
                
                if choice == "0":
                    print(f"\nUsing: {self.model}\n")
                    return
                
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(models):
                        self.model = models[idx]
                        self.save_config()
                        print(f"\n✓ Model selected: {self.model}\n")
                        return
                
                print(f"Please enter a number between 0 and {len(models)}")
            except (ValueError, KeyboardInterrupt):
                print(f"\nUsing: {self.model}\n")
                return

    def select_agent(self, agent_name: str):
        if agent_name in self.agents:
            self.current_agent = self.agents[agent_name]
            print(f"Agent selected: {self.current_agent.description}")
        else:
            print(f"Agent '{agent_name}' not found")

    def select_skill(self, skill_name: str):
        if skill_name in self.skills:
            self.current_skill = self.skills[skill_name]
            print(f"Skill selected: {self.current_skill.description}")
        else:
            print(f"Skill '{skill_name}' not found")

    def clear_selection(self):
        self.current_agent = None
        self.current_skill = None
        print("Selection cleared")

    def build_system_prompt(self) -> str:
        parts = []
        
        parts.append("""You are a helpful AI assistant in a chat interface.
The user can select agents and skills to customize your behavior.

Keep responses concise and helpful.
""")
        
        if self.current_agent:
            parts.append(f"\n[ACTIVE AGENT: {self.current_agent.name}]\n")
            parts.append(self.current_agent.system_prompt)
        
        if self.current_skill:
            parts.append(f"\n[ACTIVE SKILL: {self.current_skill.name}]\n")
            parts.append(self.current_skill.content)
        
        return "\n".join(parts)

    def chat(self, message: str) -> str:
        system_prompt = self.build_system_prompt()
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.conversation_history)
        messages.append({"role": "user", "content": message})
        
        try:
            response = httpx.post(
                f"{self.ollama_url}/api/chat",
                json={"model": self.model, "messages": messages, "stream": False},
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                assistant_message = data["message"]["content"]
                
                self.conversation_history.append({"role": "user", "content": message})
                self.conversation_history.append({"role": "assistant", "content": assistant_message})
                
                return assistant_message
            else:
                return f"Error: {response.status_code} - {response.text}"
                
        except httpx.ConnectError:
            return "Error: Cannot connect to Ollama. Make sure Ollama is running (ollama serve)"
        except Exception as e:
            return f"Error: {str(e)}"

    def print_agents(self):
        print("\n" + "="*60)
        print("AVAILABLE AGENTS")
        print("="*60)
        for name, agent in self.agents.items():
            marker = " [ACTIVE]" if self.current_agent and self.current_agent.name == name else ""
            print(f"  /agent {name:<25} - {agent.description}{marker}")
        print()

    def print_skills(self):
        print("="*60)
        print("AVAILABLE SKILLS")
        print("="*60)
        for name, skill in self.skills.items():
            marker = " [ACTIVE]" if self.current_skill and self.current_skill.name == name else ""
            print(f"  /skill {name:<22} - {skill.description}{marker}")
        print()

    def print_web_help(self):
        print("""
╔══════════════════════════════════════════════════════════════════════╗
║                         WEB SEARCH HELP                             ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  Commands:                                                            ║
║    /web <query>        - Quick web search                            ║
║    /search <query>    - Search with LLM summary                     ║
║    /open <url>        - Open URL in browser                         ║
║    /fetch <url>       - Fetch & summarize webpage                   ║
║                                                                       ║
║  Providers:                                                           ║
║    Default: Wikipedia (no API key required)                          ║
║    Brave: export BRAVE_API_KEY                                        ║
║    Google: export GOOGLE_API_KEY + GOOGLE_CSE_ID                      ║
║                                                                       ║
║  Examples:                                                            ║
║    /web Python best practices                                         ║
║    /search Docker alternatives 2024                                   ║
║    /open https://github.com                                           ║
║    /fetch https://example.com                                         ║
╚══════════════════════════════════════════════════════════════════════╝
""")

    def print_access_help(self):
        print("""
╔══════════════════════════════════════════════════════════════════════╗
║                       ACCESS CONTROL HELP                           ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  Commands:                                                            ║
║    /access <path>     - Check path access permissions                 ║
║    /audit [path]      - Audit directory recursively                   ║
║    /project           - Check project access                          ║
║    /home              - Check home directory access                   ║
║                                                                       ║
║  Examples:                                                            ║
║    /access /home/user/Documents                                      ║
║    /audit .                                                           ║
║    /project                                                          ║
║    /home                                                             ║
╚══════════════════════════════════════════════════════════════════════╝
""")

    def print_help(self):
        print("""
╔════════════════════════════════════════════════════════════════════════════════════╗
║                              OPENCODE CHAT COMMANDS                                 ║
╠════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                    ║
║  Model Commands:                                                                    ║
║    /models          - List all available models                                      ║
║    /model <name>    - Change LLM model                                             ║
║                                                                                    ║
║  Agent Commands:                                                                   ║
║    /agents          - List all available agents                                     ║
║    /agent <name>    - Select an agent                                              ║
║                                                                                    ║
║  Skill Commands:                                                                   ║
║    /skills          - List all available skills                                     ║
║    /skill <name>    - Select a skill                                               ║
║                                                                                    ║
║  ══════════════════════════════════════════════════════════════════════════════    ║
║  HOOKS (Power Tools):                                                              ║
║  ══════════════════════════════════════════════════════════════════════════════    ║
║                                                                                    ║
║  /hooks              - List all available hooks                                     ║
║  /hook <name>        - Execute a hook with parameters                               ║
║                                                                                    ║
║  SOULS (File System):                                                              ║
║    /souls            - SOULS help                                                  ║
║    /tree [path]      - Show directory tree                                          ║
║    /ls [path]        - List directory contents                                      ║
║    /size [path]      - Calculate directory size                                     ║
║    /sys              - System information                                          ║
║                                                                                    ║
║  Meeting Assistant:                                                                ║
║    /meeting          - Meeting assistant help                                       ║
║    /meeting new      - Create new meeting                                           ║
║    /meeting notes    - Add notes to meeting                                         ║
║    /meeting actions  - List action items                                           ║
║    /agenda <topics>  - Create agenda from topics                                   ║
║                                                                                    ║
║  Access Control:                                                                   ║
║    /access <path>    - Check path access permissions                                ║
║    /audit [path]     - Audit directory permissions                                 ║
║    /project          - Check project access                                         ║
║    /home             - Check home directory access                                   ║
║                                                                                    ║
║  Quick Search Commands:                                                             ║
║    /web <query>      - Quick web search (Wikipedia)                                ║
║    /search <query>   - Web search with LLM summary                                 ║
║    /open <url>       - Open URL in browser                                         ║
║    /fetch <url>      - Fetch & summarize webpage                                   ║
║                                                                                    ║
║  Code Tools:                                                                       ║
║    /analyze <code>   - Analyze code for issues                                      ║
║    /security <code>  - Security scan                                                ║
║                                                                                    ║
║  Help:                                                                             ║
║    /help             - Show general help                                            ║
║    /help agents      - List all agents                                             ║
║    /help skills      - List all skills                                             ║
║    /help hooks       - List all hooks                                              ║
║    /help web         - Web search help                                             ║
║                                                                                    ║
║  Other Commands:                                                                   ║
║    /clear            - Clear agent/skill selection                                  ║
║    /reset            - Reset conversation history                                   ║
║    /status           - Show current model/agent/skill                               ║
║    /quit             - Exit the chat                                                ║
║                                                                                    ║
╚════════════════════════════════════════════════════════════════════════════════════╝
""")

    def print_header(self):
        print("""
╔══════════════════════════════════════════════════════════════════════╗
║                        OPENCODE CHAT INTERFACE                         ║
║              Interactive LLM Chat with Agents & Skills                ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  Model: {model:<57} ║
╚══════════════════════════════════════════════════════════════════════╝
""".format(model=self.model))

    def print_status(self):
        parts = []
        parts.append(f"Model: {self.model}")
        if self.current_agent:
            parts.append(f"Agent: {self.current_agent.name}")
        if self.current_skill:
            parts.append(f"Skill: {self.current_skill.name}")
        print(f"Status: {' | '.join(parts)}")

    def handle_help(self, topic: str = None):
        """Handle /help command with optional topic."""
        if not topic or topic == "":
            self.print_help()
            return
        
        topic = topic.lower().strip()
        
        if topic in ["agents", "agent"]:
            self.print_agents()
        elif topic in ["skills", "skill"]:
            self.print_skills()
        elif topic in ["hooks", "hook"]:
            self.print_hooks()
        elif topic in ["web", "search"]:
            self.print_web_help()
        elif topic in ["meeting", "meetings"]:
            self.print_meeting_help()
        elif topic in ["souls", "system", "fs", "file"]:
            self.print_souls_help()
        elif topic in ["access"]:
            self.print_access_help()
        elif topic in ["email", "gmail"]:
            self.execute_email("")
        else:
            print(f"\nUnknown topic: {topic}")
            print("Available topics: agents, skills, hooks, web, meeting, souls, access")
            print("Type /help for general help\n")

    def run(self):
        print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                      OPENCODE CHAT INTERFACE                             ║
║            Interactive LLM Chat with Agents, Skills & Hooks              ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  Type /help for commands, /quit to exit                                  ║
║  Use /help agents, /help skills, /help hooks for specific lists          ║
╚══════════════════════════════════════════════════════════════════════════╝
""")
        
        if not self.check_ollama_connection():
            print("⚠️  Cannot connect to Ollama")
            print("   Make sure Ollama is running: ollama serve\n")
        else:
            print(f"✓ Connected to Ollama ({self.model})\n")
        
        while True:
            try:
                user_input = input("Ready: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ["/quit", "/exit", "q"]:
                    print("\nGoodbye! 👋\n")
                    break
                
                elif user_input.startswith("/help"):
                    self.handle_help(user_input[5:].strip())
                    
                elif user_input == "/status":
                    self.print_status()
                    
                elif user_input == "/agents":
                    self.print_agents()
                    
                elif user_input == "/skills":
                    self.print_skills()
                    
                elif user_input == "/hooks":
                    self.print_hooks()
                    
                elif user_input == "/models":
                    models = self.list_models()
                    print("\n" + "="*60)
                    print("AVAILABLE MODELS")
                    print("="*60)
                    if models:
                        for m in models:
                            marker = " ← current" if m == self.model else ""
                            print(f"  {m}{marker}")
                    else:
                        print("  No models found. Pull one: ollama pull <model>")
                    print()
                    
                elif user_input.startswith("/agent "):
                    agent_name = user_input[7:].strip()
                    self.select_agent(agent_name)
                    
                elif user_input.startswith("/skill "):
                    skill_name = user_input[7:].strip()
                    self.select_skill(skill_name)
                    
                elif user_input.startswith("/model "):
                    model_name = user_input[7:].strip()
                    self.set_model(model_name)
                    
                elif user_input.startswith("/hook "):
                    self.execute_hook(user_input[6:].strip())
                    
                elif user_input.startswith("/web "):
                    query = user_input[5:].strip()
                    self.quick_web_search(query)
                    
                elif user_input.startswith("/search "):
                    query = user_input[8:].strip()
                    self.web_search_with_summary(query)
                    
                elif user_input.startswith("/open "):
                    url = user_input[6:].strip()
                    self.open_url(url)
                
                elif user_input.startswith("/fetch "):
                    url = user_input[7:].strip()
                    self.fetch_url(url)
                
                elif user_input.startswith("/analyze "):
                    code = user_input[9:].strip()
                    self.analyze_code(code)
                    
                elif user_input.startswith("/security "):
                    code = user_input[10:].strip()
                    self.scan_security(code)
                    
                elif user_input == "/clear":
                    self.clear_selection()
                    
                elif user_input == "/reset":
                    self.conversation_history = []
                    print("Conversation history cleared.")
                
                # SOULS Commands
                elif user_input.startswith("/souls"):
                    self.execute_souls_full(user_input[7:].strip())
                    
                elif user_input.startswith("/tree"):
                    parts = user_input[6:].strip().split()
                    path = parts[0] if parts else "."
                    depth = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 2
                    self.execute_souls("tree", path=path, max_depth=depth)
                    
                elif user_input.startswith("/ls"):
                    path = user_input[4:].strip() or "."
                    self.execute_souls("list", path=path)
                    
                elif user_input.startswith("/size"):
                    path = user_input[6:].strip() or "."
                    self.execute_souls("size", path=path)
                    
                elif user_input.startswith("/find"):
                    pattern = user_input[6:].strip()
                    if pattern:
                        self.execute_souls("find", path=".", pattern=pattern)
                    else:
                        print("Usage: /find <pattern>")
                    
                elif user_input in ["/sys", "/system"]:
                    self.execute_souls("system")
                    
                elif user_input.startswith("/todo"):
                    self.execute_todo(user_input[5:].strip())
                    
                elif user_input.startswith("/note"):
                    self.execute_note(user_input[5:].strip())
                    
                # Meeting Commands
                elif user_input in ["/meeting", "/meeting help"]:
                    self.print_meeting_help()
                    
                elif user_input.startswith("/meeting new"):
                    self.execute_meeting("new", **self._parse_meeting_args(user_input[12:]))
                    
                elif user_input.startswith("/meeting notes"):
                    notes = user_input[14:].strip()
                    if notes:
                        self.execute_meeting("notes", notes=notes)
                    else:
                        print("Usage: /meeting notes <your notes>")
                        
                elif user_input.startswith("/meeting action"):
                    self.execute_meeting("action", **self._parse_meeting_args(user_input[15:]))
                    
                elif user_input.startswith("/meeting summary"):
                    self.execute_meeting("summary")
                    
                elif user_input.startswith("/meeting list"):
                    self.execute_meeting("list")
                    
                elif user_input.startswith("/agenda"):
                    topics = user_input[7:].strip()
                    if topics:
                        self.execute_meeting("agenda", topics=topics)
                    else:
                        print("Usage: /agenda topic1|topic2|topic3")
                
                # Access Commands
                elif user_input.startswith("/access"):
                    path = user_input[8:].strip() or "."
                    self.execute_access("check", path=path)
                    
                elif user_input.startswith("/audit"):
                    path = user_input[7:].strip() or "."
                    self.execute_access("audit", path=path)
                    
                elif user_input in ["/project", "/project access"]:
                    self.execute_access("project_access")
                    
                elif user_input in ["/home", "/home access"]:
                    self.execute_access("home_access")
                
                # Email Commands
                elif user_input.startswith("/email") or user_input.startswith("/gmail"):
                    self.execute_email(user_input.split(maxsplit=1)[1] if ' ' in user_input else "")
                
                else:
                    status_parts = []
                    if self.current_agent:
                        status_parts.append(f"Agent: {self.current_agent.name}")
                    if self.current_skill:
                        status_parts.append(f"Skill: {self.current_skill.name}")
                    
                    if status_parts:
                        print(f"\n  [{' | '.join(status_parts)}]")
                    
                    response = self.chat(user_input)
                    print(f"\nAssistant: {response}")
                    
            except KeyboardInterrupt:
                print("\n\nGoodbye! 👋\n")
                break
            except Exception as e:
                print(f"Error: {e}")

    def print_hooks(self):
        print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                         AVAILABLE HOOKS                                     ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  HOOK NAME           DESCRIPTION                                            ║
║  ──────────────────────────────────────────────────────────────────────   ║
║  web_search         Search the web (Wikipedia, Brave, Google)              ║
║  code_analysis      Analyze Python code (syntax, complexity, security)       ║
║  notification       Send notifications (terminal, macOS, Slack, email)      ║
║  ollama_tools       Ollama tools (generate, chat, embeddings)              ║
║  souls              File system operations (list, tree, size, system)       ║
║  meeting            Meeting assistant (notes, actions, summaries)           ║
║  access             Access control (permissions, audit)                     ║
║  email              Email client (Gmail, Outlook)                           ║
║                                                                            ║
║  ════════════════════════════════════════════════════════════════════════   ║
║  QUICK COMMANDS:                                                            ║
║  ────────────────────────────────────────────────────────────────────────  ║
║                                                                            ║
║  /web <query>       - Quick web search                                      ║
║  /search <query>    - Search with LLM summary                               ║
║  /open <url>        - Open URL in browser                                   ║
║  /fetch <url>       - Fetch & summarize webpage                             ║
║  /analyze <code>    - Analyze code                                          ║
║  /security <code>   - Security scan                                         ║
║                                                                            ║
║  /tree [path]       - Directory tree                                         ║
║  /ls [path]         - List directory                                         ║
║  /size [path]       - Directory size                                         ║
║  /sys               - System information                                      ║
║                                                                            ║
║  /meeting new       - Create meeting                                         ║
║  /meeting notes     - Add notes                                              ║
║  /meeting action    - Add action item                                        ║
║  /agenda <topics>   - Create agenda                                          ║
║                                                                            ║
║  /access <path>     - Check path access                                      ║
║  /audit [path]      - Audit directory                                        ║
║  /project           - Check project access                                   ║
║  /home              - Check home access                                      ║
║                                                                            ║
║  /email setup       - Configure email (Gmail, Outlook)                      ║
║  /email list        - List recent emails                                    ║
║  /email read <id>   - Read email                                            ║
║  /email send        - Send email                                            ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
""")
        print("  USAGE:")
        print('    /hook web_search query="your search" provider="duckduckgo"')
        print('    /hook code_analysis code="def foo(): pass"')
        print('    /hook notification message="Done!" channel="terminal"')
        print('    /hook ollama_tools tool="generate" prompt="Hello"')
        print()
        print("  QUICK COMMANDS:")
        print('    /web <query>      - Quick search')
        print('    /search <query>   - Search with LLM summary')
        print('    /open <url>       - Open URL in browser')
        print('    /fetch <url>      - Fetch & summarize webpage')
        print('    /analyze <code>   - Analyze code')
        print()

    def execute_hook(self, hook_args: str):
        """Execute a hook with arguments."""
        parts = self._parse_command_args(hook_args)
        
        if not parts:
            print("Usage: /hook <hook_name> arg1=value1 arg2=value2")
            return
        
        hook_name = parts[0]
        kwargs = parts[1] if len(parts) > 1 else {}
        
        result = self.hook_manager.execute(hook_name, **kwargs)
        self._print_hook_result(result)
    
    def _parse_command_args(self, args_str: str) -> list:
        """Parse command arguments like: hook_name key=value key2=value2"""
        parts = args_str.split()
        if not parts:
            return []
        
        result = [parts[0]]
        kwargs = {}
        
        for part in parts[1:]:
            if '=' in part:
                key, value = part.split('=', 1)
                value = value.strip('"\'')
                kwargs[key.strip()] = value
        
        result.append(kwargs)
        return result
    
    def _print_hook_result(self, result: dict):
        """Format and print hook results."""
        if "error" in result:
            print(f"\n❌ Error: {result['error']}")
            if "available" in result:
                print(f"   Available: {result['available']}")
            return
        
        if "results" in result:
            print("\n" + "="*60)
            print("SEARCH RESULTS")
            print("="*60)
            for i, r in enumerate(result["results"], 1):
                print(f"\n  [{i}] {r.get('title', 'No title')}")
                print(f"      {r.get('url', '')}")
                desc = r.get('description', '')[:150]
                print(f"      {desc}...")
        
        if "summary" in result:
            print("\n" + "="*60)
            print("LLM SUMMARY")
            print("="*60)
            print(f"\n{result['summary']}\n")
        
        if "complexity" in result:
            print("\n" + "="*60)
            print("CODE ANALYSIS")
            print("="*60)
            c = result["complexity"]
            print(f"\n  Functions: {c.get('functions', 0)}")
            print(f"  Classes: {c.get('classes', 0)}")
            print(f"  Loops: {c.get('loops', 0)}")
            print(f"  Conditionals: {c.get('conditionals', 0)}")
            print(f"  Complexity Score: {c.get('score', 0)} ({c.get('rating', '')})")
        
        if "security" in result:
            s = result["security"]
            print(f"\n  Security Score: {s.get('security_score', 0)}/100")
            if s.get("issues"):
                print(f"\n  Issues found:")
                for issue in s["issues"][:5]:
                    print(f"    [{issue['severity']}] Line {issue['line']}: {issue['message']}")
        
        if "success" in result:
            status = "✓" if result["success"] else "✗"
            print(f"\n{status} {result.get('channel', 'hook')}: {result}")
        
        if "response" in result:
            print(f"\n{result['response']}")
        
        if "model" in result and "response" not in result and "success" not in result:
            print(json.dumps(result, indent=2))
        
        print()

    def quick_web_search(self, query: str):
        """Quick web search."""
        if not query:
            print("Usage: /web <search query>")
            return
        
        print(f"\n🔍 Searching: {query}")
        print("-" * 40)
        
        hook = WebSearchHook()
        result = hook.run(query, num_results=5)
        self._print_hook_result(result)
    
    def web_search_with_summary(self, query: str):
        """Web search with LLM summary."""
        if not query:
            print("Usage: /search <search query>")
            return
        
        print(f"\n🔍 Searching with LLM summary: {query}")
        print("-" * 40)
        
        hook = WebSearchHook()
        result = hook.search_with_llm_summary(query)
        self._print_hook_result(result)
    
    def open_url(self, url: str):
        """Open URL in browser."""
        if not url:
            print("Usage: /open <url>")
            return
        
        hook = NotificationHook()
        result = hook._open_url(url)
        
        if result.get("success"):
            print(f"\n✓ Opened: {url}")
        else:
            print(f"\n✗ Error: {result.get('error', 'Unknown error')}")
    
    def fetch_url(self, url: str):
        """Fetch URL and summarize with LLM."""
        if not url:
            print("Usage: /fetch <url>")
            return
        
        url = url.strip().strip("'\"")
        
        print(f"\n🔍 Fetching: {url}")
        print("-" * 40)
        
        hook = WebSearchHook()
        result = hook.fetch_and_summarize(url)
        
        if "error" in result:
            print(f"\n❌ Error: {result['error']}")
            return
        
        print("\n" + "="*60)
        print(result.get("title", "Page"))
        print("="*60)
        print(f"\n📄 URL: {result.get('url')}")
        print(f"\n📝 SUMMARY:")
        print("-" * 40)
        print(result.get("summary", "No summary available"))
        print()
    
    def analyze_code(self, code: str):
        """Analyze code."""
        if not code:
            print("Usage: /analyze <code>")
            return
        
        hook = CodeAnalysisHook()
        result = hook.run(code=code, analysis_type="full")
        self._print_hook_result(result)
    
    def scan_security(self, code: str):
        """Security scan code."""
        if not code:
            print("Usage: /security <code>")
            return
        
        hook = CodeAnalysisHook()
        result = hook.run(code=code, analysis_type="security")
        self._print_hook_result(result)
    
    # ==================== SOULS Commands ====================
    
    def print_souls_help(self):
        """Print SOULS help."""
        print("""
╔══════════════════════════════════════════════════════════════════════╗
║                         SOULS - File System                         ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  Commands:                                                            ║
║    /souls             - Show this help                               ║
║    /tree [path]       - Show directory tree                          ║
║    /ls [path]         - List directory contents                      ║
║    /size [path]       - Calculate directory size                     ║
║    /sys               - System information                           ║
║                                                                       ║
║  Examples:                                                            ║
║    /tree /home/user/projects                                         ║
║    /ls ~/Documents                                                   ║
║    /size .                                                           ║
╚══════════════════════════════════════════════════════════════════════╝
""")
    
    def execute_souls(self, action: str, **kwargs):
        """Execute SOULS actions."""
        try:
            from hooks.souls import SOULS2Hook
            hook = SOULS2Hook()
            result = hook.run(action=action, **kwargs)
            self._print_souls_result(result)
        except Exception as e:
            print(f"Error: {e}")
    
    def execute_souls_full(self, args: str):
        """Execute SOULS with full command parsing."""
        import re
        try:
            from hooks.souls import SOULS2Hook
            hook = SOULS2Hook()
            
            parts = args.split()
            if not parts:
                result = hook.run("help")
                self._print_souls_result(result)
                return
            
            action = parts[0]
            
            if action == "todo":
                if len(parts) > 1:
                    subaction = parts[1]
                    if subaction == "add" and len(parts) > 2:
                        result = hook.run("add", task=" ".join(parts[2:]))
                    elif subaction == "done" and len(parts) > 2:
                        result = hook.run("done", task_id=parts[2])
                    elif subaction == "pending":
                        result = hook.run("pending")
                    else:
                        result = hook.run("tasks")
                else:
                    result = hook.run("tasks")
                self._print_souls_result(result)
                return
            
            if action == "note":
                if len(parts) > 1:
                    subaction = parts[1]
                    if subaction == "add" and len(parts) > 2:
                        title = parts[2]
                        content = " ".join(parts[3:]) if len(parts) > 3 else ""
                        result = hook.run("addnote", title=title, content=content)
                    elif subaction == "read" and len(parts) > 2:
                        result = hook.run("readnote", note_id=parts[2])
                    else:
                        result = hook.run("notes")
                else:
                    result = hook.run("notes")
                self._print_souls_result(result)
                return
            
            if action == "bookmark":
                if len(parts) > 1:
                    subaction = parts[1]
                    if subaction == "add" and len(parts) > 3:
                        result = hook.run("bookmark", name=parts[2], url=parts[3])
                    elif subaction == "open" and len(parts) > 2:
                        result = hook.run("open", name=parts[2])
                    else:
                        result = hook.run("bookmarks")
                else:
                    result = hook.run("bookmarks")
                self._print_souls_result(result)
                return
            
            if action == "cmd" or action == "shell":
                result = hook.run("cmd", command=" ".join(parts[1:]))
            elif action == "calc":
                result = hook.run("calc", expression=" ".join(parts[1:]))
            elif action == "kill":
                result = hook.run("kill", pid=parts[1] if len(parts) > 1 else "")
            elif action == "sys" or action == "system":
                result = hook.run("sys")
            elif action == "calendar":
                result = hook.run("calendar")
            elif action == "tree":
                path = parts[1] if len(parts) > 1 else "."
                depth = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 2
                result = hook.run("tree", path=path, max_depth=depth)
            elif action == "list" or action == "ls":
                path = parts[1] if len(parts) > 1 else "."
                result = hook.run("list", path=path)
            elif action == "size":
                path = parts[1] if len(parts) > 1 else "."
                result = hook.run("size", path=path)
            elif action == "find":
                pattern = parts[1] if len(parts) > 1 else "*"
                result = hook.run("find", pattern=pattern)
            else:
                kwargs = {}
                for part in parts[1:]:
                    match = re.match(r'(\w+)=(.+)', part)
                    if match:
                        kwargs[match.group(1)] = match.group(2).strip('"\'')
                result = hook.run(action, **kwargs)
            
            self._print_souls_result(result)
            
        except Exception as e:
            print(f"Error: {e}")
    
    def execute_todo(self, args: str):
        """Execute TODO commands."""
        self.execute_souls_full(f"todo {args}")
    
    def execute_note(self, args: str):
        """Execute NOTE commands."""
        self.execute_souls_full(f"note {args}")
    
    def _print_souls_result(self, result: dict):
        """Print SOULS result."""
        if "help" in result:
            print(result["help"])
            return
        
        if "tree" in result:
            print("\n" + "="*60)
            print("📂 DIRECTORY TREE")
            print("="*60)
            print(f"\n{result.get('tree', '')}\n")
            return
        
        if "total_bytes" in result:
            print("\n" + "="*60)
            print("💾 DIRECTORY SIZE")
            print("="*60)
            print(f"\n  Path: {result.get('path')}")
            print(f"  Total: {result.get('total_formatted')}")
            print(f"  Files: {result.get('file_count')}")
            print(f"  Directories: {result.get('directory_count')}\n")
            return
        
        if "platform" in result or "cpu" in result:
            print("\n" + "="*60)
            print("🖥️  SYSTEM INFORMATION")
            print("="*60)
            if "platform" in result:
                print(f"\n  Platform: {result.get('platform')}")
            if "hostname" in result:
                print(f"  Hostname: {result.get('hostname')}")
            if "cpu" in result:
                print(f"  CPU: {result.get('cpu', {}).get('cores')} cores @ {result.get('cpu', {}).get('usage')}")
            if "memory" in result:
                mem = result.get("memory", {})
                print(f"  Memory: {mem.get('used')} / {mem.get('total')} ({mem.get('percent')})")
            if "disk" in result:
                disk = result.get("disk", {})
                print(f"  Disk: {disk.get('used')} / {disk.get('total')} ({disk.get('percent')})")
            if "load" in result:
                print(f"  Load: {result.get('load')}")
            print()
            return
        
        if "items" in result:
            print("\n" + "="*60)
            print(f"📁 {result.get('path', '')}")
            print("="*60)
            print(f"{'Name':<30} {'Type':<6} {'Size':<12}")
            print("-" * 50)
            for item in result.get("items", [])[:20]:
                size = item.get("size")
                if size is not None:
                    size_str = self._format_size(size)
                else:
                    size_str = "-"
                item_type = "📁 DIR" if item.get("type") == "dir" else "📄"
                print(f"{item.get('name', ''):<30} {item_type:<6} {size_str:<12}")
            print(f"\n  Total: {result.get('total', 0)} items\n")
            return
        
        if "matches" in result:
            print("\n" + "="*60)
            print(f"🔍 Search: {result.get('pattern', '')}")
            print("="*60)
            for match in result.get("matches", []):
                print(f"\n  {match.get('path', '')}")
                print(f"     {self._format_size(match.get('size', 0))} - {match.get('modified', '')}")
            print(f"\n  Found: {result.get('total', 0)} files\n")
            return
        
        if "all" in result or "pending" in result:
            print("\n" + "="*60)
            print("✅ TASKS")
            print("="*60)
            tasks = result.get("all", result.get("pending", []))
            counts = result.get("counts", {})
            if counts:
                print(f"\n  Total: {counts.get('total', 0)} | Pending: {counts.get('pending', 0)} | Done: {counts.get('completed', 0)}\n")
            for task in tasks:
                status = "✓" if task.get("status") == "completed" else "○"
                prio = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task.get("priority", "medium"), "⚪")
                print(f"  [{task.get('id')}] {status} {prio} {task.get('task', '')}")
                if task.get("status") == "completed":
                    print(f"       Done: {task.get('completed', '')}")
            print()
            return
        
        if "notes" in result or result.get("note", {}).get("title"):
            print("\n" + "="*60)
            print("📝 NOTES")
            print("="*60)
            notes = result.get("notes", [result.get("note")])
            for note in notes:
                if note:
                    print(f"\n  [{note.get('id')}] {note.get('title', '')}")
                    if note.get("content"):
                        print(f"      {note.get('content', '')[:50]}...")
                    print(f"      Created: {note.get('created', '')}")
            print()
            return
        
        if "bookmarks" in result or "bookmark" in result:
            print("\n" + "="*60)
            print("🔖 BOOKMARKS")
            print("="*60)
            bookmarks = result.get("bookmarks", [result.get("bookmark")])
            for bm in bookmarks:
                if bm:
                    print(f"\n  {bm.get('name', '')}")
                    print(f"     {bm.get('url', '')}")
            print()
            return
        
        if "expression" in result:
            print(f"\n  🧮 {result.get('expression')} = {result.get('result')}\n")
            return
        
        if "success" in result:
            print(f"\n✓ {result.get('message', 'Success')}\n")
            return
        
        if "calendar" in result:
            print("\n" + "="*60)
            print("📅 CALENDAR")
            print("="*60)
            print(f"\n{result.get('month', '')} - {result.get('today', '')}\n")
            print(result.get('calendar', ''))
            print()
            return
        
        if "error" in result:
            print(f"\n❌ Error: {result.get('error')}")
            if "usage" in result:
                print(f"   {result.get('usage')}")
            print()
            return
        
        print(json.dumps(result, indent=2))
    
    def _format_size(self, bytes_size: int) -> str:
        """Format bytes to human readable size."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_size < 1024:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.1f} PB"
    
    # ==================== Meeting Commands ====================
    
    def print_meeting_help(self):
        """Print Meeting Assistant help."""
        print("""
╔══════════════════════════════════════════════════════════════════════╗
║                     MEETING ASSISTANT                                ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  Commands:                                                            ║
║    /meeting              - Show this help                             ║
║    /meeting new          - Create new meeting                        ║
║    /meeting notes <text> - Add notes to current meeting              ║
║    /meeting action       - Add action item                            ║
║    /meeting summary      - Generate meeting summary                   ║
║    /meeting list         - List all meetings                         ║
║    /agenda <topics>      - Create agenda (use | to separate topics)  ║
║                                                                       ║
║  Examples:                                                            ║
║    /meeting new title="Sprint Planning" duration=60                   ║
║    /meeting notes Discussed the timeline                              ║
║    /meeting action task="Update docs" assignee="John"                ║
║    /agenda Intro|Discussion|Review|Wrap up                           ║
╚══════════════════════════════════════════════════════════════════════╝
""")
    
    def _parse_meeting_args(self, args: str) -> dict:
        """Parse meeting command arguments."""
        import re
        kwargs = {}
        
        key_value_pattern = r'(\w+)=(["\'])([^"\']+)\2'
        matches = re.findall(key_value_pattern, args)
        for key, quote, value in matches:
            kwargs[key.strip()] = value.strip()
        
        if not kwargs and '=' in args:
            parts = args.split('=')
            if len(parts) >= 2:
                key = parts[0].strip()
                value = '='.join(parts[1:]).strip().strip('"\'')
                if key:
                    kwargs[key] = value
        
        return kwargs
    
    def execute_meeting(self, action: str, **kwargs):
        """Execute Meeting Assistant actions."""
        try:
            if self.meeting_assistant is None:
                from hooks.meeting_assistant import MeetingAssistantHook
                self.meeting_assistant = MeetingAssistantHook()
            
            result = self.meeting_assistant.run(action=action, **kwargs)
            
            if "agenda" in result:
                print("\n" + "="*60)
                print("MEETING AGENDA")
                print("="*60)
                print(f"\n{result.get('agenda', '')}\n")
            elif "summary" in result:
                print("\n" + "="*60)
                print("MEETING SUMMARY")
                print("="*60)
                print(f"\n{result.get('summary', '')}\n")
            elif "success" in result and "meeting" in result:
                print(f"\n✓ Meeting created: {result.get('message', '')}")
            elif "success" in result:
                print(f"\n✓ {result}")
            elif "meetings" in result:
                print("\n" + "="*60)
                print("MEETINGS")
                print("="*60)
                for m in result.get("meetings", []):
                    print(f"\n  [{m.get('id')}] {m.get('title')}")
                    print(f"      Date: {m.get('date')}")
                    print(f"      Status: {m.get('status')}")
                    print(f"      Notes: {m.get('notes_count')} | Actions: {m.get('action_count')}")
                print()
            elif "action_item" in result:
                print(f"\n✓ Action item added: {result.get('action_item', {}).get('task')}")
            else:
                print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error: {e}")
    
    # ==================== Access Commands ====================
    
    def execute_access(self, action: str, **kwargs):
        """Execute Access Control actions."""
        try:
            from hooks.access_control import AccessControlHook
            hook = AccessControlHook()
            result = hook.run(action=action, **kwargs)
            
            if "accessible_count" in result and "paths" in result:
                print("\n" + "="*60)
                print("ACCESS CHECK")
                print("="*60)
                if "home_directory" in result:
                    print(f"\nHome: {result.get('home_directory')}")
                    print(f"Accessible: {result.get('accessible_count')}/{result.get('total_count')}\n")
                    for name, info in result.get("paths", {}).items():
                        status = "✓" if info.get("accessible") else "✗"
                        print(f"  {status} {name}: {info.get('path')}")
                        if info.get("exists"):
                            print(f"      Items: {info.get('item_count', 0)}")
                print()
            elif "all_paths_accessible" in result:
                print("\n" + "="*60)
                print("PROJECT ACCESS")
                print("="*60)
                print(f"\nProject: {result.get('project_path')}")
                print(f"All accessible: {'Yes' if result.get('all_paths_accessible') else 'No'}\n")
                for name, info in result.get("paths", {}).items():
                    status = "✓" if info.get("readable") else "✗"
                    print(f"  {status} {name}: {info.get('path')}")
                print()
            elif "exists" in result:
                print("\n" + "="*60)
                print("ACCESS CHECK")
                print("="*60)
                print(f"\nPath: {result.get('path')}")
                print(f"Exists: {result.get('exists')}")
                if result.get("exists"):
                    perms = []
                    if "can_read" in result:
                        perms.append(f"R:{result.get('can_read')}")
                    if "can_write" in result:
                        perms.append(f"W:{result.get('can_write')}")
                    if "can_execute" in result:
                        perms.append(f"X:{result.get('can_execute')}")
                    if perms:
                        print(f"Permissions: {', '.join(perms)}")
                print()
            elif "summary" in result:
                print("\n" + "="*60)
                print("DIRECTORY AUDIT")
                print("="*60)
                print(f"\nDirectory: {result.get('path')}")
                print(f"Score: {result.get('accessibility_score', 0)}%")
                print(f"Total items: {result.get('summary', {}).get('total_items')}")
                print(f"Readable: {result.get('summary', {}).get('readable')}")
                print(f"Blocked: {result.get('summary', {}).get('blocked')}\n")
            else:
                print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error: {e}")
    
    # ==================== Email Commands ====================
    
    def execute_email(self, args: str = ""):
        """Execute Email actions."""
        import re
        try:
            if self.email_hook is None:
                from hooks.email_hook import EmailHook
                self.email_hook = EmailHook()
            
            parts = args.split()
            if not parts:
                result = self.email_hook.run("help")
                self._print_email_result(result)
                return
            
            action = parts[0]
            
            kwargs = {}
            for part in parts[1:]:
                match = re.match(r'(\w+)=(.+)', part)
                if match:
                    kwargs[match.group(1)] = match.group(2).strip('"\'')
            
            result = self.email_hook.run(action, **kwargs)
            self._print_email_result(result)
            
        except Exception as e:
            print(f"Error: {e}")
    
    def _print_email_result(self, result: dict):
        """Print email result."""
        if "error" in result and not result.get("success"):
            print(f"\n❌ Error: {result['error']}")
            if "instructions" in result:
                print(result["instructions"])
            if "required_env" in result:
                print("\nRequired environment variables:")
                for key, val in result["required_env"].items():
                    print(f"  {key}={val}")
            if "example" in result and "\n" not in result.get("example", ""):
                print(result["example"])
            print()
            return
        
        if result.get("success"):
            print(f"\n✓ {result.get('message', 'Success')}")
            if result.get("provider"):
                print(f"  Provider: {result.get('provider')}")
            if result.get("user"):
                print(f"  User: {result.get('user')}")
            print()
            return
        
        if "emails" in result:
            print("\n" + "="*60)
            print(f"📧 EMAILS - {result.get('folder', 'INBOX')}")
            if result.get('total_in_folder'):
                print(f"   ({result.get('count', 0)} shown of {result.get('total_in_folder')} total)")
            print("="*60)
            for email in result.get("emails", []):
                attach = "📎 " if email.get("has_attachments") else "   "
                print(f"\n  [{email.get('id')}] {attach}{email.get('subject', '')}")
                print(f"      From: {email.get('from', '')} | {email.get('date', '')}")
            print()
            return
        
        if "body" in result:
            print("\n" + "="*60)
            print("📧 EMAIL CONTENT")
            print("="*60)
            print(f"\nFrom:    {result.get('from', '')}")
            print(f"To:      {result.get('to', '')}")
            if result.get('cc'):
                print(f"Cc:      {result.get('cc', '')}")
            print(f"Subject: {result.get('subject', '')}")
            print(f"Date:    {result.get('date', '')}")
            if result.get('attachments'):
                print(f"\n📎 Attachments: {', '.join(a['filename'] for a in result.get('attachments', []))}")
            print("\n" + "-"*40)
            print(result.get('body', '')[:1000])
            if len(result.get('body', '')) > 1000:
                print(f"\n... (truncated, full email has {len(result.get('body', ''))} chars)")
            print()
            return
        
        if "results" in result and "query" in result:
            print(f"\n🔍 Search: \"{result.get('query', '')}\"")
            print(f"   Found: {result.get('count', 0)} emails\n")
            for r in result.get("results", []):
                print(f"  [{r.get('id')}] {r.get('subject', '')}")
                print(f"       {r.get('from', '')} - {r.get('date', '')}")
            print()
            return
        
        if "labels" in result:
            print("\n📁 EMAIL FOLDERS")
            print("="*40)
            for label in result.get("labels", []):
                print(f"  • {label.get('name', '')}")
            print()
            return
        
        if "help" in result:
            print(result["help"])
            return
        
        print(json.dumps(result, indent=2))


def main():
    chat = OpenCodeChat()
    chat.run()


if __name__ == "__main__":
    main()
