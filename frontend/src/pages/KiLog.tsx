import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  Card,
  CardHeader,
  CardBody,
  Badge,
  Button,
  Spinner,
  Breadcrumbs,
  BreadcrumbItem,
} from '@nordlig/components';
import { fetchAILog, fetchAILogDetail } from '@/api/training';
import type { AILogEntry, AILogDetail } from '@/api/training';

const USE_CASE_LABELS: Record<string, string> = {
  session_analysis: 'Session-Analyse',
  exercise_enrichment: 'Übungs-Anreicherung',
};

function getUseCaseLabel(useCase: string): string {
  return USE_CASE_LABELS[useCase] ?? useCase;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function PromptBlock({ label, content }: { label: string; content: string }) {
  const [expanded, setExpanded] = useState(false);
  const preview = content.slice(0, 200);
  const isLong = content.length > 200;

  return (
    <div className="space-y-1">
      <h4 className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wide">
        {label}
      </h4>
      <pre className="text-xs whitespace-pre-wrap bg-[var(--color-bg-subtle)] rounded-[var(--radius-component-sm)] p-3 overflow-auto max-h-[400px] text-[var(--color-text-base)]">
        {expanded || !isLong ? content : `${preview}...`}
      </pre>
      {isLong && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setExpanded(!expanded)}
          className="text-xs"
        >
          {expanded ? 'Weniger anzeigen' : 'Mehr anzeigen'}
        </Button>
      )}
    </div>
  );
}

function DetailTitle({ detail }: { detail: AILogDetail }) {
  if (detail.workout_id != null && detail.session_date) {
    return <>Eintrag #{detail.id} — Session vom {detail.session_date}</>;
  }
  if (detail.context_label) {
    return <>Eintrag #{detail.id} — {detail.context_label}</>;
  }
  return <>Eintrag #{detail.id}</>;
}

function LogDetail({ logId, onClose }: { logId: number; onClose: () => void }) {
  const [detail, setDetail] = useState<AILogDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetchAILogDetail(logId)
      .then(setDetail)
      .finally(() => setLoading(false));
  }, [logId]);

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <Spinner size="md" />
      </div>
    );
  }

  if (!detail) return null;

  return (
    <Card elevation="raised" padding="spacious">
      <CardHeader>
        <div className="flex items-center justify-between">
          <h3 className="text-base font-semibold">
            <DetailTitle detail={detail} />
          </h3>
          <Button variant="ghost" size="sm" onClick={onClose}>
            Schließen
          </Button>
        </div>
        <div className="flex flex-wrap gap-2 mt-1 text-xs text-[var(--color-text-muted)]">
          <Badge variant="info">{getUseCaseLabel(detail.use_case)}</Badge>
          <span>{detail.provider}</span>
          <span>&middot;</span>
          <span>{formatDate(detail.created_at)}</span>
          {detail.duration_ms != null && (
            <>
              <span>&middot;</span>
              <span>{(detail.duration_ms / 1000).toFixed(1)}s</span>
            </>
          )}
        </div>
      </CardHeader>
      <CardBody className="space-y-4">
        <PromptBlock label="System-Prompt" content={detail.system_prompt} />
        <PromptBlock label="User-Prompt" content={detail.user_prompt} />
        <PromptBlock label="KI-Antwort" content={detail.raw_response} />
      </CardBody>
    </Card>
  );
}

function ContextCell({ entry }: { entry: AILogEntry }) {
  if (entry.workout_id != null && entry.session_date) {
    return (
      <Link
        to={`/sessions/${entry.workout_id}`}
        onClick={(e) => e.stopPropagation()}
        className="text-[var(--color-text-link)] hover:underline"
      >
        {entry.session_date} ({entry.session_type})
      </Link>
    );
  }
  if (entry.context_label) {
    return <span>{entry.context_label}</span>;
  }
  return <span className="text-[var(--color-text-muted)]">&mdash;</span>;
}

function LogTable({
  entries,
  onSelect,
}: {
  entries: AILogEntry[];
  onSelect: (id: number) => void;
}) {
  return (
    <Card elevation="raised" padding="compact">
      <CardBody className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--color-border-subtle)] text-left text-xs text-[var(--color-text-muted)] uppercase tracking-wide">
                <th className="px-4 py-3">Datum</th>
                <th className="px-4 py-3">Typ</th>
                <th className="px-4 py-3">Kontext</th>
                <th className="px-4 py-3">Provider</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Dauer</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr
                  key={entry.id}
                  onClick={() => onSelect(entry.id)}
                  className="border-b border-[var(--color-border-subtle)] cursor-pointer hover:bg-[var(--color-bg-subtle)] transition-colors"
                >
                  <td className="px-4 py-3 whitespace-nowrap">{formatDate(entry.created_at)}</td>
                  <td className="px-4 py-3">
                    <Badge variant="info">{getUseCaseLabel(entry.use_case)}</Badge>
                  </td>
                  <td className="px-4 py-3">
                    <ContextCell entry={entry} />
                  </td>
                  <td className="px-4 py-3 text-[var(--color-text-muted)]">{entry.provider}</td>
                  <td className="px-4 py-3">
                    <Badge variant={entry.parsed_ok ? 'success' : 'error'}>
                      {entry.parsed_ok ? 'OK' : 'Fehler'}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-[var(--color-text-muted)]">
                    {entry.duration_ms != null
                      ? `${(entry.duration_ms / 1000).toFixed(1)}s`
                      : '\u2014'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardBody>
    </Card>
  );
}

export function KiLogPage() {
  const [entries, setEntries] = useState<AILogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [offset, setOffset] = useState(0);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const limit = 20;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchAILog(limit, offset);
      setEntries(data.items);
      setTotal(data.total);
    } finally {
      setLoading(false);
    }
  }, [offset]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="p-4 pt-6 md:p-6 md:pt-8 max-w-5xl mx-auto space-y-6">
      <div className="space-y-2 pb-2">
        <Breadcrumbs>
          <BreadcrumbItem>
            <Link to="/profile">Profil</Link>
          </BreadcrumbItem>
          <BreadcrumbItem isCurrent>KI Log</BreadcrumbItem>
        </Breadcrumbs>
        <h1 className="text-2xl md:text-3xl font-semibold">KI Analyse-Log</h1>
        <p className="text-xs text-[var(--color-text-muted)]">
          Transparente Übersicht aller KI-Anfragen und -Antworten
        </p>
      </div>

      {selectedId != null && <LogDetail logId={selectedId} onClose={() => setSelectedId(null)} />}

      {loading ? (
        <div className="flex justify-center py-12">
          <Spinner size="lg" />
        </div>
      ) : entries.length === 0 ? (
        <Card elevation="raised" padding="spacious">
          <CardBody>
            <p className="text-sm text-[var(--color-text-muted)] text-center py-8">
              Noch keine KI-Analysen durchgeführt.
            </p>
          </CardBody>
        </Card>
      ) : (
        <>
          <LogTable entries={entries} onSelect={setSelectedId} />

          {total > limit && (
            <div className="flex justify-between items-center text-sm">
              <span className="text-[var(--color-text-muted)]">
                {offset + 1}–{Math.min(offset + limit, total)} von {total}
              </span>
              <div className="flex gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={offset === 0}
                  onClick={() => setOffset(Math.max(0, offset - limit))}
                >
                  Zurück
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={offset + limit >= total}
                  onClick={() => setOffset(offset + limit)}
                >
                  Weiter
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
