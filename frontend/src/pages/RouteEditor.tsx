/**
 * Route-Editor Seite — Trainingsrouten auf der Karte erstellen/bearbeiten.
 *
 * Part of Epic #508, Story #527.
 */

import { useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  Button,
  Card,
  CardBody,
  Input,
  Breadcrumbs,
  BreadcrumbItem,
  Spinner,
  useToast,
} from '@nordlig/components';
import { ChevronRight, Save, Mountain, Ruler, MapPin } from 'lucide-react';
import { RouteEditorMap } from '@/features/maps/RouteEditorMap';
import { useRouteEditor } from '@/hooks/useRouteEditor';
import type { UseRouteEditorReturn } from '@/hooks/useRouteEditor';

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

function EditorActionBar({
  editor,
  onSave,
  onCancel,
}: {
  editor: UseRouteEditorReturn;
  onSave: () => void;
  onCancel: () => void;
}) {
  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 border-t border-[var(--color-border-default)] bg-[var(--color-bg-surface)] px-4 py-3 flex items-center justify-end gap-3">
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
  );
}

export function RouteEditorPage() {
  const { routeId } = useParams<{ routeId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const isNew = !routeId;
  const editor = useRouteEditor();

  useEffect(() => {
    if (routeId) {
      editor.loadRoute(Number(routeId)).catch(() => {
        toast({ title: 'Route konnte nicht geladen werden', variant: 'error' });
        navigate('/plan/routes');
      });
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
      />

      {editor.routePoints.length > 1 && (
        <Card>
          <CardBody>
            <h3 className="text-sm font-medium text-[var(--color-text-base)] mb-2">Höhenprofil</h3>
            <div className="text-xs text-[var(--color-text-muted)]">
              Höhenprofil wird nach Integration mit Elevation API angezeigt.
            </div>
          </CardBody>
        </Card>
      )}

      <EditorActionBar
        editor={editor}
        onSave={handleSave}
        onCancel={() => navigate('/plan/routes')}
      />
      <div className="h-16" />
    </div>
  );
}
