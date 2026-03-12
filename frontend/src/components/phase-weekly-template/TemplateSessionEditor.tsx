/**
 * Editor for a single session within a phase weekly template day.
 */
import { useState } from 'react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  Button,
  Input,
  Label,
  Select,
} from '@nordlig/components';
import { LayoutTemplate, Trash2 } from 'lucide-react';
import type { PhaseWeeklyTemplateSessionEntry, RunType } from '@/api/training-plans';
import type { RunDetails } from '@/api/weekly-plan';
import type { TemplateExercise } from '@/api/session-templates';
import { getSessionTemplate } from '@/api/session-templates';
import type { SessionTemplateSummary } from '@/api/session-templates';
import { getPresetSegments, hasSegmentData } from '@/config/segmentPresets';
import { SESSION_TYPE_OPTIONS } from '@/constants/plan';
import { RunDetailsEditor } from '../RunDetailsEditor';
import { StrengthExerciseEditor } from '../StrengthExerciseEditor';
import { TemplatePickerDialog } from '../TemplatePickerDialog';

const RUN_TYPE_OPTIONS: { value: RunType; label: string }[] = [
  { value: 'easy', label: 'Easy Run' },
  { value: 'recovery', label: 'Recovery' },
  { value: 'long_run', label: 'Long Run' },
  { value: 'progression', label: 'Progression' },
  { value: 'tempo', label: 'Tempo' },
  { value: 'intervals', label: 'Intervalle' },
  { value: 'repetitions', label: 'Repetitions' },
  { value: 'fartlek', label: 'Fartlek' },
  { value: 'race', label: 'Wettkampf' },
];

interface TemplateSessionEditorProps {
  session: PhaseWeeklyTemplateSessionEntry;
  canRemove: boolean;
  showRestOption?: boolean;
  onUpdate: (updated: PhaseWeeklyTemplateSessionEntry) => void;
  onRemove: () => void;
  onMakeRest?: () => void;
}

// eslint-disable-next-line max-lines-per-function -- JSX-heavy session editor
export function TemplateSessionEditor({
  session,
  canRemove,
  showRestOption,
  onUpdate,
  onRemove,
  onMakeRest,
}: TemplateSessionEditorProps) {
  const [pickerOpen, setPickerOpen] = useState(false);
  const [pendingRunType, setPendingRunType] = useState<string | null>(null);

  const typeOptions = showRestOption
    ? [{ value: 'rest', label: 'Ruhetag' }, ...SESSION_TYPE_OPTIONS]
    : SESSION_TYPE_OPTIONS;

  const handleTypeChange = (val: string) => {
    if (val === 'rest') {
      onMakeRest?.();
      return;
    }
    if (val === 'strength') {
      onUpdate({
        ...session,
        training_type: 'strength',
        run_type: null,
        run_details: undefined,
        exercises: null,
      });
    } else {
      const preset = getPresetSegments('easy');
      onUpdate({
        ...session,
        training_type: 'running',
        run_type: 'easy',
        run_details: {
          run_type: 'easy',
          target_duration_minutes: null,
          target_pace_min: null,
          target_pace_max: null,
          target_hr_min: null,
          target_hr_max: null,
          intervals: null,
          segments: preset,
        },
        exercises: undefined,
      });
    }
  };

  const applyRunTypeWithPreset = (runType: string) => {
    const preset = getPresetSegments(runType as RunType);
    onUpdate({
      ...session,
      run_type: runType as RunType,
      run_details: {
        run_type: runType as RunDetails['run_type'],
        target_duration_minutes: null,
        target_pace_min: null,
        target_pace_max: null,
        target_hr_min: null,
        target_hr_max: null,
        intervals: null,
        segments: preset,
      },
    });
  };

  const applyRunTypeKeepSegments = (runType: string) => {
    onUpdate({
      ...session,
      run_type: runType as RunType,
      run_details: session.run_details
        ? { ...session.run_details, run_type: runType as RunDetails['run_type'] }
        : undefined,
    });
  };

  const handleRunTypeChange = (runType: string) => {
    if (hasSegmentData(session.run_details?.segments)) {
      setPendingRunType(runType);
    } else {
      applyRunTypeWithPreset(runType);
    }
  };

  const handleRunDetailsChange = (details: RunDetails | null) => {
    onUpdate({ ...session, run_details: details ?? undefined });
  };

  const handleExercisesChange = (exercises: TemplateExercise[] | null) => {
    onUpdate({ ...session, exercises });
  };

  const handleTemplateSelect = async (tmplSummary: SessionTemplateSummary | null) => {
    setPickerOpen(false);
    if (!tmplSummary) return;
    try {
      const full = await getSessionTemplate(tmplSummary.id);
      if (session.training_type === 'strength') {
        onUpdate({
          ...session,
          template_id: full.id,
          template_name: full.name,
          exercises: full.exercises.length > 0 ? full.exercises : null,
          notes: full.description ?? session.notes,
        });
      } else if (session.training_type === 'running' && full.run_details) {
        onUpdate({
          ...session,
          template_id: full.id,
          template_name: full.name,
          run_details: full.run_details,
          run_type: full.run_details.run_type as RunType,
        });
      }
    } catch {
      /* template fetch failed — ignore */
    }
  };

  return (
    <div className="space-y-2">
      <div>
        <Label className="text-xs mb-1">Trainingstyp</Label>
        <Select
          options={typeOptions}
          value={session.training_type}
          onChange={(val) => {
            if (val) handleTypeChange(val);
          }}
          inputSize="sm"
          aria-label="Trainingstyp"
        />
      </div>

      {/* Template picker button + name */}
      <div className="space-y-1">
        <Button
          variant="secondary"
          size="sm"
          onClick={() => setPickerOpen(true)}
          className="w-full"
        >
          <LayoutTemplate className="w-4 h-4 mr-1" />
          {session.template_id ? 'Vorlage wechseln' : 'Vorlage laden'}
        </Button>
        {session.template_name && (
          <p className="text-xs text-[var(--color-text-muted)] truncate px-1">
            Vorlage:{' '}
            <span className="font-medium text-[var(--color-text-base)]">
              {session.template_name}
            </span>
          </p>
        )}
      </div>

      {session.training_type === 'running' && (
        <>
          <div>
            <Label className="text-xs mb-1">Lauftyp</Label>
            <Select
              options={RUN_TYPE_OPTIONS}
              value={session.run_type ?? 'easy'}
              onChange={(val) => {
                if (val) handleRunTypeChange(val);
              }}
              inputSize="sm"
              aria-label="Lauftyp"
            />
          </div>
          <RunDetailsEditor
            runDetails={session.run_details ?? null}
            runType={session.run_type}
            onChange={handleRunDetailsChange}
          />
        </>
      )}

      {session.training_type === 'strength' && (
        <StrengthExerciseEditor
          exercises={session.exercises ?? null}
          onChange={handleExercisesChange}
        />
      )}

      {/* Notes */}
      <div>
        <Label className="text-xs mb-1">Notiz</Label>
        <Input
          type="text"
          value={session.notes ?? ''}
          onChange={(e) => onUpdate({ ...session, notes: e.target.value || null })}
          inputSize="sm"
          placeholder={
            session.training_type === 'running'
              ? 'z.B. lockerer Dauerlauf, Fokus Technik'
              : 'z.B. Aufwärmen, Mobilität'
          }
          aria-label="Session Notiz"
        />
      </div>

      {canRemove && (
        <div className="flex justify-end pt-3">
          <Button variant="destructive-outline" size="sm" onClick={onRemove}>
            <Trash2 className="w-4 h-4 mr-1" />
            Session entfernen
          </Button>
        </div>
      )}

      {/* Template Picker Dialog */}
      <TemplatePickerDialog
        open={pickerOpen}
        onOpenChange={setPickerOpen}
        sessionType={session.training_type}
        onSelect={handleTemplateSelect}
      />

      {/* Preset confirmation dialog */}
      <AlertDialog
        open={pendingRunType !== null}
        onOpenChange={(open) => {
          if (!open) setPendingRunType(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Segmente ersetzen?</AlertDialogTitle>
            <AlertDialogDescription>
              Du hast bereits Segmente konfiguriert. Moechtest du sie mit der Vorlage fuer &ldquo;
              {RUN_TYPE_OPTIONS.find((o) => o.value === pendingRunType)?.label ?? pendingRunType}
              &rdquo; ersetzen?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel
              onClick={() => {
                if (pendingRunType) applyRunTypeKeepSegments(pendingRunType);
                setPendingRunType(null);
              }}
            >
              Beibehalten
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (pendingRunType) applyRunTypeWithPreset(pendingRunType);
                setPendingRunType(null);
              }}
            >
              Ersetzen
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
