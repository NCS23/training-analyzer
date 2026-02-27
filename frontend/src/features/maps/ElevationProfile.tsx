import { useMemo, useCallback } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  ChartTooltip,
  ResponsiveContainer,
} from '@nordlig/components';
import { TrendingUp, TrendingDown, Mountain } from 'lucide-react';
import type { GPSPoint } from '@/api/training';
import { buildElevationProfile, smoothAltitude, getElevationSummary } from '@/utils/gpsUtils';
import type { ElevationDataPoint } from '@/utils/gpsUtils';

/* ------------------------------------------------------------------ */
/*  Props                                                              */
/* ------------------------------------------------------------------ */

export interface ElevationProfileProps {
  points: GPSPoint[];
  totalAscentM: number | null;
  totalDescentM: number | null;
  /** Called when user hovers on chart. pointIndex into GPSPoint[], or null. */
  onHoverPoint?: (pointIndex: number | null) => void;
  /** Currently hovered point index (from external source, e.g. map). */
  hoveredPointIndex?: number | null;
}

/* ------------------------------------------------------------------ */
/*  Custom Tooltip                                                     */
/* ------------------------------------------------------------------ */

interface TooltipPayloadItem {
  value: number;
  payload: ElevationDataPoint;
}

function ElevationTooltipContent({
  active,
  payload,
}: {
  active?: boolean;
  payload?: TooltipPayloadItem[];
}) {
  if (!active || !payload?.[0]) return null;
  const d = payload[0].payload;
  return (
    <div className="rounded-[var(--radius-component-sm)] border border-[var(--color-border-default)] bg-[var(--color-bg-surface)] px-2.5 py-1.5 text-xs shadow-sm">
      <p className="font-medium text-[var(--color-text-base)]">{Math.round(d.altitudeM)} m</p>
      <p className="text-[var(--color-text-muted)]">{d.distanceKm.toFixed(2)} km</p>
      {d.hr != null && <p className="text-[var(--color-text-muted)]">{d.hr} bpm</p>}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export function ElevationProfile({
  points,
  totalAscentM,
  totalDescentM,
  onHoverPoint,
  hoveredPointIndex,
}: ElevationProfileProps) {
  const profileData = useMemo(() => {
    const raw = buildElevationProfile(points);
    return smoothAltitude(raw, 5);
  }, [points]);

  const summary = useMemo(() => getElevationSummary(profileData), [profileData]);

  // Y-axis domain: pad by 10m for visual breathing room
  const yDomain = useMemo((): [number, number] => {
    if (!summary) return [0, 100];
    return [Math.max(0, summary.minAltitudeM - 10), summary.maxAltitudeM + 10];
  }, [summary]);

  const handleMouseMove = useCallback(
    (state: Record<string, unknown>) => {
      if (!onHoverPoint) return;
      const idx = typeof state?.activeTooltipIndex === 'number' ? state.activeTooltipIndex : null;
      if (idx != null && profileData[idx]) {
        onHoverPoint(profileData[idx].pointIndex);
      }
    },
    [onHoverPoint, profileData],
  );

  const handleMouseLeave = useCallback(() => {
    onHoverPoint?.(null);
  }, [onHoverPoint]);

  // Find the active data index for external hover
  const activeIndex = useMemo(() => {
    if (hoveredPointIndex == null) return undefined;
    const idx = profileData.findIndex((d) => d.pointIndex >= hoveredPointIndex);
    return idx >= 0 ? idx : undefined;
  }, [hoveredPointIndex, profileData]);

  if (profileData.length < 2) return null;

  return (
    <div className="space-y-3">
      {/* Summary metrics */}
      <div className="flex flex-wrap gap-3 text-xs text-[var(--color-text-muted)]">
        {totalAscentM != null && (
          <span className="inline-flex items-center gap-1">
            <TrendingUp className="w-3.5 h-3.5" />
            {totalAscentM} m
          </span>
        )}
        {totalDescentM != null && (
          <span className="inline-flex items-center gap-1">
            <TrendingDown className="w-3.5 h-3.5" />
            {totalDescentM} m
          </span>
        )}
        {summary && (
          <span className="inline-flex items-center gap-1">
            <Mountain className="w-3.5 h-3.5" />
            {summary.minAltitudeM}–{summary.maxAltitudeM} m
          </span>
        )}
      </div>

      {/* Chart */}
      <div
        className="h-[150px] md:h-[200px]"
        aria-label={
          `Hoehenprofil: ${totalAscentM ?? '?'} m Anstieg, ${totalDescentM ?? '?'} m Abstieg` +
          (summary ? `, ${summary.minAltitudeM}–${summary.maxAltitudeM} m` : '')
        }
      >
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={profileData}
            onMouseMove={handleMouseMove}
            onMouseLeave={handleMouseLeave}
            margin={{ top: 4, right: 4, bottom: 0, left: -16 }}
          >
            <defs>
              <linearGradient id="elevGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--color-primary-1-500)" stopOpacity={0.3} />
                <stop offset="100%" stopColor="var(--color-primary-1-500)" stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="var(--color-border-subtle)"
              vertical={false}
            />
            <XAxis
              dataKey="distanceKm"
              type="number"
              domain={['dataMin', 'dataMax']}
              tickFormatter={(v: number) => `${v.toFixed(1)}`}
              tick={{ fontSize: 10, fill: 'var(--color-text-muted)' }}
              axisLine={{ stroke: 'var(--color-border-default)' }}
              tickLine={false}
              unit=" km"
            />
            <YAxis
              domain={yDomain}
              tickFormatter={(v: number) => `${Math.round(v)}`}
              tick={{ fontSize: 10, fill: 'var(--color-text-muted)' }}
              axisLine={false}
              tickLine={false}
              unit=" m"
              width={48}
            />
            <ChartTooltip
              content={<ElevationTooltipContent />}
              cursor={{ stroke: 'var(--color-primary-1-400)', strokeWidth: 1 }}
            />
            <Area
              type="monotone"
              dataKey="altitudeM"
              stroke="var(--color-primary-1-500)"
              strokeWidth={1.5}
              fill="url(#elevGradient)"
              dot={false}
              activeDot={
                activeIndex != null
                  ? { r: 4, fill: 'var(--color-primary-1-500)', stroke: '#fff', strokeWidth: 2 }
                  : undefined
              }
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
