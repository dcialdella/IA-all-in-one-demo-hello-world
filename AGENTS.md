# OpenCode Chat - Agentes y Configuración

## Project Overview

OpenCode Chat es una aplicación CLI interactiva que conecta con Ollama LLM local, ofreciendo agentes especializados, skills, hooks avanzados y utilidades del sistema.

## Project Structure

```
ia-prompt-agentes/
├── src/
│   ├── main.py                 # Interfaz de chat principal
│   └── hooks/                   # Hooks del sistema (8 archivos)
│       ├── __init__.py         # HookManager
│       ├── souls.py            # SOULS 2.0
│       ├── email_hook.py       # Cliente email
│       ├── web_search.py       # Búsqueda + fetch URL
│       ├── code_analysis.py    # Análisis de código
│       ├── notification.py     # Notificaciones
│       ├── ollama_tools.py     # Herramientas Ollama
│       ├── meeting_assistant.py # Reuniones
│       └── access_control.py   # Permisos
├── .opencode/
│   ├── agents/                 # 9 agentes
│   ├── prompts/                # Prompts
│   └── skills/                  # 7 skills
├── .venv/                      # Virtual environment
├── run.sh                      # Script de ejecución
├── README.md                   # Documentación completa
└── opencode.json              # Configuración
```

## Running the Project

```bash
cd ia-prompt-agentes
./run.sh
```

Select an Ollama model at startup and start chatting.

## Available Commands

### Web Commands
- `/web <query>` - Quick search (Wikipedia)
- `/search <query>` - Search with LLM summary
- `/open <url>` - Open URL in browser
- `/fetch <url>` - Fetch & summarize webpage with LLM

### SOULS 2.0 Commands
- `/souls list [path]` - List directory
- `/souls tree [path]` - Directory tree
- `/souls size [path]` - Directory size
- `/souls sys` - System info
- `/souls todo add <task>` - Add task
- `/souls note add <title> <content>` - Add note
- `/souls cmd <command>` - Run shell command
- `/souls calc <expression>` - Calculator

### Meeting Commands
- `/meeting new title="..."` - Create meeting
- `/meeting notes="..."` - Add notes
- `/meeting action task="..."` - Add action item
- `/agenda <topics>` - Create agenda

### Hook Commands
- `/hook web_search query="..."`
- `/hook code_analysis code="..."`
- `/hook notification message="..."`
- `/hook ollama_tools tool="models"`
- `/hook souls action="sys"`

### Utility Commands
- `/tree [path]` - Directory tree
- `/ls [path]` - List files
- `/analyze <code>` - Analyze code
- `/security <code>` - Security scan
- `/help` - Show help
- `/help agents` - List agents
- `/help skills` - List skills
- `/help hooks` - List hooks

## Available Agents (9)

1. **python-expert** - Python code improvements
2. **javascript-expert** - JavaScript/Node.js
3. **code-reviewer** - Code reviews
4. **database-expert** - SQL and databases
5. **security-expert** - Security analysis
6. **docs-expert** - Technical documentation
7. **devops-expert** - Docker, CI/CD
8. **api-expert** - RESTful/GraphQL APIs
9. **performance-expert** - Optimization
10. **architect** - System design

### Agent Examples

```
@python-expert improve this function
@security-expert analyze for vulnerabilities
@devops-expert setup Docker
```

## Available Skills (7)

| Skill | Description |
|-------|-------------|
| `python-tests` | Creates pytest tests |
| `api-rest-design` | Designs REST APIs |
| `docker-setup` | Docker configurations |
| `security-audit` | Security analysis |
| `database-migration` | DB migrations |
| `ci-cd-pipeline` | CI/CD pipelines |
| `performance-profile` | Performance analysis |

### Skill Examples

```
Create tests using python-tests skill
Design API using api-rest-design skill
Add Docker using docker-setup skill
```

## Available Hooks (8)

| Hook | Description |
|------|-------------|
| `web_search` | Web search (Wikipedia, Brave, Google, SearXNG) |
| `code_analysis` | Python code analysis |
| `notification` | Notifications (terminal, macOS, Slack, email) |
| `ollama_tools` | Ollama API tools |
| `souls` | SOULS 2.0 system utilities |
| `meeting` | Meeting management |
| `access_control` | Permission verification |
| `email` | Email client (IMAP/SMTP) |

## Environment Variables

```bash
# Web Search
BRAVE_API_KEY, GOOGLE_API_KEY, GOOGLE_CSE_ID

# Notifications  
SLACK_WEBHOOK_URL, WEBHOOK_URL

# Email
EMAIL_HOST, EMAIL_USER, EMAIL_PASSWORD
SMTP_HOST, SMTP_USER, SMTP_PASS
```

## Recommended Models

| Model | Size | Use |
|-------|------|-----|
| llama3.1 | 4.9GB | General |
| qwen2.5-coder:7b | 4.7GB | Coding |
| deepseek-r1 | 5.2GB | Reasoning |
| gemma3 | 3.3GB | Fast |
