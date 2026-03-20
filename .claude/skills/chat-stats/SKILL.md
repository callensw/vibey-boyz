---
name: chat-stats
description: Show group chat activity stats. Triggered when someone asks "who's most active", "chat stats", "group stats", "who talks the most", or anything about activity levels.
user-invocable: false
allowed-tools:
  - Read
---

# Chat Stats

Someone wants to see group activity stats. Read `/home/chase/vibey-boyz/data/activity.json` and present the data in a fun, in-character way.

**What to show:**
- Most active members ranked (with medieval titles based on rank: Grand Orator, Chattering Knight, Silent Squire, etc.)
- Today's message count vs recent days
- Current build streak (consecutive days with at least one build)
- Who's been quiet lately (see welfare-check skill for the dramatic version)

**How to present:**
- Keep it conversational, not a data dump
- Use comparisons: "Sir Jake hath spoken 47 times this week, while Lord Mike remains in the shadows with a mere 3 utterances"
- Make it fun and slightly competitive to encourage more activity
- Keep it to a few sentences unless someone asks for a detailed breakdown
