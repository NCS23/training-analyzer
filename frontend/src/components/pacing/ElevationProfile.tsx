import { useRef } from 'react';
import { Button, useToast } from '@nordlig/components';
import { Upload, X } from 'lucide-react';
import type { ElevationSegment } from '@/api/pacing';
import { parseGpxElevation } from '@/api/pacing';
import { ElevationChart } from './ElevationChart';

interface ElevationProfileProps {
  segments: ElevationSegment[] | null;
  onSegmentsChange: (segments: ElevationSegment[] | null) => void;
  disabled?: boolean;
}

export function ElevationProfile({ segments, onSegmentsChange, disabled }: ElevationProfileProps) {
  const { toast } = useToast();
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      const parsed = await parseGpxElevation(file);
      if (parsed.length === 0) {
        toast({ title: 'Keine Höhendaten in der GPX-Datei gefunden', variant: 'error' });
        return;
      }
      onSegmentsChange(parsed);
    } catch {
      toast({ title: 'GPX-Datei konnte nicht gelesen werden', variant: 'error' });
    } finally {
      if (fileRef.current) fileRef.current.value = '';
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-[var(--color-text-base)]">
          Streckenprofil (GPX)
        </span>
        <div className="flex items-center gap-2">
          {segments && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onSegmentsChange(null)}
              disabled={disabled}
            >
              <X size={14} />
              Entfernen
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => fileRef.current?.click()}
            disabled={disabled}
          >
            <Upload size={14} />
            GPX hochladen
          </Button>
        </div>
      </div>

      <input
        ref={fileRef}
        type="file"
        accept=".gpx"
        onChange={handleFileChange}
        className="hidden"
        aria-label="GPX-Datei hochladen"
      />

      {segments && <ElevationChart segments={segments} />}
    </div>
  );
}
