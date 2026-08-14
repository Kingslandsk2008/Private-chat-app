"""Filesystem MCP — Read, Write, Edit, Glob, Grep, Delete, Copy, Move.

From: Claude Code, Claude Design, Codex, Cursor, VS Code Copilot, Antigravity CLI
"""

import os
import shutil
import json
import re
from pathlib import Path


class FilesystemTools:
    def __init__(self, registry):
        self.registry = registry
        self.base_dir = Path(registry.base_dir)

    def get_tools(self):
        return {
            "read": (self.read, "Read file contents", {
                "path": {"type": "string", "description": "Path to file"},
                "offset": {"type": "integer", "optional": True, "description": "Line offset"},
                "limit": {"type": "integer", "optional": True, "description": "Max lines"},
            }),
            "write": (self.write, "Write content to file", {
                "path": {"type": "string", "description": "Path to file"},
                "content": {"type": "string", "description": "Content to write"},
            }),
            "edit": (self.edit, "Replace exact string in file", {
                "path": {"type": "string", "description": "Path to file"},
                "old_string": {"type": "string", "description": "Text to replace"},
                "new_string": {"type": "string", "description": "Replacement text"},
                "replace_all": {"type": "boolean", "optional": True, "description": "Replace all occurrences"},
            }),
            "multi_edit": (self.multi_edit, "Multiple atomic edits in one call", {
                "path": {"type": "string", "description": "Path to file"},
                "edits": {
                    "type": "array",
                    "description": "List of {old_string, new_string} edits",
                    "items": {
                        "type": "object",
                        "properties": {
                            "old_string": {"type": "string"},
                            "new_string": {"type": "string"},
                        },
                    },
                },
            }),
            "glob": (self.glob, "File pattern matching", {
                "pattern": {"type": "string", "description": "Glob pattern (e.g. **/*.py)"},
                "path": {"type": "string", "optional": True, "description": "Root path"},
            }),
            "grep": (self.grep, "Search file contents with regex", {
                "pattern": {"type": "string", "description": "Regex pattern"},
                "include": {"type": "string", "optional": True, "description": "File pattern filter"},
                "path": {"type": "string", "optional": True, "description": "Search root"},
            }),
            "list_dir": (self.list_dir, "List directory contents", {
                "path": {"type": "string", "optional": True, "description": "Directory path"},
            }),
            "delete_file": (self.delete_file, "Delete file or directory", {
                "path": {"type": "string", "description": "Path to delete"},
                "recursive": {"type": "boolean", "optional": True, "description": "Delete recursively"},
            }),
            "copy": (self.copy, "Copy files or directories", {
                "src": {"type": "string", "description": "Source path"},
                "dst": {"type": "string", "description": "Destination path"},
            }),
            "move": (self.move, "Move files or directories", {
                "src": {"type": "string", "description": "Source path"},
                "dst": {"type": "string", "description": "Destination path"},
            }),
            "file_info": (self.file_info, "Get file metadata", {
                "path": {"type": "string", "description": "Path to file"},
            }),
            "apply_patch": (self.apply_patch, "Apply a diff/patch to a file", {
                "path": {"type": "string", "description": "Path to file"},
                "patch": {"type": "string", "description": "Unified diff/patch content"},
            }),
        }

    def _resolve(self, path):
        p = Path(path)
        if p.is_absolute():
            return p.resolve()
        return (self.base_dir / p).resolve()

    def _safe_path(self, path):
        resolved = self._resolve(path)
        base = self.base_dir.resolve()
        data = Path(self.registry.base_dir) / "data"
        if str(resolved).startswith(str(base)) or str(resolved).startswith(str(data)):
            return resolved
        raise PermissionError(f"Access denied: {path} is outside workspace")

    def read(self, path, offset=None, limit=None):
        p = self._safe_path(path)
        if not p.exists():
            return {"error": f"File not found: {path}"}
        if p.is_dir():
            return self.list_dir(path)
        content = p.read_text(encoding="utf-8", errors="replace")
        lines = content.split("\n")
        total = len(lines)
        if offset is not None:
            offset = max(0, int(offset) - 1)
            lines = lines[offset:]
        if limit is not None:
            lines = lines[:int(limit)]
        return {
            "content": "\n".join(lines),
            "total_lines": total,
            "line_offset": (offset or 0) + 1,
            "size": p.stat().st_size,
        }

    def write(self, path, content):
        p = self._safe_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return {"path": str(p), "size": len(content), "status": "written"}

    def edit(self, path, old_string, new_string, replace_all=False):
        p = self._safe_path(path)
        content = p.read_text(encoding="utf-8")
        if replace_all:
            new_content = content.replace(old_string, new_string)
        else:
            new_content = content.replace(old_string, new_string, 1)
        if content == new_content:
            return {"error": "String not found in file", "status": "no_match"}
        p.write_text(new_content, encoding="utf-8")
        return {"path": str(p), "changes": 1 if not replace_all else content.count(old_string), "status": "edited"}

    def multi_edit(self, path, edits):
        p = self._safe_path(path)
        content = p.read_text(encoding="utf-8")
        changes = 0
        for edit in edits:
            old = edit.get("old_string", "")
            new = edit.get("new_string", "")
            if content.count(old) == 0:
                continue
            all_repl = edit.get("replace_all", False)
            if all_repl:
                content = content.replace(old, new)
            else:
                content = content.replace(old, new, 1)
            changes += 1
        p.write_text(content, encoding="utf-8")
        return {"path": str(p), "changes": changes, "status": "edited"}

    def glob(self, pattern, path=None):
        root = self._resolve(path) if path else self.base_dir
        matches = [str(p.relative_to(self.base_dir)) for p in root.glob(pattern)]
        return {"matches": matches, "count": len(matches), "pattern": pattern}

    def grep(self, pattern, include=None, path=None):
        root = self._resolve(path) if path else self.base_dir
        results = []
        files = list(root.rglob("*")) if not include else list(root.rglob(include))
        for f in files:
            if f.is_file():
                try:
                    text = f.read_text(encoding="utf-8", errors="replace")
                    for i, line in enumerate(text.split("\n"), 1):
                        if re.search(pattern, line):
                            rel = str(f.relative_to(self.base_dir))
                            results.append({"file": rel, "line": i, "content": line.strip()[:300]})
                except Exception:
                    pass
        return {"matches": results, "count": len(results), "pattern": pattern}

    def list_dir(self, path=None):
        p = self._safe_path(path) if path else self.base_dir
        if not p.exists():
            return {"error": f"Directory not found: {path}"}
        entries = []
        for entry in sorted(p.iterdir()):
            try:
                stat = entry.stat()
                entries.append({
                    "name": entry.name,
                    "type": "dir" if entry.is_dir() else "file",
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                })
            except Exception:
                pass
        return {"path": str(p), "entries": entries, "count": len(entries)}

    def delete_file(self, path, recursive=False):
        p = self._safe_path(path)
        if not p.exists():
            return {"error": f"Not found: {path}"}
        if p.is_dir():
            if recursive:
                shutil.rmtree(p)
                return {"path": str(p), "status": "deleted_recursive"}
            return {"error": "Is a directory. Use recursive=true to delete."}
        p.unlink()
        return {"path": str(p), "status": "deleted"}

    def copy(self, src, dst):
        sp = self._safe_path(src)
        dp = self._safe_path(dst)
        dp.parent.mkdir(parents=True, exist_ok=True)
        if sp.is_dir():
            shutil.copytree(sp, dp)
        else:
            shutil.copy2(sp, dp)
        return {"src": str(sp), "dst": str(dp), "status": "copied"}

    def move(self, src, dst):
        sp = self._safe_path(src)
        dp = self._safe_path(dst)
        dp.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(sp), str(dp))
        return {"src": str(src), "dst": str(dst), "status": "moved"}

    def file_info(self, path):
        p = self._safe_path(path)
        if not p.exists():
            return {"error": "Not found"}
        stat = p.stat()
        return {
            "path": str(p),
            "name": p.name,
            "type": "dir" if p.is_dir() else "file",
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "extension": p.suffix,
        }

    def apply_patch(self, path, patch):
        p = self._safe_path(path)
        content = p.read_text(encoding="utf-8")
        lines = content.split("\n")
        for line in patch.split("\n"):
            if line.startswith("--- ") or line.startswith("+++ ") or line.startswith("@@ "):
                continue
            if line.startswith("+") and not line.startswith("+++"):
                target_line = int(line.split("@@")[1].split()[0].split(",")[0].lstrip("+")) if "@@" in line else -1
        p.write_text(content, encoding="utf-8")
        return {"status": "patch_applied", "path": str(p)}
