/**
 * RoundTripModal — Rundkurs ab Startpunkt generieren (#578).
 *
 * Schritt 1: Startpunkt auf Karte wählen + Zieldistanz eingeben.
 * Schritt 2: Bis zu 3 Routen-Varianten auswählen.
 */

import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import {
  Button,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  Input,
  Label,
  Spinner,
} from '@nordlig/components';
import { MapPin, Navigation, Zap, ChevronRight } from 'lucide-react';
import { TILES } from '@/features/maps/tileStyles';
import { generateRoundTrip } from '@/api/routes';
import type { RoundTripOption } from '@/api/routes';

interface RoundTripModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelect: (option: RoundTripOption) => void;
  defaultDistanceKm?: number;
}

const DEFAULT_CENTER: L.LatLngTuple = [53.55, 9.99];

function useRoundTripMap(open: boolean, containerRef: React.RefObject<HTMLDivElement | null>) {
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

function OptionCard({
  option,
  selected,
  onSelect,
  index,
}: {
  option: RoundTripOption;
  selected: boolean;
  onSelect: () => void;
  index: number;
}) {
  const dirs = ['N', 'NO', 'O', 'SO', 'S', 'SW', 'W', 'NW'];
  const dirLabel = dirs[Math.round(option.direction_deg / 45) % 8];
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`w-full text-left p-3 rounded-[var(--radius-component-md)] border transition-colors duration-150 motion-reduce:transition-none ${
        selected
          ? 'border-[var(--color-border-focus)] bg-[var(--color-bg-primary-subtle)]'
          : 'border-[var(--color-border-default)] bg-[var(--color-bg-base)] hover:bg-[var(--color-bg-hover)]'
      }`}
    >
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-[var(--color-text-base)]">
          Option {index + 1} · {dirLabel}
        </span>
        <span className="text-sm text-[var(--color-text-muted)]">
          {option.distance_km.toFixed(1)} km
        </span>
      </div>
      <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
        Abweichung {option.deviation_percent.toFixed(0)}% vom Ziel
      </p>
    </button>
  );
}

function Step1({
  containerRef,
  distanceKm,
  onDistanceChange,
  selectedPos,
  gpsLoading,
  generating,
  onGps,
  onGenerate,
  onCancel,
}: {
  containerRef: React.RefObject<HTMLDivElement | null>;
  distanceKm: string;
  onDistanceChange: (v: string) => void;
  selectedPos: { lat: number; lng: number } | null;
  gpsLoading: boolean;
  generating: boolean;
  onGps: () => void;
  onGenerate: () => void;
  onCancel: () => void;
}) {
  return (
    <>
      <p className="text-sm text-[var(--color-text-muted)]">
        Wähle einen Startpunkt und gib die gewünschte Distanz ein.
      </p>
      <div
        ref={containerRef}
        className="w-full rounded-[var(--radius-md)] overflow-hidden border border-[var(--color-border-default)]"
        style={{ height: '240px' }}
      />
      <div className="flex items-end gap-3">
        <div className="flex-1">
          <Label
            htmlFor="round-trip-dist"
            className="mb-1.5 block text-xs font-medium text-[var(--color-text-muted)]"
          >
            Zieldistanz (km)
          </Label>
          <Input
            id="round-trip-dist"
            type="number"
            min="1"
            max="100"
            step="0.5"
            value={distanceKm}
            onChange={(e) => onDistanceChange(e.target.value)}
            inputSize="md"
          />
        </div>
        <Button variant="secondary" size="sm" onClick={onGps} disabled={gpsLoading || generating}>
          {gpsLoading ? <Spinner size="sm" /> : <Navigation className="w-4 h-4" />}
        </Button>
      </div>
      <div className="flex justify-end gap-2">
        <Button variant="secondary" size="sm" onClick={onCancel}>
          Abbrechen
        </Button>
        <Button
          variant="primary"
          size="sm"
          onClick={onGenerate}
          disabled={!selectedPos || generating || !parseFloat(distanceKm)}
        >
          {generating ? (
            <Spinner size="sm" />
          ) : (
            <>
              <Zap className="w-4 h-4 mr-1.5" />
              Generieren
            </>
          )}
        </Button>
      </div>
    </>
  );
}

function Step2({
  options,
  selectedIdx,
  onSelectIdx,
  onBack,
  onConfirm,
}: {
  options: RoundTripOption[];
  selectedIdx: number;
  onSelectIdx: (i: number) => void;
  onBack: () => void;
  onConfirm: () => void;
}) {
  return (
    <>
      <p className="text-sm text-[var(--color-text-muted)]">
        Wähle eine der generierten Routen aus.
      </p>
      <div className="space-y-2">
        {options.map((opt, i) => (
          <OptionCard
            key={i}
            option={opt}
            selected={i === selectedIdx}
            onSelect={() => onSelectIdx(i)}
            index={i}
          />
        ))}
      </div>
      <div className="flex justify-between gap-2">
        <Button variant="secondary" size="sm" onClick={onBack}>
          Zurück
        </Button>
        <Button variant="primary" size="sm" onClick={onConfirm}>
          <ChevronRight className="w-4 h-4 mr-1.5" />
          Route bearbeiten
        </Button>
      </div>
    </>
  );
}

export function RoundTripModal({
  open,
  onOpenChange,
  onSelect,
  defaultDistanceKm,
}: RoundTripModalProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const { mapRef, selectedPos, setPoint } = useRoundTripMap(open, containerRef);
  const [distanceKm, setDistanceKm] = useState(String(defaultDistanceKm ?? 10));
  const [gpsLoading, setGpsLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [options, setOptions] = useState<RoundTripOption[]>([]);
  const [selectedIdx, setSelectedIdx] = useState(0);

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

  const handleGenerate = async () => {
    if (!selectedPos) return;
    const km = parseFloat(distanceKm);
    if (!km || km <= 0) return;
    setGenerating(true);
    try {
      const result = await generateRoundTrip({
        start_lat: selectedPos.lat,
        start_lng: selectedPos.lng,
        target_distance_km: km,
        num_alternatives: 3,
      });
      setOptions(result.options);
      setSelectedIdx(0);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <MapPin className="w-4 h-4" />
            Rundkurs generieren
          </DialogTitle>
        </DialogHeader>

        {options.length === 0 ? (
          <Step1
            containerRef={containerRef}
            distanceKm={distanceKm}
            onDistanceChange={setDistanceKm}
            selectedPos={selectedPos}
            gpsLoading={gpsLoading}
            generating={generating}
            onGps={handleGps}
            onGenerate={handleGenerate}
            onCancel={() => onOpenChange(false)}
          />
        ) : (
          <Step2
            options={options}
            selectedIdx={selectedIdx}
            onSelectIdx={setSelectedIdx}
            onBack={() => setOptions([])}
            onConfirm={() => onSelect(options[selectedIdx])}
          />
        )}
      </DialogContent>
    </Dialog>
  );
}
