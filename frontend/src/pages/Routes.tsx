/**
 * Routen-Liste — Alle gespeicherten Trainingsrouten.
 *
 * Part of Epic #508, Story #527.
 */

import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  CardBody,
  Button,
  Badge,
  Spinner,
  EmptyState,
  Input,
  useToast,
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from '@nordlig/components';
import {
  Plus,
  EllipsisVertical,
  Trash2,
  Pencil,
  Star,
  MapPin,
  Mountain,
  Ruler,
} from 'lucide-react';
import { listRoutes, deleteRoute } from '@/api/routes';
import type { TrainingRouteSummary } from '@/api/routes';

function RouteCard({
  route,
  onEdit,
  onDelete,
}: {
  route: TrainingRouteSummary;
  onEdit: () => void;
  onDelete: () => void;
}) {
  return (
    <Card
      className="cursor-pointer hover:shadow-[var(--shadow-md)] transition-shadow motion-reduce:transition-none"
      onClick={onEdit}
    >
      <CardBody>
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="font-medium text-[var(--color-text-base)] truncate">{route.name}</h3>
              {route.is_favorite && (
                <Star className="w-4 h-4 text-[var(--color-text-warning)] fill-current flex-shrink-0" />
              )}
            </div>
            <div className="flex flex-wrap items-center gap-3 mt-1.5 text-xs text-[var(--color-text-muted)]">
              <span className="inline-flex items-center gap-1">
                <Ruler className="w-3.5 h-3.5" />
                {route.distance_km.toFixed(1)} km
              </span>
              <span className="inline-flex items-center gap-1">
                <Mountain className="w-3.5 h-3.5" />↑{route.elevation_gain_m}m
              </span>
              {route.location_name && (
                <span className="inline-flex items-center gap-1">
                  <MapPin className="w-3.5 h-3.5" />
                  {route.location_name}
                </span>
              )}
            </div>
            {route.tags && route.tags.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {route.tags.map((tag) => (
                  <Badge key={tag} variant="neutral" size="sm">
                    {tag}
                  </Badge>
                ))}
              </div>
            )}
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                onClick={(e) => e.stopPropagation()}
                className="p-1.5 rounded-[var(--radius-component-sm)] hover:bg-[var(--color-bg-subtle)] min-w-[44px] min-h-[44px] flex items-center justify-center"
              >
                <EllipsisVertical className="w-4 h-4 text-[var(--color-text-muted)]" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={(e) => {
                  e.stopPropagation();
                  onEdit();
                }}
              >
                <Pencil className="w-4 h-4 mr-2" />
                Bearbeiten
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete();
                }}
                className="text-[var(--color-text-error)]"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Löschen
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardBody>
    </Card>
  );
}

export function RoutesPage() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [routes, setRoutes] = useState<TrainingRouteSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  const loadRoutes = useCallback(
    async (q?: string) => {
      try {
        setLoading(true);
        const result = await listRoutes(q ? { search: q } : undefined);
        setRoutes(result.routes);
      } catch {
        toast({ title: 'Laden fehlgeschlagen', variant: 'error' });
      } finally {
        setLoading(false);
      }
    },
    [toast],
  );

  useEffect(() => {
    loadRoutes();
  }, [loadRoutes]);

  const handleDelete = async (id: number, name: string) => {
    try {
      await deleteRoute(id);
      toast({ title: `„${name}" gelöscht`, variant: 'success' });
      loadRoutes(search || undefined);
    } catch {
      toast({ title: 'Löschen fehlgeschlagen', variant: 'error' });
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div className="flex-1 max-w-xs">
          <Input
            placeholder="Route suchen…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && loadRoutes(search || undefined)}
          />
        </div>
        <Button variant="primary" onClick={() => navigate('/plan/routes/new')}>
          <Plus className="w-4 h-4 mr-1.5" />
          Neue Route
        </Button>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-12">
          <Spinner size="lg" />
        </div>
      )}

      {!loading && routes.length === 0 && (
        <EmptyState
          title="Keine Routen vorhanden"
          description="Erstelle deine erste Trainingsroute auf der Karte."
          action={
            <Button variant="primary" onClick={() => navigate('/plan/routes/new')}>
              <Plus className="w-4 h-4 mr-1.5" />
              Route erstellen
            </Button>
          }
        />
      )}

      {!loading && routes.length > 0 && (
        <div className="grid gap-3">
          {routes.map((route) => (
            <RouteCard
              key={route.id}
              route={route}
              onEdit={() => navigate(`/plan/routes/${route.id}`)}
              onDelete={() => handleDelete(route.id, route.name)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
