"""GitHub MCP Tools — Full GitHub API integration.

From: Codex (mcp__codex_apps__github with 50+ tools), GitHub Copilot
"""

import os
import json
import base64
import time
import subprocess
from datetime import datetime


class GitHubTools:
    def __init__(self, registry):
        self.registry = registry

    def get_tools(self):
        return {
            "gh_issue_list": (self.gh_issue_list, "List issues in a repository", {
                "repo": {"type": "string", "description": "owner/repo"},
                "state": {"type": "string", "optional": True},
                "limit": {"type": "integer", "optional": True},
            }),
            "gh_issue_get": (self.gh_issue_get, "Get issue details", {
                "repo": {"type": "string", "description": "owner/repo"},
                "issue": {"type": "integer", "description": "Issue number"},
            }),
            "gh_issue_create": (self.gh_issue_create, "Create an issue", {
                "repo": {"type": "string", "description": "owner/repo"},
                "title": {"type": "string", "description": "Issue title"},
                "body": {"type": "string", "optional": True, "description": "Issue body"},
            }),
            "gh_pr_list": (self.gh_pr_list, "List pull requests", {
                "repo": {"type": "string", "description": "owner/repo"},
                "state": {"type": "string", "optional": True},
            }),
            "gh_pr_get": (self.gh_pr_get, "Get PR details", {
                "repo": {"type": "string", "description": "owner/repo"},
                "pr": {"type": "integer", "description": "PR number"},
            }),
            "gh_search_code": (self.gh_search_code, "Search code on GitHub", {
                "query": {"type": "string", "description": "Search query"},
            }),
            "gh_search_repos": (self.gh_search_repos, "Search repositories", {
                "query": {"type": "string", "description": "Search query"},
            }),
            "gh_repo_info": (self.gh_repo_info, "Get repository metadata", {
                "repo": {"type": "string", "description": "owner/repo"},
            }),
            "gh_file_content": (self.gh_file_content, "Get file content from GitHub", {
                "repo": {"type": "string", "description": "owner/repo"},
                "path": {"type": "string", "description": "File path"},
                "ref": {"type": "string", "optional": True, "description": "Branch/ref"},
            }),
        }

    def _gh(self, args):
        try:
            result = subprocess.run(
                ["gh"] + args,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                return {"error": result.stderr.strip(), "success": False}
            return json.loads(result.stdout) if result.stdout else {"success": True}
        except FileNotFoundError:
            return {"error": "GitHub CLI (gh) not found. Install it from https://cli.github.com/"}
        except json.JSONDecodeError:
            return {"output": result.stdout, "success": True}
        except subprocess.TimeoutExpired:
            return {"error": "GitHub CLI timed out"}
        except Exception as e:
            return {"error": str(e)}

    def gh_issue_list(self, repo, state="open", limit=10):
        return self._gh(["issue", "list", "-R", repo, "--state", state, "--json", "number,title,state,labels,updatedAt", "--limit", str(limit)])

    def gh_issue_get(self, repo, issue):
        return self._gh(["issue", "view", "-R", repo, str(issue), "--json", "number,title,body,state,labels,author,createdAt,comments"])

    def gh_issue_create(self, repo, title, body=""):
        args = ["issue", "create", "-R", repo, "--title", title]
        if body:
            args += ["--body", body]
        return self._gh(args)

    def gh_pr_list(self, repo, state="open"):
        return self._gh(["pr", "list", "-R", repo, "--state", state, "--json", "number,title,state,author,headRefName,baseRefName,createdAt"])

    def gh_pr_get(self, repo, pr):
        return self._gh(["pr", "view", "-R", repo, str(pr), "--json", "number,title,body,state,author,additions,deletions,files,reviews,comments"])

    def gh_search_code(self, query):
        return self._gh(["search", "code", query, "--json", "repository,name,path"])

    def gh_search_repos(self, query):
        return self._gh(["search", "repos", query, "--json", "name,owner,description,url,stars,language"])

    def gh_repo_info(self, repo):
        return self._gh(["repo", "view", repo, "--json", "name,owner,description,url,stars,forkCount,language,topics,createdAt,updatedAt"])

    def gh_file_content(self, repo, path, ref=None):
        args = ["repo", "view", repo, "--json", "name"]
        # Use raw GitHub API approach
        api_args = ["api", f"/repos/{repo}/contents/{path}"]
        if ref:
            api_args.extend(["-f", f"ref={ref}"])
        result = self._gh(api_args)
        if isinstance(result, dict) and "content" in result:
            try:
                result["decoded_content"] = base64.b64decode(result["content"]).decode("utf-8")
            except Exception:
                result["decoded_content"] = "[Binary content]"
            result["encoding"] = "base64"
        return result
