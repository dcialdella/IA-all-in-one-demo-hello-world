"""
Access Control Hook - Verify and manage local folder/file access

Provides:
- Permission checking
- Access audit
- Path validation
- Directory access verification
"""

import os
import stat
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict


class AccessControlHook:
    """Verify and manage local folder and file access."""
    
    def run(self, action: str = None, **kwargs) -> dict:
        """
        Execute access control actions.
        
        Actions:
            - check: Check access for a path
            - audit: Audit directory access recursively
            - verify: Verify specific permissions
            - blocked: Find blocked paths
            - writable_dirs: Find all writable directories
            - readable_dirs: Find all readable directories
            - home_access: Check home directory access
            - project_access: Check project directory access
        """
        actions = {
            "check": self._check_path_access,
            "audit": self._audit_directory,
            "verify": self._verify_permissions,
            "blocked": self._find_blocked_paths,
            "writable_dirs": self._find_writable_dirs,
            "readable_dirs": self._find_readable_dirs,
            "home_access": self._check_home_access,
            "project_access": self._check_project_access,
        }
        
        if action is None:
            return {"available_actions": list(actions.keys())}
        
        if action not in actions:
            return {"error": f"Unknown action: {action}", "available": list(actions.keys())}
        
        return actions[action](**kwargs)
    
    def _check_path_access(self, path: str = ".", **kwargs) -> dict:
        """Check all access permissions for a path."""
        try:
            target = Path(path).expanduser().resolve()
            
            result = {
                "path": str(target),
                "exists": target.exists(),
                "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            if not target.exists():
                parent = target.parent
                result["parent_exists"] = parent.exists()
                result["can_create"] = parent.exists() and os.access(parent, os.W_OK)
                result["message"] = f"Path does not exist. Can create: {result['can_create']}"
                return result
            
            result["is_directory"] = target.is_dir()
            result["is_file"] = target.is_file()
            result["is_symlink"] = target.is_symlink()
            
            if target.is_dir():
                result["can_list"] = os.access(target, os.R_OK)
                result["can_create_files"] = os.access(target, os.W_OK)
                result["can_execute"] = os.access(target, os.X_OK)
            else:
                result["can_read"] = os.access(target, os.R_OK)
                result["can_write"] = os.access(target, os.W_OK)
                result["can_execute"] = os.access(target, os.X_OK)
            
            if hasattr(os, "stat"):
                st = os.stat(target)
                result["mode"] = oct(st.st_mode)
                result["uid"] = st.st_uid
                result["gid"] = st.st_gid
                result["permissions"] = self._format_mode(st.st_mode)
            
            result["is_accessible"] = all([
                target.exists(),
                os.access(target, os.R_OK),
                os.access(target.parent, os.X_OK) if target.exists() else False
            ])
            
            return result
        except PermissionError as e:
            return {"error": "Permission denied", "details": str(e)}
        except Exception as e:
            return {"error": str(e)}
    
    def _audit_directory(self, path: str = ".", max_depth: int = 2, **kwargs) -> dict:
        """Audit directory contents and their permissions."""
        try:
            target = Path(path).expanduser().resolve()
            
            if not target.exists():
                return {"error": f"Directory does not exist: {path}"}
            
            if not target.is_dir():
                return {"error": f"Not a directory: {path}"}
            
            audit = {
                "path": str(target),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "summary": {
                    "total_items": 0,
                    "readable": 0,
                    "writable": 0,
                    "executable": 0,
                    "blocked": 0
                },
                "items": []
            }
            
            def audit_recursive(current_path: Path, depth: int = 0):
                if depth > max_depth:
                    return
                
                try:
                    for item in current_path.iterdir():
                        if item.name.startswith('.') and item.name not in ['.git', '.opencode']:
                            continue
                        
                        audit["summary"]["total_items"] += 1
                        
                        item_info = {
                            "path": str(item),
                            "name": item.name,
                            "type": "dir" if item.is_dir() else "file"
                        }
                        
                        try:
                            can_read = os.access(item, os.R_OK)
                            can_write = os.access(item, os.W_OK)
                            can_exec = os.access(item, os.X_OK)
                            
                            item_info["read"] = can_read
                            item_info["write"] = can_write
                            item_info["execute"] = can_exec
                            item_info["accessible"] = can_read and can_exec
                            
                            if can_read:
                                audit["summary"]["readable"] += 1
                            if can_write:
                                audit["summary"]["writable"] += 1
                            if can_exec:
                                audit["summary"]["executable"] += 1
                            if not can_read:
                                audit["summary"]["blocked"] += 1
                                item_info["blocked"] = True
                            
                        except PermissionError:
                            item_info["blocked"] = True
                            audit["summary"]["blocked"] += 1
                        
                        audit["items"].append(item_info)
                        
                        if item.is_dir() and "blocked" not in item_info:
                            audit_recursive(item, depth + 1)
                            
                except PermissionError:
                    pass
            
            audit_recursive(target)
            
            audit["accessibility_score"] = round(
                (audit["summary"]["readable"] / max(audit["summary"]["total_items"], 1)) * 100, 1
            )
            
            return audit
        except Exception as e:
            return {"error": str(e)}
    
    def _verify_permissions(self, path: str = ".", read: bool = True, 
                           write: bool = False, execute: bool = False, **kwargs) -> dict:
        """Verify specific permissions exist."""
        try:
            target = Path(path).expanduser().resolve()
            
            checks = {
                "path": str(target),
                "requested": {
                    "read": read,
                    "write": write,
                    "execute": execute
                }
            }
            
            if not target.exists():
                parent = target.parent
                checks["exists"] = False
                checks["can_create"] = parent.exists() and os.access(parent, os.W_OK)
                return checks
            
            checks["exists"] = True
            
            if read:
                checks["read_ok"] = os.access(target, os.R_OK)
            if write:
                checks["write_ok"] = os.access(target, os.W_OK)
            if execute:
                checks["execute_ok"] = os.access(target, os.X_OK)
            
            all_checks = [checks.get(f"{p}_ok", True) for p in ["read", "write", "execute"] 
                         if kwargs.get(p)]
            checks["all_permissions_granted"] = all(all_checks) if all_checks else True
            
            return checks
        except Exception as e:
            return {"error": str(e)}
    
    def _find_blocked_paths(self, paths: List[str] = None, **kwargs) -> dict:
        """Find blocked/unreadable paths from a list."""
        if paths is None:
            paths = [str(Path.cwd()), str(Path.home())]
        
        blocked = []
        accessible = []
        
        for path_str in paths:
            path = Path(path_str).expanduser().resolve()
            if os.access(path, os.R_OK):
                accessible.append(str(path))
            else:
                blocked.append(str(path))
        
        return {
            "blocked": blocked,
            "accessible": accessible,
            "blocked_count": len(blocked),
            "accessible_count": len(accessible)
        }
    
    def _find_writable_dirs(self, base_path: str = ".", max_depth: int = 2, **kwargs) -> dict:
        """Find all writable directories under a path."""
        try:
            target = Path(base_path).expanduser().resolve()
            
            if not target.exists():
                return {"error": f"Path does not exist: {base_path}"}
            
            writable = []
            
            def search_dirs(current: Path, depth: int = 0):
                if depth > max_depth:
                    return
                
                if os.access(current, os.W_OK):
                    writable.append({
                        "path": str(current),
                        "name": current.name,
                        "depth": depth
                    })
                
                if current.is_dir():
                    try:
                        for item in current.iterdir():
                            if item.is_dir() and not item.is_symlink():
                                search_dirs(item, depth + 1)
                    except PermissionError:
                        pass
            
            search_dirs(target)
            
            return {
                "base_path": str(target),
                "writable_directories": writable,
                "count": len(writable)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _find_readable_dirs(self, base_path: str = ".", max_depth: int = 2, **kwargs) -> dict:
        """Find all readable directories under a path."""
        try:
            target = Path(base_path).expanduser().resolve()
            
            if not target.exists():
                return {"error": f"Path does not exist: {base_path}"}
            
            readable = []
            
            def search_dirs(current: Path, depth: int = 0):
                if depth > max_depth:
                    return
                
                if os.access(current, os.R_OK):
                    readable.append({
                        "path": str(current),
                        "name": current.name,
                        "depth": depth
                    })
                
                if current.is_dir():
                    try:
                        for item in current.iterdir():
                            if item.is_dir() and not item.is_symlink():
                                search_dirs(item, depth + 1)
                    except PermissionError:
                        pass
            
            search_dirs(target)
            
            return {
                "base_path": str(target),
                "readable_directories": readable,
                "count": len(readable)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _check_home_access(self, **kwargs) -> dict:
        """Check access to common home directory locations."""
        home = Path.home()
        
        paths_to_check = {
            "home": home,
            "desktop": home / "Desktop",
            "documents": home / "Documents",
            "downloads": home / "Downloads",
            "projects": home / "Projects",
            "code": home / "Code",
            "opencode_config": home / ".config" / "opencode",
        }
        
        results = {}
        
        for name, path in paths_to_check.items():
            result = {"path": str(path), "exists": path.exists()}
            
            if path.exists():
                result["readable"] = os.access(path, os.R_OK)
                result["writable"] = os.access(path, os.W_OK)
                result["accessible"] = result["readable"]
                
                if path.is_dir():
                    try:
                        result["item_count"] = len(list(path.iterdir()))
                    except:
                        result["accessible"] = False
            else:
                result["readable"] = False
                result["writable"] = False
                result["accessible"] = False
            
            results[name] = result
        
        accessible_count = sum(1 for r in results.values() if r.get("accessible"))
        
        return {
            "home_directory": str(home),
            "paths": results,
            "accessible_count": accessible_count,
            "total_count": len(paths_to_check)
        }
    
    def _check_project_access(self, **kwargs) -> dict:
        """Check access to the current project directory."""
        project_dir = Path.cwd()
        
        result = {
            "project_path": str(project_dir),
            "project_name": project_dir.name,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        important_paths = {
            "root": project_dir,
            "src": project_dir / "src",
            "config": project_dir / ".opencode",
            "tests": project_dir / "tests",
            "readme": project_dir / "README.md",
            "git": project_dir / ".git",
        }
        
        result["paths"] = {}
        
        for name, path in important_paths.items():
            info = {"path": str(path), "exists": path.exists()}
            if path.exists():
                info["readable"] = os.access(path, os.R_OK)
                info["writable"] = os.access(path, os.W_OK)
                if path.is_dir():
                    try:
                        info["item_count"] = len(list(path.iterdir()))
                    except:
                        pass
            result["paths"][name] = info
        
        all_readable = all(
            info.get("readable", False) 
            for info in result["paths"].values() 
            if info["exists"]
        )
        
        result["all_paths_accessible"] = all_readable
        
        return result
    
    def _format_mode(self, mode: int) -> str:
        """Format file mode to readable permissions string."""
        perms = []
        
        for who, shift in [("USR", 6), ("GRP", 3), ("OTH", 0)]:
            for what, char in [((mode >> (shift + 2)) & 1, 'r'),
                               ((mode >> (shift + 1)) & 1, 'w'),
                               ((mode >> shift) & 1, 'x')]:
                perms.append(char if what else '-')
        
        return "".join(perms)
    
    def help(self) -> str:
        return """
Access Control Hook - Verify local folder/file access
======================================================
Usage: /hook access action="check" path="/path/to/folder"

Actions:
  check          - Check access for a specific path
  audit          - Audit directory recursively
  verify         - Verify specific permissions
  blocked        - Find blocked paths
  writable_dirs  - Find all writable directories
  readable_dirs  - Find all readable directories
  home_access    - Check home directory access
  project_access - Check current project access

Examples:
  /hook access action="check" path="/home/user/Documents"
  /hook access action="audit" path="." max_depth=3
  /hook access action="verify" path="/tmp" read=true write=true
  /hook access action="home_access"
  /hook access action="project_access"
"""


if __name__ == "__main__":
    hook = AccessControlHook()
    
    result = hook.run(action="project_access")
    print(json.dumps(result, indent=2) if isinstance(result, dict) else result)
