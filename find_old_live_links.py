#!/usr/bin/env python3
"""Find likely live-demo URLs in earlier README.md versions in this Git repository."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
PROJECTS_FILE = ROOT / "projects.json"
URL_RE = re.compile(r"https?://[^\s\"'<>\)\]]+", re.IGNORECASE)
LIVE_WORDS = re.compile(r"live|demo|preview|website|visit|try|launch|deployed|online|web app|view app", re.I)
LIKELY_HOSTS = (".onrender.com", ".vercel.app", ".netlify.app", ".github.io", ".pages.dev", ".web.app", ".firebaseapp.com", ".surge.sh")
SKIP_HOSTS = ("img.shields.io", "github-readme-stats.vercel.app", "streak-stats.demolab.com")


def run_git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Fill blank live_url values only when exactly one candidate is found for a project.")
    args = parser.parse_args()
    try:
        projects = json.loads(PROJECTS_FILE.read_text(encoding="utf-8"))
        commits = run_git("log", "--all", "--format=%H", "--", "README.md").splitlines()
        sources: list[tuple[str, str]] = []
        for commit in commits:
            try:
                sources.append((commit[:7], run_git("show", f"{commit}:README.md")))
            except RuntimeError:
                continue

        # The user's earlier working folder mentioned in the setup conversation may
        # be kept beside this clone. Include it when present so links can be restored
        # even if the older README is not part of the cloned repository history.
        legacy_readme = ROOT.parent / "Anik2059-Profile-Repo" / "README.md"
        if legacy_readme.is_file():
            try:
                sources.append((f"file:{legacy_readme}", legacy_readme.read_text(encoding="utf-8", errors="replace")))
            except OSError:
                pass

        if not sources:
            print("No earlier README.md history or adjacent backup was found. Run this inside your cloned profile repository.")
            return 0

        found: dict[str, dict[str, tuple[str, str, str]]] = {p["name"]: {} for p in projects}
        inspected = 0

        aliases_by_project: dict[str, list[str]] = {}
        for project in projects:
            project_name = project["name"]
            names = [project_name]
            name = project_name.lower()
            if "shopping" in name:
                names += ["mj_shopping", "mj shopping", "mj mart"]
            elif "chat" in name:
                names += ["client-server chat", "client server chat", "clients-and-server-chat"]
            elif "tcp" in name:
                names += ["tcp flow", "congestion simulator", "tcp-flow-congestion-java"]
            elif "music" in name:
                names += ["mj-music-player", "mj music"]
            aliases_by_project[project_name] = names

        for source_label, source in sources:
            # The current README links are already known. Focus on older README versions.
            if "FEATURED_PROJECTS_START" in source:
                continue
            inspected += 1
            lines = source.splitlines()

            # Record where each project is mentioned so nearby live-demo URLs can be
            # associated with the closest project, instead of assigning one URL to
            # several projects whose cards happen to be adjacent in a table.
            mentions: dict[str, list[int]] = {p["name"]: [] for p in projects}
            for line_no, line in enumerate(lines):
                for project_name, aliases in aliases_by_project.items():
                    if any(alias.lower() in line.lower() for alias in aliases):
                        mentions[project_name].append(line_no)

            for line_no, line in enumerate(lines):
                for url in URL_RE.findall(line):
                    url = url.rstrip(".,;:")
                    host = urlparse(url).netloc.lower()
                    if any(skip in host for skip in SKIP_HOSTS):
                        continue
                    if any(url.rstrip("/") == p.get("repository_url", "").rstrip("/") for p in projects):
                        continue
                    lo, hi = max(0, line_no - 2), min(len(lines), line_no + 3)
                    context = "\n".join(lines[lo:hi])
                    if not (LIVE_WORDS.search(context) or any(host.endswith(h) for h in LIKELY_HOSTS)):
                        continue

                    # Most READMEs place a project's demo link after that project's
                    # heading. Prefer the nearest project heading above the URL; only
                    # use a following heading when there is no nearby preceding one.
                    preceding = {
                        project_name: max(pos for pos in project_lines if 0 <= line_no - pos <= 8)
                        for project_name, project_lines in mentions.items()
                        if any(0 <= line_no - pos <= 8 for pos in project_lines)
                    }
                    if preceding:
                        last_heading_line = max(preceding.values())
                        nearest = [name for name, pos in preceding.items() if pos == last_heading_line]
                    else:
                        following = {
                            project_name: min(pos for pos in project_lines if 0 < pos - line_no <= 4)
                            for project_name, project_lines in mentions.items()
                            if any(0 < pos - line_no <= 4 for pos in project_lines)
                        }
                        if not following:
                            continue
                        first_heading_line = min(following.values())
                        nearest = [name for name, pos in following.items() if pos == first_heading_line]
                    # If two projects share the exact heading line, don't guess.
                    if len(nearest) != 1:
                        continue
                    project_name = nearest[0]
                    line_for_url = line.strip()
                    found[project_name][url] = (source_label, line_for_url, context.strip().replace("\n", " | "))

        print(f"Checked {inspected} older README version(s).")
        any_found = False
        for project_name, urls in found.items():
            print(f"\n{project_name}:")
            if not urls:
                print("  No likely live-demo URL found automatically.")
                continue
            any_found = True
            for url, (commit, line, context) in urls.items():
                print(f"  URL: {url}")
                print(f"  From commit: {commit}")
                print(f"  Context: {context[:350]}")
        if not any_found:
            print("\nNo likely live-demo links were found. You can still paste an old README's URL into the matching live_url field manually.")
        elif args.apply:
            applied = []
            for project in projects:
                candidates = found.get(project["name"], {})
                if project.get("live_url", "").strip():
                    continue
                if len(candidates) == 1:
                    url = next(iter(candidates))
                    project["live_url"] = url
                    applied.append((project["name"], url))
            PROJECTS_FILE.write_text(json.dumps(projects, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            if applied:
                print("\nFilled these blank live_url fields automatically:")
                for project_name, url in applied:
                    print(f"  {project_name}: {url}")
            else:
                print("\nNo unambiguous URL was available to apply. Review the report and fill live_url manually.")
            print("Now run: python update_readme.py")
            print("Review every applied URL to make sure it is the correct still-live deployment.")
        else:
            print("\nCopy the correct URL into the matching project's live_url field in projects.json.")
            print("To auto-fill only unambiguous matches, run: python find_old_live_links.py --apply")
            print("Then run: python update_readme.py")
        return 0
    except (OSError, json.JSONDecodeError, RuntimeError) as exc:
        print(f"Could not inspect README history: {exc}")
        print("Make sure this script is inside your cloned Anik2059 repository and Git is installed.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
