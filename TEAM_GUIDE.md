# Team Guide

## Rules

1. **Never commit directly to `main`.** (On a free private GitHub repo this is a team rule, GitHub cannot enforce it.)
2. **One branch per task**, named `feature/<short-task>` (e.g. `feature/scraper-site1`, `feature/db-api`).
3. **Every change goes through a Pull Request** and is reviewed by a teammate before merging.
4. Do not commit: `.env`, passwords, API keys, the `.db` file, or large raw data.
5. Keep the shared data format in `scraper/base.py` (`FIELDS`) and `database/schema.sql`. If you change one, tell the team and change both.

## One-time setup

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
git clone <repo-url>
cd used-vehicle-price-system
python -m venv venv && pip install -r requirements.txt   # activate the venv first
```
Sign in to GitHub when VS Code / Git asks (browser login), or use a Personal Access Token.

## Every task

```bash
git checkout main
git pull
git checkout -b feature/your-task
# ... work, run `python -m pytest` ...
git add .
git commit -m "Short description of what you did"
git push -u origin feature/your-task
```
Then on GitHub: **Compare & pull request** -> ask a teammate to review -> **Merge**.

After merging, everyone runs `git checkout main && git pull`.

## Conflicts

If GitHub says a branch has conflicts: `git checkout main && git pull`, then
`git checkout feature/your-task && git merge main`, fix the marked files in VS Code
(Source Control panel shows them), commit, and push again.

## Suggested split (4 people)

| Person | Branches | Work |
|---|---|---|
| A | `feature/scraper-site1`, `feature/scraper-site2` | Scrapers (`scraper/`) |
| B | `feature/data-cleaning` | Cleaning + analysis (`analysis/`) |
| C | `feature/db-and-api` | Database + API (`database/`, `backend/`) |
| D | `feature/frontend` | Dashboard (`frontend/`) + README/report |

## Definition of done for a Pull Request
- Tests pass (`python -m pytest`)
- No secrets or data files committed
- README updated if setup or usage changed
