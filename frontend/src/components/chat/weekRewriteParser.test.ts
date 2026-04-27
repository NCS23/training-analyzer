import { describe, expect, it } from 'vitest';
import { parseWeekRewrites } from './weekRewriteParser';

describe('parseWeekRewrites', () => {
  it('extracts a valid week-rewrite block', () => {
    const content = [
      'Hier ist mein Vorschlag:',
      '```week-rewrite',
      JSON.stringify({
        review_week_start: '2026-04-20',
        target_week_start: '2026-04-27',
        plan_id: 1,
        summary: 'Volumen reduzieren',
        reason: 'Hohe Belastung',
        recommendations: ['Long Run kuerzen', 'Tempo durch Easy ersetzen'],
      }),
      '```',
    ].join('\n');

    const { text, rewrites } = parseWeekRewrites(content);

    expect(text).toBe('Hier ist mein Vorschlag:');
    expect(rewrites).toHaveLength(1);
    expect(rewrites[0].review_week_start).toBe('2026-04-20');
    expect(rewrites[0].recommendations).toHaveLength(2);
  });

  it('ignores blocks without recommendations', () => {
    const content = [
      '```week-rewrite',
      JSON.stringify({
        review_week_start: '2026-04-20',
        summary: 'Leere Empfehlungen',
        reason: 'Test',
        recommendations: [],
      }),
      '```',
    ].join('\n');

    const { rewrites } = parseWeekRewrites(content);
    expect(rewrites).toHaveLength(0);
  });

  it('ignores malformed JSON blocks', () => {
    const content = '```week-rewrite\n{not valid json\n```';
    const { text, rewrites } = parseWeekRewrites(content);
    expect(rewrites).toHaveLength(0);
    expect(text).toBe('');
  });

  it('returns empty list when no block present', () => {
    const { text, rewrites } = parseWeekRewrites('Nur Text, kein Block.');
    expect(text).toBe('Nur Text, kein Block.');
    expect(rewrites).toHaveLength(0);
  });
});
