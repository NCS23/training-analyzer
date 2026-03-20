import { useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Button,
  Card,
  CardHeader,
  CardBody,
  Badge,
  Textarea,
  Spinner,
  Alert,
  AlertDescription,
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogAction,
  AlertDialogCancel,
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  Popover,
  PopoverTrigger,
  PopoverContent,
  Breadcrumbs,
  BreadcrumbItem,
  useToast,
} from '@nordlig/components';
import {
  ChevronRight,
  Calendar,
  Trash2,
  Pencil,
  EllipsisVertical,
  BookmarkPlus,
  RefreshCw,
  Download,
} from 'lucide-react';
import { format, parseISO } from 'date-fns';
import { de } from 'date-fns/locale';
import {
  trainingTypeLabels,
  trainingTypeBadgeVariant,
  trainingTypeHints,
} from '@/constants/training';
import { createTemplateFromSession } from '@/api/session-templates';
import { reparseSession, exportSessionFit } from '@/api/training';
import type { StrengthExercisesEditorRef } from '@/components/StrengthExercisesEditor';
import { generateInsights } from '@/utils/insights';
import type { InsightType } from '@/utils/insights';
import { useSessionData } from '@/hooks/useSessionData';
import { useSessionEditing } from '@/hooks/useSessionEditing';
import { useMapState } from '@/hooks/useMapState';
import {
  SessionMetricsGrid,
  SessionRouteSection,
  SessionHRZonesSection,
  SessionSplitsSection,
  SessionExercisesSection,
  SessionEditFields,
  SessionComparisonSection,
  SessionAIAnalysis,
} from '@/components/session-detail';
import { SessionEnvironmentSection } from '@/components/session-detail/SessionEnvironmentSection';

const workoutTypeHeadings: Record<string, string> = {
  running: 'Lauftraining',
  strength: 'Krafttraining',
};

function formatDateShort(dateStr: string): string {
  try {
    return format(parseISO(dateStr), 'dd.MM.yyyy', { locale: de });
  } catch {
    return dateStr;
  }
}

const insightVariantMap: Record<InsightType, 'success' | 'warning' | 'info'> = {
  positive: 'success',
  warning: 'warning',
  neutral: 'info',
};

// eslint-disable-next-line max-lines-per-function, complexity -- page orchestrator with dialogs and layout
export function SessionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { toast } = useToast();
  const sessionId = Number(id);

  const exercisesEditorRef = useRef<StrengthExercisesEditorRef>(null);

  // Data loading
  const data = useSessionData(sessionId);
  const { session, loading, error, setError, gpsTrack, kmSplits, sessionGap, workingHrZones } =
    data;

  // Editing state + handlers
  const editing = useSessionEditing({
    sessionId,
    session,
    setSession: data.setSession,
    setError,
    localLaps: data.localLaps,
    setLocalLaps: data.setLocalLaps,
    setWorkingHrZones: data.setWorkingHrZones,
  });

  // Map state + computed values
  const map = useMapState({
    athleteRestingHr: session?.athlete_resting_hr,
    athleteMaxHr: session?.athlete_max_hr,
    gpsTrack,
    kmSplits,
    localLaps: data.localLaps,
  });

  const effectiveRpe = editing.localRpe ?? session?.rpe ?? null;
  const hrZones = session?.hr_zones;

  // Loading skeleton
  if (loading) {
    return (
      <div className="p-4 pt-6 md:p-6 md:pt-10 max-w-5xl mx-auto space-y-4 md:space-y-6">
        <Breadcrumbs separator={<ChevronRight className="w-3.5 h-3.5" />}>
          <BreadcrumbItem>
            <Link to="/sessions" className="hover:underline underline-offset-2">
              Sessions
            </Link>
          </BreadcrumbItem>
          <BreadcrumbItem isCurrent>Detail</BreadcrumbItem>
        </Breadcrumbs>
        <Card elevation="raised">
          <CardBody className="space-y-4">
            <div className="h-6 w-56 bg-[var(--color-bg-muted)] rounded animate-pulse" />
            <div className="border-t border-[var(--color-border-default)]" />
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-3">
              {[...Array(4)].map((_, i) => (
                <div
                  key={i}
                  className="rounded-[var(--radius-component-md)] bg-[var(--color-bg-paper)] px-3 py-3"
                >
                  <div className="h-4 w-16 bg-[var(--color-bg-muted)] rounded animate-pulse mb-2" />
                  <div className="h-7 w-20 bg-[var(--color-bg-muted)] rounded animate-pulse" />
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
        <Card elevation="raised">
          <CardBody className="flex items-center justify-center py-12">
            <Spinner size="lg" />
          </CardBody>
        </Card>
      </div>
    );
  }

  // Error state
  if (error && !session) {
    return (
      <div className="p-4 pt-6 md:p-6 md:pt-10 max-w-5xl mx-auto space-y-4 md:space-y-6">
        <Breadcrumbs separator={<ChevronRight className="w-3.5 h-3.5" />}>
          <BreadcrumbItem>
            <Link to="/sessions" className="hover:underline underline-offset-2">
              Sessions
            </Link>
          </BreadcrumbItem>
          <BreadcrumbItem isCurrent>Detail</BreadcrumbItem>
        </Breadcrumbs>
        <Alert variant="error">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  if (!session) return null;

  const insights = generateInsights(session);

  return (
    <div
      className={`p-4 pt-6 md:p-6 md:pt-10 max-w-5xl mx-auto space-y-4 md:space-y-6 ${editing.isEditing ? 'pb-20' : ''}`}
    >
      {/* Breadcrumbs + Header */}
      <div className="space-y-1">
        <Breadcrumbs separator={<ChevronRight className="w-3.5 h-3.5" />}>
          <BreadcrumbItem>
            <Link to="/sessions" className="hover:underline underline-offset-2">
              Sessions
            </Link>
          </BreadcrumbItem>
          <BreadcrumbItem isCurrent>Detail</BreadcrumbItem>
        </Breadcrumbs>

        <header className="flex items-center justify-between gap-2">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
              <h1 className="text-xl sm:text-2xl font-semibold text-[var(--color-text-base)]">
                {workoutTypeHeadings[session.workout_type] || session.workout_type}{' '}
                {formatDateShort(session.date)}
              </h1>
              {editing.trainingTypeInfo?.effective && (
                <Popover>
                  <PopoverTrigger asChild>
                    {/* prettier-ignore */}
                    <button type="button" className="cursor-pointer">{/* ds-ok: Radix PopoverTrigger asChild */}
                      <Badge
                        variant={
                          trainingTypeBadgeVariant[editing.trainingTypeInfo.effective] ?? 'neutral'
                        }
                        size="xs"
                      >
                        {trainingTypeLabels[editing.trainingTypeInfo.effective] ??
                          editing.trainingTypeInfo.effective}
                      </Badge>
                    </button>
                  </PopoverTrigger>
                  <PopoverContent side="bottom" showArrow className="text-xs leading-relaxed">
                    {trainingTypeHints[editing.trainingTypeInfo.effective] ?? ''}
                  </PopoverContent>
                </Popover>
              )}
            </div>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger>
              <Button variant="ghost" size="sm" aria-label="Aktionen" className="shrink-0">
                <EllipsisVertical className="w-4 h-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                icon={<Pencil />}
                disabled={editing.isEditing}
                onSelect={() => editing.setIsEditing(true)}
              >
                Bearbeiten
              </DropdownMenuItem>
              <DropdownMenuItem
                icon={<BookmarkPlus />}
                onSelect={async () => {
                  try {
                    await createTemplateFromSession(Number(id));
                    toast({
                      title: 'Template erstellt',
                      description: 'Session wurde als Template gespeichert.',
                      variant: 'success',
                    });
                  } catch {
                    toast({
                      title: 'Fehler',
                      description: 'Template konnte nicht erstellt werden.',
                      variant: 'error',
                    });
                  }
                }}
              >
                Als Template speichern
              </DropdownMenuItem>
              {session?.workout_type === 'running' && (
                <DropdownMenuItem
                  icon={<Download />}
                  onSelect={async () => {
                    try {
                      await exportSessionFit(Number(id));
                    } catch {
                      toast({
                        title: 'Fehler',
                        description: 'FIT-Export fehlgeschlagen.',
                        variant: 'error',
                      });
                    }
                  }}
                >
                  Als FIT exportieren
                </DropdownMenuItem>
              )}
              <DropdownMenuItem
                icon={<RefreshCw />}
                onSelect={async () => {
                  try {
                    const result = await reparseSession(Number(id));
                    toast({
                      title: 'Neu analysiert',
                      description: `${result.changes.laps_count} Laps, HR ø${result.changes.hr_avg ?? '-'} bpm`,
                      variant: 'success',
                    });
                    // Seite neu laden um aktualisierten Daten anzuzeigen
                    window.location.reload();
                  } catch (err) {
                    const msg = err instanceof Error ? err.message : 'Reparse fehlgeschlagen';
                    const isNoFile = typeof msg === 'string' && msg.includes('409');
                    toast({
                      title: 'Fehler',
                      description: isNoFile
                        ? 'Keine Originaldatei gespeichert. Bitte neu hochladen.'
                        : msg,
                      variant: 'error',
                    });
                  }
                }}
              >
                Neu analysieren
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                icon={<Trash2 />}
                destructive
                onSelect={() => editing.setShowDeleteConfirm(true)}
              >
                Löschen
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </header>
      </div>

      {/* Delete confirmation dialog */}
      <AlertDialog open={editing.showDeleteConfirm} onOpenChange={editing.setShowDeleteConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Session löschen?</AlertDialogTitle>
            <AlertDialogDescription>
              Diese Aktion kann nicht rückgängig gemacht werden. Alle Daten dieser Trainingseinheit
              werden unwiderruflich gelöscht.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Abbrechen</AlertDialogCancel>
            <AlertDialogAction onClick={editing.handleDelete} disabled={editing.deleting}>
              {editing.deleting ? <Spinner size="sm" /> : 'Löschen'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Error banner */}
      {error && (
        <Alert variant="error" closeable onClose={() => setError(null)}>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Edit fields + Recalculate dialog */}
      {editing.isEditing && (
        <SessionEditFields
          session={session}
          editing={editing}
          effectiveRpe={effectiveRpe}
          hrZones={hrZones}
        />
      )}

      {/* Metrics */}
      <SessionMetricsGrid session={session} sessionGap={sessionGap} effectiveRpe={effectiveRpe} />

      {/* Insights — nur als Fallback wenn keine KI-Analyse vorhanden */}
      {insights.length > 0 && !session.ai_analysis && (
        <section aria-label="Insights">
          <Card elevation="raised">
            <CardHeader>
              <h2 className="text-sm font-semibold text-[var(--color-text-base)]">Insights</h2>
            </CardHeader>
            <CardBody>
              <div className="space-y-2 break-words">
                {insights.map((insight, i) => (
                  <Alert key={i} variant={insightVariantMap[insight.type]}>
                    <AlertDescription>{insight.message}</AlertDescription>
                  </Alert>
                ))}
              </div>
            </CardBody>
          </Card>
        </section>
      )}

      {/* KI-Analyse (#32) */}
      <SessionAIAnalysis
        sessionId={sessionId}
        cachedAnalysis={session.ai_analysis ?? null}
        onAnalysisLoaded={(analysis) =>
          data.setSession((prev) => (prev ? { ...prev, ai_analysis: analysis } : prev))
        }
      />

      {/* Exercises (Strength) */}
      {session.exercises && session.exercises.length > 0 && (
        <SessionExercisesSection
          exercises={session.exercises}
          sessionId={sessionId}
          isEditing={editing.isEditing}
          editorRef={exercisesEditorRef}
        />
      )}

      {/* GPS Route Map + Elevation Profile */}
      {gpsTrack && gpsTrack.points.length > 0 && (
        <SessionRouteSection
          gpsTrack={gpsTrack}
          elevationCorrected={session.elevation_corrected}
          map={map}
          onKmMarkerClick={(km) => {
            map.setSplitsTab('km');
            map.setHighlightedKm(km);
          }}
          onLapMarkerClick={(lap) => {
            map.setSplitsTab('laps');
            map.setHighlightedLap(lap);
          }}
        />
      )}

      {/* Umgebungsbedingungen (Wetter, Luftqualität, Location, Untergrund, Tageszeit) */}
      {(session.weather ||
        session.air_quality ||
        session.location_name ||
        session.surface ||
        session.daytime_tag) && (
        <SessionEnvironmentSection
          weather={session.weather}
          airQuality={session.air_quality}
          locationName={session.location_name}
          surface={session.surface}
          daytimeTag={session.daytime_tag}
          daytimeLabel={session.daytime_label}
          sunrise={session.sunrise}
          sunset={session.sunset}
        />
      )}

      {/* HR Zones */}
      {hrZones && Object.keys(hrZones).length > 0 && (
        <SessionHRZonesSection hrZones={hrZones} workingHrZones={workingHrZones} />
      )}

      {/* Soll/Ist-Vergleich */}
      {data.comparison && <SessionComparisonSection comparison={data.comparison} />}

      {/* Laps / Km Splits */}
      {(data.localLaps.length > 0 || kmSplits) && (
        <SessionSplitsSection
          localLaps={data.localLaps}
          kmSplits={kmSplits}
          splitsTab={map.splitsTab}
          setSplitsTab={map.setSplitsTab}
          isEditing={editing.isEditing}
          savingLaps={editing.savingLaps}
          onLapTypeChange={editing.handleLapTypeChange}
          highlightedKm={map.highlightedKm}
          setHighlightedKm={map.setHighlightedKm}
          highlightedLap={map.highlightedLap}
          setHighlightedLap={map.setHighlightedLap}
        />
      )}

      {/* Notes */}
      <section aria-label="Notizen">
        <Card elevation="raised">
          <CardHeader className="flex flex-row items-center justify-between">
            <h2 className="text-sm font-semibold text-[var(--color-text-base)]">Notizen</h2>
            {editing.isEditing && editing.savingNotes && <Spinner size="sm" />}
          </CardHeader>
          <CardBody>
            {editing.isEditing ? (
              <Textarea
                value={editing.notes}
                onChange={editing.handleNotesChange}
                rows={3}
                placeholder="Wie hast du dich gefühlt? Notizen zum Training..."
              />
            ) : (
              <p className="text-sm text-[var(--color-text-base)]">
                {editing.notes || (
                  <span className="text-[var(--color-text-muted)]">Keine Notizen</span>
                )}
              </p>
            )}
          </CardBody>
        </Card>
      </section>

      {/* Footer */}
      <footer className="flex flex-wrap items-center justify-between gap-y-1 text-xs text-[var(--color-text-muted)]">
        <div className="flex items-center gap-1">
          <Calendar className="w-3 h-3" aria-hidden />
          <span>
            Erstellt:{' '}
            {session.created_at
              ? format(parseISO(session.created_at), 'dd.MM.yyyy HH:mm', { locale: de })
              : '-'}
          </span>
        </div>
        <span>Session #{session.id}</span>
      </footer>

      {/* Fixed edit mode bar */}
      {editing.isEditing && (
        <div
          role="toolbar"
          className="fixed bottom-[82px] lg:bottom-0 left-0 lg:left-[224px] right-0 z-40 bg-[var(--color-actionbar-bg)] border-t border-[var(--color-actionbar-border)] rounded-t-[var(--radius-actionbar)] [box-shadow:var(--shadow-actionbar-default)] px-[var(--spacing-actionbar-padding-x)] py-[var(--spacing-actionbar-padding-y)] flex items-center justify-between gap-[var(--spacing-actionbar-gap)]"
        >
          <span className="text-xs text-[var(--color-actionbar-text)] hidden sm:inline">
            Ungespeicherte Änderungen
          </span>
          <div className="flex gap-2 ml-auto">
            <Button variant="ghost" size="sm" onClick={() => editing.setIsEditing(false)}>
              Abbrechen
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={async () => {
                if (exercisesEditorRef.current) {
                  try {
                    const updated = await exercisesEditorRef.current.save();
                    if (updated) {
                      data.setSession((prev) => (prev ? { ...prev, exercises: updated } : prev));
                      toast({ title: 'Übungen gespeichert', variant: 'success' });
                    } else {
                      return;
                    }
                  } catch {
                    toast({ title: 'Speichern fehlgeschlagen', variant: 'error' });
                    return;
                  }
                }
                editing.setIsEditing(false);
              }}
            >
              Fertig
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
