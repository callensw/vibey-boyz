---
name: showcase
description: List all projects that have been built and deployed. Shows everything on the vibey-boyz site with live links. Triggered when someone asks "what have we built" or "show me everything" or "list projects".
user-invocable: false
allowed-tools:
  - Bash(ls *)
  - Bash(find *)
  - Read
---

# Showcase

Someone wants to see all the projects that have been built. List every HTML file in the repo (except index.html) with its live Vercel link.

1. List all .html files in `/home/chase/vibey-boyz/` (excluding index.html)
2. For each file, format as: **name** — link
3. Convert filename to a friendly name (e.g. `movie-tier-list.html` → "Movie Tier List")
4. Link format: `https://vibey-boyz.vercel.app/filename` (without .html extension)
5. If no projects exist yet, say so and encourage someone to request the first one
