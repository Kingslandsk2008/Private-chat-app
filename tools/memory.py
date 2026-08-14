"""Memory System — Persistent user memory across conversations.

From: Claude chat web (memory_append, memory_read, memory_list, memory_write, memory_delete, memory_str_replace)
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path


class MemoryTools:
    def __init__(self, registry):
        self.registry = registry
        data_dir = getattr(registry, "data_dir", None)
        if not data_dir:
            if os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"):
                data_dir = Path("/tmp/kajuu_data")
            else:
                data_dir = Path(registry.base_dir) / "data"
        self.memory_dir = Path(data_dir) / "memory"
        try:
            self.memory_dir.mkdir(parents=True, exist_ok=True)
            self.index_file = self.memory_dir / "MEMORY.md"
            self._ensure_index()
        except Exception as e:
            print(f"MemoryTools init warning: {e}")

    def _ensure_index(self):
        try:
            if not self.index_file.exists():
                self.index_file.write_text(
                    "# KAJUU Memory Index\n\n"
                    "User memories, preferences, and conversation notes.\n\n"
                    f"Created: {datetime.utcnow().isoformat()}\n\n"
                    "## Documents\n\n"
                )
        except Exception as e:
            print(f"MemoryTools _ensure_index warning: {e}")

    def get_tools(self):
        return {
            "memory_append": (self.memory_append, "Append to a memory document", {
                "name": {"type": "string", "description": "Memory document name"},
                "content": {"type": "string", "description": "Content to append"},
            }),
            "memory_write": (self.memory_write, "Write/overwrite a memory document", {
                "name": {"type": "string", "description": "Memory document name"},
                "content": {"type": "string", "description": "Content to write"},
            }),
            "memory_read": (self.memory_read, "Read a memory document", {
                "name": {"type": "string", "description": "Memory document name"},
            }),
            "memory_list": (self.memory_list, "List all memory documents", {}),
            "memory_delete": (self.memory_delete, "Delete a memory document", {
                "name": {"type": "string", "description": "Memory document name"},
            }),
            "memory_search": (self.memory_search, "Search across all memory documents", {
                "query": {"type": "string", "description": "Search query"},
            }),
            "memory_update_index": (self.memory_update_index, "Update the memory index file", {}),
        }

    def _doc_path(self, name):
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
        return self.memory_dir / f"{safe_name}.md"

    def memory_append(self, name, content):
        path = self._doc_path(name)
        timestamp = datetime.utcnow().isoformat()
        entry = f"\n\n## {timestamp}\n\n{content}\n"
        if path.exists():
            with open(path, "a") as f:
                f.write(entry)
        else:
            path.write_text(f"# {name}\n\nCreated: {timestamp}\n{entry}")
        self.memory_update_index()
        return {"name": name, "status": "appended", "path": str(path)}

    def memory_write(self, name, content):
        path = self._doc_path(name)
        timestamp = datetime.utcnow().isoformat()
        path.write_text(f"# {name}\n\nUpdated: {timestamp}\n\n{content}\n")
        self.memory_update_index()
        return {"name": name, "status": "written", "path": str(path)}

    def memory_read(self, name):
        path = self._doc_path(name)
        if not path.exists():
            return {"error": f"Memory document not found: {name}"}
        return {"name": name, "content": path.read_text(), "path": str(path), "size": path.stat().st_size}

    def memory_list(self):
        docs = []
        for f in sorted(self.memory_dir.glob("*.md")):
            if f.name == "MEMORY.md":
                continue
            docs.append({
                "name": f.stem,
                "path": str(f),
                "size": f.stat().st_size,
                "modified": f.stat().st_mtime,
            })
        return {"documents": docs, "count": len(docs)}

    def memory_delete(self, name):
        path = self._doc_path(name)
        if not path.exists():
            return {"error": f"Memory document not found: {name}"}
        path.unlink()
        self.memory_update_index()
        return {"name": name, "status": "deleted"}

    def memory_search(self, query):
        results = []
        for f in self.memory_dir.glob("*.md"):
            if f.name == "MEMORY.md":
                continue
            content = f.read_text()
            if query.lower() in content.lower():
                lines = content.split("\n")
                matching = [l.strip() for l in lines if query.lower() in l.lower()]
                results.append({
                    "document": f.stem,
                    "matches": matching[:5],
                    "match_count": len(matching),
                })
        return {"query": query, "results": results, "count": len(results)}

    def memory_update_index(self):
        docs = []
        for f in sorted(self.memory_dir.glob("*.md")):
            if f.name == "MEMORY.md":
                continue
            docs.append(f"- **{f.stem}**: {f.stat().st_size} bytes (modified {datetime.fromtimestamp(f.stat().st_mtime).isoformat()})")
        content = [
            "# KAJUU Memory Index",
            "",
            "User memories, preferences, and conversation notes.",
            "",
            f"Updated: {datetime.utcnow().isoformat()}",
            "",
            "## Documents",
            "",
        ]
        content.extend(docs)
        content.append("")
        self.index_file.write_text("\n".join(content))
        return {"status": "index_updated", "doc_count": len(docs)}
