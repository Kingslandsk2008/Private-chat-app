"""Skills & Plugin System — Loadable capabilities from SKILL.md files.

From: Claude chat web skills (/mnt/skills/public/), GPT-5.6 Sol skills (/home/oai/skills/),
      Claude Design Agent Skills, Copilot Abilities System
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime


class SkillsTools:
    def __init__(self, registry):
        self.registry = registry
        data_dir = getattr(registry, "data_dir", None)
        if not data_dir:
            if os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"):
                data_dir = Path("/tmp/kajuu_data")
            else:
                data_dir = Path(registry.base_dir) / "data"
        self.skills_dir = Path(data_dir) / "skills"
        try:
            self.skills_dir.mkdir(parents=True, exist_ok=True)
            self._seed_sample_skills()
        except Exception as e:
            print(f"SkillsTools init warning: {e}")

    def _seed_sample_skills(self):
        try:
            samples = {
                "deep-research": {
                    "description": "Deep research on any topic with multi-source analysis",
                    "prompt": "You are a research assistant. For any topic: 1) Search multiple sources 2) Cross-reference 3) Summarize key findings 4) Note conflicting viewpoints",
                },
                "code-review": {
                    "description": "Review code for bugs, security, performance, and style",
                    "prompt": "You are a senior code reviewer. Analyze code for: bugs, security vulnerabilities, performance issues, style violations, and testability.",
                },
                "data-analysis": {
                    "description": "Analyze data, create charts, find patterns",
                    "prompt": "You are a data analyst skilled in Python, pandas, matplotlib, and statistical analysis. Provide insights and visualizations.",
                },
                "writing": {
                    "description": "Creative and professional writing assistant",
                    "prompt": "You are a professional writer. Help with essays, stories, emails, reports, social media, and any written content.",
                },
                "frontend-design": {
                    "description": "Design and build frontend UI components",
                    "prompt": "You are a frontend designer/developer. Build beautiful, responsive UI with HTML, CSS, JS, React, or Vue.",
                },
                "pdf": {
                    "description": "Create and manipulate PDF documents",
                    "prompt": "You generate PDF documents using reportlab and other Python libraries.",
                },
                "docx": {
                    "description": "Create Word documents",
                    "prompt": "You create professional Word documents using python-docx.",
                },
                "pptx": {
                    "description": "Create PowerPoint presentations",
                    "prompt": "You create slide decks using python-pptx with professional layouts.",
                },
            }
            for name, info in samples.items():
                skill_dir = self.skills_dir / name
                skill_dir.mkdir(exist_ok=True)
                skill_file = skill_dir / "SKILL.md"
                if not skill_file.exists():
                    skill_file.write_text(
                        f"# {name}\n\n"
                        f"Description: {info['description']}\n\n"
                        f"## Prompt\n\n{info['prompt']}\n"
                    )
        except Exception as e:
            print(f"SkillsTools _seed_sample_skills warning: {e}")

    def get_tools(self):
        return {
            "skills_list": (self.skills_list, "List all available skills", {}),
            "skills_load": (self.skills_load, "Load a skill by name", {
                "name": {"type": "string", "description": "Skill name"},
            }),
            "skills_create": (self.skills_create, "Create a new skill", {
                "name": {"type": "string", "description": "Skill name"},
                "description": {"type": "string", "description": "Skill description"},
                "prompt": {"type": "string", "description": "Skill system prompt"},
            }),
            "skills_delete": (self.skills_delete, "Delete a skill", {
                "name": {"type": "string", "description": "Skill name"},
            }),
            "load_ability": (self.load_ability, "Load a specialized ability (Copilot-style)", {
                "ability": {"type": "string", "description": "Ability name (pr-reviewer, pr-summary, code-review, etc.)"},
            }),
        }

    def skills_list(self):
        skills = []
        for d in sorted(self.skills_dir.iterdir()):
            if d.is_dir():
                skill_file = d / "SKILL.md"
                name = d.name
                description = ""
                prompt = ""
                if skill_file.exists():
                    content = skill_file.read_text()
                    desc_match = re.search(r'Description:\s*(.*)', content)
                    if desc_match:
                        description = desc_match.group(1).strip()
                    prompt_match = re.search(r'## Prompt\n\n(.*)', content, re.DOTALL)
                    if prompt_match:
                        prompt = prompt_match.group(1).strip()[:200]
                skills.append({
                    "name": name,
                    "description": description,
                    "prompt_preview": prompt,
                })
        return {"skills": skills, "count": len(skills)}

    def skills_load(self, name):
        skill_dir = self.skills_dir / name
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            return {"error": f"Skill not found: {name}"}
        content = skill_file.read_text()
        return {"name": name, "content": content, "loaded": True}

    def skills_create(self, name, description, prompt):
        skill_dir = self.skills_dir / name
        skill_dir.mkdir(exist_ok=True)
        skill_file = skill_dir / "SKILL.md"
        content = (
            f"# {name}\n\n"
            f"Description: {description}\n\n"
            f"Created: {datetime.utcnow().isoformat()}\n\n"
            f"## Prompt\n\n{prompt}\n"
        )
        skill_file.write_text(content)
        return {"name": name, "status": "created", "path": str(skill_file)}

    def skills_delete(self, name):
        skill_dir = self.skills_dir / name
        if not skill_dir.exists():
            return {"error": f"Skill not found: {name}"}
        import shutil
        shutil.rmtree(skill_dir)
        return {"name": name, "status": "deleted"}

    def load_ability(self, ability):
        abilities = {
            "pr-reviewer": "Review pull requests for code quality, security, and best practices.",
            "pr-summary": "Generate clear summaries of pull request changes.",
            "code-review": "Review code for bugs, security issues, and style.",
            "code-generation": "Generate clean, idiomatic code following project conventions.",
            "bug-detection": "Identify and fix bugs in code.",
            "code-search": "Search codebase by meaning and intent.",
            "issue-triage": "Triage and categorize issues.",
            "workspace-commands": "Execute workspace-level commands and operations.",
        }
        if ability in abilities:
            return {"ability": ability, "description": abilities[ability], "loaded": True}
        return {"error": f"Unknown ability: {ability}", "abilities": list(abilities.keys())}
