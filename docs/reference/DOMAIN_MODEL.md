# 🏃‍♂️ Training Analyzer - Domänenmodell

## 📋 Executive Summary

**Zukunftssicheres, sport-agnostisches Domänenmodell für Training Analyzer**

**Design-Philosophie:**
- 🎯 **Sport-agnostisch** - Läuft für Running, Cycling, Swimming, Triathlon, Strength
- 🔧 **Flexible Targets** - Neue Metriken ohne Schema-Änderungen
- 📊 **Trainingswissenschaftlich fundiert** - Periodisierung, Zonen, Load Management
- 🚀 **Erweiterbar** - Alle Felder optional, progressive Enhancement
- 🤖 **AI-Ready** - Strukturiert für Machine Learning & LLM-Analyse

**Kern-Entities (11):**
1. Athlete - Athletenprofil
2. Training Plan - Periodisierter Plan
3. Training Phase - Phasen mit Fokus
4. Planned Training - Soll-Vorgaben
5. Training Target - Flexible Zielvorgaben
6. Workout Structure - Detaillierte Workouts
7. Training Session - Ist-Daten (★ 200+ Felder!)
8. Training Lap - Lap-Klassifizierung
9. Training Evaluation - Soll/Ist + AI
10. HR Zone Config - Personalisierte Zonen
11. Activity Type - Sport-Definitionen

**Supporting Entities (4):**
12. Equipment - Schuhe, Bike, etc.
13. Health Event - Injuries, Illness
14. Sleep Session - Schlaf-Tracking
15. Training Goal - Messbare Ziele

**Training Session - Datenfelder-Kategorien:**
- ✅ **Basis** (Phase 1): duration, distance, pace, HR, laps
- ✅ **GPS & Elevation** (Phase 1): route, höhenprofil, GAP
- ✅ **Weather** (Phase 2): temp, wind, humidity, UV
- ✅ **Physiological** (Phase 2): HRV, SpO2, power, running dynamics
- ✅ **Recovery** (Phase 2): sleep, readiness, mood
- ✅ **Nutrition** (Phase 3): pre/during/post nutrition
- ✅ **Equipment** (Phase 2): shoes, bike tracking
- ✅ **Terrain** (Phase 3): surface, difficulty
- ✅ **Social** (Phase 6): Strava segments, kudos
- ✅ **Health** (Phase 2): injuries, medications
- ✅ **Calculated** (Phase 4): TRIMP, TSS, efficiency
- ✅ **AI Analysis** (Phase 5): insights, predictions, injury risk
- ✅ **Timeseries** (Phase 1+6): HR/pace/power curves

**Total Fields in TrainingSession:** ~200+ (alle optional!)

**Implementation:** 6 Phasen über 16+ Wochen, MVP in 3 Wochen

---

## 🎯 Design-Prinzipien

1. **Generisch & Erweiterbar**: Sport-agnostisch wo möglich
2. **Trainingswissenschaftlich fundiert**: Periodisierung, Belastung/Erholung, Progression
3. **Flexibel konfigurierbar**: Unterschiedliche Trainingsphilosophien unterstützen
4. **Datengetrieben**: Metriken, Zonen, Schwellenwerte konfigurierbar
5. **AI-Ready**: Strukturiert für LLM-Analyse und Feedback

---

## 📊 Core Domain Entities

### 1. **Athlete** (Athlet)
Der Trainierende - Zentrum des Domänenmodells.

```typescript
Athlete {
  id: UUID
  name: string
  birth_date: Date
  
  // Physiologische Basisdaten (optional, für Berechnungen)
  resting_hr?: number          // Ruhepuls
  max_hr?: number               // Maximalpuls
  lactate_threshold_hr?: number // Anaerobe Schwelle
  vo2_max?: number              // VO2max
  
  // Konfigurierbare HR-Zonen (überschreibt Standard)
  hr_zones?: HRZoneConfig[]
  
  // Präferenzen
  preferences: {
    distance_unit: 'km' | 'mi'
    pace_format: 'min_per_km' | 'min_per_mi'
    week_start: 'monday' | 'sunday'
  }
  
  created_at: DateTime
  updated_at: DateTime
}
```

**Rationale**: Zentrales Profil, ermöglicht personalisierte Zonen, Schwellenwerte und Analysen.

---

### 2. **Training Plan** (Trainingsplan)
Strukturierte Planung über einen Zeitraum mit Ziel.

```typescript
TrainingPlan {
  id: UUID
  athlete_id: UUID
  
  name: string
  description?: string
  goal: TrainingGoal           // z.B. "Sub-2h HM", "5k PR", "Kraft aufbauen"
  
  start_date: Date
  end_date: Date
  target_event_date?: Date     // Wettkampf/Zieldatum
  
  // Periodisierung
  phases: TrainingPhase[]      // Aufbau, Spezifisch, Tapering, etc.
  
  // Wochenstruktur (Template)
  weekly_structure?: {
    rest_days: DayOfWeek[]     // z.B. [monday, sunday]
    fixed_slots?: {
      day: DayOfWeek
      activity_type: string    // "strength", "quality_run", etc.
    }[]
  }
  
  status: 'draft' | 'active' | 'completed' | 'paused'
  
  created_at: DateTime
  updated_at: DateTime
}
```

**Rationale**: Ermöglicht Periodisierung (trainingswissenschaftlich essentiell), flexible Phasen-Definition.

---

### 3. **Training Phase** (Trainingsphase)
Abschnitt im Plan mit spezifischem Fokus.

```typescript
TrainingPhase {
  id: UUID
  training_plan_id: UUID
  
  name: string                 // "Phase 1 - Aufbau", "Tapering"
  phase_type: PhaseType        // 'base' | 'build' | 'peak' | 'taper' | 'transition'
  
  start_week: number           // Woche 1, 2, 3...
  end_week: number
  
  // Trainingswissenschaftliche Schwerpunkte
  focus: {
    primary: Focus[]           // ['endurance', 'speed', 'strength']
    secondary?: Focus[]
  }
  
  // Ziel-Metriken für diese Phase
  target_metrics?: {
    weekly_volume_min?: number     // Min. Wochenumfang (km oder min)
    weekly_volume_max?: number     // Max. Wochenumfang
    quality_sessions_per_week?: number
    avg_intensity_distribution?: { // % Zeit pro Zone
      zone_1?: number
      zone_2?: number
      zone_3?: number
    }
  }
  
  notes?: string
  
  created_at: DateTime
}
```

**Rationale**: Periodisierung ist fundamental im Training. Phasen haben unterschiedliche Ziele und Metriken.

---

### 4. **Planned Training** (Geplantes Training)
Ein einzelnes geplantes Training (Soll-Vorgabe).

```typescript
PlannedTraining {
  id: UUID
  training_plan_id: UUID
  phase_id?: UUID              // Optional: Zuordnung zu Phase
  
  // Zeitplanung
  scheduled_date: Date
  week_number: number          // Trainingswoche (relativ zu Plan)
  
  // Training-Definition
  activity_type: ActivityType  // 'running' | 'strength' | 'cycling' | 'swimming' | 'other'
  training_type: string        // Generisch: "longrun", "intervals", "tempo", "recovery"
  
  // Ziel-Vorgaben (flexibel)
  targets: TrainingTarget[]    // Liste von Zielvorgaben
  
  // Optional: Strukturierte Workout-Definition
  workout_structure?: WorkoutStructure
  
  notes?: string
  coach_notes?: string         // Hinweise vom Trainer/Plan
  
  // Status
  status: 'planned' | 'completed' | 'skipped' | 'moved'
  completed_training_id?: UUID // Link zum tatsächlichen Training
  
  created_at: DateTime
  updated_at: DateTime
}
```

**Rationale**: Flexibles Target-System erlaubt verschiedene Vorgaben (Pace, HR, Dauer, etc.) ohne Schema-Änderungen.

---

### 5. **Training Target** (Trainingsziel)
Einzelne Zielvorgabe für ein Training.

```typescript
TrainingTarget {
  id: UUID
  planned_training_id: UUID
  
  target_type: TargetType      // 'duration' | 'distance' | 'pace' | 'hr_zone' | 'power' | 'rpe'
  
  // Wert (abhängig von target_type)
  value_min?: number           // z.B. min. 60 min Dauer
  value_max?: number           // z.B. max. 75 min Dauer
  value_target?: number        // Exakter Zielwert
  
  unit?: string                // 'min', 'km', 'min/km', 'bpm', 'watts'
  
  // Kontextualisierung
  applies_to?: string          // 'total' | 'intervals' | 'main_set' | 'warmup' | 'cooldown'
  priority: number             // 1 = highest (für Soll/Ist-Vergleich)
  
  // Toleranzen
  tolerance_percentage?: number // ±10% z.B.
  
  notes?: string
  
  created_at: DateTime
}
```

**Beispiele:**
- Longrun: `{type: 'duration', value_min: 75, value_max: 80, unit: 'min', applies_to: 'total'}`
- Intervalle: `{type: 'pace', value_target: 6.31, unit: 'min/km', applies_to: 'intervals'}`
- Recovery: `{type: 'hr_zone', value_max: 150, unit: 'bpm', applies_to: 'total'}`

**Rationale**: Maximale Flexibilität. Neue Metriken (Power, RPE) einfach erweiterbar. Multi-Target pro Training möglich.

---

### 6. **Workout Structure** (Workout-Struktur)
Detaillierte Trainingsstruktur mit Intervallen (optional).

```typescript
WorkoutStructure {
  id: UUID
  planned_training_id: UUID
  
  // Phasen des Workouts
  segments: WorkoutSegment[]
  
  total_duration_target?: number  // Gesamt-Zieldauer
  
  created_at: DateTime
}

WorkoutSegment {
  id: UUID
  workout_structure_id: UUID
  
  order: number                // 1, 2, 3...
  segment_type: SegmentType    // 'warmup' | 'work' | 'rest' | 'cooldown' | 'drill'
  
  duration?: number            // in Minuten oder
  distance?: number            // in km
  repetitions?: number         // für Intervalle
  
  // Intensitätsvorgaben
  targets: {
    pace_min?: number
    pace_max?: number
    hr_min?: number
    hr_max?: number
    rpe?: number               // Rate of Perceived Exertion (1-10)
  }
  
  notes?: string
}
```

**Beispiel Intervalltraining:**
```
Segment 1: warmup, 10 min, HR <140
Segment 2: work, 3 min × 5, pace 6:31/km, HR >160
Segment 3: rest, 2 min × 5, active recovery
Segment 4: cooldown, 5 min, HR <130
```

**Rationale**: Ermöglicht präzise Workouts, aber optional (nicht alle Trainings brauchen diese Detailtiefe).

---

### 7. **Training Session** (Durchgeführtes Training)
Das tatsächlich durchgeführte Training (Ist-Daten).

```typescript
TrainingSession {
  id: UUID
  athlete_id: UUID
  planned_training_id?: UUID   // Link zum Plan (falls vorhanden)
  
  // ═══════════════════════════════════════════════════════
  // BASISDATEN (MVP - Phase 1)
  // ═══════════════════════════════════════════════════════
  session_date: Date
  activity_type: ActivityType
  training_type?: string       // User-definiert oder aus Plan
  
  // Erfassung
  data_source: 'manual' | 'csv_upload' | 'garmin' | 'strava' | 'apple_health'
  uploaded_file_id?: UUID      // Link zur Original-CSV/Datei
  external_id?: string         // ID in Quellsystem (Strava Activity ID, etc.)
  
  // Haupt-Metriken (aus Upload/Berechnung)
  duration_seconds: number
  distance_km?: number
  avg_pace?: number            // min/km
  avg_hr?: number
  max_hr?: number
  min_hr?: number
  avg_cadence?: number
  max_cadence?: number
  
  // Strukturierte Lap-Daten
  laps: TrainingLap[]
  
  // HF-Zonen Analyse
  hr_zones: HRZoneDistribution
  hr_zones_working?: HRZoneDistribution  // Ohne Warmup/Cooldown
  
  // ═══════════════════════════════════════════════════════
  // GPS & ELEVATION DATA (Phase 1 - haben wir schon in CSV!)
  // ═══════════════════════════════════════════════════════
  
  // GPS Route
  route_data?: {
    start_location?: {
      latitude: number
      longitude: number
      name?: string           // Geocoded: "Bochum, Germany"
    }
    end_location?: {
      latitude: number
      longitude: number
      name?: string
    }
    route_hash?: string       // Hash für Route-Recognition
    route_name?: string       // "Heimatrunde Bochum"
  }
  
  // Elevation Analysis
  elevation_profile?: {
    total_ascent_m: number    // Gesamte Höhenmeter bergauf
    total_descent_m: number   // Gesamte Höhenmeter bergab
    min_elevation_m: number
    max_elevation_m: number
    avg_gradient_percent?: number
    max_gradient_percent?: number
    elevation_gain_per_km?: number  // m/km average
    
    // Für Höhenprofil-Chart
    elevation_points?: {
      distance_km: number
      elevation_m: number
    }[]
  }
  
  // Grade Adjusted Pace (normalisiert für Steigung)
  gap?: {
    avg_gap: number           // Grade Adjusted Pace (min/km)
    equivalent_flat_distance_km: number
    effort_score: number      // Kombiniert Distanz + Elevation
  }
  
  // ═══════════════════════════════════════════════════════
  // WEATHER DATA (Phase 2 - External API)
  // ═══════════════════════════════════════════════════════
  weather?: {
    temperature_celsius: number
    feels_like_celsius: number
    humidity_percent: number
    wind_speed_kmh: number
    wind_direction_degrees?: number
    wind_gust_kmh?: number
    precipitation_mm?: number
    precipitation_type?: 'none' | 'rain' | 'snow' | 'sleet'
    cloud_cover_percent?: number
    uv_index?: number
    pressure_hpa?: number
    visibility_km?: number
    weather_condition: string  // "Clear", "Cloudy", "Rain", etc.
    weather_description?: string
    sunrise?: DateTime
    sunset?: DateTime
    
    // Metadata
    data_source: 'openweathermap' | 'weatherapi' | 'manual'
    fetched_at?: DateTime
  }
  
  // ═══════════════════════════════════════════════════════
  // PHYSIOLOGICAL DATA (Phase 2 - Wearable Integration)
  // ═══════════════════════════════════════════════════════
  
  // Heart Rate Variability
  hrv?: {
    rmssd: number             // Root Mean Square of Successive Differences (ms)
    sdnn?: number             // Standard Deviation of NN intervals
    stress_score?: number     // 1-100
    recovery_status?: 'excellent' | 'good' | 'fair' | 'poor'
  }
  
  // Respiratory
  avg_respiration_rate?: number    // Atemzüge/min
  
  // Blood Oxygen
  avg_spo2?: number           // Sauerstoffsättigung %
  min_spo2?: number
  
  // Body Temperature (newer watches)
  avg_body_temp_celsius?: number
  max_body_temp_celsius?: number
  
  // Power (Cycling, Running Power Meter)
  power_data?: {
    avg_power_watts: number
    max_power_watts: number
    normalized_power: number  // NP für variable Belastung
    intensity_factor?: number // IF = NP / FTP
    training_stress_score?: number  // TSS
    power_zones?: PowerZoneDistribution
  }
  
  // Stryd / Running Power specific
  running_power?: {
    avg_power_watts: number
    avg_form_power: number    // Vertical oscillation power
    avg_leg_spring_stiffness: number
    ground_contact_time_ms: number
    vertical_oscillation_cm: number
  }
  
  // ═══════════════════════════════════════════════════════
  // SLEEP & RECOVERY (Phase 2 - Pre-Session Data)
  // ═══════════════════════════════════════════════════════
  pre_session_state?: {
    // Schlaf letzte Nacht
    sleep_duration_hours?: number
    sleep_quality_score?: number  // 1-100
    deep_sleep_minutes?: number
    rem_sleep_minutes?: number
    sleep_disruptions?: number
    
    // Readiness / Body Battery
    readiness_score?: number      // 1-100 (Garmin, Whoop, Oura)
    body_battery?: number         // Garmin Body Battery
    recovery_score?: number       // Whoop Recovery
    
    // Morning Metrics
    resting_hr_morning?: number
    hrv_morning?: number
    weight_kg?: number
    hydration_status?: 'well_hydrated' | 'normal' | 'dehydrated'
    
    // Subjektiv
    mood?: 'excellent' | 'good' | 'neutral' | 'tired' | 'exhausted'
    stress_level?: number         // 1-10
    muscle_soreness?: number      // 1-10
    energy_level?: number         // 1-10
  }
  
  // ═══════════════════════════════════════════════════════
  // NUTRITION (Phase 3 - Optional)
  // ═══════════════════════════════════════════════════════
  nutrition?: {
    pre_training?: {
      timing_hours_before?: number
      carbs_grams?: number
      protein_grams?: number
      caffeine_mg?: number
      meal_description?: string
    }
    during_training?: {
      carbs_grams?: number        // Gels, Drinks
      fluids_ml?: number
      electrolytes_mg?: number
    }
    post_training?: {
      timing_hours_after?: number
      carbs_grams?: number
      protein_grams?: number
      meal_description?: string
    }
  }
  
  // ═══════════════════════════════════════════════════════
  // EQUIPMENT (Phase 2)
  // ═══════════════════════════════════════════════════════
  equipment_used?: {
    shoes?: {
      id: UUID                    // Link zu Equipment DB
      name: string                // "Nike Pegasus 40"
      total_km_before: number     // Km vor diesem Training
      total_km_after: number      // Km nach diesem Training
    }
    bike?: {
      id: UUID
      name: string
      total_km_before: number
    }
    // Weitere Ausrüstung
    heart_rate_monitor?: string
    power_meter?: string
    sports_watch?: string
  }
  
  // ═══════════════════════════════════════════════════════
  // TERRAIN & SURFACE (Phase 3 - ML/Manual)
  // ═══════════════════════════════════════════════════════
  terrain?: {
    primary_surface?: 'road' | 'trail' | 'track' | 'treadmill' | 'mixed'
    surface_distribution?: {
      road_percent?: number
      trail_percent?: number
      gravel_percent?: number
      grass_percent?: number
    }
    terrain_difficulty?: 'easy' | 'moderate' | 'technical' | 'very_technical'
  }
  
  // ═══════════════════════════════════════════════════════
  // STRAVA/SOCIAL (Phase 3)
  // ═══════════════════════════════════════════════════════
  social_data?: {
    strava_activity_id?: string
    kudos_count?: number
    comment_count?: number
    
    // Segments
    segments?: {
      segment_id: string
      segment_name: string
      elapsed_time_seconds: number
      pr_rank?: number           // Personal Record Ranking
      kom_rank?: number          // King/Queen of Mountain Ranking
    }[]
    
    // Group Activity
    group_run?: {
      participants: string[]
      group_name?: string
    }
  }
  
  // ═══════════════════════════════════════════════════════
  // HEALTH EVENTS (Phase 2)
  // ═══════════════════════════════════════════════════════
  health_notes?: {
    injuries?: {
      body_part: string          // "left knee", "right achilles"
      severity: 'minor' | 'moderate' | 'severe'
      pain_level: number         // 1-10
      description?: string
    }[]
    
    illness?: {
      type: 'cold' | 'flu' | 'stomach' | 'other'
      severity: 'mild' | 'moderate' | 'severe'
    }
    
    medications?: {
      name: string
      dosage?: string
      timing?: string            // "before", "during", "after"
    }[]
    
    menstrual_cycle_day?: number  // Für weibliche Athleten
  }
  
  // ═══════════════════════════════════════════════════════
  // ZEITREIHEN-DATEN (Phase 1 - für Charts)
  // ═══════════════════════════════════════════════════════
  timeseries_data?: {
    sampling_rate_seconds: number
    data_points: {
      timestamp_seconds: number  // Sekunden seit Start
      
      // Core Metrics
      hr?: number
      pace?: number              // min/km
      speed?: number             // km/h
      cadence?: number
      
      // GPS
      latitude?: number
      longitude?: number
      altitude_m?: number
      
      // Advanced
      power?: number
      vertical_oscillation?: number
      ground_contact_time?: number
      stride_length?: number
      
      // Environmental
      temperature?: number
      wind_speed?: number
    }[]
  }
  
  // ═══════════════════════════════════════════════════════
  // BERECHNETE METRIKEN (Phase 2-3)
  // ═══════════════════════════════════════════════════════
  calculated_metrics?: {
    // Training Load
    trimp?: number               // Training Impulse
    tss?: number                 // Training Stress Score
    hrTSS?: number               // HR-based TSS
    
    // Efficiency
    running_economy?: number     // ml O2/kg/km
    efficiency_factor?: number   // NP/Avg HR oder Pace/Avg HR
    decoupling?: number          // Cardiac Drift %
    
    // Fatigue
    fatigue_index?: number       // Performance drop over session
    variability_index?: number   // Pace consistency
  }
  
  // ═══════════════════════════════════════════════════════
  // SUBJEKTIVE BEWERTUNG (Phase 1)
  // ═══════════════════════════════════════════════════════
  perceived_exertion?: number    // RPE 1-10
  perceived_recovery?: number    // 1-10
  session_enjoyment?: number     // 1-10
  confidence_level?: number      // 1-10 (vor Wettkampf)
  notes?: string
  
  // ═══════════════════════════════════════════════════════
  // AI-ANALYSE (Phase 4)
  // ═══════════════════════════════════════════════════════
  ai_analysis?: {
    version: string              // AI Model Version
    generated_at: DateTime
    
    insights: string[]           // Positive Erkenntnisse
    warnings: string[]           // Warnungen (HF zu hoch, etc.)
    recommendations: string[]    // Nächste Schritte
    
    performance_prediction?: {
      race_distance_km: number
      predicted_time: string
      confidence: number         // 0-1
    }
    
    injury_risk_assessment?: {
      risk_level: 'low' | 'moderate' | 'high'
      risk_factors: string[]
      recommendations: string[]
    }
    
    optimal_recovery_time_hours?: number
  }
  
  // ═══════════════════════════════════════════════════════
  // METADATA
  // ═══════════════════════════════════════════════════════
  created_at: DateTime
  updated_at: DateTime
  
  // Data Provenance (wann wurden welche Daten hinzugefügt?)
  weather_fetched_at?: DateTime
  elevation_calculated_at?: DateTime
  ai_analyzed_at?: DateTime
  strava_synced_at?: DateTime
}
```

**Rationale**: Zentrale Speicherung aller Ist-Daten. Trennung von rohen Daten und berechneten Metriken.

---

### 8. **Training Lap** (Trainings-Lap)
Einzelner Lap/Abschnitt eines Trainings.

```typescript
TrainingLap {
  id: UUID
  training_session_id: UUID
  
  lap_number: number
  
  // Klassifizierung
  lap_type: LapType            // 'warmup' | 'interval' | 'recovery' | 'tempo' | 'cooldown' | 'work'
  classification_source: 'auto' | 'user_override'
  confidence?: 'high' | 'medium' | 'low'
  
  // Metriken
  duration_seconds: number
  distance_km?: number
  avg_pace?: number
  avg_hr?: number
  max_hr?: number
  min_hr?: number
  avg_cadence?: number
  
  // Lap-spezifische HF-Zonen
  hr_zone_distribution?: HRZoneDistribution
  
  created_at: DateTime
}
```

**Rationale**: Laps sind fundamental für Intervallanalyse. Klassifizierung essentiell für Arbeits-Laps HF-Zonen.

---

### 9. **Training Evaluation** (Soll/Ist-Vergleich)
Automatische oder manuelle Bewertung eines Trainings.

```typescript
TrainingEvaluation {
  id: UUID
  training_session_id: UUID
  planned_training_id: UUID
  
  // Gesamt-Bewertung
  overall_assessment: 'excellent' | 'good' | 'acceptable' | 'poor' | 'failed'
  
  // Target-Bewertungen
  target_achievements: TargetAchievement[]
  
  // Abweichungen
  deviations: {
    duration_deviation_percent?: number
    distance_deviation_percent?: number
    pace_deviation_percent?: number
    hr_deviation_percent?: number
  }
  
  // Warnungen/Flags
  warnings: Warning[]
  
  // AI-Kommentar
  ai_feedback?: string
  
  // Manuelle Coach/User-Bewertung
  coach_feedback?: string
  user_reflection?: string
  
  created_at: DateTime
  updated_at: DateTime
}

TargetAchievement {
  training_target_id: UUID
  achieved: boolean
  actual_value?: number
  target_value?: number
  deviation_percent?: number
  notes?: string
}

Warning {
  severity: 'info' | 'warning' | 'critical'
  category: 'intensity' | 'volume' | 'recovery' | 'progression'
  message: string
  recommendation?: string
}
```

**Beispiel Warnings:**
- `{severity: 'critical', category: 'intensity', message: 'Longrun HF 80% >160bpm (Soll: <160bpm)', recommendation: 'Nächster Longrun: Bewusst langsamer starten'}`

**Rationale**: Automatisierte Analyse ermöglicht schnelles Feedback. Strukturierte Warnings für AI-Lernen.

---

### 10. **HR Zone Config** (Herzfrequenz-Zonen Konfiguration)
Definiert Herzfrequenz-Zonen (global oder pro Athlet).

```typescript
HRZoneConfig {
  id: UUID
  athlete_id?: UUID            // null = globale Standard-Zonen
  
  name: string                 // "3-Zonen System", "5-Zonen System"
  
  zones: HRZone[]
  
  // Berechnungsmethode
  calculation_method?: 'manual' | 'percentage_max_hr' | 'percentage_lthr' | 'karvonen'
  
  active: boolean              // Aktuell verwendete Config
  
  created_at: DateTime
  updated_at: DateTime
}

HRZone {
  zone_number: number          // 1, 2, 3...
  name: string                 // "Recovery", "Base", "Tempo", "Threshold", "VO2max"
  
  // Absolut oder relativ
  hr_min?: number              // Absolut (bpm)
  hr_max?: number              // Absolut (bpm)
  
  percentage_min?: number      // Relativ (% von max_hr)
  percentage_max?: number      // Relativ (% von max_hr)
  
  description?: string         // "Lockeres Grundlagentraining"
  color?: string               // Für UI (#10b981)
}
```

**Beispiel 3-Zonen System:**
```json
{
  "name": "3-Zonen System",
  "zones": [
    {"zone_number": 1, "name": "Recovery", "hr_max": 150, "color": "#10b981"},
    {"zone_number": 2, "name": "Base", "hr_min": 150, "hr_max": 160, "color": "#f59e0b"},
    {"zone_number": 3, "name": "Tempo", "hr_min": 160, "color": "#ef4444"}
  ]
}
```

**Rationale**: Zonen sind individuell und methodenabhängig. Flexibles System unterstützt verschiedene Ansätze.

---

## 🔗 Supporting Entities

### 11. **Equipment** (Ausrüstung)
Tracking von Laufschuhen, Fahrrädern, etc.

```typescript
Equipment {
  id: UUID
  athlete_id: UUID
  
  equipment_type: 'shoes' | 'bike' | 'hr_monitor' | 'power_meter' | 'watch' | 'other'
  
  // Details
  brand: string                 // "Nike", "Garmin", etc.
  model: string                 // "Pegasus 40", "Edge 1040"
  name?: string                 // Custom Name "Meine Wettkampfschuhe"
  
  // Purchase Info
  purchase_date?: Date
  purchase_price?: number
  currency?: string
  
  // Usage Tracking
  total_distance_km: number     // Kumulativ
  total_duration_hours: number
  total_sessions: number
  
  // Lifecycle
  status: 'active' | 'retired' | 'backup'
  retired_date?: Date
  retired_reason?: string       // "Worn out", "Injury concerns"
  
  // Maintenance (bikes, etc.)
  last_maintenance_date?: Date
  maintenance_notes?: string
  
  // Alerts
  distance_alert_km?: number    // Warnung bei X km
  time_alert_hours?: number
  
  // Shoe-specific
  shoe_type?: 'training' | 'racing' | 'trail' | 'recovery'
  drop_mm?: number              // Heel-toe drop
  weight_grams?: number
  
  notes?: string
  
  created_at: DateTime
  updated_at: DateTime
}
```

**Use Cases:**
- ⚠️ "Laufschuhe haben 520 km - Zeit für neue Schuhe!"
- 📊 Performance-Vergleich: "In Racing-Schuhen 10 sec/km schneller"
- 🔧 "Fahrrad braucht Service (2000 km seit letzter Wartung)"

---

### 12. **Health Event** (Gesundheitsereignis)
Verletzungen, Krankheiten, wichtige Ereignisse.

```typescript
HealthEvent {
  id: UUID
  athlete_id: UUID
  
  event_type: 'injury' | 'illness' | 'surgery' | 'other'
  
  // Zeitraum
  start_date: Date
  end_date?: Date               // null = noch andauernd
  
  // Injury Details
  injury_details?: {
    body_part: string           // "left knee", "right achilles", "lower back"
    injury_type: string         // "strain", "sprain", "stress fracture", "tendinitis"
    severity: 'minor' | 'moderate' | 'severe'
    pain_level_initial: number  // 1-10
    pain_level_current?: number
    
    mechanism?: string          // "Overuse", "Acute trauma", "Unknown"
    suspected_cause?: string    // "Too much volume", "New shoes", "Trail fall"
  }
  
  // Illness Details  
  illness_details?: {
    illness_type: 'cold' | 'flu' | 'covid' | 'stomach' | 'allergy' | 'other'
    severity: 'mild' | 'moderate' | 'severe'
    symptoms: string[]
    fever?: boolean
  }
  
  // Treatment
  treatment?: {
    medical_professional?: string  // "Dr. Smith, Orthopedic"
    diagnosis?: string
    treatment_plan?: string
    medications: string[]
    physical_therapy?: boolean
    rest_prescribed_days?: number
  }
  
  // Impact on Training
  training_impact: 'none' | 'modified' | 'paused' | 'stopped'
  return_to_training_date?: Date
  return_to_training_protocol?: string
  
  // Recovery Tracking
  recovery_milestones?: {
    date: Date
    milestone: string           // "Pain-free walking", "First 5k run"
    pain_level: number
  }[]
  
  // Learnings
  lessons_learned?: string
  prevention_strategies?: string[]
  
  notes?: string
  
  created_at: DateTime
  updated_at: DateTime
}
```

**Use Cases:**
- 📊 Verletzungsmuster erkennen ("Immer rechte Wade nach Tempo-Einheiten")
- ⚠️ Return-to-Training Protokolle
- 📈 Präventionsstrategien entwickeln

---

### 13. **Sleep Session** (Schlaf-Session)
Detailliertes Schlaf-Tracking (von Wearables).

```typescript
SleepSession {
  id: UUID
  athlete_id: UUID
  
  sleep_date: Date              // Datum der Nacht (Start)
  
  // Timing
  bedtime: DateTime
  wake_time: DateTime
  total_time_in_bed_minutes: number
  total_sleep_time_minutes: number
  sleep_efficiency_percent: number  // (sleep time / time in bed) * 100
  
  // Sleep Stages
  awake_minutes: number
  light_sleep_minutes: number
  deep_sleep_minutes: number
  rem_sleep_minutes: number
  
  // Quality Metrics
  sleep_score: number           // 1-100 (Garmin, Oura, etc.)
  restfulness_score?: number
  sleep_disruptions: number     // Anzahl Aufwachphasen
  avg_hr_sleeping: number
  lowest_hr_sleeping: number
  hrv_during_sleep?: number
  
  // Respiratory
  avg_respiration_rate?: number
  spo2_avg?: number
  spo2_min?: number
  
  // Body Metrics
  body_temp_variation?: number  // Delta zur Baseline
  
  // Environmental (smart home integration?)
  room_temperature?: number
  room_humidity?: number
  
  // Subjective
  sleep_quality_self_rated?: number  // 1-10
  dream_recall?: boolean
  
  // Data Source
  data_source: 'garmin' | 'oura' | 'whoop' | 'apple_watch' | 'fitbit' | 'manual'
  
  notes?: string
  
  created_at: DateTime
  updated_at: DateTime
}
```

**Use Cases:**
- 📊 "Schlechter Schlaf → Training anpassen"
- 📈 "Deep Sleep <1h → Übertraining?"
- 🎯 "Nach Wettkampf: 9h Schlaf mit 2h Deep Sleep = gute Erholung"

---

### 14. **Training Goal** (Trainingsziel)
Spezifisches, messbares Ziel.

```typescript
TrainingGoal {
  id: UUID
  athlete_id: UUID
  
  goal_type: 'race' | 'performance' | 'health' | 'other'
  
  // Race-Goal
  event_name?: string          // "Hamburg Halbmarathon 2026"
  event_date?: Date
  distance?: number
  target_time?: string         // "1:59:59"
  
  // Performance-Goal
  metric?: string              // "5k_time", "vo2_max", "resting_hr"
  target_value?: number
  
  // Zeitraum
  start_date: Date
  deadline?: Date
  
  status: 'active' | 'achieved' | 'failed' | 'abandoned'
  
  created_at: DateTime
  updated_at: DateTime
}
```

---

### 12. **Activity Type** (Aktivitätstyp)
Erweiterbare Aktivitätstypen.

```typescript
ActivityType {
  id: UUID
  
  name: string                 // "Running", "Cycling", "Swimming", "Strength"
  code: string                 // "running", "cycling" (eindeutig)
  category: string             // "endurance", "strength", "flexibility"
  
  // Verfügbare Metriken
  supported_metrics: string[]  // ['pace', 'hr', 'cadence', 'power']
  
  // Default-Zonen (falls keine athlete-spezifischen)
  default_hr_zones?: UUID
  default_power_zones?: UUID
  
  active: boolean
  
  created_at: DateTime
}
```

**Rationale**: Sport-agnostisch. Neue Sportarten einfach hinzufügbar.

---

## 📊 Value Objects & Enums

```typescript
// ═══════════════════════════════════════════════════════
// BASIS-TYPEN
// ═══════════════════════════════════════════════════════
type DayOfWeek = 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday' | 'saturday' | 'sunday'

type PhaseType = 'base' | 'build' | 'peak' | 'taper' | 'transition' | 'recovery' | 'custom'

type Focus = 'endurance' | 'speed' | 'strength' | 'power' | 'technique' | 'recovery' | 'mobility'

type TargetType = 
  | 'duration' 
  | 'distance' 
  | 'pace' 
  | 'hr_zone' 
  | 'hr_avg' 
  | 'power' 
  | 'power_zone'
  | 'cadence' 
  | 'rpe' 
  | 'elevation_gain'
  | 'gap'  // Grade Adjusted Pace

type LapType = 
  | 'warmup' 
  | 'interval' 
  | 'recovery'  // Active recovery / Trab
  | 'tempo' 
  | 'cooldown' 
  | 'work' 
  | 'drill' 
  | 'unclassified'

type SegmentType = 'warmup' | 'work' | 'rest' | 'cooldown' | 'drill' | 'transition'

type DataSource = 
  | 'manual' 
  | 'csv_upload' 
  | 'garmin' 
  | 'strava' 
  | 'apple_health' 
  | 'apple_watch'
  | 'polar'
  | 'suunto'
  | 'coros'
  | 'whoop'
  | 'oura'
  | 'fitbit'

// ═══════════════════════════════════════════════════════
// HF-ZONEN DISTRIBUTION
// ═══════════════════════════════════════════════════════
interface HRZoneDistribution {
  zone_1?: {
    seconds: number
    percentage: number
    label: string
    hr_range?: string        // "< 150 bpm" oder "120-140 bpm"
  }
  zone_2?: { /* ... */ }
  zone_3?: { /* ... */ }
  zone_4?: { /* ... */ }
  zone_5?: { /* ... */ }
  // Erweiterbar für mehr Zonen-Systeme
}

// ═══════════════════════════════════════════════════════
// POWER-ZONEN DISTRIBUTION (für Radfahrer)
// ═══════════════════════════════════════════════════════
interface PowerZoneDistribution {
  zone_1_active_recovery?: {
    seconds: number
    percentage: number
    label: string
    power_range: string      // "< 150W"
  }
  zone_2_endurance?: { /* ... */ }
  zone_3_tempo?: { /* ... */ }
  zone_4_lactate_threshold?: { /* ... */ }
  zone_5_vo2max?: { /* ... */ }
  zone_6_anaerobic?: { /* ... */ }
  zone_7_neuromuscular?: { /* ... */ }
}

// ═══════════════════════════════════════════════════════
// WETTER-BEDINGUNGEN
// ═══════════════════════════════════════════════════════
type WeatherCondition = 
  | 'clear' 
  | 'partly_cloudy' 
  | 'cloudy' 
  | 'overcast'
  | 'mist' 
  | 'fog'
  | 'light_rain' 
  | 'rain' 
  | 'heavy_rain'
  | 'drizzle'
  | 'thunderstorm'
  | 'snow' 
  | 'light_snow'
  | 'sleet'
  | 'hail'

type PrecipitationType = 'none' | 'rain' | 'snow' | 'sleet' | 'hail'

// ═══════════════════════════════════════════════════════
// TERRAIN & OBERFLÄCHE
// ═══════════════════════════════════════════════════════
type SurfaceType = 
  | 'road'          // Asphalt
  | 'trail'         // Wald-/Bergpfade
  | 'track'         // Tartanbahn
  | 'treadmill'     // Laufband
  | 'gravel'        // Schotter
  | 'grass'         // Rasen
  | 'sand'          // Sand (Strand)
  | 'mixed'         // Gemischt

type TerrainDifficulty = 'easy' | 'moderate' | 'technical' | 'very_technical'

// ═══════════════════════════════════════════════════════
// EQUIPMENT TYPEN
// ═══════════════════════════════════════════════════════
type EquipmentType = 
  | 'shoes' 
  | 'bike' 
  | 'hr_monitor' 
  | 'power_meter' 
  | 'watch'
  | 'cycling_computer'
  | 'headphones'
  | 'clothing'
  | 'other'

type ShoeType = 'training' | 'racing' | 'trail' | 'recovery' | 'speed_work'

// ═══════════════════════════════════════════════════════
// GESUNDHEIT
// ═══════════════════════════════════════════════════════
type HealthEventType = 'injury' | 'illness' | 'surgery' | 'vaccination' | 'medical_checkup' | 'other'

type InjuryType = 
  | 'strain'           // Zerrung
  | 'sprain'           // Verstauchung
  | 'stress_fracture'  // Ermüdungsbruch
  | 'fracture'         // Bruch
  | 'tendinitis'       // Sehnenentzündung
  | 'bursitis'         // Schleimbeutelentzündung
  | 'fasciitis'        // Faszienent zündung
  | 'muscle_tear'      // Muskelfaserriss
  | 'ligament_tear'    // Bänderriss
  | 'cartilage_damage' // Knorpelschaden
  | 'other'

type BodyPart = 
  | 'left_foot' | 'right_foot'
  | 'left_ankle' | 'right_ankle'
  | 'left_shin' | 'right_shin'
  | 'left_calf' | 'right_calf'
  | 'left_knee' | 'right_knee'
  | 'left_hamstring' | 'right_hamstring'
  | 'left_quad' | 'right_quad'
  | 'left_hip' | 'right_hip'
  | 'left_glute' | 'right_glute'
  | 'lower_back'
  | 'mid_back'
  | 'upper_back'
  | 'neck'
  | 'left_shoulder' | 'right_shoulder'
  | 'left_elbow' | 'right_elbow'
  | 'left_wrist' | 'right_wrist'
  | 'chest'
  | 'abdomen'
  | 'other'

type IllnessType = 
  | 'cold' 
  | 'flu' 
  | 'covid' 
  | 'stomach_bug'
  | 'food_poisoning'
  | 'allergy' 
  | 'asthma'
  | 'bronchitis'
  | 'sinus_infection'
  | 'migraine'
  | 'other'

type Severity = 'minor' | 'moderate' | 'severe'

type TrainingImpact = 'none' | 'modified' | 'paused' | 'stopped'

// ═══════════════════════════════════════════════════════
// SUBJEKTIVE BEWERTUNGEN
// ═══════════════════════════════════════════════════════
type Mood = 'excellent' | 'good' | 'neutral' | 'tired' | 'exhausted' | 'irritable'

type RecoveryStatus = 'excellent' | 'good' | 'fair' | 'poor' | 'very_poor'

type HydrationStatus = 'well_hydrated' | 'normal' | 'dehydrated' | 'very_dehydrated'

// ═══════════════════════════════════════════════════════
// AI & MACHINE LEARNING
// ═══════════════════════════════════════════════════════
type RiskLevel = 'low' | 'moderate' | 'high' | 'very_high'

type PerformanceAssessment = 'excellent' | 'good' | 'acceptable' | 'poor' | 'failed'

type WarningSeverity = 'info' | 'warning' | 'critical'

type WarningCategory = 
  | 'intensity'        // HF/Pace zu hoch
  | 'volume'           // Zu viel Umfang
  | 'recovery'         // Zu wenig Erholung
  | 'progression'      // Zu schnelle Steigerung
  | 'injury_risk'      // Verletzungsrisiko
  | 'health'           // Gesundheitliche Bedenken
  | 'equipment'        // Schuhe abgenutzt, etc.
  | 'weather'          // Extreme Bedingungen
  | 'nutrition'        // Ernährungsprobleme
  | 'sleep'            // Schlafmangel

// ═══════════════════════════════════════════════════════
// ZEITREIHEN-DATEN
// ═══════════════════════════════════════════════════════
interface DataPoint {
  timestamp_seconds: number    // Sekunden seit Start
  
  // Core Metrics
  hr?: number
  pace?: number                // min/km
  speed?: number               // km/h
  cadence?: number
  
  // GPS
  latitude?: number
  longitude?: number
  altitude_m?: number
  
  // Advanced Metrics
  power?: number
  vertical_oscillation_cm?: number
  ground_contact_time_ms?: number
  stride_length_m?: number
  left_right_balance?: number  // % links
  
  // Running Dynamics
  form_power?: number
  leg_spring_stiffness?: number
  
  // Environmental
  temperature_celsius?: number
  wind_speed_kmh?: number
  
  // Cycling-specific
  torque?: number
  pedal_smoothness?: number
  
  // Swimming-specific (future)
  stroke_rate?: number
  swolf_score?: number
}

interface TimeseriesData {
  sampling_rate_seconds: number
  data_points: DataPoint[]
  total_points: number
  data_quality_percent?: number  // % non-null values
}
```

---

## 🔄 Domain Services

### TrainingPlanService
- `createPlan(athlete, goal, duration)`
- `generateWeeklySchedule(plan)`
- `adjustPlanForProgress(plan, evaluations)`

### EvaluationService
- `evaluateSession(session, plannedTraining)`
- `detectWarnings(session, history)`
- `calculateProgression(sessions, timeframe)`

### ZoneCalculationService
- `calculateZones(athlete, method)`
- `classifyIntensity(hr, zones)`
- `getZoneDistribution(session, zones)`

### AIAnalysisService
- `analyzeSession(session, context)`
- `generateFeedback(evaluation)`
- `suggestAdjustments(plan, history)`

---

## 🎯 Trainingswissenschaftliche Prinzipien

### 1. **Periodisierung**
- Phasen mit unterschiedlichen Schwerpunkten
- Progressiver Belastungsaufbau
- Tapering vor Wettkämpfen

### 2. **Belastung & Erholung**
- Acute:Chronic Workload Ratio
- Erholungstage tracking
- Übertrainings-Warnung

### 3. **Spezifität**
- Wettkampf-spezifisches Training in Peak-Phase
- Unterschiedliche Intensitätszonen trainieren verschiedene Systeme

### 4. **Progression**
- Graduelle Steigerung (10%-Regel)
- Load-Management
- Adaptive Planung

### 5. **Individualität**
- Personalisierte Zonen
- Subjektive Bewertung (RPE)
- Anpassung an Tagesform

---

## 🔮 Erweiterbarkeit

### Einfach erweiterbar:
✅ Neue Sportarten (ActivityType)
✅ Neue Metriken (TargetType, DataPoint fields)
✅ Neue Zonen-Systeme (HRZoneConfig)
✅ Neue Bewertungskriterien (Warning categories)
✅ Integration externe Quellen (data_source)

### Geplante Features:
🔜 Power-Zonen (analog zu HR-Zonen)
🔜 Nutrition tracking
🔜 Sleep & Recovery tracking
🔜 Injury/Illness logging
🔜 Equipment tracking (Laufschuhe km)
🔜 Multi-Sport (Triathlon)

---

## 🚀 Implementation Roadmap

### 🟢 Phase 1: MVP - Core Foundation (Wochen 1-3)
**Ziel:** Basis-System funktional mit CSV Upload, Storage, einfacher Analyse

**Entities:**
- ✅ `Athlete` (minimal: id, name, preferences)
- ✅ `TrainingSession` (core fields only)
  - Basis-Metriken: duration, distance, avg_pace, avg_hr, max_hr
  - Laps: lap_number, duration, distance, avg_pace, avg_hr
  - HF-Zonen: hr_zones, hr_zones_working
  - Notes, RPE
- ✅ `TrainingLap` (mit Klassifizierung)
- ✅ `HRZoneConfig` (global default + athlete-specific)

**Features:**
- CSV Upload (Running + Strength)
- Lap Auto-Classification
- HF-Zonen Berechnung (Gesamt + Arbeits-Laps)
- Basic UI: Upload, Session View, Lap Table
- PostgreSQL Schema + Migrations

**Deliverable:** 
Training Analyzer funktioniert wie jetzt, aber mit Datenbank-Persistenz!

---

### 🟡 Phase 2: Analysis & Insights (Wochen 4-6)
**Ziel:** Intelligente Analyse, Soll/Ist-Vergleich, erweiterte Metriken

**Entities:**
- ✅ `TrainingPlan` (basic: name, goal, date range, phases)
- ✅ `TrainingPhase` (name, type, week range, focus)
- ✅ `PlannedTraining` (simple: date, type, targets)
- ✅ `TrainingTarget` (flexible target system)
- ✅ `TrainingEvaluation` (Soll/Ist-Vergleich)
- ✅ `Equipment` (Schuhe-Tracking)

**Erweiterte Session-Daten:**
- ✅ Elevation Profile (aus GPS-Daten berechnen)
- ✅ GAP (Grade Adjusted Pace)
- ✅ Route Data (Start/End Location, Route Hash)
- ✅ Equipment Used (Link zu Schuhen)

**Features:**
- Trainingsplan-Editor (UI)
- Geplante Trainings definieren mit Targets
- Automatischer Soll/Ist-Vergleich
- Warnings & Recommendations
- Equipment-Warnung ("Schuhe >500km")
- Elevation Profile Chart
- Route Recognition

**Deliverable:**
"Longrun sollte <160 bpm sein, war 167 bpm - zu intensiv!" ⚠️

---

### 🟠 Phase 3: Environmental & Health (Wochen 7-9)
**Ziel:** Kontext-Daten, Gesundheits-Tracking, externe APIs

**Entities:**
- ✅ `HealthEvent` (Injuries, Illness)
- ✅ `SleepSession` (von Wearable oder manuell)

**Erweiterte Session-Daten:**
- ✅ Weather Data (via OpenWeatherMap API)
- ✅ Pre-Session State (Sleep, Readiness, Mood)
- ✅ Health Notes (Injuries, Medications)
- ✅ Terrain Classification

**Features:**
- OpenWeatherMap Integration (historische Wetterdaten)
- Injury/Illness Logging
- Sleep-Import (Garmin/Apple Health)
- Weather Impact Analysis ("HF +10 bpm bei 28°C normal")
- Return-to-Training Protokolle
- Verletzungsmuster-Erkennung

**Deliverable:**
"Bei 30°C Hitze war deine HF 12 bpm höher als normal - das ist OK!" ☀️

---

### 🔵 Phase 4: Advanced Analytics (Wochen 10-12)
**Ziel:** Berechnete Metriken, Training Load, Progression Tracking

**Erweiterte Session-Daten:**
- ✅ Calculated Metrics (TRIMP, TSS, Efficiency)
- ✅ Power Data (für Cycling)
- ✅ Running Power (Stryd)
- ✅ Advanced Physiological (HRV, SpO2, Respiration)

**Features:**
- Training Load Berechnung (TRIMP, hrTSS)
- Acute:Chronic Workload Ratio
- Fatigue/Fitness/Form (CTL/ATL/TSB)
- Running Economy Tracking
- Cardiac Drift Analysis
- Weekly/Monthly Analytics Dashboard
- Progression Graphs

**Deliverable:**
"Dein Acute:Chronic Ratio ist 1.5 - Verletzungsrisiko erhöht!" ⚠️

---

### 🟣 Phase 5: Intelligence & Automation (Wochen 13-16)
**Ziel:** AI-Analyse, Predictive Analytics, Adaptive Planning

**Entities:**
- ✅ `WorkoutStructure` (detaillierte Workout-Definition)

**Erweiterte Session-Daten:**
- ✅ AI Analysis (Insights, Warnings, Recommendations)
- ✅ Performance Predictions
- ✅ Injury Risk Assessment

**Features:**
- AI Session Analysis (Claude API)
- Performance Prediction ("Sub-2h in 6 Wochen: 75% Wahrscheinlichkeit")
- Injury Risk ML Model
- Adaptive Plan Adjustments
- Optimal Recovery Time Calculation
- Training Plan Generator (AI-assisted)
- Race Strategy Suggestions

**Deliverable:**
"Basierend auf deinem Training: Sub-2h machbar mit 80% Confidence!" 🎯

---

### 🔴 Phase 6: Integration & Social (Wochen 17+)
**Ziel:** External APIs, Multi-Sport, Advanced Features

**Erweiterte Session-Daten:**
- ✅ Nutrition Tracking
- ✅ Social Data (Strava Segments, Kudos)
- ✅ Full Timeseries Data (für detaillierte Charts)

**Features:**
- Garmin Connect Auto-Sync
- Strava Integration (Import, Segment Matching)
- Apple Health Sync (Sleep, HRV, Activity)
- Nutrition Logging
- Multi-Sport Support (Cycling, Swimming, Triathlon)
- Group Runs / Training Partners
- Public Training Log (optional)
- Mobile App (React Native)

**Deliverable:**
Vollständig integriertes Training-Ecosystem! 🌐

---

## 📋 Feature Priority Matrix

### Must Have (Phase 1-2)
🔴 **Critical:**
- CSV Upload & Storage
- Session Viewing
- Lap Classification
- HF-Zonen Analysis
- Training Plan Creation
- Soll/Ist-Vergleich
- Equipment Tracking (Schuhe)

### Should Have (Phase 3-4)
🟠 **High Value:**
- Weather Integration
- Elevation Analysis
- Health Event Logging
- Training Load Metrics
- Progression Tracking
- Sleep Tracking

### Could Have (Phase 5-6)
🟡 **Nice to Have:**
- AI Analysis
- Performance Predictions
- Strava Integration
- Nutrition Tracking
- Social Features
- Mobile App

### Won't Have (Yet)
⚪ **Future:**
- Live Coaching
- Video Analysis
- Biomechanics AI
- Virtual Races
- Marketplace

---

## 💾 Database Schema Considerations

### PostgreSQL Schema Design:
- **JSONB** für flexible Felder (targets, timeseries)
- **Partitioning** für TrainingSession (nach Datum)
- **Indexing** auf athlete_id, session_date, planned_training_id
- **Views** für häufige Aggregationen (weekly_summary)

### Example DDL:
```sql
CREATE TABLE athletes (...);
CREATE TABLE training_plans (...);
CREATE TABLE training_phases (...);
CREATE TABLE planned_trainings (...);
CREATE TABLE training_targets (...);
CREATE TABLE training_sessions (...) PARTITION BY RANGE (session_date);
CREATE TABLE training_laps (...);
CREATE TABLE training_evaluations (...);
CREATE TABLE hr_zone_configs (...);

-- Indexes
CREATE INDEX idx_sessions_athlete_date ON training_sessions(athlete_id, session_date DESC);
CREATE INDEX idx_laps_session ON training_laps(training_session_id);
CREATE INDEX idx_evaluations_session ON training_evaluations(training_session_id);
```

---

## ✅ Design Validation

✓ **Generisch**: Neue Sportarten/Metriken ohne Schema-Änderung
✓ **Flexibel**: Target-System erlaubt beliebige Vorgaben
✓ **Wissenschaftlich**: Periodisierung, Zonen, Progression eingebaut
✓ **Erweiterbar**: Klare Extension Points (ActivityType, TargetType, etc.)
✓ **AI-Ready**: Strukturierte Daten für LLM-Analyse
✓ **Praktisch**: Deckt deinen Use Case (HM-Training) vollständig ab
✓ **Zukunftssicher**: 200+ optionale Felder, progressive Implementation

---

## 🎯 Next Steps - Konkrete Umsetzung

### Step 1: Review & Feedback (JETZT) ✅
- [ ] Domänenmodell durchlesen
- [ ] Feedback geben
- [ ] Prioritäten klären
- [ ] Offene Fragen klären

### Step 2: Database Schema Design (1-2 Tage)
**Files zu erstellen:**
- `backend/app/models/athlete.py` - SQLAlchemy Model
- `backend/app/models/training_session.py` - Haupt-Entity
- `backend/app/models/training_lap.py`
- `backend/app/models/training_plan.py`
- `backend/app/models/hr_zone_config.py`
- `backend/alembic/versions/001_initial_schema.py` - Migration

**DDL erstellen für:**
```sql
CREATE TABLE athletes (...);
CREATE TABLE hr_zone_configs (...);
CREATE TABLE training_sessions (
  id UUID PRIMARY KEY,
  athlete_id UUID REFERENCES athletes(id),
  session_date DATE NOT NULL,
  
  -- Phase 1 Fields (NOT NULL)
  duration_seconds INTEGER NOT NULL,
  avg_hr INTEGER,
  
  -- Phase 2+ Fields (NULL allowed)
  weather_data JSONB,
  elevation_profile JSONB,
  route_data JSONB,
  equipment_used JSONB,
  
  -- Timeseries (später, großes JSONB)
  timeseries_data JSONB,
  
  -- Metadata
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
) PARTITION BY RANGE (session_date);

CREATE TABLE training_laps (...);
-- etc.
```

**Partitioning Strategy:**
- Training Sessions: Partition by year (2024, 2025, 2026, ...)
- Optimiert für Queries nach Datum

### Step 3: Pydantic Schemas (1 Tag)
**Files zu erstellen:**
- `backend/app/schemas/athlete.py`
- `backend/app/schemas/training_session.py`
- `backend/app/schemas/training_lap.py`
- `backend/app/schemas/hr_zone.py`

**Example:**
```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date

class TrainingSessionCreate(BaseModel):
    athlete_id: UUID
    session_date: date
    activity_type: str
    duration_seconds: int
    distance_km: Optional[float] = None
    avg_hr: Optional[int] = None
    # ... Phase 1 fields only
    
class TrainingSessionResponse(BaseModel):
    id: UUID
    # ... all fields including computed
    laps: List[TrainingLap]
    hr_zones: dict
    
    class Config:
        from_attributes = True
```

### Step 4: API Endpoints erweitern (2 Tage)
**Routes zu erstellen/erweitern:**

`backend/app/routers/sessions.py`:
```python
@router.post("/sessions", response_model=TrainingSessionResponse)
async def create_session(session: TrainingSessionCreate, db: Session):
    """Create new training session from uploaded data"""
    
@router.get("/sessions/{session_id}")
async def get_session(session_id: UUID, db: Session):
    """Get single session with all data"""
    
@router.get("/sessions")
async def list_sessions(
    athlete_id: UUID,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    activity_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
):
    """List sessions with filters"""
    
@router.put("/sessions/{session_id}/laps/{lap_id}/classification")
async def update_lap_classification(
    session_id: UUID,
    lap_id: UUID,
    lap_type: LapType
):
    """User override for lap classification"""
```

`backend/app/routers/plans.py`:
```python
@router.post("/plans")
async def create_plan(plan: TrainingPlanCreate, db: Session):
    """Create training plan"""
    
@router.get("/plans/{plan_id}")
async def get_plan(plan_id: UUID, db: Session):
    """Get plan with phases and planned trainings"""
```

### Step 5: CSV Parser Integration (1 Tag)
**Update `csv_parser.py`:**
```python
def parse(content: str, training_type: str, training_subtype: str) -> TrainingSessionCreate:
    """Parse CSV and return Pydantic model for DB insert"""
    # Existing parsing logic
    # Return TrainingSessionCreate instead of dict
    
    return TrainingSessionCreate(
        athlete_id=get_current_athlete_id(),  # From auth context
        session_date=date.fromisoformat(metadata['date']),
        duration_seconds=total_duration,
        # ... map all fields
        laps=[TrainingLapCreate(...) for lap in laps]
    )
```

### Step 6: Frontend Integration (2-3 Tage)
**Files zu ändern:**

`frontend/src/pages/Upload.tsx`:
```typescript
// Nach Upload & Parse:
const saveSession = async (parsedData: ParsedData) => {
  const response = await fetch('/api/sessions', {
    method: 'POST',
    body: JSON.stringify({
      ...parsedData,
      athlete_id: currentUser.id
    })
  });
  
  const session = await response.json();
  navigate(`/sessions/${session.id}`);
};
```

`frontend/src/pages/SessionDetail.tsx` (NEU):
```typescript
// Session Detail View
// - Metriken-Übersicht
// - HF-Zonen
// - Lap-Tabelle (editierbar)
// - Charts (HR, Pace, Elevation)
// - Edit Notes / RPE
```

`frontend/src/pages/Sessions.tsx` (NEU):
```typescript
// Session List/Calendar View
// - Filter: Date Range, Activity Type
// - Calendar oder List View
// - Quick Stats pro Session
```

### Step 7: Testing (2 Tage)
- Unit Tests für Models
- API Integration Tests
- Frontend E2E Tests (Playwright)
- CSV Upload Flow Test

### Step 8: Migration bestehender Daten (1 Tag)
- Falls schon Daten in Files → Import Script
- Test mit deinen echten CSV-Daten

### Step 9: Deployment (1 Tag)
- Docker Compose Update (PostgreSQL)
- Alembic Migrations laufen
- Backup-Strategie
- Monitoring Setup

---

## 📅 Zeitplan Phase 1 MVP (3 Wochen)

**Woche 1: Database Foundation**
- Tag 1-2: Schema Design + Migrations
- Tag 3-4: SQLAlchemy Models
- Tag 5: Pydantic Schemas

**Woche 2: Backend Integration**
- Tag 1-2: API Endpoints
- Tag 3: CSV Parser Integration
- Tag 4-5: Testing

**Woche 3: Frontend & Polish**
- Tag 1-3: Frontend Integration
- Tag 4: Testing & Bug Fixes
- Tag 5: Deployment

**Deliverable:**
Training Sessions werden in DB gespeichert, Liste & Detail-Ansicht, CSV Upload funktioniert! 🎉

---

## 🤔 Offene Fragen für Nils-Christian

1. **Prioritäten Phase 1:**
   - Nur Running zuerst oder auch Strength?
   - HR-Zonen: 3-Zonen oder 5-Zonen System?
   - Equipment-Tracking schon in Phase 1?

2. **Multi-User oder Single-User?**
   - Nur für dich oder mehrere Athleten?
   - Authentication needed?

3. **Daten-Migration:**
   - Alte Trainings importieren oder fresh start?
   - CSV-Archiv vorhanden?

4. **External APIs:**
   - OpenWeatherMap API Key vorhanden?
   - Strava/Garmin Connect später gewünscht?

5. **Hosting:**
   - Bleibt auf NAS oder Cloud (Railway, Fly.io)?
   - Backup-Strategie?

---

**Ready to start? Was sollen wir zuerst anpacken?** 🚀
