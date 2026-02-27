import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import {
  getSession,
  getSessionTrack,
  getWorkingZones,
  getKmSplits,
  recalculateSessionZones,
  deleteSession,
  updateSessionNotes,
  updateSessionDate,
  updateTrainingType,
  updateLapOverrides,
} from '@/api/training';
import type {
  SessionDetail,
  LapDetail,
  HRZone,
  TrainingTypeInfo,
  GPSTrack,
  KmSplit,
} from '@/api/training';
import { RouteMap, ElevationProfile, MapLegend, MAP_TILE_LABELS } from '@/features/maps';
import type { MapTileStyle } from '@/features/maps';
import type { HeatMapMode } from '@/utils/colorScale';
import { computeHRZoneBoundaries } from '@/utils/colorScale';
import { buildPaceSegments, buildHRSegments } from '@/utils/segmentBuilder';
import type { KmMarkerData, LapMarkerData } from '@/utils/mapMarkers';
import {
  trainingTypeLabels,
  trainingTypeBadgeVariant,
  trainingTypeOptions,
  lapTypeLabels,
  lapTypeOptions,
} from '@/constants/training';
import {
  Button,
  Card,
  CardHeader,
  CardBody,
  Badge,
  Select,
  Textarea,
  Spinner,
  Alert,
  AlertDescription,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogAction,
  AlertDialogCancel,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DatePicker,
  Input,
  Label,
  ToggleGroup,
  ToggleGroupItem,
  useToast,
} from '@nordlig/components';
import {
  ArrowLeft,
  Calendar,
  Trash2,
  Check,
  Pencil,
  EllipsisVertical,
  Clock,
  MapPin,
  Timer,
  Heart,
  HeartPulse,
  Footprints,
  RefreshCw,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { format, parseISO } from 'date-fns';
import { de } from 'date-fns/locale';
import { generateInsights } from '@/utils/insights';
import type { InsightType } from '@/utils/insights';

const workoutTypeHeadings: Record<string, string> = {
  running: 'Lauftraining',
  strength: 'Krafttraining',
};

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }
  return `${minutes}:${String(secs).padStart(2, '0')}`;
}

function formatDateShort(dateStr: string): string {
  try {
    return format(parseISO(dateStr), 'dd.MM.yyyy', { locale: de });
  } catch {
    return dateStr;
  }
}

/** Fallback colors for 3-zone model (no Karvonen data). */
function fallbackZoneColor(key: string): string {
  if (key.includes('recovery') || key.includes('zone_1')) return '#94a3b8';
  if (key.includes('base') || key.includes('zone_2')) return '#10b981';
  return '#f59e0b';
}

export function SessionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { toast } = useToast();
  const sessionId = Number(id);

  const [session, setSession] = useState<SessionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Notes state
  const [notes, setNotes] = useState('');

  const [savingNotes, setSavingNotes] = useState(false);
  const notesTimer = useRef<ReturnType<typeof setTimeout>>();

  // Delete state
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // Training type state
  const [trainingTypeInfo, setTrainingTypeInfo] = useState<TrainingTypeInfo | null>(null);
  const [savingTrainingType, setSavingTrainingType] = useState(false);

  // Date state
  const [savingDate, setSavingDate] = useState(false);

  // GPS track state
  const [gpsTrack, setGpsTrack] = useState<GPSTrack | null>(null);
  const [hoveredPointIndex, setHoveredPointIndex] = useState<number | null>(null);
  const [mapMode, setMapMode] = useState<HeatMapMode>('route');
  const [tileStyle, setTileStyle] = useState<MapTileStyle>(() => {
    try {
      const stored = localStorage.getItem('mapTileStyle');
      return (stored as MapTileStyle) || 'streets';
    } catch {
      return 'streets';
    }
  });

  // Km splits state
  const [kmSplits, setKmSplits] = useState<KmSplit[] | null>(null);
  const [splitsTab, setSplitsTab] = useState<'laps' | 'km'>('laps');

  // Map overlay markers
  const [showKmMarkers, setShowKmMarkers] = useState(true);
  const [showLapMarkers, setShowLapMarkers] = useState(true);
  const [highlightedKm, setHighlightedKm] = useState<number | null>(null);
  const [highlightedLap, setHighlightedLap] = useState<number | null>(null);

  // Edit mode — auto-open when laps need review
  const [isEditing, setIsEditing] = useState(false);
  const [localLaps, setLocalLaps] = useState<LapDetail[]>([]);
  const [workingHrZones, setWorkingHrZones] = useState<Record<string, HRZone> | null>(null);
  const [savingLaps, setSavingLaps] = useState(false);

  // Recalculate zones dialog
  const [showRecalcDialog, setShowRecalcDialog] = useState(false);
  const [recalcRestingHr, setRecalcRestingHr] = useState('');
  const [recalcMaxHr, setRecalcMaxHr] = useState('');
  const [recalculating, setRecalculating] = useState(false);

  const loadSession = useCallback(async () => {
    if (!sessionId || isNaN(sessionId)) {
      setError('Ungueltige Session-ID.');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const data = await getSession(sessionId);
      setSession(data);
      setNotes(data.notes || '');
      setTrainingTypeInfo(data.training_type);
      const loadedLaps = data.laps || [];
      setLocalLaps(loadedLaps);

      // Load GPS track + km splits if available
      if (data.has_gps) {
        try {
          const trackData = await getSessionTrack(sessionId);
          if (trackData.has_gps && trackData.track) {
            setGpsTrack(trackData.track);
          }
        } catch {
          // Silently fail — GPS track is optional
        }
        try {
          const splitsData = await getKmSplits(sessionId);
          if (splitsData.has_splits && splitsData.splits) {
            setKmSplits(splitsData.splits);
          }
        } catch {
          // Silently fail — km splits are optional
        }
      }

      // Fetch working HR zones (read-only) if laps have types
      const hasLapTypes = loadedLaps.some((l) => l.user_override || l.suggested_type);
      if (hasLapTypes && loadedLaps.length > 0) {
        try {
          const result = await getWorkingZones(sessionId);
          if (result.hr_zones_working) {
            setWorkingHrZones(result.hr_zones_working);
          }
        } catch {
          // Silently fail — working HR zones are optional
        }
      }
    } catch {
      setError('Session konnte nicht geladen werden.');
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    loadSession();
  }, [loadSession]);

  // Show toast after upload redirect
  useEffect(() => {
    if ((location.state as { uploaded?: boolean })?.uploaded) {
      // Clear state first to prevent duplicate toast in StrictMode
      window.history.replaceState({}, '');
      toast({ title: 'Training erfolgreich hochgeladen', variant: 'success' });
    }
  }, [location.state, toast]);

  // Persist tile style preference
  useEffect(() => {
    try {
      localStorage.setItem('mapTileStyle', tileStyle);
    } catch {
      // localStorage unavailable (e.g. test env)
    }
  }, [tileStyle]);

  // Auto-save notes with debounce
  const saveNotes = useCallback(
    async (value: string) => {
      if (!sessionId) return;
      setSavingNotes(true);
      try {
        await updateSessionNotes(sessionId, value || null);
        toast({ title: 'Notizen gespeichert', variant: 'success' });
      } catch {
        setError('Notizen konnten nicht gespeichert werden.');
      } finally {
        setSavingNotes(false);
      }
    },
    [sessionId, toast],
  );

  const handleNotesChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setNotes(value);

    if (notesTimer.current) clearTimeout(notesTimer.current);
    notesTimer.current = setTimeout(() => saveNotes(value), 1000);
  };

  // Delete
  const handleDelete = async () => {
    if (!sessionId) return;
    setDeleting(true);
    try {
      await deleteSession(sessionId);
      toast({ title: 'Session gelöscht', variant: 'success' });
      navigate('/sessions', { replace: true });
    } catch {
      setError('Session konnte nicht geloescht werden.');
      setDeleting(false);
    }
  };

  // Training type override
  const handleTrainingTypeOverride = async (newType: string | undefined) => {
    if (!sessionId || !newType) return;
    setSavingTrainingType(true);
    try {
      const result = await updateTrainingType(sessionId, newType);
      if (result.training_type) {
        setTrainingTypeInfo(result.training_type);
      }
      toast({ title: 'Trainingstyp gespeichert', variant: 'success' });
    } catch {
      setError('Training Type konnte nicht gespeichert werden.');
    } finally {
      setSavingTrainingType(false);
    }
  };

  // Date override
  const handleDateChange = async (newDate: Date | undefined) => {
    if (!sessionId || !newDate || !session) return;
    const dateStr = format(newDate, 'yyyy-MM-dd');
    if (dateStr === session.date) return;
    setSavingDate(true);
    try {
      const result = await updateSessionDate(sessionId, dateStr);
      setSession(result);
      toast({ title: 'Datum gespeichert', variant: 'success' });
    } catch {
      setError('Datum konnte nicht gespeichert werden.');
    } finally {
      setSavingDate(false);
    }
  };

  // Lap type override
  const handleLapTypeChange = async (lapNumber: number, newType: string | undefined) => {
    if (!sessionId || !newType) return;
    setSavingLaps(true);
    try {
      const overrides = localLaps.map((l) => ({
        lap_number: l.lap_number,
        user_override:
          l.lap_number === lapNumber
            ? newType
            : l.user_override || l.suggested_type || 'unclassified',
      }));
      const result = await updateLapOverrides({ sessionId, overrides });
      if (result.laps) {
        setLocalLaps(result.laps as unknown as LapDetail[]);
      }
      if (result.hr_zones_working) {
        setWorkingHrZones(result.hr_zones_working as Record<string, HRZone>);
      }
      toast({ title: 'Lap-Typ gespeichert', variant: 'success' });
    } catch {
      setError('Lap-Typ konnte nicht gespeichert werden.');
    } finally {
      setSavingLaps(false);
    }
  };

  // Open recalculate dialog with current session's stored HR values
  const openRecalcDialog = () => {
    setRecalcRestingHr(session?.athlete_resting_hr?.toString() ?? '');
    setRecalcMaxHr(session?.athlete_max_hr?.toString() ?? '');
    setShowRecalcDialog(true);
  };

  // Recalculate HR zones with user-specified values
  const handleRecalculateZones = async () => {
    if (!sessionId) return;
    const rhr = parseInt(recalcRestingHr, 10);
    const mhr = parseInt(recalcMaxHr, 10);
    if (isNaN(rhr) || isNaN(mhr) || rhr >= mhr) {
      toast({ title: 'Ruhe-HF muss kleiner als Max-HF sein', variant: 'error' });
      return;
    }
    setRecalculating(true);
    try {
      const result = await recalculateSessionZones(sessionId, { resting_hr: rhr, max_hr: mhr });
      if (result.hr_zones) {
        setSession((prev) =>
          prev
            ? {
                ...prev,
                hr_zones: result.hr_zones,
                athlete_resting_hr: result.athlete_resting_hr,
                athlete_max_hr: result.athlete_max_hr,
              }
            : prev,
        );
      }
      setShowRecalcDialog(false);
      toast({ title: 'HF-Zonen aktualisiert', variant: 'success' });
    } catch {
      toast({ title: 'Neuberechnung fehlgeschlagen', variant: 'error' });
    } finally {
      setRecalculating(false);
    }
  };

  // Heat map segment computation (must be before early returns)
  const hrZoneBoundaries = useMemo(() => {
    if (session?.athlete_resting_hr != null && session?.athlete_max_hr != null) {
      return computeHRZoneBoundaries(session.athlete_resting_hr, session.athlete_max_hr);
    }
    return null;
  }, [session?.athlete_resting_hr, session?.athlete_max_hr]);

  const mapSegments = useMemo(() => {
    if (!gpsTrack || gpsTrack.points.length < 2) return undefined;
    if (mapMode === 'pace') return buildPaceSegments(gpsTrack.points);
    if (mapMode === 'hr' && hrZoneBoundaries)
      return buildHRSegments(gpsTrack.points, hrZoneBoundaries);
    return undefined;
  }, [gpsTrack, mapMode, hrZoneBoundaries]);

  const paceRange = useMemo(() => {
    if (mapMode !== 'pace' || !mapSegments || mapSegments.length === 0) return null;
    const paces = mapSegments.map((s) => s.value);
    return { min: Math.min(...paces), max: Math.max(...paces) };
  }, [mapMode, mapSegments]);

  // Km marker data from splits (boundary coordinates)
  const kmMarkerData = useMemo((): KmMarkerData[] | undefined => {
    if (!kmSplits) return undefined;
    return kmSplits
      .filter((s) => s.boundary_lat != null && s.boundary_lng != null)
      .map((s) => ({
        km_number: s.km_number,
        lat: s.boundary_lat!,
        lng: s.boundary_lng!,
        pace_formatted: s.pace_formatted,
        pace_corrected_formatted: s.pace_corrected_formatted,
        avg_hr_bpm: s.avg_hr_bpm,
        duration_formatted: s.duration_formatted,
        elevation_gain_m: s.elevation_gain_m,
        elevation_loss_m: s.elevation_loss_m,
        is_partial: s.is_partial,
        distance_km: s.distance_km,
      }));
  }, [kmSplits]);

  // Lap marker data: correlate laps with GPS points via start_seconds
  const lapMarkerData = useMemo((): LapMarkerData[] | undefined => {
    if (!localLaps || localLaps.length === 0 || !gpsTrack) return undefined;
    const pts = gpsTrack.points;
    if (pts.length === 0) return undefined;

    return localLaps
      .filter((lap) => lap.start_seconds != null)
      .map((lap) => {
        const targetSec = lap.start_seconds!;
        // Binary search for nearest GPS point
        let lo = 0;
        let hi = pts.length - 1;
        while (lo < hi) {
          const mid = (lo + hi) >> 1;
          if (pts[mid].seconds < targetSec) lo = mid + 1;
          else hi = mid;
        }
        const pt = pts[lo];
        const type = lap.user_override || lap.suggested_type || 'unclassified';
        return {
          lap_number: lap.lap_number,
          lat: pt.lat,
          lng: pt.lng,
          type,
          pace_formatted: lap.pace_formatted,
          duration_formatted: lap.duration_formatted,
          avg_hr_bpm: lap.avg_hr_bpm,
          distance_km: lap.distance_km,
        };
      });
  }, [localLaps, gpsTrack]);

  // Loading state
  if (loading) {
    return (
      <div className="p-4 pt-6 md:p-6 md:pt-8 max-w-5xl mx-auto space-y-6">
        <nav>
          <button
            onClick={() => navigate('/sessions')}
            className="inline-flex items-center gap-1.5 text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text-base)] transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Sessions
          </button>
        </nav>
        <Card elevation="raised">
          <CardBody className="space-y-4">
            <div className="h-6 w-56 bg-[var(--color-bg-muted)] rounded animate-pulse" />
            <div className="border-t border-[var(--color-border-default)]" />
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[...Array(4)].map((_, i) => (
                <div
                  key={i}
                  className="rounded-[var(--radius-component-md)] bg-[var(--color-bg-surface)] px-3 py-3"
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
      <div className="p-4 pt-6 md:p-6 md:pt-8 max-w-5xl mx-auto space-y-6">
        <nav>
          <button
            onClick={() => navigate('/sessions')}
            className="inline-flex items-center gap-1.5 text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text-base)] transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Sessions
          </button>
        </nav>
        <Alert variant="error">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  if (!session) return null;

  const hrZones = session.hr_zones;

  // Collect all metrics into a flat list for a clean grid
  const metrics: { label: string; value: string; unit: string; icon: LucideIcon }[] = [];
  if (session.duration_sec != null)
    metrics.push({
      label: 'Dauer',
      value: formatDuration(session.duration_sec),
      unit: '',
      icon: Clock,
    });
  if (session.distance_km != null)
    metrics.push({
      label: 'Distanz',
      value: String(session.distance_km),
      unit: 'km',
      icon: MapPin,
    });
  if (session.pace) metrics.push({ label: 'Pace', value: session.pace, unit: '/km', icon: Timer });
  if (session.hr_avg != null)
    metrics.push({
      label: 'Ø Herzfrequenz',
      value: String(session.hr_avg),
      unit: 'bpm',
      icon: Heart,
    });
  if (session.hr_max != null)
    metrics.push({
      label: 'Max HF',
      value: String(session.hr_max),
      unit: 'bpm',
      icon: HeartPulse,
    });
  if (session.hr_min != null)
    metrics.push({
      label: 'Min HF',
      value: String(session.hr_min),
      unit: 'bpm',
      icon: HeartPulse,
    });
  if (session.cadence_avg != null)
    metrics.push({
      label: 'Ø Kadenz',
      value: String(session.cadence_avg),
      unit: 'spm',
      icon: Footprints,
    });

  const canShowHR = hrZoneBoundaries != null;

  return (
    <div className="p-4 pt-6 md:p-6 md:pt-8 max-w-5xl mx-auto space-y-6">
      {/* Back link */}
      <nav>
        <button
          onClick={() => navigate('/sessions')}
          className="inline-flex items-center gap-1.5 text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text-base)] transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Sessions
        </button>
      </nav>

      {/* Page header */}
      <header className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
            <h1 className="text-2xl md:text-3xl font-semibold text-[var(--color-text-base)]">
              {workoutTypeHeadings[session.workout_type] || session.workout_type}{' '}
              {formatDateShort(session.date)}
            </h1>
            {trainingTypeInfo?.effective && (
              <Badge
                variant={trainingTypeBadgeVariant[trainingTypeInfo.effective] ?? 'info'}
                size="xs"
              >
                {trainingTypeLabels[trainingTypeInfo.effective] ?? trainingTypeInfo.effective}
              </Badge>
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
              disabled={isEditing}
              onSelect={() => setIsEditing(true)}
            >
              Bearbeiten
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              icon={<Trash2 />}
              destructive
              onSelect={() => setShowDeleteConfirm(true)}
            >
              Löschen
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </header>

      {/* Delete confirmation dialog */}
      <AlertDialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
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
            <AlertDialogAction
              onClick={handleDelete}
              disabled={deleting}
              className="!bg-[var(--color-bg-error)] !text-[var(--color-text-on-error)]"
            >
              {deleting ? <Spinner size="sm" /> : 'Löschen'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Recalculate zones dialog */}
      <Dialog open={showRecalcDialog} onOpenChange={setShowRecalcDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>HF-Zonen neu berechnen</DialogTitle>
            <DialogDescription>
              Gib die Herzfrequenz-Werte ein, die fuer diese Session gelten sollen.
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
                value={recalcRestingHr}
                onChange={(e) => setRecalcRestingHr(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="recalc-max">Max-HF (bpm)</Label>
              <Input
                id="recalc-max"
                type="number"
                min={120}
                max={230}
                value={recalcMaxHr}
                onChange={(e) => setRecalcMaxHr(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="secondary" onClick={() => setShowRecalcDialog(false)}>
              Abbrechen
            </Button>
            <Button
              variant="primary"
              onClick={handleRecalculateZones}
              disabled={recalculating || !recalcRestingHr || !recalcMaxHr}
            >
              {recalculating ? <Spinner size="sm" /> : 'Berechnen'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit mode banner */}
      {isEditing && (
        <div className="flex items-center justify-between gap-2 rounded-[var(--radius-component-md)] bg-[var(--color-bg-info-subtle)] border border-[var(--color-border-info)] px-4 py-2">
          <span className="text-sm text-[var(--color-text-info)] flex items-center gap-1.5">
            <Pencil className="w-3.5 h-3.5 shrink-0" />
            Bearbeitungsmodus
          </span>
          <Button
            variant="secondary"
            size="sm"
            className="shrink-0 !border-[var(--color-border-info)] !text-[var(--color-text-info)]"
            onClick={() => setIsEditing(false)}
          >
            <Check className="w-3.5 h-3.5" />
            Fertig
          </Button>
        </div>
      )}

      {/* Error banner */}
      {error && (
        <Alert variant="error" closeable onClose={() => setError(null)}>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Edit fields — only in edit mode */}
      {isEditing && (
        <Card elevation="raised">
          <CardBody>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label>Datum</Label>
                {savingDate ? (
                  <Spinner size="sm" />
                ) : (
                  <DatePicker
                    value={parseISO(session.date)}
                    onChange={handleDateChange}
                    inputSize="sm"
                  />
                )}
              </div>
              {session.workout_type === 'running' && (
                <div className="space-y-1.5">
                  <Label>Trainingstyp</Label>
                  {savingTrainingType ? (
                    <Spinner size="sm" />
                  ) : (
                    <Select
                      options={trainingTypeOptions}
                      value={trainingTypeInfo?.effective ?? undefined}
                      onChange={handleTrainingTypeOverride}
                      inputSize="sm"
                      placeholder="Typ ändern"
                    />
                  )}
                </div>
              )}
            </div>
          </CardBody>
        </Card>
      )}

      {/* Metrics */}
      <section aria-label="Kennzahlen">
        <Card elevation="raised">
          <CardBody>
            {/* Metrics grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {metrics.map((m) => (
                <div
                  key={m.label}
                  className="rounded-[var(--radius-component-md)] bg-[var(--color-bg-surface)] px-3 py-3"
                >
                  <div className="flex items-center gap-1.5 mb-1">
                    <m.icon
                      className="w-3.5 h-3.5 text-[var(--color-text-muted)]"
                      aria-hidden="true"
                    />
                    <p className="text-xs text-[var(--color-text-muted)]">{m.label}</p>
                  </div>
                  <p className="text-xl font-semibold text-[var(--color-text-base)] tabular-nums">
                    {m.value}
                    {m.unit && (
                      <span className="text-sm font-normal text-[var(--color-text-muted)] ml-1">
                        {m.unit}
                      </span>
                    )}
                  </p>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      </section>

      {/* GPS Route Map + Elevation Profile */}
      {gpsTrack && gpsTrack.points.length > 0 && (
        <section aria-label="GPS Route">
          <Card elevation="raised">
            <CardHeader className="flex flex-row items-center justify-between gap-2">
              <h2 className="text-sm font-semibold text-[var(--color-text-base)]">Route</h2>
              <div className="flex items-center gap-2">
                <Select
                  options={Object.entries(MAP_TILE_LABELS).map(([value, label]) => ({
                    value,
                    label,
                  }))}
                  value={tileStyle}
                  onChange={(val) => {
                    if (val) setTileStyle(val as MapTileStyle);
                  }}
                  inputSize="sm"
                  className="w-28"
                />
                <ToggleGroup
                  type="single"
                  variant="outline"
                  value={mapMode}
                  onValueChange={(val) => {
                    if (val) setMapMode(val as HeatMapMode);
                  }}
                  className="gap-0"
                >
                  <ToggleGroupItem value="route" className="text-xs px-2.5 py-1">
                    Route
                  </ToggleGroupItem>
                  <ToggleGroupItem value="pace" className="text-xs px-2.5 py-1">
                    Pace
                  </ToggleGroupItem>
                  <ToggleGroupItem
                    value="hr"
                    className="text-xs px-2.5 py-1"
                    disabled={!canShowHR}
                    title={canShowHR ? undefined : 'HF-Daten (Ruhe-/Max-HF) fehlen'}
                  >
                    HF
                  </ToggleGroupItem>
                </ToggleGroup>
              </div>
            </CardHeader>
            {/* Overlay toggles */}
            {(kmMarkerData?.length || lapMarkerData?.length) && (
              <div className="flex items-center gap-4 px-[var(--spacing-card-padding-normal)] pb-1 text-xs text-[var(--color-text-muted)]">
                {kmMarkerData && kmMarkerData.length > 0 && (
                  <label className="inline-flex items-center gap-1.5 cursor-pointer py-1">
                    <input
                      type="checkbox"
                      checked={showKmMarkers}
                      onChange={(e) => setShowKmMarkers(e.target.checked)}
                      className="w-3.5 h-3.5 rounded accent-[var(--color-primary-1-500)]"
                    />
                    Km-Marker
                  </label>
                )}
                {lapMarkerData && lapMarkerData.length > 0 && (
                  <label className="inline-flex items-center gap-1.5 cursor-pointer py-1">
                    <input
                      type="checkbox"
                      checked={showLapMarkers}
                      onChange={(e) => setShowLapMarkers(e.target.checked)}
                      className="w-3.5 h-3.5 rounded accent-[var(--color-primary-1-500)]"
                    />
                    Lap-Marker
                  </label>
                )}
              </div>
            )}
            <CardBody className="space-y-4">
              <RouteMap
                points={gpsTrack.points}
                height="350px"
                tileStyle={tileStyle}
                hoveredPointIndex={hoveredPointIndex}
                onHoverPoint={setHoveredPointIndex}
                mode={mapMode}
                segments={mapSegments}
                kmMarkers={kmMarkerData}
                showKmMarkers={showKmMarkers}
                lapMarkers={lapMarkerData}
                showLapMarkers={showLapMarkers}
                onKmMarkerClick={(km) => {
                  setSplitsTab('km');
                  setHighlightedKm(km);
                }}
                onLapMarkerClick={(lap) => {
                  setSplitsTab('laps');
                  setHighlightedLap(lap);
                }}
                highlightedKm={highlightedKm}
                highlightedLap={highlightedLap}
              />
              {mapMode === 'pace' && paceRange && (
                <MapLegend mode="pace" minPace={paceRange.min} maxPace={paceRange.max} />
              )}
              {mapMode === 'hr' && hrZoneBoundaries && (
                <MapLegend mode="hr" zones={hrZoneBoundaries} />
              )}
              <ElevationProfile
                points={gpsTrack.points}
                totalAscentM={gpsTrack.total_ascent_m}
                totalDescentM={gpsTrack.total_descent_m}
                onHoverPoint={setHoveredPointIndex}
                hoveredPointIndex={hoveredPointIndex}
              />
            </CardBody>
          </Card>
        </section>
      )}

      {/* Insights */}
      {(() => {
        const insights = generateInsights(session);
        if (insights.length === 0) return null;

        const iconMap: Record<InsightType, string> = {
          positive: '✓',
          warning: '!',
          neutral: '→',
        };
        const colorMap: Record<InsightType, { bg: string; text: string; border: string }> = {
          positive: {
            bg: 'bg-[var(--color-bg-success-subtle)]',
            text: 'text-[var(--color-text-success)]',
            border: 'border-[var(--color-border-success)]',
          },
          warning: {
            bg: 'bg-[var(--color-bg-warning-subtle)]',
            text: 'text-[var(--color-text-warning)]',
            border: 'border-[var(--color-border-warning)]',
          },
          neutral: {
            bg: 'bg-[var(--color-bg-surface)]',
            text: 'text-[var(--color-text-muted)]',
            border: 'border-[var(--color-border-default)]',
          },
        };

        return (
          <section aria-label="Insights">
            <Card elevation="raised">
              <CardHeader>
                <h2 className="text-sm font-semibold text-[var(--color-text-base)]">Insights</h2>
              </CardHeader>
              <CardBody>
                <div className="space-y-2">
                  {insights.map((insight, i) => {
                    const colors = colorMap[insight.type];
                    return (
                      <div
                        key={i}
                        className={`flex items-start gap-2.5 rounded-[var(--radius-component-md)] border px-3 py-2.5 ${colors.bg} ${colors.border}`}
                      >
                        <span className={`text-xs font-bold shrink-0 mt-0.5 ${colors.text}`}>
                          {iconMap[insight.type]}
                        </span>
                        <p className="text-sm text-[var(--color-text-base)]">{insight.message}</p>
                      </div>
                    );
                  })}
                </div>
              </CardBody>
            </Card>
          </section>
        );
      })()}

      {/* HR Zones — side by side */}
      {hrZones && Object.keys(hrZones).length > 0 && (
        <section aria-label="Herzfrequenz-Zonen">
          <div
            className={`grid gap-5 ${workingHrZones ? 'grid-cols-1 md:grid-cols-2' : 'grid-cols-1'}`}
          >
            {/* Gesamt */}
            <Card elevation="raised">
              <CardHeader className="flex flex-row items-center justify-between">
                <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
                  HF-Zonen Gesamt
                </h2>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={openRecalcDialog}
                  aria-label="Zonen neu berechnen"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span className="text-xs">Aktualisieren</span>
                </Button>
              </CardHeader>
              <CardBody>
                <div className="space-y-3">
                  {Object.entries(hrZones).map(([key, zone]: [string, HRZone]) => (
                    <div key={key}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-[var(--color-text-muted)]">
                          {zone.name ? `${zone.name} (${zone.label})` : zone.label}
                        </span>
                        <span className="font-medium text-[var(--color-text-base)]">
                          {zone.percentage}%
                          {zone.seconds != null && (
                            <span className="text-[var(--color-text-muted)] ml-1">
                              ({formatDuration(zone.seconds)})
                            </span>
                          )}
                        </span>
                      </div>
                      <div className="h-1.5 w-full rounded-full bg-[var(--color-bg-subtle)]">
                        <div
                          className="h-full rounded-full transition-all duration-500 ease-out"
                          style={{
                            width: `${Math.min(zone.percentage, 100)}%`,
                            backgroundColor: zone.color ?? fallbackZoneColor(key),
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardBody>
            </Card>

            {/* Arbeitsbereich — only when available */}
            {workingHrZones && (
              <Card elevation="raised">
                <CardHeader>
                  <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
                    HF-Zonen Arbeitsbereich
                  </h2>
                </CardHeader>
                <CardBody>
                  <div className="space-y-3">
                    {Object.entries(workingHrZones).map(([key, zone]: [string, HRZone]) => (
                      <div key={key}>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-[var(--color-text-muted)]">
                            {zone.name ? `${zone.name} (${zone.label})` : zone.label}
                          </span>
                          <span className="font-medium text-[var(--color-text-base)]">
                            {zone.percentage}%
                            {zone.seconds != null && (
                              <span className="text-[var(--color-text-muted)] ml-1">
                                ({formatDuration(zone.seconds)})
                              </span>
                            )}
                          </span>
                        </div>
                        <div className="h-1.5 w-full rounded-full bg-[var(--color-bg-subtle)]">
                          <div
                            className="h-full rounded-full transition-all duration-500 ease-out"
                            style={{
                              width: `${Math.min(zone.percentage, 100)}%`,
                              backgroundColor: zone.color ?? fallbackZoneColor(key),
                            }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </CardBody>
              </Card>
            )}
          </div>
        </section>
      )}

      {/* Laps / Km Splits */}
      {(localLaps.length > 0 || kmSplits) && (
        <section aria-label="Laps">
          <Card elevation="raised">
            <CardHeader className="flex flex-row items-center justify-between">
              <div className="flex items-center gap-1">
                {localLaps.length > 0 && (
                  <button
                    onClick={() => setSplitsTab('laps')}
                    className={`text-sm font-semibold px-3 py-1 rounded-[var(--radius-component-sm)] transition-colors ${
                      splitsTab === 'laps'
                        ? 'bg-[var(--color-bg-muted)] text-[var(--color-text-base)]'
                        : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-base)]'
                    }`}
                  >
                    Geraete-Laps ({localLaps.length})
                  </button>
                )}
                {kmSplits && (
                  <button
                    onClick={() => setSplitsTab('km')}
                    className={`text-sm font-semibold px-3 py-1 rounded-[var(--radius-component-sm)] transition-colors ${
                      splitsTab === 'km'
                        ? 'bg-[var(--color-bg-muted)] text-[var(--color-text-base)]'
                        : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-base)]'
                    }`}
                  >
                    Kilometer ({kmSplits.length})
                  </button>
                )}
              </div>
              {isEditing && savingLaps && splitsTab === 'laps' && <Spinner size="sm" />}
            </CardHeader>

            {/* Device Laps Table */}
            {splitsTab === 'laps' && localLaps.length > 0 && (
              <div className="overflow-x-auto -mx-[var(--spacing-card-padding-normal)]">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-12 sticky left-0 z-10 bg-[var(--color-table-header-bg)]">
                        #
                      </TableHead>
                      <TableHead>Typ</TableHead>
                      <TableHead>Dauer</TableHead>
                      <TableHead>Distanz</TableHead>
                      <TableHead>Pace</TableHead>
                      <TableHead>Ø HF</TableHead>
                      <TableHead>Kadenz</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {localLaps.map((lap: LapDetail) => {
                      const effectiveType =
                        lap.user_override || lap.suggested_type || 'unclassified';
                      return (
                        <TableRow
                          key={lap.lap_number}
                          onMouseEnter={() => setHighlightedLap(lap.lap_number)}
                          onMouseLeave={() => setHighlightedLap(null)}
                          className={
                            highlightedLap === lap.lap_number
                              ? 'bg-[var(--color-bg-info-subtle)]'
                              : ''
                          }
                        >
                          <TableCell className="font-medium text-[var(--color-text-muted)] sticky left-0 z-10 bg-[var(--color-bg-elevated)]">
                            {lap.lap_number}
                          </TableCell>
                          <TableCell>
                            {isEditing ? (
                              <Select
                                options={lapTypeOptions}
                                value={effectiveType}
                                onChange={(val) => handleLapTypeChange(lap.lap_number, val)}
                                inputSize="sm"
                                className="w-36"
                              />
                            ) : (
                              <Badge
                                variant={
                                  effectiveType === 'warmup' || effectiveType === 'cooldown'
                                    ? 'info'
                                    : effectiveType === 'pause'
                                      ? 'warning'
                                      : effectiveType === 'interval'
                                        ? 'error'
                                        : 'success'
                                }
                                size="xs"
                              >
                                {lapTypeLabels[effectiveType] || effectiveType}
                              </Badge>
                            )}
                          </TableCell>
                          <TableCell>{lap.duration_formatted}</TableCell>
                          <TableCell>
                            {lap.distance_km != null ? `${lap.distance_km} km` : '-'}
                          </TableCell>
                          <TableCell>
                            {lap.pace_formatted ? `${lap.pace_formatted} /km` : '-'}
                          </TableCell>
                          <TableCell>
                            {lap.avg_hr_bpm != null ? `${lap.avg_hr_bpm}` : '-'}
                          </TableCell>
                          <TableCell>
                            {lap.avg_cadence_spm != null ? `${lap.avg_cadence_spm}` : '-'}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
            )}

            {/* Km Splits Table */}
            {splitsTab === 'km' && kmSplits && (
              <div className="overflow-x-auto -mx-[var(--spacing-card-padding-normal)]">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-12 sticky left-0 z-10 bg-[var(--color-table-header-bg)]">
                        km
                      </TableHead>
                      <TableHead>Dauer</TableHead>
                      <TableHead>Pace</TableHead>
                      <TableHead
                        title="Hoehenkorrigierter Pace: Bergauf-Laeufe erhalten Zeitgutschrift, Bergab-Laeufe Zeitabzug"
                      >
                        GAP
                      </TableHead>
                      <TableHead>Ø HF</TableHead>
                      <TableHead>Anstieg</TableHead>
                      <TableHead>Abstieg</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {kmSplits.map((split) => (
                      <TableRow
                        key={split.km_number}
                        onMouseEnter={() => setHighlightedKm(split.km_number)}
                        onMouseLeave={() => setHighlightedKm(null)}
                        className={
                          highlightedKm === split.km_number
                            ? 'bg-[var(--color-bg-info-subtle)]'
                            : ''
                        }
                      >
                        <TableCell className="font-medium text-[var(--color-text-muted)] sticky left-0 z-10 bg-[var(--color-bg-elevated)]">
                          {split.is_partial ? split.distance_km : split.km_number}
                        </TableCell>
                        <TableCell>{split.duration_formatted}</TableCell>
                        <TableCell>
                          {split.pace_formatted ? `${split.pace_formatted} /km` : '-'}
                        </TableCell>
                        <TableCell
                          title={split.pace_corrected_formatted ? 'Grade Adjusted Pace — korrigiert fuer Steigung/Gefaelle' : undefined}
                        >
                          {split.pace_corrected_formatted ? (
                            <span className="text-[var(--color-text-info)]">
                              {split.pace_corrected_formatted} /km
                            </span>
                          ) : (
                            '-'
                          )}
                        </TableCell>
                        <TableCell>{split.avg_hr_bpm ?? '-'}</TableCell>
                        <TableCell>
                          {split.elevation_gain_m != null ? `${split.elevation_gain_m} m` : '-'}
                        </TableCell>
                        <TableCell>
                          {split.elevation_loss_m != null ? `${split.elevation_loss_m} m` : '-'}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </Card>
        </section>
      )}

      {/* Notes */}
      <section aria-label="Notizen">
        <Card elevation="raised">
          <CardHeader className="flex flex-row items-center justify-between">
            <h2 className="text-sm font-semibold text-[var(--color-text-base)]">Notizen</h2>
            {isEditing && savingNotes && <Spinner size="sm" />}
          </CardHeader>
          <CardBody>
            {isEditing ? (
              <Textarea
                value={notes}
                onChange={handleNotesChange}
                rows={3}
                placeholder="Wie hast du dich gefuehlt? Notizen zum Training..."
              />
            ) : (
              <p className="text-sm text-[var(--color-text-base)]">
                {notes || <span className="text-[var(--color-text-muted)]">Keine Notizen</span>}
              </p>
            )}
          </CardBody>
        </Card>
      </section>

      {/* Session metadata */}
      <footer className="flex items-center justify-between text-xs text-[var(--color-text-muted)]">
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
    </div>
  );
}
