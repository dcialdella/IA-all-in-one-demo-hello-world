"""
Code Analysis Hook - Analyze code for various purposes

Provides:
- Syntax checking
- Complexity analysis
- Security scanning
- Documentation generation
- Import analysis
"""

import ast
import re
from pathlib import Path
from typing import Optional


class CodeAnalysisHook:
    """Analyze code for various metrics and issues."""
    
    def run(self, code: str = None, file_path: str = None, analysis_type: str = "full", **kwargs) -> dict:
        """
        Analyze code.
        
        Args:
            code: Code string to analyze
            file_path: Path to file to analyze
            analysis_type: "full", "syntax", "complexity", "security", "imports"
        
        Returns:
            dict with analysis results
        """
        if file_path:
            try:
                code = Path(file_path).read_text()
            except Exception as e:
                return {"error": f"Cannot read file: {e}"}
        
        if not code:
            return {"error": "No code provided"}
        
        results = {}
        
        if analysis_type in ["full", "syntax"]:
            results["syntax"] = self._check_syntax(code)
        
        if analysis_type in ["full", "complexity"]:
            results["complexity"] = self._analyze_complexity(code)
        
        if analysis_type in ["full", "security"]:
            results["security"] = self._scan_security(code)
        
        if analysis_type in ["full", "imports"]:
            results["imports"] = self._analyze_imports(code)
        
        if analysis_type == "full":
            results["summary"] = self._generate_summary(results)
        
        return results
    
    def _check_syntax(self, code: str) -> dict:
        """Check Python syntax."""
        try:
            ast.parse(code)
            return {"valid": True, "errors": []}
        except SyntaxError as e:
            return {
                "valid": False,
                "errors": [{
                    "line": e.lineno,
                    "column": e.offset,
                    "message": str(e)
                }]
            }
    
    def _analyze_complexity(self, code: str) -> dict:
        """Analyze code complexity."""
        try:
            tree = ast.parse(code)
        except:
            return {"error": "Cannot parse code"}
        
        complexity = {
            "functions": 0,
            "classes": 0,
            "loops": 0,
            "conditionals": 0,
            "nested_depth": 0,
            "lines_of_code": len(code.splitlines()),
        }
        
        max_depth = [0]
        
        class ComplexityVisitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                complexity["functions"] += 1
                self.generic_visit(node)
            
            def visit_AsyncFunctionDef(self, node):
                complexity["functions"] += 1
                self.generic_visit(node)
            
            def visit_ClassDef(self, node):
                complexity["classes"] += 1
                self.generic_visit(node)
            
            def visit_For(self, node):
                complexity["loops"] += 1
                self.generic_visit(node)
            
            def visit_While(self, node):
                complexity["loops"] += 1
                self.generic_visit(node)
            
            def visit_If(self, node):
                complexity["conditionals"] += 1
                self.generic_visit(node)
            
            def visit_Try(self, node):
                complexity["conditionals"] += 1
                for handler in node.handlers:
                    complexity["conditionals"] += 1
                self.generic_visit(node)
        
        visitor = ComplexityVisitor()
        visitor.visit(tree)
        
        complexity["score"] = (
            complexity["functions"] * 1 +
            complexity["classes"] * 2 +
            complexity["loops"] * 2 +
            complexity["conditionals"] * 1
        )
        
        if complexity["score"] < 10:
            complexity["rating"] = "Low (Good)"
        elif complexity["score"] < 25:
            complexity["rating"] = "Medium (Acceptable)"
        elif complexity["score"] < 50:
            complexity["rating"] = "High (Consider refactoring)"
        else:
            complexity["rating"] = "Very High (Needs refactoring)"
        
        return complexity
    
    def _scan_security(self, code: str) -> dict:
        """Scan for security issues."""
        issues = []
        
        patterns = [
            (r"eval\s*\(", "Use of eval() - code injection risk", "HIGH"),
            (r"exec\s*\(", "Use of exec() - code injection risk", "HIGH"),
            (r"os\.system\s*\(", "Use of os.system() - shell injection risk", "HIGH"),
            (r"subprocess\.call\s*\([^,)]*shell\s*=\s*True", "shell=True in subprocess - shell injection risk", "HIGH"),
            (r"pickle\.loads?", "Use of pickle - arbitrary code execution risk", "HIGH"),
            (r"yaml\.load\s*\([^,)]*\)(?!.*Loader\s*=\s*yaml\.SafeLoader)", "yaml.load without SafeLoader - arbitrary code execution risk", "HIGH"),
            (r"password\s*=\s*['\"][^'\"]+['\"]", "Hardcoded password detected", "CRITICAL"),
            (r"api[_-]?key\s*=\s*['\"][^'\"]+['\"]", "Hardcoded API key detected", "CRITICAL"),
            (r"secret\s*=\s*['\"][^'\"]+['\"]", "Hardcoded secret detected", "CRITICAL"),
            (r"input\s*\(", "Use of input() - potential injection", "MEDIUM"),
            (r"assert\s+", "Assert statements removed in optimization", "LOW"),
        ]
        
        lines = code.splitlines()
        for i, line in enumerate(lines, 1):
            for pattern, message, severity in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append({
                        "line": i,
                        "message": message,
                        "severity": severity,
                        "code": line.strip()
                    })
        
        security_score = 100 - (len(issues) * 10)
        
        return {
            "issues": issues,
            "issue_count": len(issues),
            "security_score": max(0, security_score)
        }
    
    def _analyze_imports(self, code: str) -> dict:
        """Analyze imports."""
        try:
            tree = ast.parse(code)
        except:
            return {"error": "Cannot parse code"}
        
        imports = {
            "stdlib": [],
            "third_party": [],
            "local": [],
            "missing": []
        }
        
        stdlib_modules = {
            "os", "sys", "re", "json", "datetime", "time", "math", "random",
            "collections", "itertools", "functools", "operator", "string",
            "pathlib", "typing", "abc", "enum", "dataclasses", "copy",
            "pickle", "sqlite3", "csv", "io", "buffer", "struct", "base64",
            "hashlib", "hmac", "secrets", "ssl", "socket", "urllib",
            "http", "email", "html", "xml", "argparse", "configparser",
            "logging", "warnings", "threading", "multiprocessing", "asyncio",
            "unittest", "doctest", "inspect", "gc", "weakref", "types",
            "contextlib", "atexit", "traceback", "linecache", "tokenize"
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name.split('.')[0]
                    if name in stdlib_modules:
                        imports["stdlib"].append(alias.name)
                    else:
                        imports["third_party"].append(alias.name)
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    name = node.module.split('.')[0]
                    if name in stdlib_modules:
                        imports["stdlib"].append(node.module)
                    else:
                        imports["third_party"].append(node.module)
        
        imports["stdlib"] = sorted(set(imports["stdlib"]))
        imports["third_party"] = sorted(set(imports["third_party"]))
        imports["local"] = sorted(set(imports["local"]))
        
        return imports
    
    def _generate_summary(self, results: dict) -> str:
        """Generate a human-readable summary."""
        parts = []
        
        if results.get("syntax", {}).get("valid"):
            parts.append("✓ Syntax is valid")
        else:
            parts.append("✗ Syntax errors found")
        
        if "complexity" in results:
            c = results["complexity"]
            parts.append(f"• {c['functions']} functions, {c['classes']} classes")
            parts.append(f"• Complexity: {c.get('rating', 'Unknown')}")
        
        if "security" in results:
            s = results["security"]
            parts.append(f"• {s['issue_count']} security issues (score: {s['security_score']}/100)")
        
        return "\n".join(parts)
    
    def help(self) -> str:
        return """
Code Analysis Hook
=================
Usage: /hook code_analysis code="..." analysis_type="full"

Analysis types:
- full (default): All checks
- syntax: Check Python syntax
- complexity: Measure code complexity
- security: Scan for security issues
- imports: Analyze dependencies

Examples:
  /hook code_analysis file_path="src/main.py"
  /hook code_analysis code="def foo(): pass" analysis_type="security"
"""


if __name__ == "__main__":
    hook = CodeAnalysisHook()
    code = '''
import os
import json

API_KEY = "hardcoded_key_12345"

def process_data(data):
    if data:
        for item in data:
            eval(item)  # Security issue
    return True
'''
    result = hook.run(code=code, analysis_type="full")
    import json
    print(json.dumps(result, indent=2))
