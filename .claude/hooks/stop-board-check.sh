#!/usr/bin/env bash
# Stop hook: reminds Claude to update Project Board before finishing.
# Stdout is shown to Claude before it stops.

cat <<'REMINDER'
=== STOP-CHECK ===
Bevor du aufhörst, prüfe:
- [ ] Hast du den Project Board Status aktualisiert? (In Progress → Done)
- [ ] Hast du das GitHub Issue kommentiert?
- [ ] Hast du den User gefragt ob er zur nächsten Story wechseln will?
===
REMINDER

exit 0
