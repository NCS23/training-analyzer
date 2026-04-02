/**
 * Route-Detail/Editor Seite — Trainingsrouten ansehen und bearbeiten.
 *
 * Part of Epic #508, Story #527 + #532.
 * Layout folgt dem SessionDetail-Pattern: 3-stufige Breadcrumbs,
 * h1 + Kebab in flex-Zeile, MetricsGrid, Card-basierte Sektionen.
 */

import { useEffect, useState } from 'react';
import { useParams, useNavigate, useLocation, Link } from 'react-router-dom';
import type { RouteFromTemplatePreview } from '@/api/routes';
import {
  ActionBar,
  Button,
  Card,
  CardBody,
  CardHeader,
  Input,
  Breadcrumbs,
  BreadcrumbItem,
  Spinner,
  useToast,
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from '@nordlig/components';
import {
  ChevronRight,
  Save,
  Mountain,
  Ruler,
  MapPin,
  Wand2,
  Plus,
  Download,
  Pencil,
  Trash2,
  EllipsisVertical,
} from 'lucide-react';
import { RouteEditorMap } from '@/features/maps/RouteEditorMap';
import { useRouteEditor } from '@/hooks/useRouteEditor';
import { useSegmentEditor } from '@/hooks/useSegmentEditor';
import type { UseSegmentEditorReturn } from '@/hooks/useSegmentEditor';
import { SegmentBar } from '@/components/route-editor/SegmentBar';
import { SegmentTable } from '@/components/route-editor/SegmentTable';
import { PacingPanel } from '@/components/route-editor/PacingPanel';
import type { UseRouteEditorReturn } from '@/hooks/useRouteEditor';
import { exportRouteFit, exportRouteGpx, deleteRoute } from '@/api/routes';

// ---------------------------------------------------------------------------
// Metric tile — wie SessionMetricsGrid
// ---------------------------------------------------------------------------

type MetricTileProps = { label: string; value: string; icon: React.ElementType };

function MetricTile({ label, value, icon: Icon }: MetricTileProps) {
  return (
    <div className="rounded-[var(--radius-component-md)] bg-[var(--color-bg-paper)] border border-[var(--color-border-default)] px-2.5 py-2 sm:px-3.5 sm:py-3">
      <div className="flex items-center gap-1 mb-1 sm:mb-2">
        <Icon
          className="w-[10px] h-[10px] sm:w-[11px] sm:h-[11px] text-[var(--color-text-muted)]"
          aria-hidden="true"
        />
        <p className="text-[10px] sm:text-[11px] font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">
          {label}
        </p>
      </div>
      <p className="text-base sm:text-[22px] font-semibold text-[var(--color-text-base)] leading-none">
        {value}
      </p>
    </div>
  );
}

function RouteMetricsGrid({ editor }: { editor: UseRouteEditorReturn }) {
  return (
    <section aria-label="Routenkennzahlen">
      <Card elevation="raised">
        <CardBody>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            <MetricTile icon={Ruler} label="Distanz" value={`${editor.distanceKm.toFixed(1)} km`} />
            <MetricTile
              icon={Mountain}
              label="Höhenmeter"
              value={`↑${editor.elevationGainM}m ↓${editor.elevationLossM}m`}
            />
            <MetricTile icon={MapPin} label="Wegpunkte" value={String(editor.waypoints.length)} />
          </div>
        </CardBody>
      </Card>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Segment-Sektion
// ---------------------------------------------------------------------------

function SegmentSection({
  segEditor,
  distanceKm,
  routeId,
  isEditing,
}: {
  segEditor: UseSegmentEditorReturn;
  distanceKm: number;
  routeId: number | null;
  isEditing: boolean;
}) {
  if (distanceKm <= 0) return null;
  // Im Read-only ohne Segmente: nichts zeigen
  if (!isEditing && segEditor.segments.length === 0) return null;

  return (
    <>
      <Card elevation="raised">
        <CardHeader>
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
              Segmente{segEditor.segments.length > 0 ? ` (${segEditor.segments.length})` : ''}
            </h2>
            {isEditing && segEditor.segments.length === 0 && (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => segEditor.autoSegment(distanceKm)}
              >
                <Wand2 className="w-3.5 h-3.5 mr-1" />
                Auto-Segmentierung
              </Button>
            )}
            {isEditing && segEditor.segments.length > 0 && (
              <Button
                variant="secondary"
                size="sm"
                onClick={segEditor.addSegment}
                disabled={distanceKm <= 0}
              >
                <Plus className="w-3.5 h-3.5 mr-1" />
                Segment
              </Button>
            )}
          </div>
        </CardHeader>
        {/* SegmentBar innerhalb der Card — kein floatendes Element auf dem Hintergrund */}
        {segEditor.segments.length > 0 && (
          <SegmentBar
            segments={segEditor.segments}
            totalDistanceKm={distanceKm}
            onSegmentClick={segEditor.setActiveSegment}
            activeSegment={segEditor.activeSegment}
          />
        )}
        <CardBody>
          {segEditor.segments.length === 0 ? (
            <p className="text-sm text-[var(--color-text-muted)] text-center py-4">
              Noch keine Segmente. Klicke „Auto-Segmentierung" um die Route aufzuteilen.
            </p>
          ) : (
            <SegmentTable
              segments={segEditor.segments}
              totalDistanceKm={distanceKm}
              onUpdate={segEditor.updateSegment}
              onDelete={segEditor.deleteSegment}
              onAdd={segEditor.addSegment}
              activeSegment={segEditor.activeSegment}
              onSegmentClick={segEditor.setActiveSegment}
              readOnly={!isEditing}
            />
          )}
        </CardBody>
      </Card>

      {segEditor.segments.length > 0 && (
        <PacingPanel
          routeId={routeId}
          distanceKm={distanceKm}
          segments={segEditor.segments}
          onSegmentsUpdate={isEditing ? segEditor.setSegments : () => {}}
        />
      )}
    </>
  );
}

// ---------------------------------------------------------------------------
// Kebab-Menü
// ---------------------------------------------------------------------------

function RouteKebabMenu({
  routeId,
  routeName,
  onEdit,
  onDelete,
}: {
  routeId: number;
  routeName: string;
  onEdit: () => void;
  onDelete: () => void;
}) {
  const { toast } = useToast();

  const handleGpx = async () => {
    try {
      await exportRouteGpx(routeId, routeName);
    } catch {
      toast({ title: 'GPX-Export fehlgeschlagen', variant: 'error' });
    }
  };

  const handleFit = async () => {
    try {
      await exportRouteFit(routeId, routeName);
    } catch {
      toast({ title: 'FIT-Export fehlgeschlagen', variant: 'error' });
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger>
        <Button variant="ghost" size="sm" aria-label="Aktionen" className="shrink-0">
          <EllipsisVertical className="w-4 h-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem icon={<Pencil />} onSelect={onEdit}>
          Bearbeiten
        </DropdownMenuItem>
        <DropdownMenuItem icon={<Download />} onSelect={handleGpx}>
          Als GPX exportieren
        </DropdownMenuItem>
        <DropdownMenuItem icon={<Download />} onSelect={handleFit}>
          Als FIT exportieren
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem icon={<Trash2 />} destructive onSelect={onDelete}>
          Löschen
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

// ---------------------------------------------------------------------------
// ActionBar (Edit-Modus)
// ---------------------------------------------------------------------------

function EditActionBar({
  editor,
  onSave,
  onCancel,
}: {
  editor: UseRouteEditorReturn;
  onSave: () => void;
  onCancel: () => void;
}) {
  return (
    <ActionBar
      sticky={false}
      className="fixed bottom-[82px] lg:bottom-0 left-0 lg:left-[224px] right-0 z-40"
    >
      <div className="flex items-center justify-end gap-3 w-full">
        <Button variant="secondary" onClick={onCancel}>
          Abbrechen
        </Button>
        <Button
          variant="primary"
          onClick={onSave}
          disabled={editor.saving || editor.waypoints.length < 2 || !editor.name.trim()}
        >
          {editor.saving ? (
            <Spinner size="sm" />
          ) : (
            <>
              <Save className="w-4 h-4 mr-1.5" />
              Speichern
            </>
          )}
        </Button>
      </div>
    </ActionBar>
  );
}

// ---------------------------------------------------------------------------
// Seiten-Komponente
// ---------------------------------------------------------------------------

// eslint-disable-next-line max-lines-per-function -- Seiten-Orchestrator mit Read/Edit-Modus
export function RouteEditorPage() {
  const { routeId } = useParams<{ routeId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { toast } = useToast();
  const isNew = !routeId;
  const [isEditing, setIsEditing] = useState(isNew);
  const editor = useRouteEditor();
  const segEditor = useSegmentEditor();

  useEffect(() => {
    if (routeId) {
      editor.loadRoute(Number(routeId)).catch(() => {
        toast({ title: 'Route konnte nicht geladen werden', variant: 'error' });
        navigate('/plan/routes');
      });
      return;
    }
    const preview = (location.state as { routePreview?: RouteFromTemplatePreview } | null)
      ?.routePreview;
    if (preview) {
      editor.loadPreview(preview);
      segEditor.setSegments(preview.route_segments);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [routeId]);

  const handleSave = async () => {
    if (!editor.name.trim()) {
      toast({ title: 'Bitte einen Namen eingeben', variant: 'error' });
      return;
    }
    if (editor.waypoints.length < 2) {
      toast({ title: 'Mindestens 2 Wegpunkte setzen', variant: 'error' });
      return;
    }
    try {
      const id = await editor.save();
      if (id) {
        toast({ title: 'Route gespeichert', variant: 'success' });
        if (isNew) {
          navigate(`/plan/routes/${id}`);
        } else {
          setIsEditing(false);
        }
      }
    } catch {
      toast({ title: 'Speichern fehlgeschlagen', variant: 'error' });
    }
  };

  const handleDelete = async () => {
    if (!routeId) return;
    try {
      await deleteRoute(Number(routeId));
      toast({ title: 'Route gelöscht', variant: 'success' });
      navigate('/plan/routes');
    } catch {
      toast({ title: 'Löschen fehlgeschlagen', variant: 'error' });
    }
  };

  const handleCancelEdit = () => {
    if (isNew) {
      navigate('/plan/routes');
    } else {
      editor.loadRoute(Number(routeId)).catch(() => {});
      setIsEditing(false);
    }
  };

  if (editor.loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Spinner size="lg" />
      </div>
    );
  }

  const routeName = editor.name || 'Route';

  return (
    <div
      className={`p-4 pt-6 md:p-6 md:pt-10 max-w-5xl mx-auto space-y-4 md:space-y-6 ${isEditing ? 'pb-20' : ''}`}
    >
      {/* Breadcrumbs + Header — gleiche Struktur wie SessionDetail */}
      <div className="space-y-1">
        <Breadcrumbs separator={<ChevronRight className="w-3.5 h-3.5" />}>
          <BreadcrumbItem>
            <Link to="/plan">Plan</Link>
          </BreadcrumbItem>
          <BreadcrumbItem>
            <Link to="/plan/routes">Routen</Link>
          </BreadcrumbItem>
          <BreadcrumbItem isCurrent>{isNew ? 'Neue Route' : routeName}</BreadcrumbItem>
        </Breadcrumbs>

        {/* h1 ist immer statisch — kein Inline-Edit des Titels */}
        <header className="flex items-center justify-between gap-2 pb-2">
          <h1 className="text-xl sm:text-2xl font-semibold text-[var(--color-text-base)] truncate">
            {isNew ? 'Neue Route' : routeName}
          </h1>
          {!isNew && routeId && !isEditing && (
            <RouteKebabMenu
              routeId={Number(routeId)}
              routeName={routeName}
              onEdit={() => setIsEditing(true)}
              onDelete={handleDelete}
            />
          )}
          {isEditing && !isNew && (
            <Button variant="ghost" size="sm" onClick={handleCancelEdit}>
              Abbrechen
            </Button>
          )}
        </header>
      </div>

      {/* Kennzahlen — immer sichtbar */}
      <RouteMetricsGrid editor={editor} />

      {/* Edit-Modus: Routenname als eigenes Feld */}
      {isEditing && (
        <Card elevation="raised">
          <CardBody>
            <label className="block">
              <span className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-1.5 block">
                Routenname
              </span>
              <Input
                placeholder="z.B. Alsterrunde 21 km"
                value={editor.name}
                onChange={(e) => editor.setName(e.target.value)}
              />
            </label>
          </CardBody>
        </Card>
      )}

      {/* Karte in Card — wie SessionDetail: Card mit Padding, Map mit eigenem border-radius */}
      <Card elevation="raised">
        <CardBody>
          <div className="rounded-[var(--radius-component-md)] overflow-hidden">
            <RouteEditorMap
              waypoints={editor.waypoints}
              routePoints={editor.routePoints}
              onWaypointAdd={editor.addWaypoint}
              onWaypointMove={editor.moveWaypoint}
              onWaypointDelete={editor.deleteWaypoint}
              routing={editor.routing}
              height="52vh"
              segments={segEditor.segments}
              readOnly={!isEditing}
            />
          </div>
        </CardBody>
      </Card>

      {/* Segmente */}
      <SegmentSection
        segEditor={segEditor}
        distanceKm={editor.distanceKm}
        routeId={routeId ? Number(routeId) : null}
        isEditing={isEditing}
      />

      {isEditing && (
        <>
          <EditActionBar editor={editor} onSave={handleSave} onCancel={handleCancelEdit} />
          <div className="h-24 lg:h-16" />
        </>
      )}
    </div>
  );
}
