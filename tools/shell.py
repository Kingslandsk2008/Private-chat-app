"""Shell & Code Execution Tools — Bash, Python, Container execution.

From: Claude Code, Codex, Cursor, Antigravity CLI, Gemini
"""

import os
import sys
import subprocess
import tempfile
import json
import io
import contextlib


class ShellTools:
    def __init__(self, registry):
        self.registry = registry
        self.workdir = registry.base_dir

    def get_tools(self):
        return {
            "bash": (self.bash, "Execute shell commands", {
                "command": {"type": "string", "description": "Shell command to execute"},
                "workdir": {"type": "string", "optional": True, "description": "Working directory"},
                "timeout": {"type": "integer", "optional": True, "description": "Timeout in seconds"},
            }),
            "python": (self.python, "Execute Python code", {
                "code": {"type": "string", "description": "Python code to execute"},
                "timeout": {"type": "integer", "optional": True, "description": "Timeout in seconds"},
            }),
            "python_visible": (self.python_visible, "Execute Python with visible output (plots, charts)", {
                "code": {"type": "string", "description": "Python code with visualizations"},
                "timeout": {"type": "integer", "optional": True, "description": "Timeout in seconds"},
            }),
            "container_exec": (self.container_exec, "Execute command in container sandbox", {
                "image": {"type": "string", "optional": True, "description": "Container image"},
                "command": {"type": "string", "description": "Command to run"},
                "files": {"type": "object", "optional": True, "description": "Files to inject"},
            }),
        }

    def bash(self, command, workdir=None, timeout=30):
        cwd = workdir or self.workdir
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "success": result.returncode == 0,
            }
        except subprocess.TimeoutExpired:
            return {"error": f"Command timed out after {timeout}s", "stdout": "", "stderr": ""}
        except Exception as e:
            return {"error": str(e), "stdout": "", "stderr": ""}

    def python(self, code, timeout=30):
        stdout = io.StringIO()
        stderr = io.StringIO()
        result = {"stdout": "", "stderr": "", "returned": None, "success": True}
        try:
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exec_globals = {"__builtins__": __builtins__}
                exec(code, exec_globals)
            result["stdout"] = stdout.getvalue()
            result["stderr"] = stderr.getvalue()
        except Exception as e:
            result["stderr"] = stderr.getvalue() + str(e)
            result["success"] = False
            result["error"] = str(e)
        return result

    def python_visible(self, code, timeout=30):
        result = self.python(code, timeout)
        stdout = result.get("stdout", "")
        if "<img" in stdout or "![svg]" in stdout or "plotly" in code.lower():
            result["has_visualization"] = True
        return result

    def container_exec(self, command, image="python:3.11-slim", files=None, timeout=60):
        with tempfile.TemporaryDirectory() as tmpdir:
            if files:
                for name, content in files.items():
                    fp = os.path.join(tmpdir, name)
                    os.makedirs(os.path.dirname(fp), exist_ok=True)
                    with open(fp, "w") as f:
                        f.write(content)
            cmd = [
                "docker", "run", "--rm",
                "-v", f"{tmpdir}:/workspace",
                "-w", "/workspace",
                image,
                "sh", "-c", command,
            ]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
                return {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.returncode,
                    "success": result.returncode == 0,
                }
            except FileNotFoundError:
                return {"error": "Docker not available", "stdout": "", "stderr": ""}
            except subprocess.TimeoutExpired:
                return {"error": "Container timed out", "stdout": "", "stderr": ""}
            except Exception as e:
                return {"error": str(e), "stdout": "", "stderr": ""}
