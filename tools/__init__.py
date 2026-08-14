"""KAJUU.AI — Tool Registry & Modular Tool System.

All tools, MCPs, servers, and functions from leaked system prompts combined into one unified framework.
"""

import os
import json
import time
import traceback

from .filesystem import FilesystemTools
from .shell import ShellTools
from .web import WebTools
from .git import GitTools
from .memory import MemoryTools
from .skills import SkillsTools
from .agent import AgentTools
from .github import GitHubTools


from pathlib import Path


class ToolRegistry:
    def __init__(self, base_dir=None, data_dir=None):
        self.base_dir = str(base_dir or os.getcwd())
        if data_dir:
            self.data_dir = Path(data_dir)
        elif os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"):
            self.data_dir = Path("/tmp/kajuu_data")
        else:
            self.data_dir = Path(self.base_dir) / "data"
        self._tools = {}
        self._register_all()

    def _register_all(self):
        modules = [
            FilesystemTools(self),
            ShellTools(self),
            WebTools(self),
            GitTools(self),
            MemoryTools(self),
            SkillsTools(self),
            AgentTools(self),
            GitHubTools(self),
        ]
        for mod in modules:
            for name, (fn, desc, schema) in mod.get_tools().items():
                self._tools[name] = (fn, desc, schema)

    def list_tools(self):
        return {name: {"description": desc, "schema": schema} for name, (fn, desc, schema) in self._tools.items()}

    def get_tool(self, name):
        return self._tools.get(name)

    def call_tool(self, tool_name, **params):
        entry = self._tools.get(tool_name)
        if not entry:
            return {"error": f"Unknown tool: {tool_name}", "status": "error"}
        fn, desc, schema = entry
        try:
            start = time.time()
            result = fn(**params)
            elapsed = time.time() - start
            return {"status": "ok", "result": result, "elapsed_ms": round(elapsed * 1000)}
        except Exception as e:
            return {"status": "error", "error": str(e), "traceback": traceback.format_exc()}

    def call_tools_parallel(self, calls):
        results = []
        for call in calls:
            tname = call.get("tool")
            params = call.get("params", {})
            results.append(self.call_tool(tname, **params))
        return results
