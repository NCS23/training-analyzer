"""Chat Tool Definitions — JSON-Schemas fuer Claude Tool Use.

Definiert die 11 Tools, die der KI-Chat nutzen kann, um
Trainingsdaten on-demand nachzuladen.
"""

CHAT_TOOLS: list[dict] = [
    {
        "name": "get_session_details",
        "description": (
            "Laedt vollstaendige Details einer Trainingseinheit: "
            "Segmente/Laps, HF-Zonen, Wetter, Luftqualitaet, Hoehenmeter, "
            "KI-Analyse, Soll/Ist-Vergleich, Notizen, RPE. "
            "Nutze dieses Tool wenn der User nach Details einer bestimmten Session fragt."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "integer",
                    "description": "ID der Session (aus dem Kontext oder vorherigen Suchergebnissen)",
                },
            },
            "required": ["session_id"],
        },
    },
    {
        "name": "search_sessions",
        "description": (
            "Sucht und filtert Trainingseinheiten. "
            "Nutze dieses Tool fuer Fragen wie 'Alle Intervalltrainings im Februar', "
            "'Laeufe ueber 15km', 'Letzte 5 Krafttrainings'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "workout_type": {
                    "type": "string",
                    "description": "Workout-Typ: running, strength",
                    "enum": ["running", "strength"],
                },
                "training_type": {
                    "type": "string",
                    "description": (
                        "Trainingsart (nur Lauf): steady, progression, tempo, "
                        "interval, fartlek, repetitions, long_run, recovery_jog"
                    ),
                },
                "date_from": {
                    "type": "string",
                    "description": "Startdatum (YYYY-MM-DD)",
                },
                "date_to": {
                    "type": "string",
                    "description": "Enddatum (YYYY-MM-DD)",
                },
                "min_distance_km": {
                    "type": "number",
                    "description": "Minimale Distanz in km",
                },
                "max_distance_km": {
                    "type": "number",
                    "description": "Maximale Distanz in km",
                },
                "sort_by": {
                    "type": "string",
                    "description": "Sortierung",
                    "enum": ["date", "distance", "duration", "pace"],
                },
                "sort_order": {
                    "type": "string",
                    "enum": ["asc", "desc"],
                    "description": "Sortierrichtung (Standard: desc)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max. Anzahl Ergebnisse (Standard: 10, Max: 50)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_training_stats",
        "description": (
            "Liefert aggregierte Trainingsstatistiken fuer einen Zeitraum: "
            "Volumen, Durchschnittswerte, Verteilung nach Trainingstyp, Trend-Vergleich. "
            "Nutze dieses Tool fuer Fragen wie 'Wie viel bin ich diesen Monat gelaufen?', "
            "'Wie hat sich mein Volumen entwickelt?'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "description": "Zeitraum: 1w, 2w, 4w, 3m, 6m, 1y",
                    "enum": ["1w", "2w", "4w", "3m", "6m", "1y"],
                },
                "compare_previous": {
                    "type": "boolean",
                    "description": "Vergleich mit vorherigem Zeitraum (Standard: true)",
                },
            },
            "required": ["period"],
        },
    },
    {
        "name": "get_plan_details",
        "description": (
            "Laedt den aktiven Trainingsplan: Phasen, Wochenstruktur, "
            "geplante Sessions einer bestimmten Woche. "
            "Nutze dieses Tool fuer Fragen zum Trainingsplan, Phasen, was ansteht."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "week_offset": {
                    "type": "integer",
                    "description": (
                        "Wochen-Offset relativ zu heute. "
                        "0 = aktuelle Woche, 1 = naechste, -1 = letzte."
                    ),
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_plan_compliance",
        "description": (
            "Vergleicht geplante vs. tatsaechliche Sessions (Soll/Ist). "
            "Zeigt Abweichungen bei Pace, Dauer, Distanz und uebersprungene Sessions. "
            "Nutze dieses Tool fuer Fragen wie 'Habe ich meinen Plan eingehalten?'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "week_offset": {
                    "type": "integer",
                    "description": "Wochen-Offset (0 = aktuelle Woche, -1 = letzte)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_personal_records",
        "description": (
            "Liefert persoenliche Bestleistungen: schnellste Pace, "
            "laengster Lauf, hoechstes Wochenvolumen. "
            "Nutze dieses Tool fuer Fragen nach Bestleistungen oder Rekorden."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_exercises",
        "description": (
            "Durchsucht die Uebungsdatenbank nach Muskelgruppe, Kategorie, "
            "Equipment oder Level. "
            "Nutze dieses Tool fuer Fragen wie 'Welche Core-Uebungen gibt es?', "
            "'Uebungen ohne Geraete'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Kategorie: push, pull, legs, core, cardio",
                    "enum": ["push", "pull", "legs", "core", "cardio"],
                },
                "muscle_group": {
                    "type": "string",
                    "description": "Muskelgruppe (z.B. 'chest', 'quadriceps', 'abdominals')",
                },
                "equipment": {
                    "type": "string",
                    "description": "Equipment (z.B. 'body only', 'dumbbell', 'barbell')",
                },
                "level": {
                    "type": "string",
                    "description": "Schwierigkeitsgrad",
                    "enum": ["beginner", "intermediate", "expert"],
                },
                "search": {
                    "type": "string",
                    "description": "Freitext-Suche im Uebungsnamen",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max. Ergebnisse (Standard: 20)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_ai_recommendations",
        "description": (
            "Laedt bisherige KI-Empfehlungen aus Session-Analysen: "
            "Typ, Prioritaet, Begruendung, Status. "
            "Nutze dieses Tool fuer Fragen wie 'Was wurde mir empfohlen?', "
            "'Habe ich die Empfehlungen umgesetzt?'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "description": "Zeitraum: 1w, 2w, 4w, 3m",
                    "enum": ["1w", "2w", "4w", "3m"],
                },
                "status": {
                    "type": "string",
                    "description": "Filter nach Status",
                    "enum": ["pending", "applied", "dismissed"],
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_weekly_review",
        "description": (
            "Laedt den KI-Wochenrueckblick mit Zusammenfassung, "
            "Highlights, Verbesserungen, Empfehlungen fuer naechste Woche. "
            "Nutze dieses Tool fuer Fragen wie 'Wie war meine letzte Woche?'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "week_offset": {
                    "type": "integer",
                    "description": "Wochen-Offset (0 = aktuelle, -1 = letzte)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "search_conversations",
        "description": (
            "Durchsucht fruehere Chat-Konversationen nach Stichworten. "
            "Nutze dieses Tool wenn der User sich auf etwas bezieht, "
            "das in einem frueheren Gespraech besprochen wurde."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Suchbegriff(e)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max. Ergebnisse (Standard: 5)",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_plan_change_log",
        "description": (
            "Laedt die Aenderungshistorie des Trainingsplans: "
            "was wurde wann geaendert und warum. "
            "Nutze dieses Tool fuer Fragen wie 'Warum wurde mein Plan geaendert?'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "description": "Zeitraum: 1w, 2w, 4w, 3m",
                    "enum": ["1w", "2w", "4w", "3m"],
                },
                "limit": {
                    "type": "integer",
                    "description": "Max. Ergebnisse (Standard: 20)",
                },
            },
            "required": [],
        },
    },
]
