/**
 * Route-Editor Seite — Trainingsrouten auf der Karte erstellen/bearbeiten.
 *
 * Part of Epic #508, Story #527 + #532.
 */

import { useEffect } from 'react';
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
} from '@nordlig/components';
import { ChevronRight, Save, Mountain, Ruler, MapPin, Wand2, Download } from 'lucide-react';
import { RouteEditorMap } from '@/features/maps/RouteEditorMap';
import { useRouteEditor } from '@/hooks/useRouteEditor';
import { useSegmentEditor } from '@/hooks/useSegmentEditor';
import type { UseSegmentEditorReturn } from '@/hooks/useSegmentEditor';
import { SegmentBar } from '@/components/route-editor/SegmentBar';
import { SegmentTable } from '@/components/route-editor/SegmentTable';
import { PacingPanel } from '@/components/route-editor/PacingPanel';
import type { UseRouteEditorReturn } from '@/hooks/useRouteEditor';
import { exportRouteGpx } from '@/api/routes';

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
}: {
  segEditor: UseSegmentEditorReturn;
  distanceKm: number;
  routeId: number | null;
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
      <Card>
        <CardBody className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-[var(--color-text-base)]">Segmente</h3>
            {segEditor.segments.length === 0 && (
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
            onUpdate={segEditor.updateSegment}
            onDelete={segEditor.deleteSegment}
            onAdd={segEditor.addSegment}
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
          onSegmentsUpdate={segEditor.setSegments}
        />
      )}
    </>
  );
}

function EditorActionBar({
  editor,
  routeId,
  onSave,
  onCancel,
}: {
  editor: UseRouteEditorReturn;
  routeId: number | null;
  onSave: () => void;
  onCancel: () => void;
}) {
  const { toast } = useToast();

  const handleGpxDownload = async () => {
    if (!routeId) return;
    try {
      await exportRouteGpx(routeId, editor.name);
    } catch {
      toast({ title: 'GPX-Export fehlgeschlagen', variant: 'error' });
    }
  };

  return (
    <ActionBar
      sticky={false}
      className="fixed bottom-[82px] lg:bottom-0 left-0 lg:left-[224px] right-0 z-40"
    >
      <div className="flex items-center justify-end gap-3 w-full">
        <Button variant="secondary" onClick={onCancel}>
          Abbrechen
        </Button>
        {routeId && (
          <Button variant="secondary" onClick={handleGpxDownload}>
            <Download className="w-4 h-4 mr-1.5" />
            GPX
          </Button>
        )}
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

export function RouteEditorPage() {
  const { routeId } = useParams<{ routeId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { toast } = useToast();
  const isNew = !routeId;
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
    // Vorberechnete Route aus Session Template (#571)
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
        navigate(`/plan/routes/${id}`);
      }
    } catch {
      toast({ title: 'Speichern fehlgeschlagen', variant: 'error' });
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
        <Breadcrumbs separator={<ChevronRight className="w-3.5 h-3.5" />}>
          <BreadcrumbItem>
            <Link to="/plan/routes">Routen</Link>
          </BreadcrumbItem>
          <BreadcrumbItem isCurrent>
            {isNew ? 'Neue Route' : editor.name || 'Route bearbeiten'}
          </BreadcrumbItem>
        </Breadcrumbs>
      </header>

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

      <RouteEditorMap
        waypoints={editor.waypoints}
        routePoints={editor.routePoints}
        onWaypointAdd={editor.addWaypoint}
        onWaypointMove={editor.moveWaypoint}
        onWaypointDelete={editor.deleteWaypoint}
        routing={editor.routing}
        height="55vh"
        segments={segEditor.segments}
      />

      <SegmentSection
        segEditor={segEditor}
        distanceKm={editor.distanceKm}
        routeId={routeId ? Number(routeId) : null}
      />

      <EditorActionBar
        editor={editor}
        routeId={routeId ? Number(routeId) : null}
        onSave={handleSave}
        onCancel={() => navigate('/plan/routes')}
      />
      <div className="h-24 lg:h-16" />
    </div>
  );
}
