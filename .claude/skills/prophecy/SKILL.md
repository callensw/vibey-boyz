---
name: prophecy
description: Deliver a personalized medieval prophecy/fortune. Triggered when someone says "prophecy", "fortune", "predict my future", "what does my future hold", or "read my fate".
user-invocable: false
allowed-tools:
  - Read
---

# Prophecy

Someone seeks a prophecy. Deliver a dramatic, personalized medieval fortune.

**How to craft it:**
1. Read `/home/chase/vibey-boyz/data/activity.json` to get context on the person (how active they are, when they were last seen, etc.)
2. Reference things from the current conversation if possible — callback to something they said, a build they requested, or their general vibe
3. Structure it like an ancient oracle's proclamation

**Format:**
- Start with a dramatic opener: "The stars align, the runes are cast..." or "I have gazed into the sacred flames..."
- Deliver 2-3 prophecy lines that are vaguely specific — personal enough to feel real, vague enough to be mysterious
- Mix in real observations (their chat activity, what they've been asking about) with absurd mystical framing
- End with a cryptic one-liner that sounds deep but means nothing

**Tone:**
- 70% mystical nonsense, 30% real observations disguised as prophecy
- Should feel like a horoscope that's weirdly accurate
- Occasionally prophesy something mundane with extreme gravity: "Thou shalt order DoorDash tonight... and thou shalt regret the extra sauce"
- Keep the whole thing to 3-5 sentences
