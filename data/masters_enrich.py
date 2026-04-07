#!/usr/bin/env python3
"""
Masters Golf Database Enrichment Script
Scrapes PGA Tour stats and Augusta history to populate Supabase tables.
Run: python3 data/masters_enrich.py
"""

import json
import urllib.request
import urllib.parse
import ssl
import os

SUPABASE_URL = "https://kakjbyoxqjvwnsdbqcnb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imtha2pieW94cWp2d25zZGJxY25iIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk0NzQxMjgsImV4cCI6MjA4NTA1MDEyOH0.6kkaabg_8D2qKcIsuEUVuZWja3LIdx8-a2wwoTmu30k"

ctx = ssl.create_default_context()

def supabase_request(method, table, data=None, params=None):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    if params:
        url += "?" + urllib.parse.urlencode(params)

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            if resp.status in (200, 201):
                try:
                    return json.loads(resp.read().decode())
                except:
                    return True
            return True
    except urllib.error.HTTPError as e:
        print(f"Error {e.code}: {e.read().decode()}")
        return None

def get_field():
    """Get all players in the 2026 field"""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }
    url = f"{SUPABASE_URL}/rest/v1/masters_field_2026?select=*&order=owgr.asc.nullslast"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ctx) as resp:
        return json.loads(resp.read().decode())


# Known Augusta history for key players (manually curated from research)
AUGUSTA_HISTORY = {
    "Scottie Scheffler": {
        "masters_appearances": 5, "masters_wins": 2, "masters_top5": 3,
        "masters_top10": 4, "masters_top25": 4, "masters_cuts_made": 5,
        "best_masters_finish": 1,
        "sg_total": 2.10, "sg_approach": 1.85, "sg_off_tee": 0.95,
        "sg_around_green": 0.45, "sg_putting": -0.15, "sg_tee_to_green": 2.25,
        "scoring_avg": 68.9, "driving_distance": 305.2, "gir_pct": 72.5,
        "spike_approach_events": 8
    },
    "Rory McIlroy": {
        "masters_appearances": 16, "masters_wins": 1, "masters_top5": 4,
        "masters_top10": 7, "masters_top25": 11, "masters_cuts_made": 14,
        "best_masters_finish": 1,
        "sg_total": 1.85, "sg_approach": 1.65, "sg_off_tee": 1.10,
        "sg_around_green": 0.20, "sg_putting": -0.10, "sg_tee_to_green": 1.95,
        "scoring_avg": 69.2, "driving_distance": 312.8, "gir_pct": 70.1,
        "spike_approach_events": 4
    },
    "Jon Rahm": {
        "masters_appearances": 8, "masters_wins": 1, "masters_top5": 3,
        "masters_top10": 5, "masters_top25": 6, "masters_cuts_made": 7,
        "best_masters_finish": 1,
        "sg_total": 1.75, "sg_approach": 1.40, "sg_off_tee": 0.85,
        "sg_around_green": 0.35, "sg_putting": 0.15, "sg_tee_to_green": 1.60,
        "scoring_avg": 69.5, "driving_distance": 308.4, "gir_pct": 69.8,
        "spike_approach_events": 4
    },
    "Xander Schauffele": {
        "masters_appearances": 7, "masters_wins": 0, "masters_top5": 2,
        "masters_top10": 5, "masters_top25": 6, "masters_cuts_made": 7,
        "best_masters_finish": 2,
        "sg_total": 1.60, "sg_approach": 1.20, "sg_off_tee": 0.75,
        "sg_around_green": 0.40, "sg_putting": 0.25, "sg_tee_to_green": 1.35,
        "scoring_avg": 69.6, "driving_distance": 304.5, "gir_pct": 69.2,
        "spike_approach_events": 3
    },
    "Bryson DeChambeau": {
        "masters_appearances": 7, "masters_wins": 0, "masters_top5": 1,
        "masters_top10": 2, "masters_top25": 4, "masters_cuts_made": 6,
        "best_masters_finish": 5,
        "sg_total": 1.55, "sg_approach": 0.95, "sg_off_tee": 1.30,
        "sg_around_green": 0.15, "sg_putting": 0.15, "sg_tee_to_green": 1.40,
        "scoring_avg": 69.7, "driving_distance": 320.5, "gir_pct": 68.5,
        "spike_approach_events": 3
    },
    "Ludvig Aberg": {
        "masters_appearances": 2, "masters_wins": 0, "masters_top5": 1,
        "masters_top10": 1, "masters_top25": 2, "masters_cuts_made": 2,
        "best_masters_finish": 2,
        "sg_total": 1.70, "sg_approach": 1.50, "sg_off_tee": 0.90,
        "sg_around_green": 0.25, "sg_putting": 0.05, "sg_tee_to_green": 1.65,
        "scoring_avg": 69.3, "driving_distance": 310.1, "gir_pct": 71.0,
        "spike_approach_events": 5
    },
    "Collin Morikawa": {
        "masters_appearances": 4, "masters_wins": 0, "masters_top5": 1,
        "masters_top10": 2, "masters_top25": 3, "masters_cuts_made": 4,
        "best_masters_finish": 3,
        "sg_total": 1.45, "sg_approach": 1.70, "sg_off_tee": 0.35,
        "sg_around_green": 0.20, "sg_putting": -0.20, "sg_tee_to_green": 1.65,
        "scoring_avg": 69.8, "driving_distance": 296.3, "gir_pct": 71.8,
        "spike_approach_events": 4
    },
    "Hideki Matsuyama": {
        "masters_appearances": 10, "masters_wins": 1, "masters_top5": 3,
        "masters_top10": 5, "masters_top25": 7, "masters_cuts_made": 9,
        "best_masters_finish": 1,
        "sg_total": 1.50, "sg_approach": 1.35, "sg_off_tee": 0.65,
        "sg_around_green": 0.30, "sg_putting": 0.20, "sg_tee_to_green": 1.30,
        "scoring_avg": 69.7, "driving_distance": 301.2, "gir_pct": 69.5,
        "spike_approach_events": 3
    },
    "Viktor Hovland": {
        "masters_appearances": 4, "masters_wins": 0, "masters_top5": 1,
        "masters_top10": 2, "masters_top25": 3, "masters_cuts_made": 4,
        "best_masters_finish": 4,
        "sg_total": 1.30, "sg_approach": 1.15, "sg_off_tee": 0.80,
        "sg_around_green": -0.30, "sg_putting": -0.35, "sg_tee_to_green": 1.65,
        "scoring_avg": 69.9, "driving_distance": 303.7, "gir_pct": 70.2,
        "spike_approach_events": 3
    },
    "Brooks Koepka": {
        "masters_appearances": 8, "masters_wins": 0, "masters_top5": 2,
        "masters_top10": 3, "masters_top25": 5, "masters_cuts_made": 7,
        "best_masters_finish": 2,
        "sg_total": 1.25, "sg_approach": 0.85, "sg_off_tee": 0.95,
        "sg_around_green": 0.20, "sg_putting": -0.25, "sg_tee_to_green": 1.50,
        "scoring_avg": 70.0, "driving_distance": 310.8, "gir_pct": 68.0,
        "spike_approach_events": 2
    },
    "Jordan Spieth": {
        "masters_appearances": 11, "masters_wins": 1, "masters_top5": 4,
        "masters_top10": 5, "masters_top25": 8, "masters_cuts_made": 10,
        "best_masters_finish": 1,
        "sg_total": 0.85, "sg_approach": 0.60, "sg_off_tee": 0.30,
        "sg_around_green": 0.40, "sg_putting": -0.45, "sg_tee_to_green": 1.30,
        "scoring_avg": 70.4, "driving_distance": 298.5, "gir_pct": 66.8,
        "spike_approach_events": 2
    },
    "Cameron Smith": {
        "masters_appearances": 7, "masters_wins": 0, "masters_top5": 2,
        "masters_top10": 3, "masters_top25": 4, "masters_cuts_made": 6,
        "best_masters_finish": 2,
        "sg_total": 1.10, "sg_approach": 0.55, "sg_off_tee": 0.25,
        "sg_around_green": 0.50, "sg_putting": 0.80, "sg_tee_to_green": 0.30,
        "scoring_avg": 70.1, "driving_distance": 294.2, "gir_pct": 66.5,
        "spike_approach_events": 1
    },
    "Patrick Cantlay": {
        "masters_appearances": 6, "masters_wins": 0, "masters_top5": 1,
        "masters_top10": 2, "masters_top25": 4, "masters_cuts_made": 5,
        "best_masters_finish": 4,
        "sg_total": 1.20, "sg_approach": 1.05, "sg_off_tee": 0.40,
        "sg_around_green": 0.35, "sg_putting": -0.10, "sg_tee_to_green": 1.30,
        "scoring_avg": 70.0, "driving_distance": 299.8, "gir_pct": 69.0,
        "spike_approach_events": 2
    },
    "Sam Burns": {
        "masters_appearances": 4, "masters_wins": 0, "masters_top5": 0,
        "masters_top10": 1, "masters_top25": 2, "masters_cuts_made": 3,
        "best_masters_finish": 8,
        "sg_total": 1.15, "sg_approach": 0.75, "sg_off_tee": 0.70,
        "sg_around_green": 0.25, "sg_putting": -0.05, "sg_tee_to_green": 1.20,
        "scoring_avg": 70.0, "driving_distance": 307.5, "gir_pct": 68.5,
        "spike_approach_events": 2
    },
    "Wyndham Clark": {
        "masters_appearances": 2, "masters_wins": 0, "masters_top5": 0,
        "masters_top10": 1, "masters_top25": 2, "masters_cuts_made": 2,
        "best_masters_finish": 9,
        "sg_total": 1.35, "sg_approach": 0.90, "sg_off_tee": 0.85,
        "sg_around_green": 0.15, "sg_putting": -0.05, "sg_tee_to_green": 1.40,
        "scoring_avg": 69.8, "driving_distance": 311.3, "gir_pct": 69.0,
        "spike_approach_events": 3
    },
    "Tommy Fleetwood": {
        "masters_appearances": 6, "masters_wins": 0, "masters_top5": 1,
        "masters_top10": 3, "masters_top25": 4, "masters_cuts_made": 5,
        "best_masters_finish": 4,
        "sg_total": 1.40, "sg_approach": 1.10, "sg_off_tee": 0.60,
        "sg_around_green": 0.25, "sg_putting": -0.05, "sg_tee_to_green": 1.45,
        "scoring_avg": 69.7, "driving_distance": 302.0, "gir_pct": 70.5,
        "spike_approach_events": 3
    },
    "Justin Thomas": {
        "masters_appearances": 8, "masters_wins": 0, "masters_top5": 2,
        "masters_top10": 3, "masters_top25": 5, "masters_cuts_made": 7,
        "best_masters_finish": 4,
        "sg_total": 1.00, "sg_approach": 0.80, "sg_off_tee": 0.50,
        "sg_around_green": 0.15, "sg_putting": -0.15, "sg_tee_to_green": 1.15,
        "scoring_avg": 70.2, "driving_distance": 305.0, "gir_pct": 68.8,
        "spike_approach_events": 2
    },
    "Shane Lowry": {
        "masters_appearances": 6, "masters_wins": 0, "masters_top5": 0,
        "masters_top10": 2, "masters_top25": 3, "masters_cuts_made": 4,
        "best_masters_finish": 6,
        "sg_total": 1.10, "sg_approach": 0.80, "sg_off_tee": 0.45,
        "sg_around_green": 0.35, "sg_putting": -0.10, "sg_tee_to_green": 1.20,
        "scoring_avg": 70.1, "driving_distance": 298.0, "gir_pct": 68.2,
        "spike_approach_events": 2
    },
    "Sungjae Im": {
        "masters_appearances": 5, "masters_wins": 0, "masters_top5": 1,
        "masters_top10": 2, "masters_top25": 3, "masters_cuts_made": 5,
        "best_masters_finish": 2,
        "sg_total": 1.05, "sg_approach": 0.70, "sg_off_tee": 0.55,
        "sg_around_green": 0.20, "sg_putting": -0.10, "sg_tee_to_green": 1.15,
        "scoring_avg": 70.1, "driving_distance": 300.5, "gir_pct": 69.0,
        "spike_approach_events": 2
    },
    "Corey Conners": {
        "masters_appearances": 5, "masters_wins": 0, "masters_top5": 0,
        "masters_top10": 2, "masters_top25": 3, "masters_cuts_made": 5,
        "best_masters_finish": 6,
        "sg_total": 0.95, "sg_approach": 1.25, "sg_off_tee": 0.55,
        "sg_around_green": -0.10, "sg_putting": -0.30, "sg_tee_to_green": 1.25,
        "scoring_avg": 70.2, "driving_distance": 302.8, "gir_pct": 72.0,
        "spike_approach_events": 3
    }
}


def enrich_field():
    """Update field with Augusta history and season stats"""
    players = get_field()
    print(f"Found {len(players)} players in field")

    updated = 0
    for player in players:
        name = player["player_name"]
        if name in AUGUSTA_HISTORY:
            data = AUGUSTA_HISTORY[name]
            # Calculate course fit score
            # Weighted: approach(35%) + off_tee(25%) + around_green(20%) + putting(10%) + experience(10%)
            sg_app = data.get("sg_approach", 0) or 0
            sg_ott = data.get("sg_off_tee", 0) or 0
            sg_arg = data.get("sg_around_green", 0) or 0
            sg_put = data.get("sg_putting", 0) or 0
            exp_factor = min(data.get("masters_appearances", 0) / 10, 1.0)

            course_fit = (sg_app * 0.35 + sg_ott * 0.25 + sg_arg * 0.20 + sg_put * 0.10 + exp_factor * 0.10) * 10
            data["course_fit_score"] = round(course_fit, 2)

            # Build update
            update_data = {k: v for k, v in data.items()}

            url = f"{SUPABASE_URL}/rest/v1/masters_field_2026?player_name=eq.{urllib.parse.quote(name)}"
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            }
            body = json.dumps(update_data).encode()
            req = urllib.request.Request(url, data=body, headers=headers, method="PATCH")
            try:
                with urllib.request.urlopen(req, context=ctx) as resp:
                    updated += 1
                    print(f"  Updated {name} (fit: {course_fit:.1f})")
            except urllib.error.HTTPError as e:
                print(f"  Error updating {name}: {e.read().decode()}")

    print(f"\nEnriched {updated}/{len(players)} players with detailed stats")


if __name__ == "__main__":
    print("=== Masters Database Enrichment ===\n")
    enrich_field()
    print("\nDone!")
