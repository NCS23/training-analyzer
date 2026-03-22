import { Badge, Card, CardBody } from '@nordlig/components';
import type { PacingResponse } from '@/api/pacing';

interface PacingTableProps {
  result: PacingResponse;
}

export function PacingTable({ result }: PacingTableProps) {
  return (
    <Card elevation="raised">
      <CardBody className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--color-border-muted)] text-left text-xs text-[var(--color-text-muted)]">
                <th className="px-3 py-2 font-medium">km</th>
                <th className="px-3 py-2 font-medium">Pace</th>
                <th className="px-3 py-2 font-medium hidden sm:table-cell">Kumuliert</th>
                <th className="px-3 py-2 font-medium hidden md:table-cell">Höhe</th>
                <th className="px-3 py-2 font-medium">Hinweis</th>
              </tr>
            </thead>
            <tbody>
              {result.splits.map((split) => (
                <tr
                  key={split.km}
                  className="border-b border-[var(--color-border-muted)] last:border-0 hover:bg-[var(--color-bg-muted)] transition-colors duration-150 motion-reduce:transition-none"
                >
                  <td className="px-3 py-2 font-medium tabular-nums">
                    {split.distance_km < 1
                      ? `${split.km} (${(split.distance_km * 1000).toFixed(0)}m)`
                      : split.km}
                  </td>
                  <td className="px-3 py-2 tabular-nums font-semibold">
                    {split.target_pace_formatted}/km
                  </td>
                  <td className="px-3 py-2 tabular-nums hidden sm:table-cell text-[var(--color-text-muted)]">
                    {split.cumulative_formatted}
                  </td>
                  <td className="px-3 py-2 hidden md:table-cell">
                    <ElevationCell gain={split.elevation_gain_m} loss={split.elevation_loss_m} />
                  </td>
                  <td className="px-3 py-2">
                    {split.adjustment_note && (
                      <Badge
                        variant={
                          split.adjustment_note.startsWith('Bergauf')
                            ? 'accent-bold'
                            : 'primary-bold'
                        }
                        size="sm"
                      >
                        {split.adjustment_note}
                      </Badge>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="border-t-2 border-[var(--color-border-default)] font-semibold text-sm">
                <td className="px-3 py-2">Gesamt</td>
                <td className="px-3 py-2 tabular-nums">{result.avg_pace_formatted}/km</td>
                <td className="px-3 py-2 tabular-nums hidden sm:table-cell">
                  {result.target_time_formatted}
                </td>
                <td className="px-3 py-2 hidden md:table-cell">
                  <ElevationCell
                    gain={result.splits.reduce((s, sp) => s + sp.elevation_gain_m, 0)}
                    loss={result.splits.reduce((s, sp) => s + sp.elevation_loss_m, 0)}
                  />
                </td>
                <td className="px-3 py-2" />
              </tr>
            </tfoot>
          </table>
        </div>
      </CardBody>
    </Card>
  );
}

function ElevationCell({ gain, loss }: { gain: number; loss: number }) {
  if (gain === 0 && loss === 0) {
    return <span className="text-[var(--color-text-muted)]">—</span>;
  }
  return (
    <span className="text-xs tabular-nums text-[var(--color-text-muted)]">
      {gain > 0 && <span className="text-[var(--color-text-warning)]">↑{gain.toFixed(0)}m</span>}
      {gain > 0 && loss > 0 && ' '}
      {loss > 0 && <span className="text-[var(--color-text-success)]">↓{loss.toFixed(0)}m</span>}
    </span>
  );
}
