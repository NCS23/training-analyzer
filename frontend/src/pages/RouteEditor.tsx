/**
 * Route-Detail/Editor Seite — Trainingsrouten ansehen und bearbeiten.
 *
 * Part of Epic #508, Story #527 + #532.
 * Refactored: Read-only-Ansicht mit Kebab-Menü, Edit-Modus nur auf Anfrage.
 */

import { useEffect, useState } from 'react';
import { useParams, useNavigate, useLocation, Link } from 'react-router-dom';
import type { RouteFromTemplatePreview } from '@/api/routes';
import {
  ActionBar,
  Button,
  Card,
  CardBody,
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

function RouteMetrics({ editor }: { editor: UseRouteEditorReturn }) {
  return (
    <div className="flex items-center gap-4 text-sm text-[var(--color-text-muted)]">
      <span className="inline-flex items-center gap-1">
        <Ruler className="w-4 h-4" />
        {editor.distanceKm.toFixed(1)} km
      </span>
      <span className="inline-flex items-center gap-1">
        <Mountain className="w-4 h-4" />↑{editor.elevationGainM}m ↓{editor.elevationLossM}m
      </span>
      <span className="inline-flex items-center gap-1">
        <MapPin className="w-4 h-4" />
        {editor.waypoints.length} Punkte
      </span>
    </div>
  );
}

function SegmentSection({
  segEditor,
  distanceKm,
  routeId,
  readOnly,
}: {
  segEditor: UseSegmentEditorReturn;
  distanceKm: number;
  routeId: number | null;
  readOnly: boolean;
}) {
  if (distanceKm <= 0) return null;

  return (
    <>
      {segEditor.segments.length > 0 && (
        <SegmentBar
          segments={segEditor.segments}
          totalDistanceKm={distanceKm}
          onSegmentClick={segEditor.setActiveSegment}
          activeSegment={segEditor.activeSegment}
        />
      )}
      <Card elevation="raised">
        <CardBody className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-[var(--color-text-base)]">Segmente</h3>
            {!readOnly && segEditor.segments.length === 0 && (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => segEditor.autoSegment(distanceKm)}
              >
                <Wand2 className="w-3.5 h-3.5 mr-1" />
                Auto-Segmentierung
              </Button>
            )}
          </div>
          <SegmentTable
            segments={segEditor.segments}
            totalDistanceKm={distanceKm}
            onUpdate={readOnly ? () => {} : segEditor.updateSegment}
            onDelete={readOnly ? () => {} : segEditor.deleteSegment}
            onAdd={readOnly ? () => {} : segEditor.addSegment}
            activeSegment={segEditor.activeSegment}
            onSegmentClick={segEditor.setActiveSegment}
          />
        </CardBody>
      </Card>

      {segEditor.segments.length > 0 && (
        <PacingPanel
          routeId={routeId}
          distanceKm={distanceKm}
          segments={segEditor.segments}
          onSegmentsUpdate={readOnly ? () => {} : segEditor.setSegments}
        />
      )}
    </>
  );
}

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
        <Button variant="ghost" size="sm" aria-label="Aktionen">
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

  return (
    <div className="p-4 pt-6 md:p-6 md:pt-8 max-w-5xl mx-auto space-y-4">
      <header className="pb-2 space-y-2">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-2 flex-1 min-w-0">
            <Breadcrumbs separator={<ChevronRight className="w-3.5 h-3.5" />}>
              <BreadcrumbItem>
                <Link to="/plan/routes">Routen</Link>
              </BreadcrumbItem>
              <BreadcrumbItem isCurrent>
                {isNew ? 'Neue Route' : editor.name || 'Route'}
              </BreadcrumbItem>
            </Breadcrumbs>
            {!isEditing && (
              <h1 className="text-xl font-semibold text-[var(--color-text-base)] truncate">
                {editor.name}
              </h1>
            )}
          </div>
          {!isNew && routeId && (
            <RouteKebabMenu
              routeId={Number(routeId)}
              routeName={editor.name}
              onEdit={() => setIsEditing(true)}
              onDelete={handleDelete}
            />
          )}
        </div>
      </header>

      {isEditing && (
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1">
            <Input
              placeholder="Routenname"
              value={editor.name}
              onChange={(e) => editor.setName(e.target.value)}
            />
          </div>
          <RouteMetrics editor={editor} />
        </div>
      )}
      {!isEditing && (
        <Card elevation="raised">
          <CardBody>
            <RouteMetrics editor={editor} />
          </CardBody>
        </Card>
      )}

      <RouteEditorMap
        waypoints={editor.waypoints}
        routePoints={editor.routePoints}
        onWaypointAdd={editor.addWaypoint}
        onWaypointMove={editor.moveWaypoint}
        onWaypointDelete={editor.deleteWaypoint}
        routing={editor.routing}
        height="55vh"
        segments={segEditor.segments}
        readOnly={!isEditing}
      />

      <SegmentSection
        segEditor={segEditor}
        distanceKm={editor.distanceKm}
        routeId={routeId ? Number(routeId) : null}
        readOnly={!isEditing}
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
