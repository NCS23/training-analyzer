"""CSV Parser für Apple Watch Training Exports (Laufen & Krafttraining)"""
from typing import Dict, List, Optional
from enum import Enum
import pandas as pd
import io
from datetime import datetime

class TrainingType(str, Enum):
    RUNNING = "running"
    STRENGTH = "strength"

class TrainingCSVParser:
    """
    Universeller Parser für Apple Watch CSV Exports
    
    Format: Sekunden-genaue Zeitreihe mit Lap-Spalte
    - Laufen: hr, cadence, distance, speed, elevation, lat/lon
    - Kraft: hr, since_start
    """
    
    REQUIRED_COLUMNS = ['date', 'timestamp', 'ISO8601', 'since_start']
    RUNNING_COLUMNS = ['hr (count/min)', 'cadence (count/min)', 'distance (meter)', 'speed (m/s)']
    
    def parse(self, file_content: bytes, training_type: TrainingType, training_subtype: Optional[str] = None) -> Dict:
        """
        Parst Apple Watch CSV und gibt strukturierte Daten zurück
        
        Args:
            file_content: CSV Datei als Bytes
            training_type: RUNNING oder STRENGTH
            training_subtype: interval, tempo, longrun, recovery, etc.
            
        Returns:
            Dict mit parsed data, metadata, validation errors
        """
        try:
            # CSV einlesen (delimiter ist Semikolon!)
            df = pd.read_csv(io.BytesIO(file_content), delimiter=';')
            
            # Validierung
            validation_errors = self._validate_columns(df)
            if validation_errors:
                return {
                    'success': False,
                    'errors': validation_errors,
                }
            
            # Bereinige Daten (leere Zeilen am Anfang/Ende)
            df = self._clean_dataframe(df)
            
            # Nach Trainingstyp analysieren
            if training_type == TrainingType.RUNNING:
                result = self._analyze_running(df, training_subtype)
            else:
                result = self._analyze_strength(df)
            
            result['success'] = True
            result['metadata'] = {
                'training_type': training_type.value,
                'training_subtype': training_subtype,
                'total_rows': len(df),
                'parsed_at': datetime.utcnow().isoformat(),
            }
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'errors': [f'CSV Parse Error: {str(e)}'],
            }
    
    def _validate_columns(self, df: pd.DataFrame) -> List[str]:
        """Validiert ob Basis-Spalten vorhanden sind"""
        errors = []
        missing = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        
        if missing:
            errors.append(f"Fehlende Spalten: {', '.join(missing)}")
            
        return errors
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Entfernt Zeilen ohne lap-Wert (Start/End Marker)
        Konvertiert Komma-Dezimaltrennzeichen zu Punkt
        """
        # Entferne Zeilen ohne since_start (Start/End Marker)
        df = df[df['since_start'].notna()].copy()
        
        # Wenn lap-Spalte existiert, konvertiere zu int
        # Sonst erstelle eine künstliche lap=1 für alle Zeilen
        if 'lap' in df.columns:
            df = df[df['lap'].notna()].copy()
            df['lap'] = df['lap'].astype(int)
        else:
            df['lap'] = 1  # Krafttraining hat nur einen "Lap"
        
        # Rest bleibt gleich...
        numeric_columns = [
            'hr (count/min)', 'cadence (count/min)', 'distance (meter)', 
            'speed (m/s)', 'elevation (meter)', 'since_start', 'latitude', 'longitude'
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def _analyze_running(self, df: pd.DataFrame, training_subtype: Optional[str] = None) -> Dict:
        """
        Analysiert Lauf-Training
        
        Returns:
            Dict mit laps, summary, hr_zones
        """
        laps_data = []
        
        # Gruppiere nach Laps
        for lap_num, lap_df in df.groupby('lap'):
            lap_analysis = self._analyze_running_lap(lap_df, lap_num)
            laps_data.append(lap_analysis)
        
        # Classify laps
        laps_data = self._classify_laps(laps_data, training_subtype)

        # Gesamt-Summary und HF-Zonen über ALLE Laps
        summary = self._calculate_running_summary(df)
        hr_zones = self._calculate_hr_zones(df)
        
        return {
            'laps': laps_data,
            'summary': summary,
            'hr_zones': hr_zones,
        }
    
    def _analyze_running_lap(self, lap_df: pd.DataFrame, lap_num: int) -> Dict:
        """Analysiert einen einzelnen Lauf-Lap"""
        # Extrahiere Werte
        hr_values = lap_df['hr (count/min)'].dropna()
        distance_values = lap_df['distance (meter)'].dropna()
        cadence_values = lap_df['cadence (count/min)'].dropna()
        
        # Berechne Metriken
        duration_seconds = lap_df['since_start'].max() - lap_df['since_start'].min()
        
        # Distanz (letzte - erste Messung in km)
        if len(distance_values) > 0:
            distance_km = (distance_values.iloc[-1] - distance_values.iloc[0]) / 1000
        else:
            distance_km = 0
        
        # Pace (min/km)
        if distance_km > 0:
            pace_min_per_km = (duration_seconds / 60) / distance_km
        else:
            pace_min_per_km = None
        
        return {
            'lap_number': int(lap_num),
            'duration_seconds': int(duration_seconds),
            'duration_formatted': self._format_duration(int(duration_seconds)),
            'distance_km': round(distance_km, 2),
            'pace_min_per_km': round(pace_min_per_km, 2) if pace_min_per_km else None,
            'pace_formatted': self._format_pace(pace_min_per_km),  
            'avg_hr_bpm': round(hr_values.mean()) if len(hr_values) > 0 else None,
            'max_hr_bpm': int(hr_values.max()) if len(hr_values) > 0 else None,
            'min_hr_bpm': int(hr_values.min()) if len(hr_values) > 0 else None,
            'avg_cadence_spm': round(cadence_values.mean()) if len(cadence_values) > 0 else None,
        }
    
    def _calculate_running_summary(self, df: pd.DataFrame) -> Dict:
        """Berechnet Gesamt-Statistiken für Lauf (nur Hauptlap)"""
        hr_values = df['hr (count/min)'].dropna()
        distance_values = df['distance (meter)'].dropna()
        cadence_values = df['cadence (count/min)'].dropna()
        
        duration_seconds = df['since_start'].max()
        distance_km = distance_values.iloc[-1] / 1000 if len(distance_values) > 0 else 0
        pace_min_per_km = (duration_seconds / 60) / distance_km if distance_km > 0 else None
        
        return {
            'total_distance_km': round(distance_km, 2),
            'total_duration_seconds': int(duration_seconds),
            'total_duration_formatted': self._format_duration(int(duration_seconds)),
            'avg_pace_min_per_km': round(pace_min_per_km, 2) if pace_min_per_km else None,
            'avg_pace_formatted': self._format_pace(pace_min_per_km),
            'avg_hr_bpm': round(hr_values.mean()) if len(hr_values) > 0 else None,
            'max_hr_bpm': int(hr_values.max()) if len(hr_values) > 0 else None,
            'min_hr_bpm': int(hr_values.min()) if len(hr_values) > 0 else None,
            'avg_cadence_spm': round(cadence_values.mean()) if len(cadence_values) > 0 else None,
        }
    
    def _analyze_strength(self, df: pd.DataFrame) -> Dict:
        """
        Analysiert Kraft-Training
        
        Returns:
            Dict mit summary, hr_zones, hr_timeseries
        """
        hr_values = df['hr (count/min)'].dropna()
        duration_seconds = df['since_start'].max()
        
        # HF-Zeitreihe (für Visualisierung, Sampling alle 10 Sekunden)
        hr_timeseries = []
        for idx in range(0, len(df), 10):
            row = df.iloc[idx]
            if pd.notna(row['hr (count/min)']):
                hr_timeseries.append({
                    'seconds': int(row['since_start']),
                    'hr_bpm': int(row['hr (count/min)']),
                    'timestamp': row['ISO8601'],
                })
        
        summary = {
            'total_duration_seconds': int(duration_seconds),
            'total_duration_formatted': self._format_duration(int(duration_seconds)),
            'avg_hr_bpm': round(hr_values.mean()) if len(hr_values) > 0 else None,
            'max_hr_bpm': int(hr_values.max()) if len(hr_values) > 0 else None,
            'min_hr_bpm': int(hr_values.min()) if len(hr_values) > 0 else None,
        }
        
        hr_zones = self._calculate_hr_zones(df)
        
        return {
            'summary': summary,
            'hr_zones': hr_zones,
            'hr_timeseries': hr_timeseries,
        }
    
    def _calculate_hr_zones(self, df: pd.DataFrame) -> Dict:
        """
        Berechnet HF-Zonen Verteilung
        
        Zonen basierend auf deinen Vorgaben:
        - Zone 1 (Recovery): < 150 bpm
        - Zone 2 (Base): 150-160 bpm
        - Zone 3 (Tempo): > 160 bpm
        """
        hr_values = df['hr (count/min)'].dropna()
        
        if len(hr_values) == 0:
            return {}
        
        # Zähle Sekunden pro Zone
        zone_low = len(hr_values[hr_values < 150])
        zone_medium = len(hr_values[(hr_values >= 150) & (hr_values < 160)])
        zone_high = len(hr_values[hr_values >= 160])
        
        total = len(hr_values)
        
        return {
            'zone_1_recovery': {
                'seconds': zone_low,
                'percentage': round(zone_low / total * 100, 1) if total > 0 else 0,
                'label': '< 150 bpm',
            },
            'zone_2_base': {
                'seconds': zone_medium,
                'percentage': round(zone_medium / total * 100, 1) if total > 0 else 0,
                'label': '150-160 bpm',
            },
            'zone_3_tempo': {
                'seconds': zone_high,
                'percentage': round(zone_high / total * 100, 1) if total > 0 else 0,
                'label': '> 160 bpm',
            },
        }
    
    def _classify_laps(self, laps, training_subtype=None):
        """Classify laps based on training type and metrics"""
        if len(laps) == 0:
            return laps
        
        # Add classification to each lap
        for i, lap in enumerate(laps):
            lap_num = lap['lap_number']
            is_first = (i == 0)
            is_last = (i == len(laps) - 1)
            
            # Default
            suggested_type = 'unclassified'
            confidence = 'low'
            
            # Get metrics
            avg_hr = lap.get('avg_hr_bpm')
            duration = lap.get('duration_seconds', 0)
            
            if training_subtype == 'interval':
                # Interval training logic
                if is_first and avg_hr and avg_hr < 140 and duration < 600:  # <10min warmup
                    suggested_type = 'warmup'
                    confidence = 'high'
                elif is_last and avg_hr and avg_hr < 150 and duration < 600:  # <10min cooldown
                    suggested_type = 'cooldown'
                    confidence = 'high'
                elif avg_hr and avg_hr > 160:
                    suggested_type = 'interval'
                    confidence = 'high' if avg_hr > 170 else 'medium'
                elif avg_hr and avg_hr < 150:
                    suggested_type = 'pause'
                    confidence = 'medium'
                else:
                    suggested_type = 'interval'
                    confidence = 'low'
                    
            elif training_subtype == 'tempo':
                # Tempo run logic
                if is_first and duration < 600:
                    suggested_type = 'warmup'
                    confidence = 'medium'
                elif is_last and duration < 600:
                    suggested_type = 'cooldown'
                    confidence = 'medium'
                else:
                    suggested_type = 'tempo'
                    confidence = 'high'
                    
            elif training_subtype == 'longrun':
                # Long run logic
                if is_first and duration < 600:
                    suggested_type = 'warmup'
                    confidence = 'medium'
                elif is_last and duration < 600:
                    suggested_type = 'cooldown'
                    confidence = 'medium'
                else:
                    suggested_type = 'longrun'
                    confidence = 'high'
                    
            elif training_subtype == 'recovery':
                # Recovery run - all laps are recovery
                suggested_type = 'recovery'
                confidence = 'high'
                
            else:
                # Fallback: heuristic based on metrics
                if is_first and avg_hr and avg_hr < 140:
                    suggested_type = 'warmup'
                    confidence = 'low'
                elif is_last and avg_hr and avg_hr < 150:
                    suggested_type = 'cooldown'
                    confidence = 'low'
                elif avg_hr and avg_hr > 165:
                    suggested_type = 'interval'
                    confidence = 'low'
            
            lap['suggested_type'] = suggested_type
            lap['confidence'] = confidence
            lap['user_override'] = None  # Can be set by frontend
        
        return laps
    
    def _format_duration(self, seconds: int) -> str:
        """Formatiert Sekunden zu HH:MM:SS oder MM:SS"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"
    
    def _format_pace(self, pace_min_per_km: float) -> str:
        """Formatiert Pace von Dezimalminuten zu MM:SS"""
        if not pace_min_per_km:
            return None
    
        minutes = int(pace_min_per_km)
        seconds = int((pace_min_per_km - minutes) * 60)
        return f"{minutes}:{seconds:02d}"