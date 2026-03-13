import {
  Card,
  CardHeader,
  Alert,
  AlertDescription,
  Badge,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from '@nordlig/components';
import type { ComparisonResponse, MatchedSegment } from '@/api/training';
import type { Segment } from '@/api/segment';
import { lapTypeLabels, lapTypeBadgeVariant } from '@/constants/training';

interface SessionComparisonSectionProps {
  comparison: ComparisonResponse;
}

function formatDelta(seconds: number): string {
  const sign = seconds >= 0 ? '+' : '-';
  const abs = Math.abs(seconds);
  const min = Math.floor(abs / 60);
  const sec = Math.round(abs % 60);
  if (min > 0) {
    return `${sign}${min}:${String(sec).padStart(2, '0')}`;
  }
  return `${sign}${sec}s`;
}

function deltaColor(value: number | null): string {
  if (value == null || value === 0) return '';
  return value < 0 ? 'text-[var(--color-text-success)]' : 'text-[var(--color-text-error)]';
}

function formatPaceRange(planned: Segment | null): string {
  if (!planned) return '–';
  const { target_pace_min: lo, target_pace_max: hi } = planned;
  if (lo && hi) return `${lo}–${hi}`;
  return lo ?? hi ?? '–';
}

function formatHrRange(planned: Segment | null): string {
  if (!planned) return '–';
  const { target_hr_min: lo, target_hr_max: hi } = planned;
  if (lo != null && hi != null) return `${lo}–${hi}`;
  return String(lo ?? hi ?? '–');
}

function formatHrDelta(value: number | null): string {
  if (value == null) return '–';
  if (value > 0) return `+${value}`;
  return String(value);
}

function formatDurationDelta(seconds: number | null): string {
  if (seconds == null) return '–';
  return formatDelta(seconds);
}

function prepareRowData(seg: MatchedSegment) {
  const { planned, actual, delta } = seg;
  const paceDelta = delta?.pace_delta_seconds ?? null;
  const hrDelta = delta?.hr_avg_delta ?? null;
  const durDelta = delta?.duration_delta_seconds ?? null;

  return {
    rowClass: seg.match_quality !== 'matched' ? 'bg-[var(--color-bg-muted)]' : '',
    typeLabel: lapTypeLabels[seg.segment_type] ?? seg.segment_type,
    sollPace: formatPaceRange(planned),
    istPace: actual?.actual_pace_formatted ?? '–',
    paceDeltaText: delta?.pace_delta_formatted ?? '–',
    paceDeltaColor: deltaColor(paceDelta),
    sollHr: formatHrRange(planned),
    istHr: actual?.actual_hr_avg ?? '–',
    hrDeltaText: formatHrDelta(hrDelta),
    hrDeltaColor: deltaColor(hrDelta),
    durDeltaText: formatDurationDelta(durDelta),
    durDeltaColor: deltaColor(durDelta),
  };
}

function SegmentRow({ seg }: { seg: MatchedSegment }) {
  const d = prepareRowData(seg);

  return (
    <TableRow className={d.rowClass}>
      <TableCell className="font-medium text-[var(--color-text-muted)] sticky left-0 z-10 bg-[var(--color-bg-elevated)]">
        {seg.position + 1}
      </TableCell>
      <TableCell>
        <Badge variant={lapTypeBadgeVariant[seg.segment_type] ?? 'neutral'} size="xs">
          {d.typeLabel}
        </Badge>
      </TableCell>
      <TableCell className="hidden sm:table-cell">{d.sollPace}</TableCell>
      <TableCell>{d.istPace}</TableCell>
      <TableCell className={d.paceDeltaColor}>{d.paceDeltaText}</TableCell>
      <TableCell className="hidden sm:table-cell">{d.sollHr}</TableCell>
      <TableCell className="hidden sm:table-cell">{d.istHr}</TableCell>
      <TableCell className={`hidden sm:table-cell ${d.hrDeltaColor}`}>{d.hrDeltaText}</TableCell>
      <TableCell className={d.durDeltaColor}>{d.durDeltaText}</TableCell>
    </TableRow>
  );
}

export function SessionComparisonSection({ comparison }: SessionComparisonSectionProps) {
  return (
    <section aria-label="Soll/Ist-Vergleich">
      <Card elevation="raised">
        <CardHeader>
          <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
            Soll/Ist-Vergleich
          </h2>
        </CardHeader>

        {comparison.has_mismatch && (
          <div className="pb-3 -mt-1">
            <Alert variant="info">
              <AlertDescription>
                Segment-Anzahl weicht ab: {comparison.planned_count} geplant,{' '}
                {comparison.actual_count} tatsächlich
              </AlertDescription>
            </Alert>
          </div>
        )}

        <div className="overflow-x-auto -mx-[var(--spacing-card-padding-normal)]">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12 sticky left-0 z-10 bg-[var(--color-table-header-bg)]">
                  #
                </TableHead>
                <TableHead>Typ</TableHead>
                <TableHead className="hidden sm:table-cell">Soll Pace</TableHead>
                <TableHead>Ist Pace</TableHead>
                <TableHead>± Pace</TableHead>
                <TableHead className="hidden sm:table-cell">Soll HF</TableHead>
                <TableHead className="hidden sm:table-cell">Ist HF</TableHead>
                <TableHead className="hidden sm:table-cell">± HF</TableHead>
                <TableHead>± Dauer</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {comparison.segments.map((seg) => (
                <SegmentRow key={seg.position} seg={seg} />
              ))}
            </TableBody>
          </Table>
        </div>
      </Card>
    </section>
  );
}
