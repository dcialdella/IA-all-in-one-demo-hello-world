# OpenCode Chat - CLI Interactivo con Ollama

Aplicación de chat CLI interactiva que conecta con **Ollama LLM** local, ofreciendo agentes especializados, skills, hooks avanzados (incluyendo SOULS 2.0), y utilidades del sistema.

## Tabla de Contenidos

1. [Características Principales](#características-principales)
2. [Estructura del Proyecto](#estructura-del-proyecto)
3. [Instalación y Ejecución](#instalación-y-ejecución)
4. [Comandos Disponibles](#comandos-disponibles)
5. [Agentes Disponibles](#agentes-disponibles)
6. [Skills Disponibles](#skills-disponibles)
7. [Hooks del Sistema](#hooks-del-sistema)
8. [SOULS 2.0](#souls-20)
9. [Configuración de Variables de Entorno](#configuración-de-variables-de-entorno)
10. [Modelos de Ollama](#modelos-de-ollama)

---

## Características Principales

- **Chat interactivo** con LLM local (Ollama)
- **9 agentes especializados** para diferentes tareas
- **7 skills** para funcionalidades específicas
- **8 hooks** con herramientas del sistema
- **SOULS 2.0** - Sistema operativo local integrado
- **Búsqueda web** con resumen LLM
- **Análisis de código** y seguridad
- **Gestión de reuniones** y notas
- **Cliente de email** (IMAP/SMTP)
- **Notificaciones** múltiples canales

---

## Estructura del Proyecto

```
ia-prompt-agentes/
├── src/
│   ├── main.py                 # Interfaz de chat principal
│   └── hooks/                   # Módulos de hooks
│       ├── __init__.py         # HookManager
│       ├── souls.py            # SOULS 2.0
│       ├── web_search.py       # Búsqueda y fetch URL
│       ├── code_analysis.py   # Análisis de código
│       ├── notification.py    # Notificaciones
│       ├── ollama_tools.py    # Herramientas Ollama
│       ├── meeting_assistant.py # Reuniones
│       ├── email_hook.py      # Cliente email
│       └── access_control.py  # Permisos
├── .opencode/
│   ├── agents/                 # Definiciones de agentes (9)
│   ├── prompts/               # Prompts personalizados
│   └── skills/                # Definiciones de skills (7)
├── .venv/                     # Virtual environment
├── run.sh                    # Script de ejecución
└── README.md                 # Este archivo
```

---

## Instalación y Ejecución

### Requisitos Previos

- **Python 3.8+**
- **Ollama** instalado y ejecutándose en `http://localhost:11434`

### Inicio Rápido

```bash
# Clonar o descargar el proyecto
cd ia-prompt-agentes

# Ejecutar (crea venv automáticamente si no existe)
./run.sh
```

### Opciones de run.sh

```bash
./run.sh              # Setup completo y ejecutar
./run.sh --recreate  # Recrear virtual environment
./run.sh --no-setup  # Solo ejecutar (sin setup)
./run.sh --help      # Mostrar ayuda
```

### Ejecución Manual

```bash
cd ia-prompt-agentes
source .venv/bin/activate
python src/main.py
```

---

## Comandos Disponibles

### Comandos de Chat

| Comando | Descripción |
|---------|-------------|
| Mensaje normal | Envía mensaje al LLM |
| `@agente` | Cambia al agente especificado |
| `/help` | Muestra ayuda general |
| `/help agents` | Lista agentes disponibles |
| `/help skills` | Lista skills disponibles |
| `/help hooks` | Lista hooks disponibles |
| `/help web` | Ayuda de búsqueda web |
| `/status` | Muestra modelo/agent/skill actual |
| `/clear` | Limpia selección actual |
| `/reset` | Resetea historial de conversación |
| `/quit` | Salir de la aplicación |

### Comandos Web

| Comando | Descripción | Ejemplo |
|---------|-------------|---------|
| `/web <query>` | Búsqueda rápida (Wikipedia) | `/web Python tips` |
| `/search <query>` | Búsqueda con resumen LLM | `/search Docker 2024` |
| `/open <url>` | Abrir URL en navegador | `/open https://github.com` |
| `/fetch <url>` | Descargar página y resumir con LLM | `/fetch https://python.org` |

**Proveedores disponibles**: Wikipedia (defecto), Brave, Google, SearXNG

### Comandos SOULS 2.0

| Comando | Descripción |
|---------|-------------|
| `/souls list [path]` | Listar contenido de directorio |
| `/souls tree [path]` | Árbol de directorios |
| `/souls size [path]` | Tamaño de directorio |
| `/souls info <path>` | Información de archivo/directorio |
| `/souls find <pattern>` | Buscar archivos |
| `/souls sys` | Información del sistema |
| `/souls calendar` | Mostrar calendario |
| `/souls calc <expresión>` | Calculadora |
| `/souls cmd <comando>` | Ejecutar comando shell |

#### Gestión de Tareas

| Comando | Descripción |
|---------|-------------|
| `/souls todo add <tarea>` | Añadir tarea |
| `/souls todo done <id>` | Completar tarea |
| `/souls todo pending` | Ver tareas pendientes |

#### Notas y Bookmarks

| Comando | Descripción |
|---------|-------------|
| `/souls note add <título> <contenido>` | Crear nota |
| `/souls note read <id>` | Leer nota |
| `/souls notes` | Listar notas |
| `/souls bookmark add <nombre> <url>` | Añadir bookmark |
| `/souls open <nombre>` | Abrir bookmark |

### Comandos de Reunión

| Comando | Descripción | Ejemplo |
|---------|-------------|---------|
| `/meeting new title="..."` | Crear reunión | `/meeting new title="Sprint Planning"` |
| `/meeting notes="..."` | Añadir notas | `/meeting notes="-discutimos el timeline"` |
| `/meeting action task="..."` | Añadir acción | `/meeting action task="Update docs"` |
| `/meeting list` | Listar reuniones | |
| `/meeting summary` | Generar resumen | |
| `/agenda <temas>` | Crear agenda | `/agenda Intro\|Discusion\|Cierre` |

### Comandos de Hooks

```bash
/hook web_search query="Python tips"
/hook code_analysis code="def foo(): pass"
/hook notification message="Done!" channel="terminal"
/hook ollama_tools tool="models"
/hook souls action="sys"
/hook meeting action="list"
/hook access action="project_access"
/hook email action="inbox"
```

### Comandos de Código

| Comando | Descripción |
|---------|-------------|
| `/analyze <código>` | Análisis completo (sintaxis, complejidad, seguridad) |
| `/security <código>` | Escaneo de seguridad |

### Comandos de Archivo

| Comando | Descripción |
|---------|-------------|
| `/tree [path]` | Árbol de directorios |
| `/ls [path]` | Listar archivos |
| `/size [path]` | Tamaño de directorio |
| `/sys` | Información del sistema |
| `/audit [path]` | Auditoría de permisos |

---

## Agentes Disponibles

Los agentes son asistentes especializados que puedes invocar con `@nombre`.

| Agente | Descripción |
|--------|-------------|
| `@python-expert` | Experto en código Python - mejoras, refactoring |
| `@javascript-expert` | Experto en JavaScript/Node.js |
| `@code-reviewer` | Revisiones de código - best practices |
| `@database-expert` | SQL, diseño de esquemas, optimización |
| `@security-expert` | Análisis de vulnerabilidades |
| `@docs-expert` | Documentación técnica |
| `@devops-expert` | Docker, CI/CD, infraestructura |
| `@api-expert` | APIs RESTful y GraphQL |
| `@performance-expert` | Optimización y rendimiento |
| `@architect` | Diseño de sistemas y arquitectura |

### Cómo Usar Agentes

```bash
# Invocar agente específico
@python-expert improve this function

@security-expert analyze for vulnerabilities

@devops-expert setup Docker

# Cambiar a agente como principal
@python-expert
# Ahora todas las msgs van a este agente
```

---

## Skills Disponibles

Los skills definen comportamiento reutilizable que los agentes pueden cargar dinámicamente.

| Skill | Descripción |
|-------|-------------|
| `python-tests` | Crear tests con pytest |
| `api-rest-design` | Diseñar APIs REST |
| `docker-setup` | Configuración Docker |
| `security-audit` | Análisis de seguridad |
| `database-migration` | Migraciones de base de datos |
| `ci-cd-pipeline` | Pipelines CI/CD |
| `performance-profile` | Perfilado de rendimiento |

### Cómo Usar Skills

```bash
# Usar skill explícitamente
Create tests using python-tests skill
Design API using api-rest-design skill
Add Docker using docker-setup skill
```

---

## Hooks del Sistema

Los hooks son módulos funcionales que proporcionan herramientas específicas.

### 1. Web Search Hook (`web_search.py`)

**Funcionalidades:**
- Búsqueda web (Wikipedia, Brave, Google, SearXNG)
- Fetch de páginas web con resumen LLM

**Funciones principales:**
- `run(query, provider, num_results)` - Búsqueda web
- `fetch_and_summarize(url, max_length)` - Descargar y resumir página

**Uso:**
```python
from src.hooks.web_search import WebSearchHook
hook = WebSearchHook()
result = hook.run("Python best practices")
result = hook.fetch_and_summarize("https://example.com")
```

### 2. Code Analysis Hook (`code_analysis.py`)

**Funcionalidades:**
- Verificación de sintaxis Python
- Análisis de complejidad
- Escaneo de seguridad
- Análisis de imports

**Funciones principales:**
- `run(code, file_path, analysis_type)` - Análisis completo o específico

**Tipos de análisis:**
- `full` - Todos los análisis
- `syntax` - Solo sintaxis
- `complexity` - Complejidad ciclomática
- `security` - Vulnerabilidades
- `imports` - Dependencias

**Uso:**
```python
from src.hooks.code_analysis import CodeAnalysisHook
hook = CodeAnalysisHook()
result = hook.run(code="def foo(): pass", analysis_type="full")
```

### 3. Notification Hook (`notification.py`)

**Funcionalidades:**
- Notificaciones de terminal
- Notificaciones macOS
- Webhooks genéricos
- Slack
- Email
- Abrir URLs en navegador

**Funciones principales:**
- `run(message, channel, title, **kwargs)` - Enviar notificación

**Canales:**
- `terminal` - Imprimir en consola
- `macos` - Notification Center de macOS
- `webhook` - Webhook genérico
- `slack` - Slack
- `email` - Email SMTP
- `open_url` - Abrir navegador

**Uso:**
```python
from src.hooks.notification import NotificationHook
hook = NotificationHook()
hook.run("Build complete!", channel="terminal")
hook.run("Alerta", channel="slack")
```

### 4. Ollama Tools Hook (`ollama_tools.py`)

**Funcionalidades:**
- Generación de texto
- Chat con historial
- Embeddings
- Listar modelos
- Descargar modelos
- Información de modelos

**Funciones principales:**
- `run(tool, **kwargs)` - Ejecutar herramienta
- `generate(prompt, model, system)` - Generar texto
- `chat(messages, model)` - Chat con contexto
- `embeddings(prompt, model)` - Embeddings
- `list_models()` - Modelos disponibles
- `translate(text, source, target)` - Traducir
- `summarize(text, max_length)` - Resumir

**Uso:**
```python
from src.hooks.ollama_tools import OllamaToolsHook
hook = OllamaToolsHook()
result = hook.list_models()
result = hook.generate("Hello world", model="llama3.1")
result = hook.translate("Hola", target_lang="english")
```

### 5. SOULS 2.0 Hook (`souls.py`)

**Funcionalidades:**
- Sistema de archivos (list, tree, size, info, find)
- Tareas (TODO)
- Notas
- Bookmarks
- Comandos shell
- Calculadora
- Calendario
- Información del sistema

**Funciones principales:**
- `run(action, **kwargs)` - Ejecutar acción SOULS

**Uso:**
```python
from src.hooks.souls import SOULS2Hook
hook = SOULS2Hook()
hook.run("sys")
hook.run("todo add", task="Finish report")
hook.run("cmd", command="ls -la")
```

### 6. Meeting Assistant Hook (`meeting_assistant.py`)

**Funcionalidades:**
- Crear reuniones
- Añadir notas
- Añadir action items
- Generar resúmenes
- Extraer action items de texto
- Crear agendas
- Plantillas de reuniones

**Funciones principales:**
- `run(action, **kwargs)` - Ejecutar acción

**Uso:**
```python
from src.hooks.meeting_assistant import MeetingAssistantHook
hook = MeetingAssistantHook()
hook.run("new", title="Sprint Planning")
hook.run("notes", notes="Discussed timeline")
hook.run("action", task="Update docs", assignee="John")
```

### 7. Email Hook (`email_hook.py`)

**Funcionalidades:**
- Conexión IMAP (Gmail, Outlook)
- Envío SMTP
- Bandeja de entrada
- Buscar emails
- Leer, responder, reenviar
- Gestionar etiquetas

**Funciones principales:**
- `run(action, **kwargs)` - Ejecutar acción

**Uso:**
```python
from src.hooks.email_hook import EmailHook
hook = EmailHook()
hook.run("inbox", limit=10)
hook.run("send", to="dest@example.com", subject="Test", body="Hello")
hook.run("search", query="important")
```

### 8. Access Control Hook (`access_control.py`)

**Funcionalidades:**
- Verificar permisos de archivos/directorios
- Auditoría de directorios
- Encontrar directorios legibles/escribibles
- Verificar acceso a home y proyecto

**Funciones principales:**
- `run(action, **kwargs)` - Ejecutar acción

**Uso:**
```python
from src.hooks.access_control import AccessControlHook
hook = AccessControlHook()
hook.run("check", path="/tmp")
hook.run("project_access")
hook.run("audit", path=".", max_depth=2)
```

---

## SOULS 2.0

Sistema operativo local integrado que permite interactuar con el sistema de archivos, ejecutar comandos shell, gestionar tareas, notas y más.

### Sistema de Archivos

```bash
/souls list /path           # Listar directorio
/souls tree /path            # Árbol de directorios
/souls size /path            # Tamaño
/souls info file.txt         # Información
/souls find "*.py"           # Buscar archivos
```

### Gestión de Tareas

```bash
/souls todo add Finish report        # Añadir tarea
/souls todo done 1                   # Completar tarea
/souls todo pending                   # Ver pendientes
```

### Notas

```bash
/souls note add "Meeting" "Notes..."  # Crear nota
/souls note read 1                     # Leer nota
/souls notes                          # Listar notas
```

### Utilidades

```bash
/souls sys              # Información del sistema
/souls calendar         # Calendario
/souls calc 2+2*3       # Calculadora
/souls cmd ls -la       # Ejecutar comando
/souls kill 1234        # Terminar proceso
```

---

## Configuración de Variables de Entorno

Para usar funcionalidades avanzadas, configura estas variables:

### Búsqueda Web

```bash
export BRAVE_API_KEY="tu_api_key"           # https://brave.com/search/api/
export GOOGLE_API_KEY="tu_api_key"           # Google Cloud Console
export GOOGLE_CSE_ID="tu_cse_id"             # Google Custom Search Engine
```

### Notificaciones

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/..."
export WEBHOOK_URL="https://tu-webhook.com/..."
```

### Email

```bash
# IMAP (recibir)
export EMAIL_HOST="imap.gmail.com"
export EMAIL_USER="tu@email.com"
export EMAIL_PASSWORD="password"  # O app password

# SMTP (enviar)
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="tu@email.com"
export SMTP_PASS="password"
```

**Nota:** Para Gmail, usa [App Passwords](https://support.google.com/accounts/answer/185833) en lugar de tu contraseña normal.

---

## Modelos de Ollama

El proyecto se conecta a Ollama local. Modelos recomendados:

| Modelo | Tamaño | Uso Recomendado |
|--------|--------|----------------|
| `llama3.1` | 4.9GB | General, balanceado |
| `qwen2.5-coder:7b` | 4.7GB | Coding especializado |
| `deepseek-r1` | 5.2GB | Reasoning complejo |
| `gemma3` | 3.3GB | Rápido, eficiente |
| `llama3.2` | 3.8GB | Latest Llama |

### Instalar Modelos

```bash
# Desde terminal
ollama pull llama3.1
ollama pull qwen2.5-coder:7b
ollama pull deepseek-r1
```

---

## Solución de Problemas

### Ollama no responde

```bash
# Verificar que Ollama está corriendo
ollama serve

# Ver modelos disponibles
ollama list
```

### Error de conexión

```bash
# Verificar URL en main.py (línea 24)
OLLAMA_URL = "http://localhost:11434"
```

### Permisos de archivos

```bash
# El hook de acceso puede ayudar
/souls audit /path
/hook access action="project_access"
```

---

## Licencia

MIT License - Proyecto educativo.

---

## Referencias

- [Documentación OpenCode](https://opencode.ai/docs)
- [Ollama](https://ollama.ai)
- [Wikipedia API](https://www.mediawiki.org/wiki/API:Main_page)