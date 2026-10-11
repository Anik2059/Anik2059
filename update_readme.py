#!/usr/bin/env python3
"""Regenerate the Featured Projects block in README.md from projects.json."""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
README_PATH = ROOT / "README.md"
PROJECTS_PATH = ROOT / "projects.json"
START = "<!-- FEATURED_PROJECTS_START -->"
END = "<!-- FEATURED_PROJECTS_END -->"

BADGE_COLORS = {
    "HTML5": "E34F26",
    "CSS3": "1572B6",
    "JavaScript": "F7DF1E",
    "Python": "3776AB",
    "Tkinter": "2C5A7A",
    "TCP Sockets": "1F6FEB",
    "Java": "ED8B00",
    "Computer Networks": "1F6FEB",
    "React": "20232A",
    "Node.js": "339933",
    "Express": "404D59",
    "TypeScript": "3178C6",
    "FastAPI": "009688",
    "Flask": "000000",
    "Gemini AI": "8E75B2",
    "SQLAlchemy": "D71F00",
}
DARK_LOGOS = {"JavaScript"}
TECH_LOGOS = {
    "HTML5": "html5",
    "CSS3": "css3",
    "JavaScript": "javascript",
    "Python": "python",
    "Tkinter": "python",
    "TCP Sockets": "",
    "Java": "openjdk",
    "React": "react",
    "Node.js": "nodedotjs",
    "Express": "express",
    "TypeScript": "typescript",
    "FastAPI": "fastapi",
    "Flask": "flask",
    "Gemini AI": "googlegemini",
    "SQLAlchemy": "sqlalchemy",
}


def valid_optional_url(value: str, field: str, project_name: str, required: bool = False) -> str:
    value = value.strip()
    if not value and not required:
        return ""
    if not re.match(r"^https?://[^\s<>\"]+$", value, flags=re.IGNORECASE):
        raise ValueError(f"{project_name!r}: {field} must be a complete http:// or https:// URL.")
    return value


def badge(tech: str) -> str:
    color = BADGE_COLORS.get(tech, "475569")
    label = quote(tech.replace(" ", " "), safe="")
    text_color = "000000" if tech in DARK_LOGOS else "white"
    logo = TECH_LOGOS.get(tech, "")
    logo_part = f"&logo={quote(logo, safe='')}" if logo else ""
    src = f"https://img.shields.io/badge/{label}-{color}?style=flat-square{logo_part}&logoColor={text_color}"
    return f'<img src="{src}" alt="{html.escape(tech, quote=True)}" />'


def render_project(project: dict) -> str:
    name = html.escape(project["name"])
    description = html.escape(project.get("description", ""))
    repo = valid_optional_url(project.get("repository_url", ""), "repository_url", name, required=True)
    live = valid_optional_url(project.get("live_url", ""), "live_url", name)
    image = project.get("image", "assets/project-shopping.svg").strip()
    image_alt = html.escape(project.get("image_alt", f"{project['name']} illustration"), quote=True)
    technologies = project.get("technologies", [])
    if not isinstance(technologies, list) or any(not isinstance(item, str) for item in technologies):
        raise ValueError(f"{name!r}: technologies must be a list of strings.")

    links = []
    if live:
        links.append(f'<a href="{html.escape(live, quote=True)}">🚀 Live Demo</a>')
    links.append(f'<a href="{html.escape(repo, quote=True)}">View repository ↗</a>')
    tech_html = " ".join(badge(item) for item in technologies)

    return "\n".join([
        '    <td width="50%" valign="top">',
        f'      <img src="./{html.escape(image, quote=True)}" width="100%" alt="{image_alt}" />',
        f'      <h3><a href="{html.escape(repo, quote=True)}">{name}</a></h3>',
        f'      <p>{description}</p>',
        f'      <p>{tech_html}</p>' if tech_html else '',
        f'      <p>{" &nbsp;·&nbsp; ".join(links)}</p>',
        '    </td>',
    ]).replace('\n\n', '\n')


def render_projects(projects: list[dict]) -> str:
    if not isinstance(projects, list):
        raise ValueError("projects.json must contain a JSON array of project objects.")
    if not projects:
        return "<p align=\"center\"><em>No featured projects yet. Add a project in projects.json.</em></p>"

    rows = []
    for start in range(0, len(projects), 2):
        pair = projects[start:start + 2]
        cells = [render_project(project) for project in pair]
        if len(cells) == 1:
            cells.append('    <td width="50%" valign="top"></td>')
        rows.append("  <tr>\n" + "\n".join(cells) + "\n  </tr>")
    return '<table>\n' + "\n".join(rows) + '\n</table>'


def main() -> int:
    try:
        readme = README_PATH.read_text(encoding="utf-8")
        projects = json.loads(PROJECTS_PATH.read_text(encoding="utf-8"))
        if START not in readme or END not in readme:
            raise ValueError("README.md is missing the FEATURED_PROJECTS_START/END markers.")
        start_pos = readme.index(START) + len(START)
        end_pos = readme.index(END)
        if end_pos < start_pos:
            raise ValueError("Featured-project markers are in the wrong order.")
        content = "\n\n" + render_projects(projects) + "\n"
        updated = readme[:start_pos] + content + readme[end_pos:]
        README_PATH.write_text(updated, encoding="utf-8", newline="\n")
        print(f"Updated README.md with {len(projects)} featured project(s).")
        print("Review the changes with: git diff -- README.md")
        return 0
    except (OSError, json.JSONDecodeError, ValueError, KeyError, TypeError) as exc:
        print(f"Could not update README: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
