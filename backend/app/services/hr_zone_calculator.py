"""HR Zone Calculator mit Karvonen-Formel."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class KarvonenZoneDef:
    """Definition einer Karvonen-Zone."""

    zone: int
    name: str
    pct_min: float
    pct_max: float
    color: str


# Karvonen 5-Zone Intensitaeten (% der Herzfrequenzreserve)
KARVONEN_ZONES: list[KarvonenZoneDef] = [
    KarvonenZoneDef(1, "Recovery", 0.50, 0.60, "#94a3b8"),
    KarvonenZoneDef(2, "Base", 0.60, 0.70, "#10b981"),
    KarvonenZoneDef(3, "Tempo", 0.70, 0.80, "#f59e0b"),
    KarvonenZoneDef(4, "Threshold", 0.80, 0.90, "#f97316"),
    KarvonenZoneDef(5, "VO2max", 0.90, 1.00, "#ef4444"),
]


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


def calculate_zone_distribution(
    hr_values: list[int],
    resting_hr: Optional[int] = None,
    max_hr: Optional[int] = None,
) -> dict:
    """Berechnet Zeit in jeder Zone.

    Wenn resting_hr und max_hr gesetzt: 5-Zonen Karvonen.
    Sonst: 3-Zonen Fallback.
    """
    if not hr_values:
        return {}

    use_karvonen = resting_hr is not None and max_hr is not None
    total = len(hr_values)

    if use_karvonen:
        assert resting_hr is not None and max_hr is not None
        zones = calculate_karvonen_zones(resting_hr, max_hr)
        counts = [0] * len(zones)

        for hr in hr_values:
            for i, z in enumerate(zones):
                if i == len(zones) - 1:
                    # Letzte Zone: alles ab lower_bpm
                    if hr >= z["lower_bpm"]:
                        counts[i] += 1
                        break
                elif z["lower_bpm"] <= hr < z["upper_bpm"]:
                    counts[i] += 1
                    break
            else:
                # HR unter Zone 1 → zaehle zu Zone 1
                counts[0] += 1

        result = {}
        for i, z in enumerate(zones):
            key = f"zone_{z['zone']}_{z['name'].lower()}"
            result[key] = {
                "seconds": counts[i],
                "percentage": round(counts[i] / total * 100, 1) if total > 0 else 0,
                "label": f"{z['lower_bpm']}-{z['upper_bpm']} bpm",
                "zone": z["zone"],
                "name": z["name"],
                "color": z["color"],
            }
        return result
    else:
        # 3-Zone Fallback
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
