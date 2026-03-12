import {
  Card,
  CardBody,
  Select,
  Spinner,
  DatePicker,
  Input,
  Label,
  Slider,
  Button,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@nordlig/components';
import { RefreshCw } from 'lucide-react';
import { parseISO } from 'date-fns';
import { trainingTypeOptions } from '@/constants/training';
import type { SessionDetail, HRZone } from '@/api/training';
import type { SessionEditingState } from '@/hooks/useSessionEditing';

interface SessionEditFieldsProps {
  session: SessionDetail;
  editing: SessionEditingState;
  effectiveRpe: number | null;
  hrZones: Record<string, HRZone> | undefined | null;
}

// eslint-disable-next-line max-lines-per-function, complexity -- edit card with conditional fields + dialog
export function SessionEditFields({
  session,
  editing,
  effectiveRpe,
  hrZones,
}: SessionEditFieldsProps) {
  return (
    <>
      <Card elevation="raised">
        <CardBody>
          <div
            className={`grid grid-cols-1 gap-4 ${session.workout_type === 'running' ? (hrZones ? 'sm:grid-cols-3' : 'sm:grid-cols-2') : ''}`}
          >
            <div className="space-y-1.5">
              <Label>Datum</Label>
              {editing.savingDate ? (
                <Spinner size="sm" />
              ) : (
                <DatePicker
                  value={parseISO(session.date)}
                  onChange={editing.handleDateChange}
                  inputSize="sm"
                />
              )}
            </div>
            {session.workout_type === 'running' && (
              <div className="space-y-1.5">
                <Label>Trainingstyp</Label>
                {editing.savingTrainingType ? (
                  <Spinner size="sm" />
                ) : (
                  <Select
                    options={trainingTypeOptions}
                    value={editing.trainingTypeInfo?.effective ?? undefined}
                    onChange={editing.handleTrainingTypeOverride}
                    inputSize="sm"
                    placeholder="Typ ändern"
                  />
                )}
              </div>
            )}
            {hrZones && (
              <div className="space-y-1.5">
                <Label>HF-Zonen</Label>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={editing.openRecalcDialog}
                  className="w-full"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  Zonen neu berechnen
                </Button>
              </div>
            )}
          </div>
          <div className="mt-4 space-y-1.5">
            <Label>RPE (Anstrengung): {effectiveRpe ?? '–'}</Label>
            <Slider
              value={[effectiveRpe ?? 5]}
              onValueChange={([val]) => editing.handleRpeChange(val)}
              min={1}
              max={10}
              step={1}
              showValue
              aria-label="Rate of Perceived Exertion"
            />
          </div>
          <div className="mt-4 space-y-1.5">
            <Label>Geplante Session</Label>
            {editing.savingPlannedEntry ? (
              <Spinner size="sm" />
            ) : (
              <Select
                options={[
                  { value: '', label: 'Keine Zuordnung' },
                  ...editing.plannedSessions.map((ps) => ({
                    value: String(ps.id),
                    label: [
                      ps.training_type === 'strength' ? 'Kraft' : 'Laufen',
                      ps.run_type ? `— ${ps.run_type}` : '',
                      ps.template_name ? `(${ps.template_name})` : '',
                    ]
                      .filter(Boolean)
                      .join(' '),
                  })),
                ]}
                value={session.planned_entry_id ? String(session.planned_entry_id) : ''}
                onChange={editing.handlePlannedEntryChange}
                inputSize="sm"
                aria-label="Geplante Session zuordnen"
              />
            )}
            {editing.plannedSessions.length === 0 && (
              <p className="text-xs text-[var(--color-text-muted)]">
                Keine geplanten Sessions für diesen Tag
              </p>
            )}
          </div>
        </CardBody>
      </Card>

      {/* Recalculate zones dialog */}
      <Dialog open={editing.showRecalcDialog} onOpenChange={editing.setShowRecalcDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>HF-Zonen neu berechnen</DialogTitle>
            <DialogDescription>
              Gib die Herzfrequenz-Werte ein, die für diese Session gelten sollen.
            </DialogDescription>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="recalc-resting">Ruhe-HF (bpm)</Label>
              <Input
                id="recalc-resting"
                type="number"
                min={30}
                max={120}
                value={editing.recalcRestingHr}
                onChange={(e) => editing.setRecalcRestingHr(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="recalc-max">Max-HF (bpm)</Label>
              <Input
                id="recalc-max"
                type="number"
                min={120}
                max={230}
                value={editing.recalcMaxHr}
                onChange={(e) => editing.setRecalcMaxHr(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="secondary" onClick={() => editing.setShowRecalcDialog(false)}>
              Abbrechen
            </Button>
            <Button
              variant="primary"
              onClick={editing.handleRecalculateZones}
              disabled={editing.recalculating || !editing.recalcRestingHr || !editing.recalcMaxHr}
            >
              {editing.recalculating ? <Spinner size="sm" /> : 'Berechnen'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
