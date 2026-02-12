# 🤖 KI-Analyse Integration - Training Analyzer

## 💡 Die Vision

**"Claude als Trainingsassistent"** - Intelligente Analyse & Empfehlungen basierend auf Training-Daten

---

## 🎯 Was KI-Analyse bringt

### **1. Automatische Insights**
```
Input: Training Session (FIT/CSV)
   ↓
Claude analysiert:
   ├─ "Du bist die Intervalle zu schnell angegangen"
   ├─ "HF in Pause zu hoch - bessere Erholung nötig"
   ├─ "Longrun-Pace perfekt für GA1"
   └─ "Kadenz konstant - gute Lauftechnik!"
   ↓
Output: Natürlichsprachige Analyse + Handlungsempfehlungen
```

### **2. Training Plan Erstellung**
```
Input: Ziel (Sub-2h HM) + Aktuelle Form + Historie
   ↓
Claude erstellt:
   ├─ Wochenplan mit progressiver Belastung
   ├─ Spezifische Pace-Vorgaben
   ├─ Regenerationszeiten
   └─ Tapering-Strategie
   ↓
Output: Individualisierter Trainingsplan
```

### **3. Form-Tracking & Warnsignale**
```
Kontinuierliche Analyse über Wochen:
   ├─ "Ruhepuls steigt - mögliches Übertraining"
   ├─ "HF-Decoupling in Longruns - Form wird besser!"
   ├─ "Pace-Progression zu aggressiv - Verletzungsrisiko"
   └─ "Recovery-HF verbessert sich - gute Anpassung"
```

### **4. Vergleiche & Benchmarks**
```
"Dein heutiger Longrun im Vergleich zu KW04:
   ├─ Pace: 6:46/km → 6:52/km (6 Sek langsamer ✅)
   ├─ Avg HR: 167 → 155 bpm (12 bpm niedriger ✅✅)
   ├─ HF-Effizienz: +15% verbessert! 🎉
   └─ Empfehlung: Genau dieses Tempo beibehalten!"
```

---

## 🏗️ Architektur-Optionen

### **Option A: Anthropic API (Claude) ⭐ EMPFOHLEN**

```
┌─────────────────────────────────────────────┐
│  Training Analyzer Backend (FastAPI)       │
│                                             │
│  Training Data → Structured Prompt          │
│       ↓                                     │
│  Anthropic API (Claude Sonnet 4.5)          │
│       ↓                                     │
│  Analysis Response → Parse & Store          │
└─────────────────────────────────────────────┘
```

**Pro:**
- ✅ Beste Analyse-Qualität
- ✅ Versteht Kontext & Nuancen
- ✅ Natürliche Sprache
- ✅ Kontinuierliche Verbesserung (neue Claude Versionen)

**Con:**
- ⚠️ API-Kosten (~$3-5/1000 Analysen)
- ⚠️ Internet erforderlich

**Kosten-Beispiel:**
```
1 Training = ~2000 Tokens Input + 1000 Output = ~$0.02
100 Trainings analysieren = ~$2
→ Sehr günstig für persönlichen Use!
```

---

### **Option B: Lokales LLM (Llama, Mistral)**

```
┌─────────────────────────────────────────────┐
│  Training Analyzer Backend                 │
│                                             │
│  Ollama (lokal auf NAS)                     │
│  └─ Llama 3 8B / Mistral                   │
│                                             │
│  Komplett offline! ✅                        │
└─────────────────────────────────────────────┘
```

**Pro:**
- ✅ Kostenlos (keine API)
- ✅ Offline
- ✅ Privat (Daten bleiben lokal)

**Con:**
- ⚠️ Schwächere Analyse-Qualität
- ⚠️ NAS-Ressourcen erforderlich
- ⚠️ Langsamer

---

### **Option C: Hybrid ⭐⭐ BESTE LÖSUNG**

```
┌─────────────────────────────────────────────┐
│  PRIMARY: Anthropic Claude API             │
│  └─ Tiefe Analysen, Pläne, Vergleiche      │
│                                             │
│  FALLBACK: Lokale Regeln/Heuristiken       │
│  └─ Basis-Insights ohne Internet           │
│                                             │
│  OPTIONAL: Lokales LLM (wenn verfügbar)    │
│  └─ Einfache Analysen offline              │
└─────────────────────────────────────────────┘
```

**Pro:**
- ✅ Beste Qualität (Claude)
- ✅ Funktioniert offline (Fallback)
- ✅ Kostenoptimiert (Cache, Selective Use)

---

## 🔧 Implementation Details

### **Backend API Integration**

```python
# backend/app/services/ai_analysis.py
from anthropic import Anthropic
from app.models.training import TrainingSession

class AIAnalysisService:
    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        
    async def analyze_session(
        self, 
        session: TrainingSession,
        context: list[TrainingSession] = None
    ) -> AnalysisResult:
        """
        Analysiert eine Training Session mit Claude
        
        Args:
            session: Aktuelle Session
            context: Vorherige Sessions für Vergleich
        """
        
        # 1. Strukturiere Daten für Claude
        prompt = self._build_analysis_prompt(session, context)
        
        # 2. Call Claude API
        response = await self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": prompt
            }],
            system="""Du bist ein Lauftraining-Experte.
            Analysiere Training-Sessions basierend auf:
            - Herzfrequenz-Daten
            - Pace/Tempo
            - Lap-Struktur
            - Running Dynamics
            
            Gib konkrete, umsetzbare Feedback in natürlicher Sprache.
            """
        )
        
        # 3. Parse Response
        analysis_text = response.content[0].text
        
        # 4. Strukturiere & Speichere
        return AnalysisResult(
            session_id=session.id,
            analysis_text=analysis_text,
            insights=self._extract_insights(analysis_text),
            recommendations=self._extract_recommendations(analysis_text),
            created_at=datetime.now()
        )
    
    def _build_analysis_prompt(
        self, 
        session: TrainingSession, 
        context: list[TrainingSession]
    ) -> str:
        """Erstellt strukturierten Prompt für Claude"""
        
        prompt = f"""
# Training Session Analyse

## Aktuelle Session
- Datum: {session.date}
- Typ: {session.training_type}
- Dauer: {session.duration} min
- Distanz: {session.distance} km
- Durchschnittspace: {session.avg_pace} min/km
- Durchschnitts-HF: {session.avg_heart_rate} bpm

## Lap Details
"""
        
        for lap in session.laps:
            prompt += f"""
Lap {lap.lap_number} ({lap.lap_type}):
  - Dauer: {lap.duration}s
  - Pace: {lap.avg_pace} min/km
  - HR: {lap.avg_heart_rate} bpm (Min: {lap.min_hr}, Max: {lap.max_hr})
"""
        
        # Running Dynamics (wenn FIT)
        if session.avg_cadence:
            prompt += f"""
## Running Dynamics
- Kadenz: {session.avg_cadence} spm
- Bodenkontaktzeit: {session.avg_ground_contact_time} ms
- Vertical Oscillation: {session.avg_vertical_oscillation} cm
- Vertical Ratio: {session.avg_vertical_ratio}%
"""
        
        # Kontext (vorherige Sessions)
        if context:
            prompt += "\n## Vorherige Sessions (Vergleich)\n"
            for prev in context[-3:]:  # Last 3 sessions
                prompt += f"""
- {prev.date}: {prev.training_type}, {prev.avg_pace} min/km @ {prev.avg_heart_rate} bpm
"""
        
        prompt += """

## Aufgaben
1. Analysiere die Session-Qualität
2. Identifiziere Stärken & Schwächen
3. Vergleiche mit vorherigen Sessions (wenn verfügbar)
4. Gib konkrete Verbesserungsvorschläge
5. Warne vor Übertraining-Signalen

Antworte in Deutsch, natürlich & konkret!
"""
        
        return prompt
```

---

### **Frontend Integration**

```typescript
// frontend/src/components/AIAnalysis.tsx
import React, { useState, useEffect } from 'react';

interface AIAnalysisProps {
  sessionId: string;
}

export const AIAnalysis: React.FC<AIAnalysisProps> = ({ sessionId }) => {
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  
  const requestAnalysis = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/v1/sessions/${sessionId}/analyze`,
        { method: 'POST' }
      );
      const result = await response.json();
      setAnalysis(result);
    } catch (error) {
      console.error('Analysis failed:', error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="ai-analysis">
      <h3>🤖 KI-Analyse</h3>
      
      {!analysis && (
        <button onClick={requestAnalysis} disabled={loading}>
          {loading ? '🔄 Analysiere...' : '🚀 Training analysieren'}
        </button>
      )}
      
      {analysis && (
        <>
          <div className="analysis-text">
            <h4>💡 Insights</h4>
            <p>{analysis.analysis_text}</p>
          </div>
          
          <div className="recommendations">
            <h4>📋 Empfehlungen</h4>
            <ul>
              {analysis.recommendations.map((rec, i) => (
                <li key={i}>{rec}</li>
              ))}
            </ul>
          </div>
          
          <div className="metadata">
            <small>Analysiert: {analysis.created_at}</small>
          </div>
        </>
      )}
    </div>
  );
};
```

---

## 🎯 Integration in Roadmap

### **Phase 1A: Basic AI Analysis (Woche 5-6)**

```python
Features:
✅ API Integration (Anthropic Claude)
✅ Single Session Analysis
✅ Basic Insights & Recommendations
✅ Frontend: "Analysieren" Button
⏳ Caching (vermeidet Duplikate)
```

**Aufwand:** ~1 Woche

---

### **Phase 1B: Context-Aware Analysis (Woche 7-8)**

```python
Features:
✅ Multi-Session Vergleich
✅ Trend-Erkennung
✅ Warnsignale (Übertraining)
✅ Form-Tracking über Zeit
```

**Aufwand:** ~1 Woche

---

### **Phase 1C: AI Training Planning (Woche 9-10)**

```python
Features:
✅ "Training Plan erstellen" Feature
   └─ Input: Ziel, aktuelle Form, verfügbare Zeit
   └─ Output: Wochenplan mit konkreten Sessions
✅ Plan-Anpassung basierend auf tatsächlichem Training
✅ Tapering-Empfehlungen
```

**Aufwand:** ~1 Woche

---

### **Phase 2 & 3: Enhanced AI**

```python
Phase 2 (iOS Companion):
✅ AI-Analyse auch in iOS App
✅ Push Notifications mit Insights
✅ Siri Shortcuts ("Analysiere letztes Training")

Phase 3 (Native):
✅ Lokales LLM als Fallback (offline)
✅ Core ML für Pattern Recognition
✅ On-Device AI für Basis-Analysen
```

---

## 💰 Kosten-Kalkulation

### **Anthropic API (Claude Sonnet 4.5)**

**Pricing (Februar 2026):**
- Input: $3 / 1M Tokens
- Output: $15 / 1M Tokens

**Beispiel-Analyse:**
```
Prompt (1 Session + 3 Context):
├─ Session Data: ~1500 Tokens
├─ Context: ~500 Tokens
└─ System Prompt: ~200 Tokens
Total Input: ~2200 Tokens = $0.0066

Response (Analysis):
└─ ~800 Tokens = $0.012

Total Cost per Analysis: ~$0.018 (~2 Cent!)
```

**Monatliche Kosten (persönlicher Use):**
```
20 Trainings/Monat × $0.02 = $0.40/Monat
→ Vernachlässigbar! ✅
```

**Mit Caching (50% wiederverwendbar):**
```
→ Noch günstiger: ~$0.20/Monat
```

---

## 🧪 Prompt Engineering Best Practices

### **1. Strukturierte Daten**
```python
# GOOD: Strukturiert, parsebar
lap_data = {
    "lap_number": 1,
    "type": "warmup",
    "duration_seconds": 300,
    "avg_pace_min_km": 7.5,
    "avg_heart_rate": 145
}

# BAD: Fließtext, schwer zu parsen
lap_text = "Das erste Lap war warmup und dauerte 5 Minuten..."
```

### **2. Klare Aufgaben**
```
✅ "Analysiere die Herzfrequenz-Verteilung und bewerte die Regeneration"
❌ "Sag mir was über das Training"
```

### **3. Kontext geben**
```
✅ "Vergleiche mit den letzten 3 Sessions gleichen Typs"
❌ "Ist das gut?"
```

### **4. Output-Format definieren**
```
✅ "Antworte in 3 Abschnitten: 1) Stärken 2) Schwächen 3) Empfehlungen"
❌ Freies Format
```

---

## 🔒 Datenschutz & Sicherheit

### **Best Practices:**

1. **Keine PII in Prompts**
   ```python
   # GOOD
   prompt = f"Session vom {session.date.strftime('%Y-%m-%d')}"
   
   # BAD
   prompt = f"Session von {user.full_name} am {session.date}"
   ```

2. **API Key Security**
   ```python
   # .env file (NICHT in Git!)
   ANTHROPIC_API_KEY=sk-ant-...
   
   # settings.py
   class Settings(BaseSettings):
       anthropic_api_key: str = Field(..., env="ANTHROPIC_API_KEY")
   ```

3. **Rate Limiting**
   ```python
   # Prevent abuse
   @app.post("/api/v1/sessions/{id}/analyze")
   @limiter.limit("10/hour")
   async def analyze_session(id: UUID):
       ...
   ```

4. **Caching**
   ```python
   # Vermeidet doppelte API Calls
   if existing_analysis := await get_cached_analysis(session_id):
       return existing_analysis
   
   analysis = await ai_service.analyze_session(session)
   await cache_analysis(session_id, analysis)
   return analysis
   ```

---

## 📊 Success Metrics

### **Phase 1A Success:**
```
✅ KI-Analyse funktioniert für alle Session-Typen
✅ Response-Zeit < 5 Sekunden
✅ Kosten < $1/Monat
✅ Insights sind hilfreich (subjektiv!)
```

### **Phase 1B Success:**
```
✅ Kontext-Aware Analysen zeigen Trends
✅ Warnsignale werden erkannt (Übertraining)
✅ Vergleiche sind akkurat
```

### **Phase 1C Success:**
```
✅ AI generiert valide Trainingspläne
✅ Pläne sind individualisiert
✅ Plan-Anpassung funktioniert
```

---

## 🚀 Quick Start (Integration in Phase 1)

### **Woche 1: Setup**
```bash
# Install Anthropic SDK
pip install anthropic

# .env
ANTHROPIC_API_KEY=sk-ant-api03-...
```

### **Woche 2: Basic Integration**
```python
# Minimal Implementation
@app.post("/api/v1/sessions/{id}/analyze")
async def analyze_session(id: UUID):
    session = await get_session(id)
    
    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"Analysiere dieses Training: {session.to_json()}"
        }]
    )
    
    return {"analysis": response.content[0].text}
```

### **Woche 3: Refinement**
- Prompt Engineering
- Strukturiertes Output
- Caching
- Error Handling

---

## ✅ Zusammenfassung

### **KI-Analyse = Game Changer! 🎯**

**Warum:**
- ✅ Automatische Insights (keine manuelle Analyse!)
- ✅ Natürlichsprachiges Feedback
- ✅ Kontext-Aware (Trends, Vergleiche)
- ✅ Training Plan Erstellung
- ✅ Sehr günstig (~$0.02/Analyse)

**Wann:**
- **Phase 1A:** Woche 5-6 (Basic Analysis)
- **Phase 1B:** Woche 7-8 (Context-Aware)
- **Phase 1C:** Woche 9-10 (AI Planning)

**Wie:**
- Anthropic Claude API (primary)
- Hybrid mit lokalen Fallbacks
- Strukturiertes Prompt Engineering

---

## 📝 Nächste Schritte

**Um KI-Analyse zu integrieren:**

1. **API Key besorgen** (anthropic.com)
2. **SDK installieren** (`pip install anthropic`)
3. **Ersten Prompt testen** (manuell)
4. **Backend Endpoint** implementieren
5. **Frontend Button** hinzufügen
6. **Testen mit echten Daten!**

**Willst du das direkt nach FIT Import + Lap Classification einbauen?** 🤔

