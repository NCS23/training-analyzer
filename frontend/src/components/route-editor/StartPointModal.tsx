/**
 * StartPointModal — Startpunkt für Auto-Route aus Template wählen (#571).
 *
 * Kleine Leaflet-Karte: Klick = Startpunkt setzen, GPS-Button = aktueller Standort.
 */

import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import {
  Button,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  Spinner,
} from '@nordlig/components';
import { MapPin, Navigation, Zap } from 'lucide-react';
import { TILES } from '@/features/maps/tileStyles';

interface StartPointModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  templateName: string;
  loading: boolean;
  onConfirm: (lat: number, lng: number) => void;
}

const DEFAULT_CENTER: L.LatLngTuple = [53.55, 9.99]; // Hamburg

function useStartPointMap(open: boolean, containerRef: React.RefObject<HTMLDivElement | null>) {
  const mapRef = useRef<L.Map | null>(null);
  const markerRef = useRef<L.Marker | null>(null);
  const [selectedPos, setSelectedPos] = useState<{ lat: number; lng: number } | null>(null);

  const setPoint = (map: L.Map, lat: number, lng: number) => {
    markerRef.current?.remove();
    const icon = L.divIcon({
      className: '',
      html: `<div style="width:16px;height:16px;border-radius:50%;background:#3b82f6;border:3px solid #fff;box-shadow:0 0 4px rgba(0,0,0,0.4)"></div>`,
      iconSize: [16, 16],
      iconAnchor: [8, 8],
    });
    markerRef.current = L.marker([lat, lng], { icon }).addTo(map);
    setSelectedPos({ lat, lng });
  };

  useEffect(() => {
    if (!open || !containerRef.current) return;

    const map = L.map(containerRef.current, { center: DEFAULT_CENTER, zoom: 13 });
    L.tileLayer(TILES.streets.url, { attribution: TILES.streets.attribution, maxZoom: 19 }).addTo(
      map,
    );
    map.on('click', (e: L.LeafletMouseEvent) => setPoint(map, e.latlng.lat, e.latlng.lng));
    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
      markerRef.current = null;
      setSelectedPos(null);
    };
  }, [open]); // eslint-disable-line react-hooks/exhaustive-deps

  return { mapRef, selectedPos, setPoint };
}

export function StartPointModal({
  open,
  onOpenChange,
  templateName,
  loading,
  onConfirm,
}: StartPointModalProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const { mapRef, selectedPos, setPoint } = useStartPointMap(open, containerRef);
  const [gpsLoading, setGpsLoading] = useState(false);

  const handleGps = () => {
    if (!navigator.geolocation || !mapRef.current) return;
    setGpsLoading(true);
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        if (mapRef.current) {
          mapRef.current.setView([coords.latitude, coords.longitude], 14);
          setPoint(mapRef.current, coords.latitude, coords.longitude);
        }
        setGpsLoading(false);
      },
      () => setGpsLoading(false),
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <MapPin className="w-4 h-4" />
            Startpunkt wählen
          </DialogTitle>
        </DialogHeader>

        <p className="text-sm text-[var(--color-text-muted)]">
          Klicke auf die Karte, um den Startpunkt für{' '}
          <span className="font-medium text-[var(--color-text-base)]">{templateName}</span> zu
          setzen.
        </p>

        <div
          ref={containerRef}
          className="w-full rounded-[var(--radius-md)] overflow-hidden border border-[var(--color-border-default)]"
          style={{ height: '280px' }}
        />

        <div className="flex items-center justify-between gap-3">
          <Button
            variant="secondary"
            size="sm"
            onClick={handleGps}
            disabled={gpsLoading || loading}
          >
            {gpsLoading ? (
              <Spinner size="sm" />
            ) : (
              <>
                <Navigation className="w-4 h-4 mr-1.5" />
                Aktueller Standort
              </>
            )}
          </Button>
          <div className="flex gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => onOpenChange(false)}
              disabled={loading}
            >
              Abbrechen
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => selectedPos && onConfirm(selectedPos.lat, selectedPos.lng)}
              disabled={!selectedPos || loading}
            >
              {loading ? (
                <Spinner size="sm" />
              ) : (
                <>
                  <Zap className="w-4 h-4 mr-1.5" />
                  Route generieren
                </>
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
