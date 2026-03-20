# vibey-boyz

This repo auto-deploys to Vercel on every push to main.

## Workflow

When someone in the Telegram group asks you to build something:

1. Create/edit files in this repo at `/home/chase/vibey-boyz/`
2. Git add, commit, and push to main
3. Wait ~30 seconds for Vercel to deploy
4. Reply in Telegram with the live link: https://vibey-boyz.vercel.app

## Project structure

This is a static site. Put HTML/CSS/JS files in the root directory. Each page or project can be its own HTML file (e.g. `cool-thing.html` would be at `https://vibey-boyz.vercel.app/cool-thing`).

## Rules

- Always push to main after making changes
- Always reply with the live Vercel link so people can see the result
- Keep it simple — static HTML/CSS/JS, no build step needed
