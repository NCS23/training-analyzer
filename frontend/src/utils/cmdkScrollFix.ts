/**
 * Workaround für den bekannten cmdk-Bug (#784):
 * `Command.Item` hat ein `onPointerMove` das bei jedem Maus-Move die Selektion
 * ändert und mit `scrollIntoView` springt. Bei Wheel-Scroll bewegt sich der
 * Cursor relativ zu den Items → die Selektion springt rauf/runter, der
 * Scroll-Effekt wird unflüssig oder bricht ab.
 *
 * Lösung: Während aktiv gewheelt wird, setzen wir `cmdk-scrolling` Class auf
 * dem `[cmdk-list]`. CSS in `index.css` deaktiviert dann `pointer-events` auf
 * den Items für die Dauer des Scroll-Bursts (150 ms nach letztem Wheel-Event).
 * Klick/Tastatur-Navigation bleiben unbeeinflusst.
 *
 * Referenz: https://github.com/pacocoursey/cmdk/issues/267
 */

const SCROLL_END_DELAY_MS = 150;
const scrollTimeouts = new WeakMap<Element, number>();

function handleWheel(event: Event): void {
  const target = event.target as Element | null;
  const list = target?.closest('[cmdk-list]');
  if (!list) return;

  list.classList.add('cmdk-scrolling');

  const previousTimeout = scrollTimeouts.get(list);
  if (previousTimeout !== undefined) {
    window.clearTimeout(previousTimeout);
  }

  const timeout = window.setTimeout(() => {
    list.classList.remove('cmdk-scrolling');
    scrollTimeouts.delete(list);
  }, SCROLL_END_DELAY_MS);

  scrollTimeouts.set(list, timeout);
}

let installed = false;

/** Installiert den globalen Wheel-Listener. Idempotent. */
export function installCmdkScrollFix(): void {
  if (installed || typeof window === 'undefined') return;
  // capture: true — wir hören das Event bevor cmdk's eigene Listener greifen.
  // passive: true — wir verhindern niemals den Default-Scroll.
  window.addEventListener('wheel', handleWheel, { capture: true, passive: true });
  installed = true;
}
