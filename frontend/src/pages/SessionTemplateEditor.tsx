import { Link } from 'react-router-dom';
import { useParams } from 'react-router-dom';
import {
  Button,
  Card,
  CardBody,
  Input,
  Select,
  Label,
  Badge,
  Spinner,
  Alert,
  AlertDescription,
  Breadcrumbs,
  BreadcrumbItem,
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '@nordlig/components';
import { Dumbbell, Footprints, Save, ChevronRight, Pencil, EllipsisVertical } from 'lucide-react';
import { trainingTypeOptions } from '@/constants/training';
import { RunDetailsEditor } from '@/components/RunDetailsEditor';
import { StrengthExercisesEditSection } from '@/components/session-template/StrengthExercisesEditSection';
import { StrengthExercisesReadView } from '@/components/session-template/StrengthExercisesReadView';
import { RunningReadView } from '@/components/session-template/RunningReadView';
import { useExerciseListEditor } from '@/hooks/useExerciseListEditor';
import { useExerciseSuggestions } from '@/hooks/useExerciseSuggestions';
import { useSessionTemplateForm } from '@/hooks/useSessionTemplateForm';

// --- Constants ---

type TemplateSessionType = 'strength' | 'running';

const SESSION_TYPE_OPTIONS: { value: TemplateSessionType; label: string; icon: string }[] = [
  { value: 'strength', label: 'Kraft', icon: 'dumbbell' },
  { value: 'running', label: 'Laufen', icon: 'footprints' },
];

const RUN_TYPE_OPTIONS = trainingTypeOptions.map((opt) => ({
  value: opt.value,
  label: opt.label,
}));

// --- Component ---

// eslint-disable-next-line max-lines-per-function, complexity -- JSX-heavy page component
export function SessionTemplateEditorPage() {
  const { templateId } = useParams<{ templateId: string }>();
  const { exercises, setExercises, updateExercise, removeExercise, addExercise, moveExercise } =
    useExerciseListEditor();

  const form = useSessionTemplateForm({ templateId, exercises, setExercises });

  const suggestions = useExerciseSuggestions(
    form.sessionType === 'strength' || form.isEdit,
    updateExercise,
  );

  if (form.loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div
      className={`p-4 pt-8 md:p-6 md:pt-10 max-w-5xl mx-auto space-y-6${form.isEditing ? ' pb-24' : ''}`}
    >
      {/* Breadcrumbs + Header */}
      <div className="space-y-2 pb-2">
        <Breadcrumbs separator={<ChevronRight className="w-3.5 h-3.5" />}>
          <BreadcrumbItem>
            <Link to="/plan" className="hover:underline underline-offset-2">
              Plan
            </Link>
          </BreadcrumbItem>
          <BreadcrumbItem>
            <Link to="/plan/templates" className="hover:underline underline-offset-2">
              Vorlagen
            </Link>
          </BreadcrumbItem>
          <BreadcrumbItem isCurrent>
            {form.isEdit ? form.templateName || 'Template' : 'Neues Template'}
          </BreadcrumbItem>
        </Breadcrumbs>
        <header className="flex items-start justify-between gap-3">
          <div>
            <h1 className="text-xl md:text-2xl font-semibold text-[var(--color-text-base)]">
              {!form.isEdit
                ? 'Neues Session-Template'
                : form.isEditing
                  ? 'Template bearbeiten'
                  : form.templateName}
            </h1>
            {form.isEditing && (
              <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                {form.sessionType === 'strength'
                  ? 'Übungen, Sätze und Gewichte als Vorlage definieren.'
                  : 'Lauftyp, Dauer, Pace und Segmente als Vorlage definieren.'}
              </p>
            )}
          </div>
          {form.isEdit && (
            <DropdownMenu>
              <DropdownMenuTrigger>
                <Button variant="ghost" size="sm" aria-label="Aktionen" className="shrink-0">
                  <EllipsisVertical className="w-4 h-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem
                  icon={<Pencil />}
                  disabled={form.isEditing}
                  onSelect={() => form.setEditMode(true)}
                >
                  Bearbeiten
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </header>
      </div>

      {form.isEditing && form.error && (
        <Alert variant="error">
          <AlertDescription>{form.error}</AlertDescription>
        </Alert>
      )}

      {/* Template Meta */}
      <TemplateMetaCard form={form} />

      {/* Strength: Edit */}
      {form.sessionType === 'strength' && form.isEditing && (
        <StrengthExercisesEditSection
          exercises={exercises}
          updateExercise={updateExercise}
          removeExercise={removeExercise}
          addExercise={addExercise}
          moveExercise={moveExercise}
          suggestions={suggestions}
        />
      )}

      {/* Strength: Read-only */}
      {form.sessionType === 'strength' && !form.isEditing && (
        <StrengthExercisesReadView exercises={exercises} />
      )}

      {/* Running: Edit */}
      {form.sessionType === 'running' && form.isEditing && (
        <Card elevation="raised" padding="spacious">
          <CardBody>
            <div className="space-y-4">
              <h2 className="text-sm font-semibold text-[var(--color-text-base)]">Lauf-Details</h2>
              <div>
                <Label className="mb-1.5 block text-xs font-medium text-[var(--color-text-muted)]">
                  Lauftyp
                </Label>
                <Select
                  options={RUN_TYPE_OPTIONS}
                  value={form.runType}
                  onChange={form.handleRunTypeChange}
                  inputSize="md"
                  aria-label="Lauftyp"
                />
              </div>
              <RunDetailsEditor
                runDetails={form.runDetails}
                runType={form.runType}
                onChange={form.handleRunDetailsChange}
              />
            </div>
          </CardBody>
        </Card>
      )}

      {/* Running: Read-only */}
      {form.sessionType === 'running' && !form.isEditing && (
        <RunningReadView runType={form.runType} runDetails={form.runDetails} />
      )}

      {/* Fixed ActionBar */}
      {form.isEditing && (
        <div
          role="toolbar"
          className="fixed bottom-[82px] lg:bottom-0 left-0 lg:left-[224px] right-0 z-40 bg-[var(--color-actionbar-bg)] border-t border-[var(--color-actionbar-border)] rounded-t-[var(--radius-actionbar)] [box-shadow:var(--shadow-actionbar-default)] px-[var(--spacing-actionbar-padding-x)] py-[var(--spacing-actionbar-padding-y)] flex items-center justify-between gap-[var(--spacing-actionbar-gap)]"
        >
          <span className="text-xs text-[var(--color-actionbar-text)] hidden sm:inline">
            Ungespeicherte Änderungen
          </span>
          <div className="flex gap-2 ml-auto">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                if (form.isEdit) {
                  form.setEditMode(false);
                  form.loadTemplate();
                } else {
                  form.navigate('/plan/templates');
                }
              }}
            >
              Abbrechen
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={form.handleSubmit}
              disabled={form.submitting || !form.templateName.trim()}
            >
              {form.submitting ? (
                <Spinner size="sm" aria-hidden="true" />
              ) : (
                <>
                  <Save className="w-4 h-4 mr-1" />
                  {form.isEdit ? 'Speichern' : 'Erstellen'}
                </>
              )}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

// --- Sub-Component ---

interface TemplateMetaCardProps {
  form: ReturnType<typeof useSessionTemplateForm>;
}

function TemplateMetaCard({ form }: TemplateMetaCardProps) {
  return (
    <Card elevation="raised" padding="spacious">
      <CardBody>
        {form.isEditing ? (
          <div className="space-y-4">
            {!form.isEdit && (
              <div>
                <Label className="mb-1.5 block text-xs font-medium text-[var(--color-text-muted)]">
                  Trainingsart
                </Label>
                <div className="flex gap-2">
                  {SESSION_TYPE_OPTIONS.map((opt) => (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => form.setSessionType(opt.value)}
                      className={`flex items-center gap-2 px-4 py-2.5 min-h-[44px] text-sm rounded-[var(--radius-component-md)] border transition-colors duration-150 motion-reduce:transition-none ${
                        form.sessionType === opt.value
                          ? 'border-[var(--color-border-focus)] bg-[var(--color-bg-primary-subtle)] text-[var(--color-text-primary)] font-medium'
                          : 'border-[var(--color-border-default)] bg-[var(--color-bg-base)] text-[var(--color-text-muted)] hover:bg-[var(--color-bg-hover)]'
                      }`}
                      aria-pressed={form.sessionType === opt.value}
                    >
                      {opt.icon === 'dumbbell' ? (
                        <Dumbbell className="w-4 h-4" />
                      ) : (
                        <Footprints className="w-4 h-4" />
                      )}
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {form.isEdit && (
              <div className="flex items-center gap-2">
                <Label className="text-xs font-medium text-[var(--color-text-muted)]">
                  Trainingsart:
                </Label>
                <Badge variant="neutral" size="sm">
                  {form.sessionType === 'strength' ? 'Kraft' : 'Laufen'}
                </Badge>
              </div>
            )}
            <div>
              <Label
                htmlFor="template-name"
                className="mb-1.5 block text-xs font-medium text-[var(--color-text-muted)]"
              >
                Template-Name
              </Label>
              <Input
                id="template-name"
                value={form.templateName}
                onChange={(e) => form.setTemplateName(e.target.value)}
                placeholder={
                  form.sessionType === 'strength'
                    ? 'z.B. Studio Tag 1 — Kniedominant'
                    : 'z.B. Intervall 4×3min'
                }
                inputSize="md"
              />
            </div>
            <div>
              <Label
                htmlFor="template-description"
                className="mb-1.5 block text-xs font-medium text-[var(--color-text-muted)]"
              >
                Beschreibung (optional)
              </Label>
              <textarea
                id="template-description"
                value={form.description}
                onChange={(e) => form.setDescription(e.target.value)}
                placeholder="Fokus, Ziele, Hinweise…"
                rows={2}
                className="w-full rounded-[var(--radius-component-md)] border border-[var(--color-border-default)] bg-[var(--color-input-bg)] px-3 py-2 text-sm text-[var(--color-text-base)] placeholder:text-[var(--color-text-disabled)] focus:outline-none focus:ring-2 focus:ring-[var(--color-border-focus)] transition-colors duration-150 motion-reduce:transition-none resize-none"
              />
            </div>
          </div>
        ) : (
          <div className="space-y-2">
            <Badge variant="neutral" size="sm">
              {form.sessionType === 'strength' ? 'Kraft' : 'Laufen'}
            </Badge>
            {form.description && (
              <p className="text-sm text-[var(--color-text-muted)]">{form.description}</p>
            )}
          </div>
        )}
      </CardBody>
    </Card>
  );
}
