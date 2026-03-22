#!/usr/bin/env bash
# PostCompact hook: re-injects critical rules after context compaction.
# When context gets compressed, CLAUDE.md rules can get lost. This restores them.

cat <<'RULES'
=== KONTEXT WURDE KOMPRIMIERT — Regel-Erinnerung ===

Kritische Regeln die nach Komprimierung verloren gehen können:

NORDLIG DS:
- Nur DS-Komponenten: <Button>, <Input>, <Select>, <DatePicker> — NICHT <button>, <input>, <select>
- Nur var(--color-*) Tokens — KEINE bg-gray-*, text-red-*, bg-white, text-black
- Nur var(--radius-*) — KEINE rounded-md/lg/xl
- Nur var(--shadow-*) — KEINE shadow-sm/md/lg
- Nur Level-3/4 Tokens — KEINE --color-primary-1-500 (Level-2)

WORKFLOW:
- Project Board Status sofort updaten (In Progress / Done)
- Umlaute: ä, ö, ü, ß — KEINE ASCII-Ersetzungen
- Layout: max-w-5xl, Breadcrumbs, pb-2 auf header
- Keine Card-on-Card Schatten

Diese Regeln werden durch PreToolUse Hooks auf Edit|Write erzwungen.
===
RULES

exit 0
