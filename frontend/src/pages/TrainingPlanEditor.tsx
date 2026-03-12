import { Link } from 'react-router-dom';
import {
  Button,
  Card,
  CardBody,
  Input,
  Label,
  Badge,
  Spinner,
  Alert,
  AlertDescription,
  Breadcrumbs,
  BreadcrumbItem,
  Select,
  DatePicker,
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogAction,
  AlertDialogCancel,
  Checkbox,
  MultiSelect,
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from '@nordlig/components';
import { Save, ChevronRight, Plus, Trash2, Pencil, EllipsisVertical } from 'lucide-react';
import type { PhaseType } from '@/api/training-plans';
import { PhaseWeeklyTemplateEditor } from '@/components/PhaseWeeklyTemplateEditor';
import { PlanChangeLog } from '@/components/PlanChangeLog';
import { TrainingPlanReadView } from '@/components/TrainingPlanReadView';
import { PHASE_TYPES, STATUS_OPTIONS, STATUS_BADGE_VARIANTS } from '@/components/plan-helpers';
import { PHASE_FOCUS_TAGS, PHASE_FOCUS_DEFAULTS } from '@/constants/taxonomy';
import { usePlanForm } from '@/hooks/usePlanForm';
import { usePlanSubmit } from '@/hooks/usePlanSubmit';

// eslint-disable-next-line max-lines-per-function, complexity -- JSX-heavy page component
export function TrainingPlanEditorPage() {
  const form = usePlanForm();
  const submit = usePlanSubmit({
    planId: form.planId,
    isEdit: form.isEdit,
    name: form.name,
    description: form.description,
    startDate: form.startDate,
    endDate: form.endDate,
    targetEventDate: form.targetEventDate,
    status: form.status,
    goalId: form.goalId,
    restDays: form.restDays,
    phases: form.phases,
    navigate: form.navigate,
    toast: form.toast,
  });

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
      {/* Breadcrumbs */}
      <div className="space-y-2 pb-2">
        <Breadcrumbs separator={<ChevronRight className="w-3.5 h-3.5" />}>
          <BreadcrumbItem>
            <Link to="/plan" className="hover:underline underline-offset-2">
              Plan
            </Link>
          </BreadcrumbItem>
          <BreadcrumbItem>
            <Link to="/plan/programs" className="hover:underline underline-offset-2">
              Programme
            </Link>
          </BreadcrumbItem>
          <BreadcrumbItem isCurrent>
            {form.isEdit ? form.name || 'Plan' : 'Neuer Plan'}
          </BreadcrumbItem>
        </Breadcrumbs>
        <header className="flex items-start justify-between gap-3">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-xl md:text-2xl font-semibold text-[var(--color-text-base)]">
              {!form.isEdit
                ? 'Neuer Trainingsplan'
                : form.isEditing
                  ? 'Plan bearbeiten'
                  : form.name}
            </h1>
            {form.isEdit && !form.isEditing && (
              <Badge variant={STATUS_BADGE_VARIANTS[form.status]} size="xs">
                {STATUS_OPTIONS.find((s) => s.value === form.status)?.label ?? form.status}
              </Badge>
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
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  icon={<Trash2 />}
                  destructive
                  onSelect={() => submit.setShowDeleteDialog(true)}
                >
                  Löschen
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </header>
      </div>

      {/* Delete Dialog */}
      <AlertDialog open={submit.showDeleteDialog} onOpenChange={submit.setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Trainingsplan löschen?</AlertDialogTitle>
            <AlertDialogDescription>
              „{form.name}" und alle Phasen werden unwiderruflich gelöscht.
            </AlertDialogDescription>
          </AlertDialogHeader>

          {form.weeklyPlanWeekCount > 0 && (
            <div className="px-[var(--spacing-md)]">
              <label className="inline-flex items-center gap-2 cursor-pointer min-h-[44px]">
                <Checkbox
                  checked={submit.deleteWeeklyPlans}
                  onCheckedChange={(checked) => submit.setDeleteWeeklyPlans(checked === true)}
                />
                <span className="text-sm text-[var(--color-text-base)]">
                  {form.weeklyPlanWeekCount} Wochenpläne ebenfalls löschen
                </span>
              </label>
            </div>
          )}

          <AlertDialogFooter>
            <AlertDialogCancel>Abbrechen</AlertDialogCancel>
            <AlertDialogAction onClick={submit.handleDelete} disabled={submit.deleting}>
              {submit.deleting ? <Spinner size="sm" /> : 'Löschen'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Read-Only View */}
      {!form.isEditing && form.rawPlan && <TrainingPlanReadView plan={form.rawPlan} />}

      {/* Plan Details (Edit Mode) */}
      {form.isEditing && (
        <Card elevation="raised" padding="spacious">
          <CardBody>
            <div className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="plan-name">Name</Label>
                <Input
                  id="plan-name"
                  placeholder="z.B. HM Sub-2h Vorbereitung"
                  value={form.name}
                  onChange={(e) => form.setName(e.target.value)}
                  inputSize="sm"
                  autoFocus
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="plan-description">Beschreibung</Label>
                <Input
                  id="plan-description"
                  placeholder="Kurze Beschreibung des Plans"
                  value={form.description}
                  onChange={(e) => form.setDescription(e.target.value)}
                  inputSize="sm"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label>Startdatum</Label>
                  <DatePicker value={form.startDate} onChange={form.setStartDate} inputSize="sm" />
                </div>
                <div className="space-y-1.5">
                  <Label>Enddatum</Label>
                  <DatePicker value={form.endDate} onChange={form.setEndDate} inputSize="sm" />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label>Status</Label>
                  <Select
                    options={STATUS_OPTIONS}
                    value={form.status}
                    onChange={(v) => {
                      if (v) form.setStatus(v as typeof form.status);
                    }}
                    inputSize="sm"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label>Ziel</Label>
                  <Select
                    options={[
                      { value: '', label: 'Kein Ziel' },
                      ...form.goals.map((g) => ({ value: g.id.toString(), label: g.title })),
                    ]}
                    value={form.goalId?.toString() ?? ''}
                    onChange={(v) => form.setGoalId(v ? parseInt(v, 10) : undefined)}
                    inputSize="sm"
                    placeholder="Kein Ziel"
                  />
                </div>
              </div>
            </div>
          </CardBody>
        </Card>
      )}

      {/* Phases (Edit Mode) */}
      {form.isEditing && (
        <Card elevation="raised" padding="spacious">
          <CardBody>
            <h2 className="text-sm font-semibold text-[var(--color-text-base)] mb-4">
              Phasen ({form.phases.length})
            </h2>

            {form.phases.length === 0 ? (
              <p className="text-xs text-[var(--color-text-muted)] text-center py-4">
                Noch keine Phasen. Füge deine erste Trainingsphase hinzu.
              </p>
            ) : (
              <div className="space-y-3">
                {/* eslint-disable-next-line max-lines-per-function -- phase form JSX */}
                {form.phases.map((phase, idx) => (
                  <div
                    key={phase.id ?? `new-${idx}`}
                    className="rounded-[var(--radius-component-md)] bg-[var(--color-bg-surface)] px-3 pt-3 pb-6 space-y-3"
                  >
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div className="space-y-1">
                        <Label>Name</Label>
                        <Input
                          value={phase.name}
                          onChange={(e) => form.updatePhaseForm(idx, { name: e.target.value })}
                          inputSize="sm"
                          placeholder="z.B. Grundlagenaufbau"
                        />
                      </div>
                      <div className="space-y-1">
                        <Label>Typ</Label>
                        <Select
                          options={PHASE_TYPES}
                          value={phase.phase_type}
                          onChange={(v) => {
                            if (!v) return;
                            const newType = v as PhaseType;
                            const oldDefaults = PHASE_FOCUS_DEFAULTS[phase.phase_type];
                            const newDefaults = PHASE_FOCUS_DEFAULTS[newType];
                            const isPrimaryDefault =
                              phase.focus_primary.length === 0 ||
                              JSON.stringify([...phase.focus_primary].sort()) ===
                                JSON.stringify([...oldDefaults.primary].sort());
                            const isSecondaryDefault =
                              phase.focus_secondary.length === 0 ||
                              JSON.stringify([...phase.focus_secondary].sort()) ===
                                JSON.stringify([...oldDefaults.secondary].sort());
                            form.updatePhaseForm(idx, {
                              phase_type: newType,
                              ...(isPrimaryDefault && {
                                focus_primary: [...newDefaults.primary],
                              }),
                              ...(isSecondaryDefault && {
                                focus_secondary: [...newDefaults.secondary],
                              }),
                            });
                          }}
                          inputSize="sm"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div className="space-y-1">
                        <Label>Von Woche</Label>
                        <Input
                          type="number"
                          min={1}
                          max={52}
                          value={phase.start_week}
                          onChange={(e) =>
                            form.updatePhaseForm(idx, {
                              start_week: parseInt(e.target.value, 10) || 1,
                            })
                          }
                          inputSize="sm"
                        />
                      </div>
                      <div className="space-y-1">
                        <Label>Bis Woche</Label>
                        <Input
                          type="number"
                          min={1}
                          max={52}
                          value={phase.end_week}
                          onChange={(e) =>
                            form.updatePhaseForm(idx, {
                              end_week: parseInt(e.target.value, 10) || 1,
                            })
                          }
                          inputSize="sm"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div className="space-y-1">
                        <Label>Primäre Schwerpunkte</Label>
                        <MultiSelect
                          options={PHASE_FOCUS_TAGS}
                          value={phase.focus_primary}
                          onChange={(values) =>
                            form.updatePhaseForm(idx, { focus_primary: values })
                          }
                          placeholder="Schwerpunkte wählen…"
                          inputSize="sm"
                          aria-label="Primäre Schwerpunkte"
                        />
                      </div>
                      <div className="space-y-1">
                        <Label>Sekundäre Schwerpunkte</Label>
                        <MultiSelect
                          options={PHASE_FOCUS_TAGS}
                          value={phase.focus_secondary}
                          onChange={(values) =>
                            form.updatePhaseForm(idx, { focus_secondary: values })
                          }
                          placeholder="Schwerpunkte wählen…"
                          inputSize="sm"
                          badgeVariant="primary"
                          aria-label="Sekundäre Schwerpunkte"
                        />
                      </div>
                    </div>

                    <div className="space-y-1">
                      <Label>Notizen</Label>
                      <Input
                        value={phase.notes}
                        onChange={(e) => form.updatePhaseForm(idx, { notes: e.target.value })}
                        inputSize="sm"
                        placeholder="Optionale Hinweise zur Phase"
                      />
                    </div>

                    {/* Weekly Template */}
                    <PhaseWeeklyTemplateEditor
                      template={phase.weekly_template}
                      weeklyTemplates={phase.weekly_templates}
                      phaseType={phase.phase_type}
                      startWeek={phase.start_week}
                      endWeek={phase.end_week}
                      onChange={(t) => form.updatePhaseForm(idx, { weekly_template: t })}
                      onChangeWeeklyTemplates={(wt) =>
                        form.updatePhaseForm(idx, { weekly_templates: wt })
                      }
                    />

                    <div className="flex justify-end pt-3">
                      <Button
                        variant="destructive-outline"
                        size="sm"
                        onClick={() => form.removePhase(idx)}
                      >
                        <Trash2 className="w-4 h-4 mr-1" />
                        Phase entfernen
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <Button variant="ghost" size="sm" onClick={form.addNewPhase} className="w-full mt-2">
              <Plus className="w-4 h-4 mr-1" />
              Phase hinzufügen
            </Button>
          </CardBody>
        </Card>
      )}

      {/* Change Log */}
      {form.isEdit && form.planId && <PlanChangeLog planId={parseInt(form.planId, 10)} />}

      {/* Error — only in edit mode */}
      {form.isEditing && submit.error && (
        <Alert variant="error" closeable onClose={() => submit.setError(null)}>
          <AlertDescription>{submit.error}</AlertDescription>
        </Alert>
      )}

      {/* Fixed ActionBar — edit mode */}
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
                  form.loadPlan();
                } else {
                  form.navigate('/plan/programs');
                }
              }}
            >
              Abbrechen
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={submit.handleSave}
              disabled={submit.saving}
            >
              {submit.saving ? (
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
