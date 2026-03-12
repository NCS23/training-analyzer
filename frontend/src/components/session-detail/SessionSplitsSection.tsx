import {
  Card,
  CardHeader,
  Select,
  Spinner,
  Badge,
  SegmentedControl,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  Popover,
  PopoverTrigger,
  PopoverContent,
} from '@nordlig/components';
import type { LapDetail, KmSplit } from '@/api/training';
import {
  lapTypeLabels,
  lapTypeBadgeVariant,
  lapTypeOptions,
  lapTypeHints,
} from '@/constants/training';
import { SEGMENT_TYPES } from '@/constants/taxonomy';
import { GlossaryHint } from '@/components/GlossaryHint';

const lapTypeGlossary = SEGMENT_TYPES.map((key) => ({
  term: lapTypeLabels[key] ?? key,
  description: lapTypeHints[key] ?? '',
}));

interface SessionSplitsSectionProps {
  localLaps: LapDetail[];
  kmSplits: KmSplit[] | null;
  splitsTab: 'laps' | 'km';
  setSplitsTab: (tab: 'laps' | 'km') => void;
  isEditing: boolean;
  savingLaps: boolean;
  onLapTypeChange: (lapNumber: number, newType: string | undefined) => Promise<void>;
  highlightedKm: number | null;
  setHighlightedKm: (km: number | null) => void;
  highlightedLap: number | null;
  setHighlightedLap: (lap: number | null) => void;
}

// eslint-disable-next-line max-lines-per-function -- two tables with shared card
export function SessionSplitsSection({
  localLaps,
  kmSplits,
  splitsTab,
  setSplitsTab,
  isEditing,
  savingLaps,
  onLapTypeChange,
  highlightedKm,
  setHighlightedKm,
  highlightedLap,
  setHighlightedLap,
}: SessionSplitsSectionProps) {
  return (
    <section aria-label="Laps">
      <Card elevation="raised">
        <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <SegmentedControl
            size="sm"
            value={splitsTab}
            onChange={(val) => setSplitsTab(val as 'laps' | 'km')}
            items={[
              ...(localLaps.length > 0
                ? [{ value: 'laps', label: `Laps (${localLaps.length})` }]
                : []),
              ...(kmSplits ? [{ value: 'km', label: `km (${kmSplits.length})` }] : []),
            ]}
          />
          {isEditing && savingLaps && splitsTab === 'laps' && <Spinner size="sm" />}
        </CardHeader>

        {/* Device Laps Table */}
        {splitsTab === 'laps' && localLaps.length > 0 && (
          <div className="overflow-x-auto -mx-[var(--spacing-card-padding-normal)]">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12 sticky left-0 z-10 bg-[var(--color-table-header-bg)]">
                    #
                  </TableHead>
                  <TableHead>
                    <span className="inline-flex items-center gap-1">
                      Typ
                      <GlossaryHint entries={lapTypeGlossary} />
                    </span>
                  </TableHead>
                  <TableHead>Dauer</TableHead>
                  <TableHead>Distanz</TableHead>
                  <TableHead>Pace</TableHead>
                  <TableHead>Ø HF</TableHead>
                  <TableHead>Kadenz</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {localLaps.map((lap: LapDetail) => {
                  const effectiveType = lap.user_override || lap.suggested_type || 'unclassified';
                  return (
                    <TableRow
                      key={lap.lap_number}
                      onMouseEnter={() => setHighlightedLap(lap.lap_number)}
                      onMouseLeave={() => setHighlightedLap(null)}
                      className={
                        highlightedLap === lap.lap_number
                          ? 'bg-[var(--color-bg-primary-subtle)]'
                          : ''
                      }
                    >
                      <TableCell className="font-medium text-[var(--color-text-muted)] sticky left-0 z-10 bg-[var(--color-bg-elevated)]">
                        {lap.lap_number}
                      </TableCell>
                      <TableCell>
                        {isEditing ? (
                          <Select
                            options={lapTypeOptions}
                            value={effectiveType}
                            onChange={(val) => onLapTypeChange(lap.lap_number, val)}
                            inputSize="sm"
                            className="w-36"
                          />
                        ) : (
                          <Popover>
                            <PopoverTrigger asChild>
                              <button // ds-ok: Radix PopoverTrigger asChild
                                type="button"
                                className="cursor-pointer"
                              >
                                <Badge
                                  variant={lapTypeBadgeVariant[effectiveType] ?? 'neutral'}
                                  size="xs"
                                >
                                  {lapTypeLabels[effectiveType] || effectiveType}
                                </Badge>
                              </button>
                            </PopoverTrigger>
                            <PopoverContent
                              side="right"
                              showArrow
                              className="text-xs leading-relaxed"
                            >
                              {lapTypeHints[effectiveType] ?? ''}
                            </PopoverContent>
                          </Popover>
                        )}
                      </TableCell>
                      <TableCell>{lap.duration_formatted}</TableCell>
                      <TableCell>
                        {lap.distance_km != null ? `${lap.distance_km} km` : '-'}
                      </TableCell>
                      <TableCell>
                        {lap.pace_formatted ? `${lap.pace_formatted} /km` : '-'}
                      </TableCell>
                      <TableCell>{lap.avg_hr_bpm != null ? `${lap.avg_hr_bpm}` : '-'}</TableCell>
                      <TableCell>
                        {lap.avg_cadence_spm != null ? `${lap.avg_cadence_spm}` : '-'}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}

        {/* Km Splits Table */}
        {splitsTab === 'km' && kmSplits && (
          <div className="overflow-x-auto -mx-[var(--spacing-card-padding-normal)]">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12 sticky left-0 z-10 bg-[var(--color-table-header-bg)]">
                    km
                  </TableHead>
                  <TableHead>Dauer</TableHead>
                  <TableHead>Pace</TableHead>
                  <TableHead title="Höhenkorrigierter Pace: Bergauf-Läufe erhalten Zeitgutschrift, Bergab-Läufe Zeitabzug">
                    GAP
                  </TableHead>
                  <TableHead>Ø HF</TableHead>
                  <TableHead>Anstieg</TableHead>
                  <TableHead>Abstieg</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {kmSplits.map((split) => (
                  <TableRow
                    key={split.km_number}
                    onMouseEnter={() => setHighlightedKm(split.km_number)}
                    onMouseLeave={() => setHighlightedKm(null)}
                    className={
                      highlightedKm === split.km_number ? 'bg-[var(--color-bg-primary-subtle)]' : ''
                    }
                  >
                    <TableCell className="font-medium text-[var(--color-text-muted)] sticky left-0 z-10 bg-[var(--color-bg-elevated)]">
                      {split.is_partial ? split.distance_km : split.km_number}
                    </TableCell>
                    <TableCell>{split.duration_formatted}</TableCell>
                    <TableCell>
                      {split.pace_formatted ? `${split.pace_formatted} /km` : '-'}
                    </TableCell>
                    <TableCell
                      title={
                        split.pace_corrected_formatted
                          ? 'Grade Adjusted Pace — korrigiert für Steigung/Gefälle'
                          : undefined
                      }
                    >
                      {split.pace_corrected_formatted ? (
                        <span className="text-[var(--color-primary-1-600)]">
                          {split.pace_corrected_formatted} /km
                        </span>
                      ) : (
                        '-'
                      )}
                    </TableCell>
                    <TableCell>{split.avg_hr_bpm ?? '-'}</TableCell>
                    <TableCell>
                      {split.elevation_gain_m != null ? `${split.elevation_gain_m} m` : '-'}
                    </TableCell>
                    <TableCell>
                      {split.elevation_loss_m != null ? `${split.elevation_loss_m} m` : '-'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </Card>
    </section>
  );
}
