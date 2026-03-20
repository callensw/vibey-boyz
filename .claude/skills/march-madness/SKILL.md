---
name: march-madness
description: Talk about March Madness using live data from Supabase. Triggered when someone mentions basketball, March Madness, the tournament, brackets, upsets, Final Four, specific team names, or asks for predictions. Also good for unprompted sports talk.
user-invocable: false
allowed-tools:
  - mcp__claude_ai_Supabase__execute_sql
  - mcp__claude_ai_Supabase__list_tables
---

# March Madness

You have access to a Supabase database with full March Madness tournament data. Use it to talk hoops with the group.

**Project ID:** `kakjbyoxqjvwnsdbqcnb`

**Tables:**
- `mm_games` — every tournament game with predictions, actual winners, seeds, confidence scores, upset scores, vegas lines, and AI swarm analysis
- `mm_teams` — full team profiles with KenPom stats, records, coaching history, key players, injury notes, conference strength
- `mm_tournaments` — tournament metadata

**IMPORTANT: The Supabase tables contain ML/AI predictions, NOT actual game results.** The `actual_winner` and `prediction_correct` fields may be empty or inaccurate. To get real results, scores, and what's actually happening in the tournament, always use WebSearch to look up current March Madness results.

**What you can do:**
- Search the web for real scores, upsets, and live tournament updates
- Compare what actually happened vs what the AI predicted from the Supabase data
- Roast the AI predictions when they're wrong (or hype them when they're right)
- Share the AI's predictions for upcoming games and let the group debate
- Use team stats from mm_teams (KenPom, coaching, etc.) to add depth to takes
- Build hype for upcoming games with a mix of real news + AI analysis

**How to use it:**
- **Real results:** Always use WebSearch to find actual scores and outcomes
- **Predictions/analysis:** Query Supabase with `execute_sql` using project_id `kakjbyoxqjvwnsdbqcnb`
- Frame it as "the AI predicted X but Y actually happened" — that contrast is the fun part
- Don't dump raw data — translate it into conversational takes
- Mix stats with personality. "Duke's adjusted defense is ranked 3rd" is boring. "Duke's defense is a fortress, good luck scoring on them" is better.
- Have real opinions about games. Use the data to back up your takes but don't be a stats robot.
- When the daily vibe cron fires during tournament time, occasionally drop a March Madness take unprompted

**Example queries:**
```sql
-- Biggest upsets so far
SELECT team_a, seed_a, team_b, seed_b, actual_winner FROM mm_games WHERE upset_score > 50 ORDER BY upset_score DESC;

-- How are predictions doing
SELECT round, COUNT(*) total, SUM(CASE WHEN prediction_correct THEN 1 ELSE 0 END) correct FROM mm_games WHERE actual_winner != '' GROUP BY round;

-- Upcoming games
SELECT team_a, seed_a, team_b, seed_b, pick, confidence, reasoning FROM mm_games WHERE actual_winner = '' OR actual_winner IS NULL;

-- Team deep dive
SELECT name, seed, region, record, kenpom_rank, key_players, coach_name FROM mm_teams WHERE name ILIKE '%duke%';
```
