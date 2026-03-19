import {
  Card,
  CardHeader,
  CardBody,
  Select,
  SegmentedControl,
  Checkbox,
} from '@nordlig/components';
import { RouteMap, ElevationProfile, MapLegend, MAP_TILE_LABELS } from '@/features/maps';
import type { MapTileStyle } from '@/features/maps';
import type { HeatMapMode } from '@/utils/colorScale';
import type { GPSTrack } from '@/api/training';
import type { MapState } from '@/hooks/useMapState';

interface SessionRouteSectionProps {
  gpsTrack: GPSTrack;
  elevationCorrected?: boolean;
  map: Pick<
    MapState,
    | 'tileStyle'
    | 'setTileStyle'
    | 'mapMode'
    | 'setMapMode'
    | 'hoveredPointIndex'
    | 'setHoveredPointIndex'
    | 'showKmMarkers'
    | 'setShowKmMarkers'
    | 'showLapMarkers'
    | 'setShowLapMarkers'
    | 'mapSegments'
    | 'paceRange'
    | 'kmMarkerData'
    | 'lapMarkerData'
    | 'hrZoneBoundaries'
    | 'canShowHR'
    | 'highlightedKm'
    | 'highlightedLap'
  >;
  onKmMarkerClick: (km: number) => void;
  onLapMarkerClick: (lap: number) => void;
}

function RouteTitle({ corrected }: { corrected?: boolean }) {
  return (
    <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
      Route
      {corrected && (
        <span className="ml-2 text-[10px] font-normal text-[var(--color-text-info)]">
          (Höhendaten ergänzt)
        </span>
      )}
    </h2>
  );
}

export function SessionRouteSection({
  gpsTrack,
  elevationCorrected,
  map,
  onKmMarkerClick,
  onLapMarkerClick,
}: SessionRouteSectionProps) {
  return (
    <section aria-label="GPS Route">
      <Card elevation="raised">
        <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <RouteTitle corrected={elevationCorrected} />
          <div className="flex flex-wrap items-center gap-2">
            <Select
              options={Object.entries(MAP_TILE_LABELS).map(([value, label]) => ({
                value,
                label,
              }))}
              value={map.tileStyle}
              onChange={(val) => {
                if (val) map.setTileStyle(val as MapTileStyle);
              }}
              inputSize="sm"
              className="w-28 sm:w-32"
            />
            <SegmentedControl
              size="sm"
              value={map.mapMode}
              onChange={(val) => map.setMapMode(val as HeatMapMode)}
              items={[
                { value: 'route', label: 'Route' },
                { value: 'pace', label: 'Pace' },
                { value: 'hr', label: 'HF', disabled: !map.canShowHR },
              ]}
            />
          </div>
        </CardHeader>
        <CardBody className="space-y-4">
          <RouteMap
            points={gpsTrack.points}
            height="350px"
            tileStyle={map.tileStyle}
            hoveredPointIndex={map.hoveredPointIndex}
            onHoverPoint={map.setHoveredPointIndex}
            mode={map.mapMode}
            segments={map.mapSegments}
            kmMarkers={map.kmMarkerData}
            showKmMarkers={map.showKmMarkers}
            lapMarkers={map.lapMarkerData}
            showLapMarkers={map.showLapMarkers}
            onKmMarkerClick={onKmMarkerClick}
            onLapMarkerClick={onLapMarkerClick}
            highlightedKm={map.highlightedKm}
            highlightedLap={map.highlightedLap}
          />
          {/* Legend + Marker toggles */}
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-[var(--color-text-muted)]">
            {map.mapMode === 'pace' && map.paceRange && (
              <MapLegend mode="pace" minPace={map.paceRange.min} maxPace={map.paceRange.max} />
            )}
            {map.mapMode === 'hr' && map.hrZoneBoundaries && (
              <MapLegend mode="hr" zones={map.hrZoneBoundaries} />
            )}
            {map.kmMarkerData && map.kmMarkerData.length > 0 && (
              <label className="inline-flex items-center gap-1.5 cursor-pointer py-1">
                <Checkbox
                  checked={map.showKmMarkers}
                  onCheckedChange={(checked) => map.setShowKmMarkers(checked === true)}
                />
                <span>Km-Marker</span>
              </label>
            )}
            {map.lapMarkerData && map.lapMarkerData.length > 0 && (
              <label className="inline-flex items-center gap-1.5 cursor-pointer py-1">
                <Checkbox
                  checked={map.showLapMarkers}
                  onCheckedChange={(checked) => map.setShowLapMarkers(checked === true)}
                />
                <span>Lap-Marker</span>
              </label>
            )}
          </div>
          <ElevationProfile
            points={gpsTrack.points}
            totalAscentM={gpsTrack.total_ascent_m}
            totalDescentM={gpsTrack.total_descent_m}
            onHoverPoint={map.setHoveredPointIndex}
            hoveredPointIndex={map.hoveredPointIndex}
          />
        </CardBody>
      </Card>
    </section>
  );
}
