# AGENTS.md

**Read `/home/mayaskara/clg/CLAUDE.md` first** (that's `~/clg/CLAUDE.md`, the parent folder of this repo).
It is the main instruction file. It covers the folder layout, how notes are made, how to publish a unit to this site, and the rules.

Quick facts for this repo (`Mayaskara25/clg-notes`, the class exam-notes website):
- It holds only finished guides, in `subjects/<slug>/*.html`, each listed in `subjects/<slug>/subject.json`.
- `python3 site/build.py` builds and validates into `public/`. It must print `OK` before you push.
- Pushing to `main` redeploys on Render. Run `git pull --rebase` before pushing.
- Do not publish OS or ADLD units until the user confirms they are correct.
