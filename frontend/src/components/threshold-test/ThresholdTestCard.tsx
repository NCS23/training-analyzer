import { useState, useEffect, useMemo } from 'react';
import {
  Card,
  CardHeader,
  CardBody,
  Button,
  Input,
  Label,
  Alert,
  AlertDescription,
  Spinner,
  useToast,
} from '@nordlig/components';
import { Activity, Plus, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import {
  listThresholdTests,
  createThresholdTest,
  type ThresholdTest,
  type ThresholdTestCreate,
} from '@/api/threshold-tests';
import type { KarvonenZone } from '@/api/athlete';

// --- Sub-Components ---

function ZoneRow({ zone }: { zone: KarvonenZone }) {
  return (
    <div
      className="flex items-center justify-between py-1.5 px-3 rounded-[var(--radius-component-sm)]"
      style={{ backgroundColor: `${zone.color}15` }}
    >
      <div className="flex items-center gap-2">
        <div
          className="w-2.5 h-2.5 rounded-full shrink-0"
          style={{ backgroundColor: zone.color }}
        />
        <span className="text-xs font-medium text-[var(--color-text-base)]">
          Zone {zone.zone}: {zone.name}
        </span>
      </div>
      <span className="text-xs text-[var(--color-text-muted)]">
        {zone.lower_bpm}–{zone.upper_bpm} bpm
      </span>
    </div>
  );
}

function TestHistoryItem({ test }: { test: ThresholdTest }) {
  const dateStr = new Date(test.test_date).toLocaleDateString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
  return (
    <div className="flex items-center justify-between py-2 border-b border-[var(--color-border-default)] last:border-b-0">
      <div>
        <span className="text-sm font-medium text-[var(--color-text-base)]">{dateStr}</span>
        {test.notes && (
          <p className="text-xs text-[var(--color-text-muted)] mt-0.5">{test.notes}</p>
        )}
      </div>
      <div className="text-right">
        <span className="text-sm font-semibold text-[var(--color-text-primary)]">
          {test.lthr} bpm
        </span>
        {test.max_hr_measured && (
          <p className="text-xs text-[var(--color-text-muted)]">Max: {test.max_hr_measured} bpm</p>
        )}
      </div>
    </div>
  );
}

interface ManualEntryFormProps {
  onSave: (data: ThresholdTestCreate) => Promise<void>;
  saving: boolean;
}

function ManualEntryForm({ onSave, saving }: ManualEntryFormProps) {
  const [lthr, setLthr] = useState('');
  const [maxHr, setMaxHr] = useState('');
  const [notes, setNotes] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    const lthrVal = parseInt(lthr, 10);
    if (isNaN(lthrVal) || lthrVal < 100 || lthrVal > 220) {
      setError('LTHR muss zwischen 100 und 220 bpm liegen');
      return;
    }

    const maxHrVal = maxHr ? parseInt(maxHr, 10) : null;
    if (maxHrVal !== null && (maxHrVal < 120 || maxHrVal > 230)) {
      setError('Max-HF muss zwischen 120 und 230 bpm liegen');
      return;
    }

    setError(null);
    await onSave({
      test_date: new Date().toISOString().split('T')[0],
      lthr: lthrVal,
      max_hr_measured: maxHrVal,
      notes: notes || null,
    });

    setLthr('');
    setMaxHr('');
    setNotes('');
  };

  return (
    <div className="space-y-3 pt-3 border-t border-[var(--color-border-default)]">
      <h4 className="text-xs font-semibold text-[var(--color-text-base)]">
        Testergebnis eintragen
      </h4>
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1">
          <Label className="text-[10px]">LTHR (bpm) *</Label>
          <Input
            type="number"
            min={100}
            max={220}
            placeholder="z.B. 170"
            value={lthr}
            onChange={(e) => setLthr(e.target.value)}
            inputSize="sm"
          />
        </div>
        <div className="space-y-1">
          <Label className="text-[10px]">Max-HF (bpm)</Label>
          <Input
            type="number"
            min={120}
            max={230}
            placeholder="z.B. 192"
            value={maxHr}
            onChange={(e) => setMaxHr(e.target.value)}
            inputSize="sm"
          />
        </div>
      </div>
      <div className="space-y-1">
        <Label className="text-[10px]">Notiz</Label>
        <Input
          type="text"
          placeholder="z.B. Bahn, 30-Min-Test"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          inputSize="sm"
        />
      </div>
      {error && (
        <Alert variant="error" closeable onClose={() => setError(null)}>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      <Button
        variant="primary"
        size="sm"
        onClick={handleSubmit}
        disabled={saving || !lthr}
        className="w-full"
      >
        {saving ? <Spinner size="sm" aria-hidden="true" /> : 'Ergebnis speichern'}
      </Button>
    </div>
  );
}

function calcTestAge(testDate: string): { days: number; label: string; color: string } {
  const diff = Math.floor((Date.now() - new Date(testDate).getTime()) / (24 * 60 * 60 * 1000));
  const weeks = Math.floor(diff / 7);
  const label = weeks < 1 ? `vor ${diff} Tagen` : `vor ${weeks} Wochen`;

  if (diff <= 42) return { days: diff, label, color: 'text-[var(--color-text-success)]' };
  if (diff <= 56) return { days: diff, label, color: 'text-[var(--color-text-warning)]' };
  return { days: diff, label, color: 'text-[var(--color-text-error)]' };
}

function LthrDelta({ current, previous }: { current: number; previous: number }) {
  const delta = current - previous;
  if (delta === 0) {
    return (
      <span className="inline-flex items-center gap-1 text-xs font-medium text-[var(--color-text-muted)]">
        <Minus className="w-3 h-3" />
        ±0 bpm
      </span>
    );
  }
  const improved = delta > 0;
  return (
    <span
      className={`inline-flex items-center gap-1 text-xs font-medium ${
        improved ? 'text-[var(--color-text-success)]' : 'text-[var(--color-text-error)]'
      }`}
    >
      {improved ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
      {improved ? '+' : ''}
      {delta} bpm
    </span>
  );
}

function LthrTrendChart({ tests }: { tests: ThresholdTest[] }) {
  const chartData = useMemo(
    () =>
      [...tests].reverse().map((t) => ({
        date: new Date(t.test_date).toLocaleDateString('de-DE', {
          day: '2-digit',
          month: '2-digit',
        }),
        lthr: t.lthr,
        fullDate: new Date(t.test_date).toLocaleDateString('de-DE', {
          day: '2-digit',
          month: '2-digit',
          year: 'numeric',
        }),
      })),
    [tests],
  );

  const lthrs = chartData.map((d) => d.lthr);
  const minLthr = Math.min(...lthrs) - 3;
  const maxLthr = Math.max(...lthrs) + 3;

  return (
    <div className="pt-3 border-t border-[var(--color-border-default)]">
      <h3 className="text-xs font-semibold text-[var(--color-text-muted)] mb-2">LTHR-Trend</h3>
      <div className="h-[140px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 4, right: 8, bottom: 0, left: -20 }}>
            <XAxis
              dataKey="date"
              tick={{ fontSize: 10, fill: 'var(--color-text-muted)' }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              domain={[minLthr, maxLthr]}
              tick={{ fontSize: 10, fill: 'var(--color-text-muted)' }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'var(--color-bg-elevated)',
                border: '1px solid var(--color-border-default)',
                borderRadius: 'var(--radius-component-sm)',
                fontSize: 12,
              }}
              formatter={(value) => [`${value} bpm`, 'LTHR']}
              labelFormatter={(_label, payload) => payload?.[0]?.payload?.fullDate ?? _label}
            />
            <Line
              type="monotone"
              dataKey="lthr"
              stroke="var(--color-text-primary)"
              strokeWidth={2}
              dot={{
                r: 4,
                fill: 'var(--color-bg-elevated)',
                stroke: 'var(--color-text-primary)',
                strokeWidth: 2,
              }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function TestResultView({ latest, tests }: { latest: ThresholdTest; tests: ThresholdTest[] }) {
  const age = calcTestAge(latest.test_date);
  const previousTest = tests.length > 1 ? tests[1] : null;

  return (
    <div className="space-y-4">
      <div className="flex items-baseline gap-3">
        <span className="text-3xl font-bold text-[var(--color-text-primary)]">{latest.lthr}</span>
        <span className="text-sm text-[var(--color-text-muted)]">bpm</span>
        {previousTest && <LthrDelta current={latest.lthr} previous={previousTest.lthr} />}
        <span className={`text-xs ml-auto font-medium ${age.color}`}>{age.label}</span>
      </div>

      {latest.friel_zones && (
        <div className="space-y-1.5">
          <h3 className="text-xs font-semibold text-[var(--color-text-muted)]">
            Friel-Zonen (basierend auf LTHR)
          </h3>
          {latest.friel_zones.map((z) => (
            <ZoneRow key={z.zone} zone={z} />
          ))}
        </div>
      )}

      {tests.length >= 2 && <LthrTrendChart tests={tests} />}

      {tests.length > 1 && (
        <div className="pt-3 border-t border-[var(--color-border-default)]">
          <h3 className="text-xs font-semibold text-[var(--color-text-muted)] mb-2">
            Testhistorie
          </h3>
          {tests.slice(0, 5).map((t) => (
            <TestHistoryItem key={t.id} test={t} />
          ))}
        </div>
      )}
    </div>
  );
}

function EmptyTestState() {
  return (
    <div className="text-center py-4">
      <p className="text-sm text-[var(--color-text-muted)] mb-3">
        Noch kein Schwellentest durchgeführt.
      </p>
      <div className="text-left bg-[var(--color-bg-surface-alt)] rounded-[var(--radius-component-sm)] p-3 space-y-2">
        <h4 className="text-xs font-semibold text-[var(--color-text-base)]">30-Min-Friel-Test</h4>
        <ol className="text-xs text-[var(--color-text-muted)] space-y-1 list-decimal list-inside">
          <li>10 Min locker einlaufen</li>
          <li>30 Min so schnell wie möglich laufen (gleichmäßig!)</li>
          <li>Ø HF der letzten 20 Min = deine LTHR</li>
          <li>Auslaufen</li>
        </ol>
        <p className="text-[10px] text-[var(--color-text-muted)] italic">
          Empfehlung: Alle 6–8 Wochen wiederholen.
        </p>
      </div>
    </div>
  );
}

// --- Hooks ---

function useThresholdTests() {
  const { toast } = useToast();
  const [tests, setTests] = useState<ThresholdTest[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadTests();
  }, []);

  const loadTests = async () => {
    try {
      const data = await listThresholdTests();
      setTests(data.tests);
    } catch {
      // Stille Fehlerbehandlung — Karte ist optional
    } finally {
      setLoading(false);
    }
  };

  const saveTest = async (data: ThresholdTestCreate) => {
    setSaving(true);
    try {
      await createThresholdTest(data);
      await loadTests();
      toast({ title: 'Schwellentest gespeichert', variant: 'success' });
      return true;
    } catch {
      toast({ title: 'Fehler beim Speichern', variant: 'error' });
      return false;
    } finally {
      setSaving(false);
    }
  };

  return { tests, loading, saving, saveTest };
}

// --- Main Component ---

export function ThresholdTestCard() {
  const { tests, loading, saving, saveTest } = useThresholdTests();
  const [showForm, setShowForm] = useState(false);
  const latestTest = tests[0] ?? null;

  const handleSave = async (data: ThresholdTestCreate) => {
    const ok = await saveTest(data);
    if (ok) setShowForm(false);
  };

  if (loading) {
    return (
      <Card elevation="raised" padding="spacious">
        <CardBody className="flex justify-center py-8">
          <Spinner size="sm" />
        </CardBody>
      </Card>
    );
  }

  return (
    <Card elevation="raised" padding="spacious">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-[var(--color-text-primary)]" />
            <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
              Laktatschwelle (LTHR)
            </h2>
          </div>
          {!showForm && (
            <Button variant="ghost" size="sm" onClick={() => setShowForm(true)}>
              <Plus className="w-3.5 h-3.5 mr-1" />
              Test eintragen
            </Button>
          )}
        </div>
      </CardHeader>
      <CardBody>
        {latestTest ? <TestResultView latest={latestTest} tests={tests} /> : <EmptyTestState />}
        {showForm && <ManualEntryForm onSave={handleSave} saving={saving} />}
      </CardBody>
    </Card>
  );
}
