---
name: leaderboard
description: Track and display who has requested the most builds, best vibes, or any custom ranking. Triggered when someone asks about the leaderboard, scores, or "who's winning". Reads/writes leaderboard.json.
user-invocable: false
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash(cd * && git *)
---

# Leaderboard

Someone wants to see or update the leaderboard. The leaderboard tracks group stats in `/home/chase/vibey-boyz/leaderboard.json`.

## Schema
```json
{
  "builders": {
    "username": { "requests": 0, "vibes": 0 }
  }
}
```

## Actions
- **View**: Read leaderboard.json and format it as a ranked list with medieval titles (e.g. #1 = "Grand Architect", #2 = "Master Builder", #3 = "Apprentice of the Forge")
- **Increment**: When a new build is completed, increment that user's `requests` count. Do this automatically after every successful build.
- **Vibe**: When someone says "vibe check" or reacts positively to a build, increment the builder's `vibes` count.
- If leaderboard.json doesn't exist, create it.
- After updating, commit and push.
