---
name: weekly-chronicle
description: Generate the weekly chronicle — a summary page of the group's week. Triggered by the Sunday cron job or when someone asks "weekly recap", "what happened this week", or "chronicle".
user-invocable: false
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash(cd * && git *)
  - Bash(ls *)
---

# Weekly Chronicle

Generate a fun, themed weekly recap page and deploy it to the site.

**Steps:**
1. Read `/home/chase/vibey-boyz/data/activity.json` for stats
2. Check `git log --since="7 days ago" --oneline` for what was built this week
3. Generate an HTML page at `/home/chase/vibey-boyz/chronicles/week-YYYY-MM-DD.html`
4. Update index.html to link to the latest chronicle
5. Git add, commit, push
6. Send the link to chat -5295756665 with a dramatic announcement

**What the page should include:**
- A medieval-themed header ("The Weekly Chronicle of the Vibey Boyz")
- Date range for the week
- "Builds of the Week" — what was created, with links
- "Most Honored Knight" — most active chatter
- "The Silent Ones" — who was MIA
- "Moment of the Week" — reference something memorable from conversation if possible
- Fun stats: total messages, total builds, busiest day
- A "prophecy for next week" section with a fun prediction

**Style:**
- Match the site's dark theme (background #0a0a0f, Space Grotesk font)
- Use the purple/indigo/cyan gradient color scheme
- Make it look like a medieval scroll or newspaper
- Mobile-friendly
- Keep it fun and visual, not a wall of text
