import { useState } from 'react';
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogCancel,
  Button,
  Checkbox,
  Spinner,
} from '@nordlig/components';

interface SaveWeeklyPlanDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Save only the current week (no sync to plan template). */
  onSaveWeekOnly: () => Promise<void>;
  /** Save the current week AND sync changes to the plan template. */
  onSaveAndSync: (applyToAll: boolean) => Promise<void>;
}

/**
 * Dialog shown when saving a weekly plan that is linked to a training plan.
 * Offers two choices: save only this week, or sync changes back to the plan template.
 */
export function SaveWeeklyPlanDialog({
  open,
  onOpenChange,
  onSaveWeekOnly,
  onSaveAndSync,
}: SaveWeeklyPlanDialogProps) {
  const [applyToAll, setApplyToAll] = useState(false);
  const [saving, setSaving] = useState(false);

  const handleWeekOnly = async () => {
    setSaving(true);
    try {
      await onSaveWeekOnly();
    } finally {
      setSaving(false);
      onOpenChange(false);
    }
  };

  const handleSyncToPlan = async () => {
    setSaving(true);
    try {
      await onSaveAndSync(applyToAll);
    } finally {
      setSaving(false);
      setApplyToAll(false);
      onOpenChange(false);
    }
  };

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Änderungen speichern</AlertDialogTitle>
          <AlertDialogDescription>
            Diese Woche ist mit einem Trainingsplan verknüpft. Möchtest du die Änderungen nur für
            diese Woche speichern oder auch ins Programm übernehmen?
          </AlertDialogDescription>
        </AlertDialogHeader>

        <div className="px-[var(--spacing-md)]">
          <label className="inline-flex items-center gap-1.5 cursor-pointer min-h-[44px]">
            <Checkbox
              checked={applyToAll}
              onCheckedChange={(checked) => setApplyToAll(checked === true)}
            />
            <span className="text-sm text-[var(--color-text-muted)]">
              Für alle Wochen der Phase übernehmen
            </span>
          </label>
        </div>

        <AlertDialogFooter>
          <AlertDialogCancel disabled={saving}>Abbrechen</AlertDialogCancel>
          <Button variant="secondary" size="sm" onClick={handleWeekOnly} disabled={saving}>
            {saving ? <Spinner size="sm" /> : 'Nur diese Woche'}
          </Button>
          <Button variant="primary" size="sm" onClick={handleSyncToPlan} disabled={saving}>
            {saving ? <Spinner size="sm" /> : 'Ins Programm übernehmen'}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
