# 🏃‍♂️ FIT Import - Discussion Notes & Implementation Plan

**Status:** 💭 Discussed, NOT yet started  
**Last Updated:** 2026-02-12  
**Context:** These are notes from discussions about FIT file support

---

## 🎯 Why FIT Files?

### Advantages over CSV:
- ✅ **Structured Workout Data** - Explicit workout steps (warmup, intervals, recovery)
- ✅ **Running Dynamics** - NOT available in CSV exports!
  - Cadence (steps per minute)
  - Ground Contact Time (milliseconds)
  - Vertical Oscillation (centimeters)
  - Vertical Ratio (efficiency %)
  - Power (if available)
- ✅ **Better Lap Classification** - Can use workout structure instead of heuristics
- ✅ **More Accurate** - Direct from watch, no export conversion

### What we lose with CSV-only:
- ❌ No running dynamics
- ❌ No power data
- ❌ Less structured workout info
- ❌ More guessing for lap classification

---

## 🔧 Technical Approach

### Library: fitparse
```python
# Python library for parsing FIT files
pip install fitparse

# Basic usage
from fitparse import FitFile

fitfile = FitFile('activity.fit')
for record in fitfile.get_messages('record'):
    for data in record:
        print(f"{data.name}: {data.value}")
```

**Documentation:** https://github.com/dtcooper/python-fitparse

### FIT File Structure

```
FIT File
├── File Header
├── Messages
│   ├── file_id (metadata)
│   ├── sport (activity type)
│   ├── session (summary)
│   ├── lap (1..N)
│   │   ├── timestamp
│   │   ├── total_elapsed_time
│   │   ├── total_distance
│   │   ├── avg_heart_rate
│   │   ├── avg_cadence
│   │   ├── avg_vertical_oscillation
│   │   └── ...
│   ├── record (GPS points, 1..N per second)
│   │   ├── timestamp
│   │   ├── heart_rate
│   │   ├── cadence
│   │   ├── position_lat
│   │   ├── position_long
│   │   ├── distance
│   │   ├── speed
│   │   └── ...
│   └── workout_step (structured workout) ⭐
│       ├── message_index
│       ├── workout_step_name ("Warm Up", "Work", "Rest")
│       ├── duration_type (time, distance, etc.)
│       ├── duration_value
│       ├── target_type (speed, heart_rate, etc.)
│       └── target_value
└── CRC
```

### Key Messages for Us:

**session:**
- Total distance, duration, calories
- Average HR, pace, cadence
- Sport type

**lap:**
- Per-lap metrics
- avg_heart_rate, avg_cadence
- avg_vertical_oscillation, avg_ground_contact_time
- avg_vertical_ratio
- avg_power (if available)

**record:**
- Second-by-second data
- heart_rate, cadence, speed
- position_lat, position_long
- vertical_oscillation, ground_contact_time

**workout_step:** ⭐
- Structured workout definition
- Step names ("Warm Up", "Work", "Rest", "Cool Down")
- Can map directly to LapType!

---

## 🎨 Data Model Extensions

### Running Dynamics (Only FIT!)

```python
# In TrainingLap
class TrainingLap:
    # ... existing fields ...
    
    # Running Dynamics (FIT only, all optional)
    avg_cadence: Optional[int] = None  # steps per minute
    avg_ground_contact_time: Optional[int] = None  # milliseconds
    avg_vertical_oscillation: Optional[float] = None  # centimeters
    avg_vertical_ratio: Optional[float] = None  # percentage
    
    # Power (FIT only, if available)
    avg_power: Optional[int] = None  # watts
    max_power: Optional[int] = None
    normalized_power: Optional[int] = None
```

### Workout Structure (FIT only!)

```python
class WorkoutStep:
    """Structured workout step from FIT file"""
    step_index: int
    step_name: str  # e.g., "Warm Up", "Work", "Rest"
    duration_type: str  # time, distance, lap_button
    duration_value: float
    target_type: Optional[str]  # speed, heart_rate, cadence
    target_value: Optional[float]
    
    # Map to LapType
    def to_lap_type(self) -> LapType:
        name_lower = self.step_name.lower()
        if 'warm' in name_lower:
            return LapType.WARMUP
        elif 'cool' in name_lower:
            return LapType.COOLDOWN
        elif 'rest' in name_lower or 'recovery' in name_lower:
            return LapType.RECOVERY
        elif 'work' in name_lower or 'interval' in name_lower:
            return LapType.INTERVAL
        else:
            return LapType.STEADY
```

---

## 🚀 Implementation Plan

### Phase 1: Basic FIT Parsing
```python
# backend/app/services/fit_parser.py

from fitparse import FitFile
from typing import Dict, List

class FITParser:
    def parse_fit_file(self, file_path: Path) -> Dict:
        """Parse FIT file and extract session data"""
        fitfile = FitFile(str(file_path))
        
        # Extract session summary
        session_data = self._extract_session(fitfile)
        
        # Extract laps with running dynamics
        laps = self._extract_laps(fitfile)
        
        # Extract GPS records (optional)
        records = self._extract_records(fitfile)
        
        return {
            'session': session_data,
            'laps': laps,
            'records': records
        }
    
    def _extract_session(self, fitfile: FitFile) -> Dict:
        """Extract session-level metrics"""
        for record in fitfile.get_messages('session'):
            return {
                'sport': record.get_value('sport'),
                'total_distance': record.get_value('total_distance'),
                'total_elapsed_time': record.get_value('total_elapsed_time'),
                'avg_heart_rate': record.get_value('avg_heart_rate'),
                'avg_cadence': record.get_value('avg_cadence'),
                # ... more fields
            }
    
    def _extract_laps(self, fitfile: FitFile) -> List[Dict]:
        """Extract lap data with running dynamics"""
        laps = []
        for record in fitfile.get_messages('lap'):
            lap = {
                'timestamp': record.get_value('timestamp'),
                'total_elapsed_time': record.get_value('total_elapsed_time'),
                'total_distance': record.get_value('total_distance'),
                'avg_heart_rate': record.get_value('avg_heart_rate'),
                'avg_speed': record.get_value('avg_speed'),
                
                # Running Dynamics ⭐
                'avg_cadence': record.get_value('avg_cadence'),
                'avg_ground_contact_time': record.get_value('avg_stance_time'),
                'avg_vertical_oscillation': record.get_value('avg_vertical_oscillation'),
                'avg_vertical_ratio': record.get_value('avg_stance_time_percent'),
                
                # Power (if available)
                'avg_power': record.get_value('avg_power'),
            }
            laps.append(lap)
        return laps
    
    def _extract_records(self, fitfile: FitFile) -> List[Dict]:
        """Extract GPS/sensor records (second-by-second)"""
        records = []
        for record in fitfile.get_messages('record'):
            records.append({
                'timestamp': record.get_value('timestamp'),
                'heart_rate': record.get_value('heart_rate'),
                'cadence': record.get_value('cadence'),
                'speed': record.get_value('speed'),
                'distance': record.get_value('distance'),
                'position_lat': record.get_value('position_lat'),
                'position_long': record.get_value('position_long'),
                'altitude': record.get_value('altitude'),
            })
        return records
```

### Phase 2: Workout Structure Parsing ⭐

```python
def _extract_workout_steps(self, fitfile: FitFile) -> List[WorkoutStep]:
    """Extract structured workout from FIT"""
    steps = []
    for record in fitfile.get_messages('workout_step'):
        step = WorkoutStep(
            step_index=record.get_value('message_index'),
            step_name=record.get_value('wkt_step_name') or 'Unknown',
            duration_type=record.get_value('duration_type'),
            duration_value=record.get_value('duration_value'),
            target_type=record.get_value('target_type'),
            target_value=record.get_value('target_value'),
        )
        steps.append(step)
    return steps
```

### Phase 3: Automatic Lap Classification

```python
def classify_laps_from_workout(laps: List[Lap], workout_steps: List[WorkoutStep]):
    """
    Use FIT workout structure to classify laps automatically!
    Much better than HR-based heuristics!
    """
    for i, lap in enumerate(laps):
        if i < len(workout_steps):
            lap.lap_type = workout_steps[i].to_lap_type()
            lap.classification_confidence = 'high'  # From FIT structure!
        else:
            # Fallback to heuristics
            lap.lap_type = classify_by_hr(lap)
            lap.classification_confidence = 'medium'
```

---

## 📊 Expected Benefits

### Better Lap Classification
- **Current (CSV):** HR-based heuristics → 70-80% accuracy
- **With FIT Workout Steps:** Direct mapping → 95%+ accuracy ✅

### Running Dynamics Insights
```
Example Analysis:
"Dein Longrun heute:
 ✅ Pace: 6:52 min/km (gut!)
 ⚠️ HF: 167 bpm (zu hoch)
 📊 Kadenz: 76 spm (optimal 75-80) ✅
 📊 Bodenkontaktzeit: 245ms (etwas hoch, Ziel <240ms)
 📊 Vertikale Bewegung: 8.2cm (gut, <10cm)
 💡 Empfehlung: Kürzere Schritte für weniger Bodenkontakt!"
```

### Power-Based Training (Future)
- Training Stress Score (TSS) calculation
- Normalized Power (NP)
- Intensity Factor (IF)
- Better fatigue tracking

---

## 🚧 Implementation Challenges

### 1. File Format Complexity
- FIT is binary, more complex than CSV
- Different watches = different field names
- Not all fields always present

**Solution:** Defensive parsing, graceful degradation

### 2. Backward Compatibility
- Users might have old CSV files
- Need to support both CSV and FIT

**Solution:** Keep CSV parser, add FIT parser

### 3. Storage
- FIT files larger than CSV
- Need to decide: Store original or just parsed data?

**Solution:** Store parsed data in DB, keep original in S3/file storage (optional)

---

## 📅 Timeline (When to Implement)

### Current Priority: ⏳ NOT NOW!
**Why wait?**
- CSV parsing works well
- Database persistence more critical
- FIT is an enhancement, not MVP

### Suggested Timeline:
```
Week 1-3:   PostgreSQL + Session Persistence ⭐ (NOW)
Week 4-5:   AI Analysis Integration
Week 6-8:   Training Plan Management
Week 9-10:  FIT Import + Running Dynamics ⭐ (THEN)
```

**Rationale:**
1. Get data persisting first (DB)
2. Build core features (Plans, Analysis)
3. Then add enhanced data (FIT)

---

## 🧪 Testing Strategy

### Unit Tests
```python
def test_fit_parsing():
    parser = FITParser()
    data = parser.parse_fit_file('test_activity.fit')
    
    assert data['session']['sport'] == 'running'
    assert data['laps'][0]['avg_cadence'] is not None
    assert len(data['laps']) > 0

def test_running_dynamics_extraction():
    data = parse_fit('interval_workout.fit')
    
    lap = data['laps'][0]
    assert lap['avg_cadence'] > 70
    assert lap['avg_ground_contact_time'] > 0
    assert lap['avg_vertical_oscillation'] > 0
```

### Integration Tests
```python
@pytest.mark.integration
def test_fit_upload_endpoint():
    with open('test.fit', 'rb') as f:
        response = client.post('/api/v1/upload/fit', files={'file': f})
    
    assert response.status_code == 200
    data = response.json()
    assert 'running_dynamics' in data['laps'][0]
```

---

## 📚 Resources

### Libraries & Tools
- **fitparse:** https://github.com/dtcooper/python-fitparse
- **FIT SDK:** https://developer.garmin.com/fit/overview/
- **fitdump:** Command-line tool to inspect FIT files

### Documentation
- FIT File Format: https://developer.garmin.com/fit/protocol/
- Running Dynamics: https://www.garmin.com/en-US/running-dynamics/

### Example FIT Files
- Get from Apple Watch: "Share Activity" → Save to Files → .fit format
- Test files: https://github.com/dtcooper/python-fitparse/tree/master/tests/files

---

## ✅ Decision Points

### Before Implementation:
- [ ] Confirm fitparse works with Apple Watch FIT files
- [ ] Test parsing on real FIT export
- [ ] Verify running dynamics are present
- [ ] Check workout_step messages exist

### During Implementation:
- [ ] Support both CSV and FIT uploads
- [ ] Graceful degradation (missing fields)
- [ ] Clear UI indication (FIT = more data!)
- [ ] Document what's FIT-only vs CSV

### After Implementation:
- [ ] Migrate old CSV data? (or keep both)
- [ ] Update docs with FIT benefits
- [ ] Add FIT export option?

---

## 💡 Open Questions

1. **Do Apple Watch FIT exports contain workout_step messages?**
   - Need to test with real export!

2. **Which running dynamics are available on different watches?**
   - Apple Watch Series 6+? Series 9+?
   - Need to test across devices

3. **Storage strategy?**
   - Keep original FIT files?
   - Or just parsed data in DB?

4. **Dual upload or replace CSV?**
   - Support both?
   - Or migrate to FIT-only?

---

**Status:** Ready for implementation when we reach Week 9-10! 🚀

**Next Steps:**
1. ✅ Get 1-2 real FIT files from Apple Watch
2. ✅ Test fitparse parsing
3. ✅ Verify running dynamics present
4. ⏳ Implement when DB persistence done
