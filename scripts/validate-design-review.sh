#!/usr/bin/env bash
# Validates the design review report before push.
# Called by pre-push hook. Exit 0 = pass, Exit 1 = fail.
#
# Checks:
# 1. Report file exists
# 2. All required sections present
# 3. Screenshot file(s) referenced and exist on disk
# 4. No unchecked items in required sections
# 5. Verdict is PASS (not FAIL or placeholder)
# 6. Nordlig DS compliance grep audit (automated, independent of self-report)

set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
REVIEWS_DIR="${REPO_ROOT}/.claude/reviews"
ERRORS=0

# ============================================================
# 1. Find review file for current branch
#    Convention: .claude/reviews/<issue-number>-<slug>.md
#    Issue number is parsed from branch name like
#    "feature/759-foo-bar" → 759.
#    Old single-file pattern (.claude/design-review.md) is no longer
#    supported; reviews are kept per-branch as audit history.
# ============================================================
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '')"
ISSUE_NUM="$(echo "$BRANCH" | grep -oE '[0-9]+' | head -1 || true)"

if [ -z "$ISSUE_NUM" ]; then
  echo "  Could not extract issue number from branch '$BRANCH'."
  echo "  Branch name should contain an issue number (e.g. feature/759-foo)."
  exit 1
fi

if [ ! -d "$REVIEWS_DIR" ]; then
  echo "  Reviews directory missing: .claude/reviews/"
  echo "  Create it and add ${ISSUE_NUM}-<slug>.md from scripts/design-review-template.md."
  exit 1
fi

REVIEW="$(ls "$REVIEWS_DIR"/${ISSUE_NUM}-*.md 2>/dev/null | head -1 || true)"

if [ -z "$REVIEW" ] || [ ! -f "$REVIEW" ]; then
  echo "  No design review found for issue #${ISSUE_NUM}."
  echo "  Expected: .claude/reviews/${ISSUE_NUM}-<slug>.md"
  echo "  Copy from scripts/design-review-template.md and fill it out."
  exit 1
fi

echo "  Validating review: ${REVIEW#${REPO_ROOT}/}"

# ============================================================
# 2. Required sections must be present
# ============================================================
REQUIRED_SECTIONS=(
  "## 1. Nordlig DS Compliance"
  "## 2. Mobile-First Check"
  "## 3. Touch Targets"
  "## 4. Weissraum"
  "## 5. Gesamtbewertung"
)

for section in "${REQUIRED_SECTIONS[@]}"; do
  if ! grep -q "$section" "$REVIEW"; then
    echo "  Missing section: $section"
    ERRORS=1
  fi
done

# ============================================================
# 3. Screenshot must be referenced and file must exist
# ============================================================
SCREENSHOT_PATH=$(grep -E '^screenshot:' "$REVIEW" | head -1 | sed 's/^screenshot:[[:space:]]*//')

if [ -z "$SCREENSHOT_PATH" ] || [ "$SCREENSHOT_PATH" = "SCREENSHOT_PATH_HERE" ]; then
  echo "  No screenshot path specified (still placeholder)."
  echo "  Take a screenshot at 375px and reference it: screenshot: .claude/screenshots/mobile.png"
  ERRORS=1
elif [ ! -f "${REPO_ROOT}/${SCREENSHOT_PATH}" ]; then
  echo "  Screenshot file not found: $SCREENSHOT_PATH"
  echo "  The referenced screenshot must exist on disk."
  ERRORS=1
fi

# ============================================================
# 4. Check for unchecked items in sections 1, 3, 4
#    (These are checkboxes that must all be marked)
# ============================================================
# Extract lines between section headers and count unchecked
UNCHECKED=$(grep -c '^\- \[ \]' "$REVIEW" 2>/dev/null || true)
UNCHECKED=$(echo "$UNCHECKED" | tr -d '[:space:]')
UNCHECKED=${UNCHECKED:-0}

if [ "$UNCHECKED" -gt 0 ]; then
  echo "  $UNCHECKED unchecked items in design review:"
  grep '^\- \[ \]' "$REVIEW" | while read -r line; do
    echo "    $line"
  done
  ERRORS=1
fi

# ============================================================
# 5. Verdict must be PASS
# ============================================================
VERDICT=$(grep -E '^\*\*Verdict:\*\*' "$REVIEW" | head -1)

if echo "$VERDICT" | grep -qi 'FAIL'; then
  echo "  Design review verdict is FAIL. Fix findings before pushing."
  ERRORS=1
elif ! echo "$VERDICT" | grep -qi 'PASS'; then
  echo "  Design review verdict not set. Must be: **Verdict:** PASS"
  ERRORS=1
fi

# ============================================================
# 6. Automated Nordlig DS compliance audit
#    Runs grep on changed .tsx files — independent of self-report
#    Checks branch diff (main...HEAD) for pre-push context
# ============================================================
CHANGED_TSX=$(git diff main...HEAD --name-only 2>/dev/null | grep '\.tsx$' || true)

if [ -n "$CHANGED_TSX" ]; then
  DS_VIOLATIONS=0

  # Hardcoded colors
  for f in $CHANGED_TSX; do
    if [ -f "${REPO_ROOT}/${f}" ]; then
      HITS=$(grep -nE 'bg-(white|black|gray|slate|red|blue|green|yellow|orange|purple|pink)-' "${REPO_ROOT}/${f}" 2>/dev/null | grep -v 'ds-ok' || true)
      if [ -n "$HITS" ]; then
        echo "  Hardcoded colors in $f:"
        echo "$HITS" | while read -r line; do echo "    $line"; done
        DS_VIOLATIONS=1
      fi
    fi
  done

  # Hardcoded radii
  for f in $CHANGED_TSX; do
    if [ -f "${REPO_ROOT}/${f}" ]; then
      HITS=$(grep -nE 'rounded-(sm|md|lg|xl|2xl)' "${REPO_ROOT}/${f}" 2>/dev/null | grep -v 'ds-ok' | grep -v 'rounded-full' || true)
      if [ -n "$HITS" ]; then
        echo "  Hardcoded radii in $f:"
        echo "$HITS" | while read -r line; do echo "    $line"; done
        DS_VIOLATIONS=1
      fi
    fi
  done

  # Hardcoded shadows
  for f in $CHANGED_TSX; do
    if [ -f "${REPO_ROOT}/${f}" ]; then
      HITS=$(grep -nE 'shadow-(sm|md|lg|xl|2xl)' "${REPO_ROOT}/${f}" 2>/dev/null | grep -v 'ds-ok' | grep -v 'var(--shadow' || true)
      if [ -n "$HITS" ]; then
        echo "  Hardcoded shadows in $f:"
        echo "$HITS" | while read -r line; do echo "    $line"; done
        DS_VIOLATIONS=1
      fi
    fi
  done

  # Native HTML elements instead of DS components
  for f in $CHANGED_TSX; do
    if [ -f "${REPO_ROOT}/${f}" ]; then
      HITS=$(grep -nE '<(button|input|select|textarea)[[:space:]>]' "${REPO_ROOT}/${f}" 2>/dev/null | grep -v 'ds-ok' | grep -v 'ErrorBoundary' || true)
      if [ -n "$HITS" ]; then
        echo "  Native HTML elements in $f (use Nordlig DS components):"
        echo "$HITS" | while read -r line; do echo "    $line"; done
        DS_VIOLATIONS=1
      fi
    fi
  done

  if [ "$DS_VIOLATIONS" -eq 1 ]; then
    echo ""
    echo "  Nordlig DS compliance violations found (automated check)."
    echo "  Fix these or add '// ds-ok' comment if intentional."
    ERRORS=1
  fi
fi

# ============================================================
# Result
# ============================================================
if [ "$ERRORS" -ne 0 ]; then
  exit 1
fi

echo "  Design review validated."
exit 0
