"""Git Tools — Repository management, commits, branches, diffs, logs.

From: Claude Code, GitHub Copilot, Codex (GitHub MCP)
"""

import os
import subprocess
import json
from pathlib import Path


class GitTools:
    def __init__(self, registry):
        self.registry = registry
        self.base_dir = registry.base_dir

    def get_tools(self):
        return {
            "git_status": (self.git_status, "Show git status", {
                "path": {"type": "string", "optional": True, "description": "Repository path"},
            }),
            "git_diff": (self.git_diff, "Show git diff", {
                "path": {"type": "string", "optional": True, "description": "Repository path"},
                "staged": {"type": "boolean", "optional": True, "description": "Show staged changes"},
            }),
            "git_log": (self.git_log, "Show git log", {
                "path": {"type": "string", "optional": True, "description": "Repository path"},
                "count": {"type": "integer", "optional": True, "description": "Number of commits"},
            }),
            "git_commit": (self.git_commit, "Create a git commit", {
                "path": {"type": "string", "optional": True, "description": "Repository path"},
                "message": {"type": "string", "description": "Commit message"},
                "files": {"type": "array", "optional": True, "description": "Files to stage (all if empty)"},
            }),
            "git_branch": (self.git_branch, "List, create, or switch branches", {
                "path": {"type": "string", "optional": True, "description": "Repository path"},
                "action": {"type": "string", "optional": True, "description": "list|create|checkout|delete"},
                "name": {"type": "string", "optional": True, "description": "Branch name"},
            }),
            "git_push": (self.git_push, "Push to remote", {
                "path": {"type": "string", "optional": True, "description": "Repository path"},
                "remote": {"type": "string", "optional": True, "description": "Remote name"},
                "branch": {"type": "string", "optional": True, "description": "Branch to push"},
            }),
            "git_pull": (self.git_pull, "Pull from remote", {
                "path": {"type": "string", "optional": True, "description": "Repository path"},
                "remote": {"type": "string", "optional": True, "description": "Remote name"},
                "branch": {"type": "string", "optional": True, "description": "Branch to pull"},
            }),
            "git_init": (self.git_init, "Initialize git repository", {
                "path": {"type": "string", "optional": True, "description": "Repository path"},
            }),
            "git_clone": (self.git_clone, "Clone a repository", {
                "url": {"type": "string", "description": "Repository URL"},
                "path": {"type": "string", "optional": True, "description": "Destination path"},
            }),
            "git_add": (self.git_add, "Stage files", {
                "path": {"type": "string", "optional": True, "description": "Repository path"},
                "files": {"type": "array", "description": "Files to stage"},
            }),
        }

    def _git(self, args, path=None):
        cwd = path or self.base_dir
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "success": result.returncode == 0,
            }
        except FileNotFoundError:
            return {"error": "Git not found. Install git on your system."}
        except subprocess.TimeoutExpired:
            return {"error": "Git command timed out"}
        except Exception as e:
            return {"error": str(e)}

    def git_status(self, path=None):
        return self._git(["status", "--porcelain"], path)

    def git_diff(self, path=None, staged=False):
        args = ["diff"]
        if staged:
            args.append("--cached")
        return self._git(args, path)

    def git_log(self, path=None, count=10):
        return self._git(["log", f"-{count}", "--oneline", "--graph"], path)

    def git_commit(self, message, files=None, path=None):
        if files:
            self._git(["add"] + files, path)
        else:
            self._git(["add", "-A"], path)
        return self._git(["commit", "-m", message], path)

    def git_branch(self, action="list", name=None, path=None):
        if action == "list":
            return self._git(["branch"], path)
        elif action == "create" and name:
            return self._git(["branch", name], path)
        elif action == "checkout" and name:
            return self._git(["checkout", name], path)
        elif action == "delete" and name:
            return self._git(["branch", "-d", name], path)
        return {"error": f"Unknown action: {action}"}

    def git_push(self, remote="origin", branch=None, path=None):
        args = ["push", remote]
        if branch:
            args.append(branch)
        return self._git(args, path)

    def git_pull(self, remote="origin", branch=None, path=None):
        args = ["pull", remote]
        if branch:
            args.append(branch)
        return self._git(args, path)

    def git_init(self, path=None):
        return self._git(["init"], path)

    def git_clone(self, url, path=None):
        cwd = path or os.path.dirname(self.base_dir)
        try:
            result = subprocess.run(
                ["git", "clone", url],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=120,
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "success": result.returncode == 0,
            }
        except Exception as e:
            return {"error": str(e)}

    def git_add(self, files, path=None):
        return self._git(["add"] + files, path)
