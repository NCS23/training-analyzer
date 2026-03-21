"""HR Zone Calculator — Karvonen- und Friel-Modell.

Karvonen: Zonen basierend auf Herzfrequenzreserve (HRR = Max-HR - Ruhe-HR).
Friel: Zonen basierend auf Laktatschwellen-HR (LTHR) aus dem 30-Min-Test.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class HRZoneDef:
    """Definition einer HR-Zone (fuer Karvonen und Friel)."""

    zone: int
    name: str
    pct_min: float
    pct_max: float
    color: str


# Karvonen 5-Zone Intensitaeten (% der Herzfrequenzreserve)
KARVONEN_ZONES: list[HRZoneDef] = [
    HRZoneDef(1, "Recovery", 0.50, 0.60, "#94a3b8"),
    HRZoneDef(2, "Base", 0.60, 0.70, "#10b981"),
    HRZoneDef(3, "Tempo", 0.70, 0.80, "#f59e0b"),
    HRZoneDef(4, "Threshold", 0.80, 0.90, "#f97316"),
    HRZoneDef(5, "VO2max", 0.90, 1.00, "#ef4444"),
]

# Friel 5-Zone Intensitaeten (% der Laktatschwellen-HR)
# Basiert auf Joe Friel, The Triathlete's Training Bible
FRIEL_ZONES: list[HRZoneDef] = [
    HRZoneDef(1, "Recovery", 0.00, 0.85, "#94a3b8"),
    HRZoneDef(2, "Aerobic", 0.85, 0.90, "#10b981"),
    HRZoneDef(3, "Tempo", 0.90, 0.95, "#f59e0b"),
    HRZoneDef(4, "Sub-Threshold", 0.95, 1.00, "#f97316"),
    HRZoneDef(5, "Supra-Threshold", 1.00, 1.06, "#ef4444"),
]

# Compat alias fuer bestehenden Import in test_hr_zones.py
KarvonenZoneDef = HRZoneDef


def karvonen_bpm(resting_hr: int, max_hr: int, intensity: float) -> int:
    """Karvonen-Formel: Target HR = Ruhe-HR + (Max-HR - Ruhe-HR) * Intensitaet."""
    return round(resting_hr + (max_hr - resting_hr) * intensity)


def calculate_karvonen_zones(resting_hr: int, max_hr: int) -> list[dict]:
    """Berechnet 5-Zonen Grenzen via Karvonen-Formel."""
    zones = []
    for z in KARVONEN_ZONES:
        lower = karvonen_bpm(resting_hr, max_hr, z.pct_min)
        upper = karvonen_bpm(resting_hr, max_hr, z.pct_max)
        zones.append(
            {
                "zone": z.zone,
                "name": z.name,
                "lower_bpm": lower,
                "upper_bpm": upper,
                "color": z.color,
                "pct_min": z.pct_min,
                "pct_max": z.pct_max,
            }
        )
    return zones


def calculate_friel_zones(lthr: int) -> list[dict]:
    """Berechnet 5-Zonen Grenzen via Friel-Modell (% der LTHR)."""
    zones = []
    for z in FRIEL_ZONES:
        lower = round(lthr * z.pct_min) if z.pct_min > 0 else 0
        upper = round(lthr * z.pct_max)
        zones.append(
            {
                "zone": z.zone,
                "name": z.name,
                "lower_bpm": lower,
                "upper_bpm": upper,
                "color": z.color,
                "pct_min": z.pct_min,
                "pct_max": z.pct_max,
            }
        )
    return zones


def _distribute_hr_across_zones(hr_values: list[int], zones: list[dict]) -> dict:
    """Verteilt HR-Werte auf definierte Zonen und berechnet Anteile."""
    total = len(hr_values)
    counts = [0] * len(zones)

    for hr in hr_values:
        for i, z in enumerate(zones):
            if i == len(zones) - 1:
                if hr >= z["lower_bpm"]:
                    counts[i] += 1
                    break
            elif z["lower_bpm"] <= hr < z["upper_bpm"]:
                counts[i] += 1
                break
        else:
            counts[0] += 1

    result = {}
    for i, z in enumerate(zones):
        key = f"zone_{z['zone']}_{z['name'].lower().replace('-', '_')}"
        result[key] = {
            "seconds": counts[i],
            "percentage": round(counts[i] / total * 100, 1) if total > 0 else 0,
            "label": f"{z['lower_bpm']}-{z['upper_bpm']} bpm",
            "zone": z["zone"],
            "name": z["name"],
            "color": z["color"],
        }
    return result


def _fallback_3zone(hr_values: list[int]) -> dict:
    """3-Zonen Fallback ohne Athleten-Daten."""
    total = len(hr_values)
    zone1 = sum(1 for hr in hr_values if hr < 150)
    zone2 = sum(1 for hr in hr_values if 150 <= hr < 160)
    zone3 = sum(1 for hr in hr_values if hr >= 160)

    return {
        "zone_1_recovery": {
            "seconds": zone1,
            "percentage": round(zone1 / total * 100, 1) if total > 0 else 0,
            "label": "< 150 bpm",
        },
        "zone_2_base": {
            "seconds": zone2,
            "percentage": round(zone2 / total * 100, 1) if total > 0 else 0,
            "label": "150-160 bpm",
        },
        "zone_3_tempo": {
            "seconds": zone3,
            "percentage": round(zone3 / total * 100, 1) if total > 0 else 0,
            "label": "> 160 bpm",
        },
    }


def calculate_zone_distribution(
    hr_values: list[int],
    resting_hr: Optional[int] = None,
    max_hr: Optional[int] = None,
    lthr: Optional[int] = None,
) -> dict:
    """Berechnet Zeit in jeder Zone.

    Prioritaet: LTHR (Friel) > Karvonen > 3-Zonen Fallback.
    """
    if not hr_values:
        return {}

    if lthr is not None:
        return _distribute_hr_across_zones(hr_values, calculate_friel_zones(lthr))
    if resting_hr is not None and max_hr is not None:
        return _distribute_hr_across_zones(hr_values, calculate_karvonen_zones(resting_hr, max_hr))
    return _fallback_3zone(hr_values)
