#!/usr/bin/env python3
"""Exportiert Ziele, Trainingsplaene und Profilwerte fuer die minsaga-Migration.

Erzeugt ein versioniertes `minsaga-export.json`, das die minsaga-iOS-App
im Profil ueber "Aus Training Analyzer importieren" einliest.
Historische Workouts werden bewusst NICHT exportiert - die kommen in
minsaga aus Apple Health (Import-Master).

Verwendung:
    python scripts/export_minsaga.py --base-url https://<backend> --token <JWT>
  oder mit Login:
    python scripts/export_minsaga.py --base-url https://<backend> \
        --email you@example.com --password ...

Nur Standardbibliothek - keine Abhaengigkeiten.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request


def api_get(base_url: str, token: str, path: str):
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}{path}",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read())


def api_login(base_url: str, email: str, password: str) -> str:
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/v1/auth/login",
        data=json.dumps({"email": email, "password": password}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request) as response:
        payload = json.loads(response.read())
    token = payload.get("access_token") or payload.get("token")
    if not token:
        sys.exit("Login fehlgeschlagen: kein Token in der Antwort.")
    return token


def pick(quelle: dict, *schluessel: str) -> dict:
    return {k: quelle.get(k) for k in schluessel}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--token")
    parser.add_argument("--email")
    parser.add_argument("--password")
    parser.add_argument("--output", default="minsaga-export.json")
    args = parser.parse_args()

    token = args.token
    if not token:
        if not (args.email and args.password):
            sys.exit("Entweder --token oder --email/--password angeben.")
        token = api_login(args.base_url, args.email, args.password)

    athlete_raw = api_get(args.base_url, token, "/api/v1/athlete/settings")
    athlete = pick(athlete_raw, "lthr", "resting_hr", "max_hr")

    goals_raw = api_get(args.base_url, token, "/api/v1/goals")
    goals = [
        pick(g, "title", "race_date", "distance_km", "target_time_seconds", "is_active")
        for g in goals_raw.get("goals", goals_raw if isinstance(goals_raw, list) else [])
    ]

    plans_raw = api_get(args.base_url, token, "/api/v1/training-plans")
    plan_liste = plans_raw.get("plans", plans_raw if isinstance(plans_raw, list) else [])
    plans = []
    for eintrag in plan_liste:
        detail = api_get(args.base_url, token, f"/api/v1/training-plans/{eintrag['id']}")
        phases = []
        for phase in detail.get("phases", []):
            template = phase.get("weekly_template") or {}
            days = []
            for day in template.get("days", []):
                days.append(
                    {
                        "day_of_week": day.get("day_of_week"),
                        "is_rest_day": day.get("is_rest_day", False),
                        "sessions": [
                            pick(s, "training_type", "run_type", "notes")
                            for s in day.get("sessions", [])
                        ],
                    }
                )
            phases.append(
                {
                    **pick(phase, "name", "phase_type", "start_week", "end_week"),
                    "weekly_template": {"days": days},
                }
            )
        goal_title = None
        if detail.get("race_goal"):
            goal_title = detail["race_goal"].get("title")
        plans.append(
            {
                **pick(detail, "name", "status", "start_date", "end_date"),
                "goal_title": goal_title,
                "phases": phases,
            }
        )

    export = {"version": 1, "athlete": athlete, "goals": goals, "plans": plans}
    with open(args.output, "w", encoding="utf-8") as datei:
        json.dump(export, datei, ensure_ascii=False, indent=2)
    print(
        f"Export geschrieben: {args.output} — "
        f"{len(goals)} Ziele, {len(plans)} Plaene."
    )


if __name__ == "__main__":
    main()
