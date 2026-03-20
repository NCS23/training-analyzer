"""Trainingswissen-Datenbank fuer den KI-Chat (#394).

Einfache keyword-basierte Wissenssuche als Vorstufe zu RAG.
Kann spaeter durch eine Vector-DB (pgvector) ersetzt werden.
"""

from dataclasses import dataclass

KNOWLEDGE_ENTRIES: list[dict] = [
    {
        "id": "lactate_threshold",
        "title": "Laktatschwelle (LT2 / anaerobe Schwelle)",
        "category": "physiology",
        "keywords": ["laktatschwelle", "anaerob", "schwelle", "lt2", "threshold", "laktat"],
        "content": (
            "Die Laktatschwelle (LT2) ist die Belastungsintensitaet, ab der Laktat schneller "
            "produziert wird als es abgebaut werden kann. Sie liegt typisch bei 80-90% der max. HF. "
            "Training an der Laktatschwelle (Tempolaeufe, Cruise Intervals) verbessert die "
            "Faehigkeit, hohe Pace laenger durchzuhalten. Pfitzinger empfiehlt 15-20 min "
            "Tempo-Abschnitte bei LT-Pace fuer Halbmarathon-Vorbereitung."
        ),
        "sources": ["Pfitzinger: Advanced Marathoning", "Daniels: Running Formula"],
    },
    {
        "id": "periodization",
        "title": "Periodisierung im Lauftraining",
        "category": "training_methods",
        "keywords": ["periodisierung", "phasen", "base", "build", "peak", "taper", "makrozyklus"],
        "content": (
            "Periodisierung teilt das Training in Phasen mit unterschiedlichem Fokus: "
            "1) Base/Grundlagen (aerobe Basis, Volumen aufbauen, 8-12 Wochen), "
            "2) Build/Aufbau (spezifische Intensitaet steigern, Tempolaeufe + Intervalle), "
            "3) Peak/Spitze (Race-Pace Training, reduziertes Volumen), "
            "4) Taper (Erholung vor Wettkampf, 2-3 Wochen Volumenreduktion 40-60%). "
            "Jede Phase baut auf der vorherigen auf. Progression: max. 10% Volumen/Woche."
        ),
        "sources": ["Daniels: Running Formula", "Pfitzinger: Advanced Marathoning"],
    },
    {
        "id": "easy_running",
        "title": "Lockeres Laufen (Easy Running / GA1)",
        "category": "training_methods",
        "keywords": ["locker", "easy", "ga1", "grundlage", "aerob", "langsam", "erholung"],
        "content": (
            "Lockeres Laufen (60-75% max. HF) bildet die Basis jedes Trainingsplans. "
            "Es verbessert die aerobe Kapazitaet, Fettverbrennung und Erholung. "
            "Daniels empfiehlt 60-80% des Gesamtvolumens im Easy-Bereich. "
            "Viele Laeufer laufen zu schnell — der 'Gespraechstest' hilft: "
            "Man sollte sich beim Laufen noch normal unterhalten koennen. "
            "HM-Ziel Sub-2h: Easy Pace ca. 6:30-7:00 min/km."
        ),
        "sources": ["Daniels: Running Formula", "Maffetone: MAF Method"],
    },
    {
        "id": "interval_training",
        "title": "Intervalltraining",
        "category": "training_methods",
        "keywords": ["intervall", "interval", "vo2max", "speed", "schnelligkeit", "hiit"],
        "content": (
            "Intervalltraining verbessert VO2max und Laufeffizienz durch wiederholte "
            "hochintensive Belastungen mit Erholungspausen. Typische Formate: "
            "- 5x1000m @ VO2max-Pace (3K-5K Pace) mit 2-3 min Trabpause "
            "- 8x400m @ etwas schneller als 5K-Pace mit 90s Pause "
            "- 3x1600m @ 5K-10K Pace mit 3 min Pause "
            "Max. 8% des Wochenvolumens als Intervalle. 1-2x pro Woche in Build/Peak."
        ),
        "sources": ["Daniels: Running Formula"],
    },
    {
        "id": "long_run",
        "title": "Langer Lauf (Long Run)",
        "category": "training_methods",
        "keywords": ["langer", "long", "run", "dauerlauf", "langstrecke", "endurance"],
        "content": (
            "Der lange Lauf ist die Schluesseleinheit fuer Halbmarathon/Marathon. "
            "Er verbessert aerobe Ausdauer, Fettverbrennung und mentale Haerte. "
            "Laenge: 25-30% des Wochenvolumens, max. 2.5-3h Laufzeit. "
            "Fuer HM Sub-2h: Laengster Lauf 18-22 km bei Easy-Pace + ggf. "
            "letzte 3-5 km bei HM-Pace (Progression Long Run). "
            "Steigerung: max. 2 km pro Woche, jede 4. Woche Entlastung."
        ),
        "sources": ["Pfitzinger: Advanced Marathoning", "Daniels: Running Formula"],
    },
    {
        "id": "tapering",
        "title": "Tapering (Wettkampfvorbereitung)",
        "category": "race_prep",
        "keywords": ["taper", "wettkampf", "vorbereitung", "rennen", "race", "erholung"],
        "content": (
            "Tapering reduziert das Trainingsvolumen vor dem Wettkampf, "
            "waehrend die Intensitaet beibehalten wird. Fuer Halbmarathon: "
            "- 2 Wochen Taper (bei laengerem Training 3 Wochen) "
            "- Woche 1: 70-75% des Normalvolumens "
            "- Woche 2: 50-60% des Normalvolumens "
            "- Letzter Long Run: 10-12 km, 2 Wochen vor Wettkampf "
            "- Letzte harte Einheit: 8-10 Tage vor Wettkampf "
            "- Letzte 2-3 Tage: nur leichtes Joggen oder Ruhe"
        ),
        "sources": ["Pfitzinger: Advanced Marathoning"],
    },
    {
        "id": "strength_for_runners",
        "title": "Krafttraining fuer Laeufer",
        "category": "training_methods",
        "keywords": ["kraft", "strength", "staerkung", "gym", "uebungen", "core", "stabilisation"],
        "content": (
            "Krafttraining verbessert Laufoekonomie und reduziert Verletzungsrisiko. "
            "Empfehlung: 2x/Woche in Base, 1x/Woche in Build/Peak, 0x in Taper. "
            "Fokus: Core-Stabilitaet, Gluteus, Quadrizeps, Wadenmuskulatur. "
            "Schluesseluebungen: Squats, Lunges, Step-Ups, Deadlifts (leicht), "
            "Planks, Side Planks, Single-Leg Bridges, Calf Raises. "
            "Krafttraining nie direkt vor hartem Lauftraining am selben Tag."
        ),
        "sources": ["Pfitzinger: Advanced Marathoning", "Dicharry: Running Rewired"],
    },
    {
        "id": "overtraining",
        "title": "Uebertraining erkennen und vermeiden",
        "category": "recovery",
        "keywords": [
            "uebertraining",
            "overtraining",
            "erholung",
            "recovery",
            "muede",
            "erschoepfung",
            "ruhe",
            "regeneration",
            "uebelastung",
        ],
        "content": (
            "Uebertraining entsteht durch dauerhaft zu hohe Belastung ohne ausreichende Erholung. "
            "Warnsignale: erhoehter Ruhepuls (>5 bpm ueber normal), "
            "Schlafprobleme, Motivationsverlust, fallende Leistung trotz Training, "
            "haeufige Infekte, anhaltende Muskelschmerzen. "
            "Praevention: 10%-Regel (Volumen max. 10%/Woche steigern), "
            "jede 3.-4. Woche Entlastung (20-30% weniger), "
            "1-2 Ruhetage/Woche, genug Schlaf (7-9h)."
        ),
        "sources": ["Daniels: Running Formula"],
    },
    {
        "id": "hr_zones",
        "title": "Herzfrequenzzonen",
        "category": "physiology",
        "keywords": ["herzfrequenz", "hf", "hr", "zonen", "zone", "puls", "heart", "rate"],
        "content": (
            "Herzfrequenzzonen basieren auf der maximalen HF oder Laktatschwellen-HF: "
            "- Zone 1 (50-60% HFmax): Regeneration, sehr lockeres Gehen/Joggen "
            "- Zone 2 (60-70%): Grundlagenausdauer, lockeres Laufen (GA1) "
            "- Zone 3 (70-80%): Tempo-Ausdauer, moderates Laufen (GA2) "
            "- Zone 4 (80-90%): Schwellenbereich, Tempolaeufe, hart aber kontrolliert "
            "- Zone 5 (90-100%): VO2max, Intervalle, maximale Anstrengung "
            "80% des Trainings sollte in Zone 1-2 stattfinden (80/20-Regel)."
        ),
        "sources": ["Seiler: Polarized Training", "Daniels: Running Formula"],
    },
    {
        "id": "nutrition_running",
        "title": "Ernaehrung fuer Laeufer",
        "category": "nutrition",
        "keywords": ["ernaehrung", "nutrition", "essen", "kohlenhydrate", "carbs", "protein"],
        "content": (
            "Laeufer brauchen mehr Kohlenhydrate als Nicht-Sportler: "
            "- Leichte Tage: 5-7 g/kg Koerpergewicht Kohlenhydrate "
            "- Harte Tage/Long Run: 7-10 g/kg "
            "- Vor dem Wettkampf: Carb-Loading (8-10 g/kg, 2-3 Tage vorher) "
            "- Nach dem Training: Protein (20-25g) + Kohlenhydrate innerhalb 30-60 min "
            "- Hydration: 400-800 ml/h waehrend langer Laeufe (>60 min) "
            "- Bei Laeufen >75 min: 30-60g Kohlenhydrate/h (Gels, Riegel)"
        ),
        "sources": ["Pfitzinger: Advanced Marathoning"],
    },
    {
        "id": "injury_prevention",
        "title": "Verletzungspraevention",
        "category": "injury_prevention",
        "keywords": [
            "verletzung",
            "praevention",
            "schmerz",
            "dehnen",
            "aufwaermen",
            "shin",
            "splints",
            "knie",
            "achilles",
            "plantarfaszie",
        ],
        "content": (
            "Die haeufigsten Laufverletzungen und Praevention: "
            "- Shin Splints: Volumen langsam steigern, Krafttraining fuer Tibialis anterior "
            "- Runner's Knee: Hueftabduktoren staerken, Laufstil pruefen "
            "- Achillessehne: Exzentrische Wadenuebungen, nicht zu viel Bergtraining "
            "- Plantarfasziitis: Wadendehnung, Fussgewoelbe-Training, gutes Schuhwerk "
            "Allgemein: 10%-Regel beachten, Aufwaermen (5-10 min lockeres Laufen), "
            "Kraft + Mobility 2x/Woche, bei Schmerzen sofort reduzieren."
        ),
        "sources": ["Dicharry: Running Rewired"],
    },
    {
        "id": "half_marathon_pacing",
        "title": "Halbmarathon Pacing-Strategie",
        "category": "race_prep",
        "keywords": [
            "halbmarathon",
            "pacing",
            "pace",
            "strategie",
            "renntaktik",
            "hm",
            "21km",
            "sub2",
            "sub-2",
            "wettkampf",
        ],
        "content": (
            "Pacing-Strategie fuer Halbmarathon Sub-2h (Zielpace ~5:41 min/km): "
            "- Even Pacing oder leichtes Negative Split bevorzugen "
            "- Erste 3 km: 5:45-5:50 (bewusst zurueckhalten) "
            "- Km 3-15: gleichmaessig 5:38-5:42 "
            "- Km 15-18: Pace halten, mental fokussieren "
            "- Km 18-21: wenn moeglich, leicht beschleunigen auf 5:35-5:38 "
            "- NICHT zu schnell starten — jede Sekunde zu schnell in km 1-5 "
            "  kostet 2-3 Sekunden in km 18-21. "
            "- Bei Hitze (>25°C): Pace um 10-20 sek/km reduzieren."
        ),
        "sources": ["Pfitzinger: Advanced Marathoning"],
    },
]


@dataclass
class KnowledgeResult:
    """Ergebnis einer Wissenssuche."""

    id: str
    title: str
    category: str
    content: str
    sources: list[str]
    relevance: float


def search_knowledge(query: str, category: str | None = None, limit: int = 3) -> list[dict]:
    """Durchsucht die Trainingswissen-Datenbank via Keyword-Matching."""
    query_lower = query.lower()
    query_words = query_lower.split()

    scored: list[tuple[float, dict]] = []
    for entry in KNOWLEDGE_ENTRIES:
        if category and entry["category"] != category:
            continue

        score = 0.0
        # Keyword-Match
        for kw in entry["keywords"]:
            if kw in query_lower:
                score += 3.0
            for word in query_words:
                if word in kw or kw in word:
                    score += 1.5

        # Titel-Match
        title_lower = entry["title"].lower()
        for word in query_words:
            if word in title_lower:
                score += 2.0

        if score > 0:
            scored.append(
                (
                    score,
                    {
                        "title": entry["title"],
                        "category": entry["category"],
                        "content": entry["content"],
                        "sources": entry["sources"],
                    },
                )
            )

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:limit]]
