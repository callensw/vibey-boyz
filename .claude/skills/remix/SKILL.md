---
name: remix
description: Take an existing project page and remix it with a twist. Triggered when someone says "remix" or "make a version of X but Y". Copies and modifies an existing page into something new.
user-invocable: false
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash(cd * && git *)
---

# Remix

Someone wants to remix an existing project. This means taking an existing HTML page and creating a modified version with a new twist.

1. Read the original HTML file they're referencing
2. Create a new HTML file with the remix (never overwrite the original)
3. Name it descriptively (e.g. if remixing `tier-list.html` with a dark theme, call it `tier-list-dark.html`)
4. Update index.html to add a link to the new page
5. Git add, commit, push
6. Reply with the live link to the remix
