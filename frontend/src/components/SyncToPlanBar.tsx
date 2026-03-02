import { useState } from 'react';
import { Alert, AlertDescription, Button, Checkbox, Spinner, useToast } from '@nordlig/components';
import { ArrowUpToLine } from 'lucide-react';
import { syncToPlan } from '../api/weekly-plan';

interface SyncToPlanBarProps {
  planId: number;
  weekStart: string;
  editedCount: number;
  onSynced: () => void;
  onDismiss: () => void;
}

export function SyncToPlanBar({
  planId,
  weekStart,
  editedCount,
  onSynced,
  onDismiss,
}: SyncToPlanBarProps) {
  const [applyToAll, setApplyToAll] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const { toast } = useToast();

  const handleSync = async () => {
    setSyncing(true);
    try {
      const result = await syncToPlan({
        week_start: weekStart,
        plan_id: planId,
        apply_to_all_weeks: applyToAll,
      });
      toast({
        title: `In Phase "${result.phase_name}" übernommen`,
        description: applyToAll
          ? 'Alle Wochen der Phase aktualisiert'
          : `Woche ${result.week_key} aktualisiert`,
        variant: 'success',
      });
      onSynced();
    } catch {
      toast({ title: 'Sync fehlgeschlagen', variant: 'error' });
    } finally {
      setSyncing(false);
    }
  };

  return (
    <Alert variant="info">
      <ArrowUpToLine className="h-4 w-4" />
      <AlertDescription>
        <div className="space-y-3">
          <p>
            {editedCount === 1 ? '1 bearbeiteter Eintrag' : `${editedCount} bearbeitete Einträge`} —
            in Trainingsplan übernehmen?
          </p>
          <label className="inline-flex items-center gap-1.5 cursor-pointer min-h-[44px]">
            <Checkbox
              checked={applyToAll}
              onCheckedChange={(checked) => setApplyToAll(checked === true)}
            />
            <span className="text-sm text-[var(--color-text-muted)]">
              Für alle Wochen der Phase
            </span>
          </label>
          <div className="flex gap-2">
            <Button variant="primary" size="sm" onClick={handleSync} disabled={syncing}>
              {syncing ? <Spinner size="sm" /> : 'Übernehmen'}
            </Button>
            <Button variant="ghost" size="sm" onClick={onDismiss} disabled={syncing}>
              Nur lokal
            </Button>
          </div>
        </div>
      </AlertDescription>
    </Alert>
  );
}
