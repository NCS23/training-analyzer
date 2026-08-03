#!/usr/bin/env python3
"""Exportiert den kompletten Stand fuer die minsaga-Migration (Format v2).

Duenner Wrapper um `GET /api/v1/export/minsaga` — der Server stellt alles
zusammen: Profil + Schwellentests, Ziele, Plaene mit Changelog
(Entscheidungen samt Begruendung) und alle Wochenplan-Wochen inklusive
Anpassungen. Einfacher geht es direkt im Web-UI: Athletenprofil →
"Export fuer minsaga".

Historische Workouts sind bewusst NICHT enthalten - die kommen in
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

    export = api_get(args.base_url, token, "/api/v1/export/minsaga")

    with open(args.output, "w", encoding="utf-8") as datei:
        json.dump(export, datei, ensure_ascii=False, indent=2)
    print(
        f"Export geschrieben: {args.output} — "
        f"{len(export.get('goals', []))} Ziele, "
        f"{len(export.get('plans', []))} Plaene, "
        f"{len(export.get('weekly_plans', []))} Wochen."
    )


if __name__ == "__main__":
    main()
