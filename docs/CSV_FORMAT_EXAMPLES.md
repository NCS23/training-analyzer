# 📊 CSV Data Format Examples

**Zweck:** Dokumentation der CSV-Strukturen für Apple Watch Exports  
**Für:** Claude AI Sessions - Verständnis der Datenformate

---

## 🏃‍♂️ Running CSV Structure

### Format Overview
- **Export Quelle:** Apple Watch → "Aktivität teilen" → CSV
- **Encoding:** UTF-8
- **Separator:** Komma (`,`)
- **Decimal:** Punkt (`.`)
- **Date Format:** ISO 8601 (YYYY-MM-DDTHH:MM:SS)

### Column Headers
```csv
timestamp,heart_rate (bpm),cadence (spm),distance (meter),speed (m/s),latitude (deg),longitude (deg),elevation (meter)
```

### Example Data (Intervalltraining)
```csv
timestamp,heart_rate (bpm),cadence (spm),distance (meter),speed (m/s),latitude (deg),longitude (deg),elevation (meter)
2026-02-04T06:30:00,120,0,0,0,51.4818,7.2162,120.5
2026-02-04T06:30:05,125,72,8.5,1.7,51.4818,7.2162,120.5
2026-02-04T06:30:10,130,75,17.2,1.74,51.4818,7.2162,120.5
...
[Warm-up Phase: ~7 Minuten, HR gradually rising to ~140]
...
2026-02-04T06:37:00,149,76,750,2.56,51.4820,7.2165,121.0
[Lap 1 Start - First Interval]
2026-02-04T06:37:05,155,77,763,2.56,51.4820,7.2165,121.0
2026-02-04T06:37:10,162,78,776,2.56,51.4820,7.2165,121.0
...
[3 minutes @ 6:31 min/km = 2.56 m/s, HR climbs to 165-170]
...
2026-02-04T06:40:00,168,78,1210,2.56,51.4822,7.2168,121.2
[Lap 1 End - Pause Start]
2026-02-04T06:40:05,165,45,1215,1.0,51.4822,7.2168,121.2
2026-02-04T06:40:10,160,40,1220,1.0,51.4822,7.2168,121.2
...
[2 minutes active recovery / Trab, HR drops to ~150]
...
2026-02-04T06:42:00,152,42,1330,1.0,51.4823,7.2169,121.3
[Lap 2 Start - Second Interval]
...
[Pattern repeats: 5× (3min work / 2min rest)]
...
2026-02-04T07:02:00,145,50,4200,1.5,51.4825,7.2172,121.5
[Cool-down starts, HR dropping]
...
2026-02-04T07:07:00,125,0,4500,0,51.4825,7.2172,121.5
[End of session]
```

### Key Patterns to Recognize

**Warm-up Detection:**
- Duration: 5-10 minutes
- HR: Gradual rise from resting (~110-120) to base (~140-150)
- Speed: Consistent, moderate
- Cadence: 70-75 spm

**Interval Detection:**
- Duration: Consistent (e.g., 3 min blocks)
- HR: High (>160 bpm typically)
- Speed: Fast & consistent within interval
- Cadence: High (75-80 spm)

**Recovery/Pause Detection:**
- Duration: 1-3 minutes typically
- HR: Dropping significantly
- Speed: Low (walking/slow jog)
- Cadence: Low (40-50 spm or 0)

**Cool-down Detection:**
- Duration: 3-7 minutes
- HR: Steady decline
- Speed: Slow, consistent
- Cadence: Low to zero

### Calculated Fields (from CSV)

**Pace (min/km):**
```python
pace_min_per_km = 1000 / (speed_m_s * 60)  # if speed > 0
# Example: 2.56 m/s → 6:31 min/km
```

**Distance (km):**
```python
distance_km = distance_meter / 1000
```

**Duration (seconds):**
```python
duration = (last_timestamp - first_timestamp).total_seconds()
```

**Lap Assignment:**
- Check for significant HR/speed changes
- Consistent duration blocks
- Classify based on HR zones

---

## 💪 Strength Training CSV Structure

### Format Overview
- Similar to Running, but fewer fields
- Often indoor (no GPS data)
- Exercise type sometimes included (if manually logged)

### Column Headers
```csv
timestamp,heart_rate (bpm),exercise_type,sets,reps,weight (kg)
```

### Example Data (Krafttraining)
```csv
timestamp,heart_rate (bpm),exercise_type,sets,reps,weight (kg)
2026-02-03T06:52:00,90,Mobilität,,,
2026-02-03T06:53:00,95,Vierfüßler BWS Rotation,1,1,
2026-02-03T06:54:00,100,Hüftrotation,1,1,
2026-02-03T06:55:00,105,,,
2026-02-03T06:56:00,130,Kniebeugen,1,6,16
2026-02-03T06:57:00,145,Kniebeugen,1,6,16
2026-02-03T06:58:00,140,,,
2026-02-03T06:59:00,135,,,
2026-02-03T07:00:00,150,Bankdrücken,1,6,18
2026-02-03T07:01:00,155,Bankdrücken,1,6,18
2026-02-03T07:02:00,145,,,
2026-02-03T07:03:00,140,Dehnen,1,1,
...
2026-02-03T07:10:00,160,EGYM Bauchtrainer,2,12,33
2026-02-03T07:12:00,155,EGYM Ruderzug,2,12,41
...
2026-02-03T07:18:00,110,,,
```

### Key Patterns

**Exercise Blocks:**
- HR spikes during sets (130-165 bpm)
- Rest between sets (HR drops to 120-140)
- Exercise type sometimes populated, sometimes empty

**EGYM Exercises:**
- Automatically tracked by machine
- Sets, reps, weight populated
- Higher accuracy

**Manual Exercises (Kurzhanteln):**
- Sometimes incomplete data
- User must log sets/reps manually
- Weight often missing

### Parsing Strategy

**For Strength Training:**
1. Identify exercise blocks by HR patterns
2. Group by exercise type (if available)
3. Count sets/reps from HR spikes
4. Extract weight if logged
5. Calculate total duration
6. Average HR per exercise

---

## 📋 Metadata Fields (Both Types)

### Session Metadata
```python
{
    "activity_type": "running" | "strength",
    "date": "2026-02-04",
    "start_time": "06:30:00",
    "end_time": "07:07:00",
    "total_duration_seconds": 2220,
    "device": "Apple Watch",
    "export_format": "csv"
}
```

### GPS Metadata (Running only)
```python
{
    "has_gps": True,
    "start_location": {
        "latitude": 51.4818,
        "longitude": 7.2162,
        "city": "Bochum, Germany"
    },
    "elevation_gain_m": 15.5,
    "elevation_loss_m": 12.3
}
```

---

## 🔍 Data Quality Indicators

### Good Quality Signs
- ✅ Consistent sampling rate (every 5-10 seconds)
- ✅ No large gaps in timestamps
- ✅ HR values in plausible range (60-200 bpm)
- ✅ GPS coordinates stable (not jumping around)
- ✅ Speed/pace align with distance/time

### Poor Quality Signs
- ❌ Large timestamp gaps (>30 seconds)
- ❌ HR = 0 or null for extended periods
- ❌ GPS coordinates jumping >100m between readings
- ❌ Speed/distance mismatches
- ❌ Elevation jumps >10m suddenly

### How to Handle Poor Quality
1. **Missing HR:** Interpolate if gap <30s, otherwise mark as null
2. **GPS Jumps:** Use median filtering, discard outliers
3. **Timestamp Gaps:** Note as "paused" lap if >1min
4. **Implausible Values:** HR >220 or <40 → likely error, mark as null

---

## 🧮 Common Calculations

### Average Pace (for lap or session)
```python
total_distance_m = lap_data['distance'].iloc[-1] - lap_data['distance'].iloc[0]
total_time_s = (lap_data['timestamp'].iloc[-1] - lap_data['timestamp'].iloc[0]).total_seconds()
avg_speed_m_s = total_distance_m / total_time_s
avg_pace_min_per_km = 1000 / (avg_speed_m_s * 60) if avg_speed_m_s > 0 else None
```

### HR Zones Distribution
```python
def calculate_hr_zones(hr_data):
    total_seconds = len(hr_data)
    zone_1 = len(hr_data[hr_data < 150]) / total_seconds * 100
    zone_2 = len(hr_data[(hr_data >= 150) & (hr_data < 160)]) / total_seconds * 100
    zone_3 = len(hr_data[hr_data >= 160]) / total_seconds * 100
    return {
        "zone_1_recovery": zone_1,
        "zone_2_base": zone_2,
        "zone_3_tempo": zone_3
    }
```

### Elevation Gain/Loss
```python
def calculate_elevation(elevation_data):
    elevation_diff = elevation_data.diff()
    gain = elevation_diff[elevation_diff > 0].sum()
    loss = abs(elevation_diff[elevation_diff < 0].sum())
    return gain, loss
```

### Grade Adjusted Pace (GAP)
```python
def calculate_gap(pace_min_per_km, gradient_percent):
    # Simplified: +10 sec/km per 1% uphill, -5 sec/km per 1% downhill
    if gradient_percent > 0:
        adjustment = gradient_percent * 10
    else:
        adjustment = gradient_percent * 5
    gap = pace_min_per_km - adjustment
    return gap
```

---

## 🎯 Training Type Detection Heuristics

### Based on CSV Analysis

**Interval Training:**
- Multiple distinct HR spikes (>5)
- Regular pattern in speed changes
- Clear rest periods between efforts
- Duration: 30-60 min typically

**Tempo Run:**
- Sustained elevated HR (>150 bpm for >20 min)
- Consistent pace
- Few/no rest periods
- Duration: 40-60 min

**Long Run:**
- Duration >60 min
- Moderate HR (140-160 bpm)
- Steady pace
- Minimal HR variation

**Recovery Run:**
- Low HR (<150 bpm throughout)
- Easy pace
- Duration: 30-50 min
- Very consistent metrics

**Strength Training:**
- No GPS data
- Irregular HR pattern (spikes + drops)
- Shorter duration (20-40 min)
- Often has exercise type fields

---

## 📝 Example Filenames
```
Apple-Watch-Export-2026-02-04-Running-Intervals.csv
Apple-Watch-Export-2026-02-05-Running-Recovery.csv
Apple-Watch-Export-2026-07-Running-Longrun.csv
Apple-Watch-Export-2026-02-03-Strength-Upper.csv
Apple-Watch-Export-2026-02-06-Strength-Lower.csv
```

### Naming Convention
- Source: `Apple-Watch-Export`
- Date: `YYYY-MM-DD`
- Type: `Running` | `Strength`
- Subtype: `Intervals` | `Tempo` | `Longrun` | `Recovery` | `Upper` | `Lower`
- Extension: `.csv`

---

## 🔧 Parsing Best Practices

1. **Always validate:**
   - Check for required columns
   - Verify data types (timestamps, numbers)
   - Handle missing values gracefully

2. **Lap detection:**
   - Use both HR and pace changes
   - Consider time gaps (>1min = likely pause)
   - Confidence levels based on data quality

3. **HR Zone calculation:**
   - Use time-based (seconds), not distance-based
   - Handle nulls/zeros properly
   - Separate total vs working laps

4. **GPS processing:**
   - Smooth GPS noise (median filter)
   - Calculate elevation carefully
   - Handle indoor activities (no GPS)

5. **Error handling:**
   - Log warnings for suspicious data
   - Provide fallbacks for missing fields
   - Never crash on bad data

---

**Dieses Dokument dient als Referenz für CSV-Parsing-Logik!**
