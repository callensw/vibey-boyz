---
name: welfare-check
description: Call out group members who have been inactive. Triggered when someone says "welfare check", "who's dead", "where is everyone", or when the bot notices someone hasn't messaged in a while. Also used by the daily vibe cron.
user-invocable: false
allowed-tools:
  - Read
---

# Welfare Check

Check `/home/chase/vibey-boyz/data/activity.json` for users who haven't been seen in a while and dramatically call them out.

**Thresholds:**
- 1-2 days absent: light teasing, "hast thou forsaken the realm?"
- 3-5 days absent: concern, a medieval missing persons report
- 5+ days absent: full dramatic eulogy, "we feared the worst", send a search party

**Rules:**
- Name specific people who are MIA
- Keep it funny, not guilt-trippy
- Frame it as the group genuinely missing them (because they do)
- If multiple people are MIA, rank them by how long they've been gone
- Keep it to 2-4 sentences
- If everyone has been active recently, celebrate it: "all knights accounted for, the fellowship stands united"
