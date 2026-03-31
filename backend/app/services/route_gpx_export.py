"""GPX Export für Trainingsrouten mit Training-Extensions (#553).

Generiert GPX 1.1 Dateien mit Custom-Extensions für Pace-Ziele, HR-Ziele
und Segment-Typ — kompatibel mit WorkOutDoors und Garmin Connect.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional
from xml.etree.ElementTree import Element, SubElement, tostring

from app.models.training_route import RouteSegment, Waypoint

# ---------------------------------------------------------------------------
# Namespace-Konstanten
# ---------------------------------------------------------------------------

_NS_GPX = "http://www.topografix.com/GPX/1/1"
_NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"
_XSI_SCHEMA = "http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd"
_NS_TA = "http://training-analyzer.app/gpx/extensions/v1"

# Segment-Typ → WorkOutDoors-kompatibler Lap-Type
_SEGMENT_TYPE_MAP: dict[str, str] = {
    "warmup": "warmup",
    "cooldown": "cooldown",
    "work": "interval",
    "recovery": "recovery",
    "steady": "active",
    "threshold": "interval",
    "vo2max": "interval",
    "long_run": "active",
    "race": "active",
}


# ---------------------------------------------------------------------------
# Öffentliche API
# ---------------------------------------------------------------------------


def generate_gpx(
    route_name: str,
    waypoints: list[Waypoint],
    segments: list[RouteSegment],
    description: Optional[str] = None,
) -> bytes:
    """Erzeugt GPX-Datei als UTF-8 Bytes.

    Struktur:
    - <gpx> mit Metadaten
    - <trk> mit <name>, <desc>, <extensions> (Segment-Übersicht)
    - <trkseg> mit einem <trkpt> pro Waypoint
    - Jeder Trackpoint enthält <extensions> mit dem aktiven Segment-Typ
    """
    gpx = _build_gpx_root()
    _add_metadata(gpx, route_name)
    trk = SubElement(gpx, "trk")
    SubElement(trk, "name").text = route_name
    if description:
        SubElement(trk, "desc").text = description

    _add_segment_extensions(trk, segments)
    _add_trkseg(trk, waypoints, segments)

    xml_bytes = tostring(gpx, encoding="unicode", xml_declaration=False)
    header = '<?xml version="1.0" encoding="UTF-8"?>\n'
    return (header + xml_bytes).encode("utf-8")


# ---------------------------------------------------------------------------
# GPX-Baum aufbauen
# ---------------------------------------------------------------------------


def _build_gpx_root() -> Element:
    gpx = Element("gpx")
    gpx.set("version", "1.1")
    gpx.set("creator", "Training Analyzer")
    gpx.set("xmlns", _NS_GPX)
    gpx.set("xmlns:xsi", _NS_XSI)
    gpx.set("xsi:schemaLocation", _XSI_SCHEMA)
    gpx.set("xmlns:ta", _NS_TA)
    return gpx


def _add_metadata(gpx: Element, route_name: str) -> None:
    meta = SubElement(gpx, "metadata")
    SubElement(meta, "name").text = route_name
    SubElement(meta, "time").text = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _add_segment_extensions(trk: Element, segments: list[RouteSegment]) -> None:
    """Fügt <extensions> mit Segment-Übersicht zum <trk> Element hinzu."""
    if not segments:
        return
    ext = SubElement(trk, "extensions")
    seg_list = SubElement(ext, "ta:segments")
    for seg in segments:
        seg_el = SubElement(seg_list, "ta:segment")
        seg_el.set("type", seg.segment_type)
        seg_el.set("start_km", str(round(seg.start_km, 3)))
        seg_el.set("end_km", str(round(seg.end_km, 3)))
        if seg.target_pace_min:
            seg_el.set("pace_min", seg.target_pace_min)
        if seg.target_pace_max:
            seg_el.set("pace_max", seg.target_pace_max)
        if seg.target_hr_min is not None:
            seg_el.set("hr_min", str(seg.target_hr_min))
        if seg.target_hr_max is not None:
            seg_el.set("hr_max", str(seg.target_hr_max))
        if seg.notes:
            seg_el.set("notes", seg.notes)


def _add_trkseg(
    trk: Element,
    waypoints: list[Waypoint],
    segments: list[RouteSegment],
) -> None:
    """Fügt <trkseg> mit Trackpoints hinzu.

    Jeder Trackpoint bekommt die aktiven Segment-Ziele als <extensions>.
    """
    trkseg = SubElement(trk, "trkseg")
    for wp in waypoints:
        trkpt = SubElement(trkseg, "trkpt")
        trkpt.set("lat", f"{wp.lat:.7f}")
        trkpt.set("lon", f"{wp.lng:.7f}")
        if wp.alt is not None:
            SubElement(trkpt, "ele").text = f"{wp.alt:.1f}"

        active_seg = _find_active_segment(wp.km_marker, segments)
        if active_seg:
            _add_trkpt_extensions(trkpt, active_seg)


def _find_active_segment(
    km_marker: Optional[float],
    segments: list[RouteSegment],
) -> Optional[RouteSegment]:
    """Findet das Segment, das den gegebenen km_marker enthält."""
    if km_marker is None or not segments:
        return None
    for seg in segments:
        if seg.start_km <= km_marker <= seg.end_km:
            return seg
    return None


def _add_trkpt_extensions(trkpt: Element, seg: RouteSegment) -> None:
    """Fügt Segment-Ziele als <extensions> zu einem Trackpoint hinzu."""
    ext = SubElement(trkpt, "extensions")
    ta_ext = SubElement(ext, "ta:training")
    ta_ext.set("segment_type", seg.segment_type)
    lap_type = _SEGMENT_TYPE_MAP.get(seg.segment_type, "active")
    ta_ext.set("lap_type", lap_type)
    if seg.target_pace_min:
        ta_ext.set("pace_min", seg.target_pace_min)
    if seg.target_pace_max:
        ta_ext.set("pace_max", seg.target_pace_max)
    if seg.target_hr_min is not None:
        ta_ext.set("hr_min", str(seg.target_hr_min))
    if seg.target_hr_max is not None:
        ta_ext.set("hr_max", str(seg.target_hr_max))


# ---------------------------------------------------------------------------
# Dateiname
# ---------------------------------------------------------------------------


def safe_filename(name: str) -> str:
    """Erzeugt einen sicheren Dateinamen aus dem Routennamen."""
    safe = re.sub(r"[^\w\s\-äöüÄÖÜß]", "", name)
    safe = re.sub(r"\s+", "_", safe.strip())
    return safe[:100] or "route"
