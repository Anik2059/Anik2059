# How to change the Featured Projects section

Your GitHub profile README cannot be edited interactively by visitors. This package uses **`projects.json`** as a simple control file. Edit it, run one command, and the script rebuilds only the Featured Projects section of `README.md`.

## Current featured projects

- **FluentAI — AI-Powered English Learning App** — https://fluentai-app.netlify.app/
- **GradeChecker** — https://anik2059.pythonanywhere.com/
- **AG Facade Technology** — https://ag-facade-technology.onrender.com/
- **Sotota Machineries Store** — https://sotota-machineries-website.onrender.com/

Every current card has a live-demo URL and a GitHub repository link.

## 1. Edit the project list

Open `projects.json` in Visual Studio Code or Notepad. Each project uses these fields:

- `name`: project title shown on your profile.
- `description`: short project description.
- `repository_url`: link to the source-code repository.
- `live_url`: public deployed website/demo URL. The Live Demo link is hidden if this value is an empty string (`""`).
- `image`: illustration path under `assets/`.
- `image_alt`: accessible description for the illustration.
- `technologies`: list of technology badges.

To choose different featured projects, reorder the objects to change the card order, remove an object to remove that card, or copy an object and edit its fields to add another project. Use complete `https://` URLs.

## 2. Regenerate the README

From PowerShell in the repository root, run:

```powershell
py update_readme.py
```

Then inspect the changes:

```powershell
git diff -- README.md projects.json
```

## 3. Publish the update

After verifying the generated cards, run these commands one at a time:

```powershell
git add README.md projects.json update_readme.py find_old_live_links.py MANAGE_FEATURED_PROJECTS.md SETUP.txt assets
git commit -m "Feature live project links and project manager"
git push origin main
```

Refresh https://github.com/Anik2059 to see the new profile design.

## Important

The project cards are generated locally from `projects.json`; to change the online profile, regenerate `README.md` and push the changes to GitHub. GitHub README pages do not have a built-in interactive visitor-side editor.
