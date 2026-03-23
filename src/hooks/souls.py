"""
SOULS 2.0 - Smart Operating Utility for Local System

Enhanced capabilities:
- File system operations
- Task management (TODO)
- Notes/Notas
- System monitoring
- Bookmarks
- Quick commands
- Calendar basics
"""

import os
import json
import shutil
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict


class SOULS2Hook:
    """SOULS 2.0 - Enhanced system utility."""
    
    def __init__(self):
        self.storage_dir = Path.home() / ".opencode_chat" / "souls"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.tasks_file = self.storage_dir / "tasks.json"
        self.notes_file = self.storage_dir / "notes.json"
        self.bookmarks_file = self.storage_dir / "bookmarks.json"
        self.config_file = self.storage_dir / "config.json"
    
    def run(self, action: str = None, **kwargs) -> dict:
        """
        Execute SOULS actions.
        
        Actions:
            - list: List directory contents
            - tree: Show directory tree
            - size: Calculate directory size
            - info: Get file/directory info
            - find: Search for files
            - system: Get system information
            
            - tasks: Task management
            - todo: Add/complete tasks
            - notes: Notes management
            - note: Add/read notes
            
            - bookmarks: Bookmark management
            - open: Open bookmark
            
            - cmd: Run shell command
            - kill: Kill process
            
            - calc: Quick calculator
        """
        actions = {
            "list": self._list_directory,
            "tree": self._show_tree,
            "size": self._calc_size,
            "info": self._get_info,
            "find": self._search_files,
            "search": self._search_files,
            "system": self._system_info,
            "sys": self._system_info,
            "calendar": self._show_calendar,
            "cal": self._show_calendar,
            
            "tasks": self._manage_tasks,
            "todo": self._manage_tasks,
            "add": self._add_task,
            "done": self._complete_task,
            "pending": self._list_pending_tasks,
            
            "notes": self._manage_notes,
            "note": self._manage_notes,
            "addnote": self._add_note,
            "readnote": self._read_note,
            
            "bookmarks": self._manage_bookmarks,
            "bookmark": self._add_bookmark,
            "open": self._open_bookmark,
            
            "cmd": self._run_command,
            "shell": self._run_command,
            "kill": self._kill_process,
            
            "calc": self._calculate,
            
            "calendar": self._show_calendar,
            "cal": self._show_calendar,
        }
        
        if action is None or action == "help":
            return self._show_help()
        
        if action not in actions:
            return {"error": f"Unknown action: {action}", "available": list(actions.keys())}
        
        return actions[action](**kwargs)
    
    def _show_help(self) -> dict:
        """Show SOULS help."""
        help_text = """
╔══════════════════════════════════════════════════════════════════════════╗
║                         SOULS 2.0 HELP                                 ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  FILE SYSTEM:                                                          ║
║    /souls list [path]         - List directory contents                ║
║    /souls tree [path] [depth] - Show directory tree                    ║
║    /souls size [path]          - Calculate directory size               ║
║    /souls info <path>         - Get file/directory info                 ║
║    /souls find <pattern>      - Search for files                        ║
║    /souls sys                 - System information                       ║
║                                                                          ║
║  TASKS (TODO):                                                        ║
║    /souls tasks              - Show all tasks                         ║
║    /souls todo add <task>     - Add new task                           ║
║    /souls todo done <id>      - Mark task as done                      ║
║    /souls todo pending        - Show pending tasks                      ║
║                                                                          ║
║  NOTES:                                                               ║
║    /souls notes              - Show all notes                          ║
║    /souls note add <title>   - Add new note                           ║
║    /souls note read <id>     - Read specific note                      ║
║                                                                          ║
║  BOOKMARKS:                                                          ║
║    /souls bookmarks          - List all bookmarks                       ║
║    /souls bookmark add <name> <url> - Add bookmark                    ║
║    /souls open <name>        - Open bookmark in browser                 ║
║                                                                          ║
║  SYSTEM:                                                              ║
║    /souls cmd <command>       - Run shell command                      ║
║    /souls kill <pid>          - Kill process by PID                   ║
║    /souls calc <expression>    - Quick calculator                       ║
║    /souls calendar            - Show current month calendar              ║
║                                                                          ║
║  EXAMPLES:                                                           ║
║    /souls todo add Finish report                                        ║
║    /souls note add \"Meeting notes\" \"Discussed Q1 goals\"              ║
║    /souls bookmark add GitHub https://github.com                       ║
║    /souls cmd ls -la                                                    ║
║    /souls calc 2+2*3                                                   ║
╚══════════════════════════════════════════════════════════════════════════╝
"""
        return {"help": help_text}
    
    # ==================== File System ====================
    
    def _list_directory(self, path: str = ".", show_hidden: bool = False, **kwargs) -> dict:
        """List directory contents."""
        try:
            target = Path(path).expanduser().resolve()
            
            if not target.exists():
                return {"error": f"Path does not exist: {path}"}
            
            if not target.is_dir():
                return {"error": f"Not a directory: {path}"}
            
            items = []
            for item in sorted(target.iterdir()):
                if not show_hidden and item.name.startswith('.'):
                    continue
                
                stat = item.stat()
                items.append({
                    "name": item.name,
                    "type": "dir" if item.is_dir() else "file",
                    "size": stat.st_size if item.is_file() else None,
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                })
            
            return {
                "action": "list",
                "path": str(target),
                "items": items,
                "total": len(items)
            }
        except PermissionError:
            return {"error": f"Permission denied: {path}"}
        except Exception as e:
            return {"error": str(e)}
    
    def _show_tree(self, path: str = ".", max_depth: int = 3, **kwargs) -> dict:
        """Show directory tree."""
        try:
            target = Path(path).expanduser().resolve()
            
            if not target.exists():
                return {"error": f"Path does not exist: {path}"}
            
            lines = []
            
            def walk_tree(current_path: Path, prefix: str = "", depth: int = 0):
                if depth >= max_depth:
                    lines.append(f"{prefix}...")
                    return
                
                try:
                    items = sorted(current_path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
                    
                    for i, item in enumerate(items):
                        is_last = i == len(items) - 1
                        current_prefix = "└── " if is_last else "├── "
                        icon = "📁" if item.is_dir() else "📄"
                        lines.append(f"{prefix}{current_prefix}{icon} {item.name}")
                        
                        if item.is_dir():
                            next_prefix = prefix + ("    " if is_last else "│   ")
                            walk_tree(item, next_prefix, depth + 1)
                except PermissionError:
                    lines.append(f"{prefix}└── [PERMISSION DENIED]")
            
            lines.insert(0, f"📂 {target.name}")
            walk_tree(target)
            
            return {"tree": "\n".join(lines), "path": str(target)}
        except Exception as e:
            return {"error": str(e)}
    
    def _calc_size(self, path: str = ".", **kwargs) -> dict:
        """Calculate directory size."""
        try:
            target = Path(path).expanduser().resolve()
            
            if not target.exists():
                return {"error": f"Path does not exist: {path}"}
            
            total_size = 0
            file_count = 0
            dir_count = 0
            
            if target.is_file():
                total_size = target.stat().st_size
                file_count = 1
            else:
                for item in target.rglob("*"):
                    if item.is_file():
                        try:
                            total_size += item.stat().st_size
                            file_count += 1
                        except:
                            pass
                    elif item.is_dir():
                        dir_count += 1
            
            return {
                "path": str(target),
                "total_bytes": total_size,
                "total_formatted": self._format_size(total_size),
                "file_count": file_count,
                "directory_count": dir_count
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_info(self, path: str = ".", **kwargs) -> dict:
        """Get detailed info about a path."""
        try:
            target = Path(path).expanduser().resolve()
            
            if not target.exists():
                return {"error": f"Path does not exist: {path}"}
            
            stat = target.stat()
            
            info = {
                "path": str(target),
                "name": target.name,
                "type": "directory" if target.is_dir() else "file",
                "size": stat.st_size if target.is_file() else None,
                "size_formatted": self._format_size(stat.st_size) if target.is_file() else None,
                "created": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "permissions": self._format_mode(stat.st_mode),
                "readable": os.access(target, os.R_OK),
                "writable": os.access(target, os.W_OK),
                "executable": os.access(target, os.X_OK),
            }
            
            return info
        except Exception as e:
            return {"error": str(e)}
    
    def _search_files(self, path: str = ".", pattern: str = "*", **kwargs) -> dict:
        """Search for files matching pattern."""
        try:
            target = Path(path).expanduser().resolve()
            
            if not target.exists():
                return {"error": f"Path does not exist: {path}"}
            
            matches = []
            for match in target.rglob(pattern):
                if match.is_file():
                    matches.append({
                        "path": str(match),
                        "name": match.name,
                        "size": match.stat().st_size,
                        "modified": datetime.fromtimestamp(match.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                    })
                    if len(matches) >= 100:
                        matches.append({"note": "... (truncated at 100 results)"})
                        break
            
            return {
                "pattern": pattern,
                "path": str(target),
                "matches": matches,
                "total": len(matches)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _system_info(self, **kwargs) -> dict:
        """Get system information."""
        try:
            import platform
            import psutil
            
            info = {
                "platform": f"{platform.system()} {platform.release()}",
                "hostname": platform.node(),
                "python": platform.python_version(),
                "user": os.environ.get("USER", "unknown"),
                "home": str(Path.home()),
                "cwd": str(Path.cwd()),
                "cpu": {
                    "cores": psutil.cpu_count(),
                    "usage": f"{psutil.cpu_percent(interval=0.1)}%",
                    "frequency": f"{psutil.cpu_freq().current:.0f} MHz" if hasattr(psutil, 'cpu_freq') and psutil.cpu_freq() else "N/A"
                },
                "memory": {
                    "total": self._format_size(psutil.virtual_memory().total),
                    "used": self._format_size(psutil.virtual_memory().used),
                    "available": self._format_size(psutil.virtual_memory().available),
                    "percent": f"{psutil.virtual_memory().percent}%"
                },
                "disk": {
                    "total": self._format_size(psutil.disk_usage("/").total),
                    "used": self._format_size(psutil.disk_usage("/").used),
                    "free": self._format_size(psutil.disk_usage("/").free),
                    "percent": f"{psutil.disk_usage('/').percent}%"
                },
                "network": {
                    "primary_ip": self._get_ip_address(),
                }
            }
            
            if hasattr(os, "getloadavg"):
                load = os.getloadavg()
                info["load"] = f"{load[0]:.2f} (1m), {load[1]:.2f} (5m), {load[2]:.2f} (15m)"
            
            return info
        except ImportError:
            return {
                "platform": platform.system(),
                "hostname": platform.node(),
                "user": os.environ.get("USER", "unknown"),
                "note": "Install psutil for full system info: pip install psutil"
            }
        except Exception as e:
            return {"error": str(e)}
    
    # ==================== Tasks (TODO) ====================
    
    def _manage_tasks(self, action: str = "list", **kwargs) -> dict:
        """Manage tasks."""
        tasks = self._load_tasks()
        
        if action in ["add", "new"]:
            return self._add_task(**kwargs)
        elif action in ["done", "complete"]:
            return self._complete_task(**kwargs)
        elif action == "pending":
            return self._list_pending_tasks()
        else:
            return self._list_all_tasks()
    
    def _load_tasks(self) -> List[Dict]:
        """Load tasks from file."""
        try:
            if self.tasks_file.exists():
                return json.loads(self.tasks_file.read_text())
        except:
            pass
        return []
    
    def _save_tasks(self, tasks: List[Dict]):
        """Save tasks to file."""
        self.tasks_file.write_text(json.dumps(tasks, indent=2))
    
    def _add_task(self, task: str = None, priority: str = "medium", **kwargs) -> dict:
        """Add a new task."""
        if not task:
            return {"error": "Task description required", "usage": "/souls todo add <task description>"}
        
        tasks = self._load_tasks()
        
        new_task = {
            "id": len(tasks) + 1,
            "task": task,
            "priority": priority,
            "status": "pending",
            "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "completed": None
        }
        
        tasks.append(new_task)
        self._save_tasks(tasks)
        
        return {
            "success": True,
            "message": f"Task added: {task}",
            "task": new_task
        }
    
    def _complete_task(self, task_id: str = None, **kwargs) -> dict:
        """Mark task as done."""
        if not task_id:
            return {"error": "Task ID required", "usage": "/souls todo done <id>"}
        
        try:
            task_id = int(task_id)
        except:
            return {"error": "Invalid task ID"}
        
        tasks = self._load_tasks()
        
        for task in tasks:
            if task["id"] == task_id:
                task["status"] = "completed"
                task["completed"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                self._save_tasks(tasks)
                return {"success": True, "message": f"Task completed: {task['task']}"}
        
        return {"error": f"Task {task_id} not found"}
    
    def _list_all_tasks(self) -> dict:
        """List all tasks."""
        tasks = self._load_tasks()
        
        pending = [t for t in tasks if t["status"] == "pending"]
        completed = [t for t in tasks if t["status"] == "completed"]
        
        return {
            "all": tasks,
            "pending": pending,
            "completed": completed,
            "counts": {"total": len(tasks), "pending": len(pending), "completed": len(completed)}
        }
    
    def _list_pending_tasks(self) -> dict:
        """List pending tasks."""
        tasks = self._load_tasks()
        pending = [t for t in tasks if t["status"] == "pending"]
        return {"pending": pending, "count": len(pending)}
    
    # ==================== Notes ====================
    
    def _manage_notes(self, action: str = "list", **kwargs) -> dict:
        """Manage notes."""
        notes = self._load_notes()
        
        if action in ["add", "new"]:
            return self._add_note(**kwargs)
        elif action in ["read", "show"]:
            return self._read_note(**kwargs)
        elif action == "delete":
            return self._delete_note(**kwargs)
        else:
            return self._list_all_notes()
    
    def _load_notes(self) -> List[Dict]:
        """Load notes from file."""
        try:
            if self.notes_file.exists():
                return json.loads(self.notes_file.read_text())
        except:
            pass
        return []
    
    def _save_notes(self, notes: List[Dict]):
        """Save notes to file."""
        self.notes_file.write_text(json.dumps(notes, indent=2))
    
    def _add_note(self, title: str = None, content: str = None, **kwargs) -> dict:
        """Add a new note."""
        if not title:
            return {"error": "Note title required", "usage": "/souls note add <title> <content>"}
        
        if content is None:
            content = ""
        
        notes = self._load_notes()
        
        new_note = {
            "id": len(notes) + 1,
            "title": title,
            "content": content,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "modified": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        notes.append(new_note)
        self._save_notes(notes)
        
        return {
            "success": True,
            "message": f"Note added: {title}",
            "note": new_note
        }
    
    def _read_note(self, note_id: str = None, **kwargs) -> dict:
        """Read a specific note."""
        notes = self._load_notes()
        
        if note_id:
            try:
                note_id = int(note_id)
                for note in notes:
                    if note["id"] == note_id:
                        return note
                return {"error": f"Note {note_id} not found"}
            except:
                return {"error": "Invalid note ID"}
        
        return self._list_all_notes()
    
    def _delete_note(self, note_id: str = None, **kwargs) -> dict:
        """Delete a note."""
        if not note_id:
            return {"error": "Note ID required"}
        
        try:
            note_id = int(note_id)
        except:
            return {"error": "Invalid note ID"}
        
        notes = self._load_notes()
        notes = [n for n in notes if n["id"] != note_id]
        self._save_notes(notes)
        
        return {"success": True, "message": f"Note {note_id} deleted"}
    
    def _list_all_notes(self) -> dict:
        """List all notes."""
        notes = self._load_notes()
        return {"notes": notes, "count": len(notes)}
    
    # ==================== Bookmarks ====================
    
    def _manage_bookmarks(self, action: str = "list", **kwargs) -> dict:
        """Manage bookmarks."""
        if action in ["add", "new"]:
            return self._add_bookmark(**kwargs)
        elif action in ["open", "goto"]:
            return self._open_bookmark(**kwargs)
        else:
            return self._list_bookmarks()
    
    def _load_bookmarks(self) -> List[Dict]:
        """Load bookmarks from file."""
        try:
            if self.bookmarks_file.exists():
                return json.loads(self.bookmarks_file.read_text())
        except:
            pass
        return []
    
    def _save_bookmarks(self, bookmarks: List[Dict]):
        """Save bookmarks to file."""
        self.bookmarks_file.write_text(json.dumps(bookmarks, indent=2))
    
    def _add_bookmark(self, name: str = None, url: str = None, **kwargs) -> dict:
        """Add a bookmark."""
        if not name or not url:
            return {"error": "Name and URL required", "usage": "/souls bookmark add <name> <url>"}
        
        bookmarks = self._load_bookmarks()
        
        bookmark = {
            "id": len(bookmarks) + 1,
            "name": name,
            "url": url,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        bookmarks.append(bookmark)
        self._save_bookmarks(bookmarks)
        
        return {
            "success": True,
            "message": f"Bookmark added: {name}",
            "bookmark": bookmark
        }
    
    def _open_bookmark(self, name: str = None, **kwargs) -> dict:
        """Open a bookmark in browser."""
        if not name:
            return {"error": "Bookmark name required", "usage": "/souls open <name>"}
        
        bookmarks = self._load_bookmarks()
        
        for bm in bookmarks:
            if bm["name"].lower() == name.lower():
                try:
                    import webbrowser
                    webbrowser.open(bm["url"])
                    return {"success": True, "message": f"Opened: {bm['url']}"}
                except Exception as e:
                    return {"error": str(e)}
        
        return {"error": f"Bookmark '{name}' not found"}
    
    def _list_bookmarks(self) -> dict:
        """List all bookmarks."""
        bookmarks = self._load_bookmarks()
        return {"bookmarks": bookmarks, "count": len(bookmarks)}
    
    # ==================== System Commands ====================
    
    def _run_command(self, command: str = None, **kwargs) -> dict:
        """Run shell command."""
        if not command:
            return {"error": "Command required", "usage": "/souls cmd <command>"}
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "command": command,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {"error": "Command timed out (30s limit)"}
        except Exception as e:
            return {"error": str(e)}
    
    def _kill_process(self, pid: str = None, **kwargs) -> dict:
        """Kill a process by PID."""
        if not pid:
            return {"error": "PID required", "usage": "/souls kill <pid>"}
        
        try:
            pid = int(pid)
            os.kill(pid, 9)
            return {"success": True, "message": f"Process {pid} killed"}
        except ProcessLookupError:
            return {"error": f"Process {pid} not found"}
        except PermissionError:
            return {"error": f"Permission denied. Cannot kill process {pid}"}
        except Exception as e:
            return {"error": str(e)}
    
    def _calculate(self, expression: str = None, **kwargs) -> dict:
        """Simple calculator."""
        if not expression:
            return {"error": "Expression required", "usage": "/souls calc 2+2*3"}
        
        try:
            result = eval(expression)
            return {
                "expression": expression,
                "result": result
            }
        except Exception as e:
            return {"error": f"Invalid expression: {e}"}
    
    def _show_calendar(self, **kwargs) -> dict:
        """Show calendar for current month."""
        import calendar
        
        now = datetime.now()
        cal = calendar.TextCalendar(calendar.SUNDAY)
        month_cal = cal.formatmonth(now.year, now.month)
        
        return {
            "calendar": month_cal,
            "month": now.strftime("%B %Y"),
            "today": now.strftime("%Y-%m-%d %A")
        }
    
    # ==================== Helpers ====================
    
    def _format_size(self, bytes_size: int) -> str:
        """Format bytes to human readable size."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_size < 1024:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.1f} PB"
    
    def _format_mode(self, mode: int) -> str:
        """Format file mode."""
        perms = []
        for who, shift in [("USR", 6), ("GRP", 3), ("OTH", 0)]:
            for what, char in [((mode >> (shift + 2)) & 1, 'r'),
                               ((mode >> (shift + 1)) & 1, 'w'),
                               ((mode >> shift) & 1, 'x')]:
                perms.append(char if what else '-')
        return "".join(perms) if len(perms) >= 9 else "---------"
    
    def _get_ip_address(self) -> str:
        """Get primary IP address."""
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"


if __name__ == "__main__":
    hook = SOULS2Hook()
    result = hook.run("system")
    print(json.dumps(result, indent=2))
