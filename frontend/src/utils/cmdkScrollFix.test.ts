import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { installCmdkScrollFix } from './cmdkScrollFix';

function buildCmdkFixture(): { list: HTMLElement; item: HTMLElement } {
  const list = document.createElement('div');
  list.setAttribute('cmdk-list', '');
  const item = document.createElement('div');
  item.setAttribute('cmdk-item', '');
  item.textContent = 'Item 1';
  list.appendChild(item);
  document.body.appendChild(list);
  return { list, item };
}

describe('cmdkScrollFix (#784)', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    document.body.replaceChildren();
    installCmdkScrollFix();
  });

  afterEach(() => {
    vi.useRealTimers();
    document.body.replaceChildren();
  });

  it('adds cmdk-scrolling class on wheel inside [cmdk-list]', () => {
    const { list, item } = buildCmdkFixture();

    item.dispatchEvent(new Event('wheel', { bubbles: true }));

    expect(list.classList.contains('cmdk-scrolling')).toBe(true);
  });

  it('removes cmdk-scrolling class 150ms after last wheel event', () => {
    const { list, item } = buildCmdkFixture();

    item.dispatchEvent(new Event('wheel', { bubbles: true }));
    expect(list.classList.contains('cmdk-scrolling')).toBe(true);

    vi.advanceTimersByTime(150);

    expect(list.classList.contains('cmdk-scrolling')).toBe(false);
  });

  it('keeps the class active while wheel events keep firing (debounce)', () => {
    const { list, item } = buildCmdkFixture();

    item.dispatchEvent(new Event('wheel', { bubbles: true }));
    vi.advanceTimersByTime(100);
    expect(list.classList.contains('cmdk-scrolling')).toBe(true);

    // Another wheel event resets the timeout
    item.dispatchEvent(new Event('wheel', { bubbles: true }));
    vi.advanceTimersByTime(100);
    // Still scrolling because we're within 150ms of the latest event
    expect(list.classList.contains('cmdk-scrolling')).toBe(true);

    vi.advanceTimersByTime(60);
    // Now > 150ms after the latest event → cleaned up
    expect(list.classList.contains('cmdk-scrolling')).toBe(false);
  });

  it('does nothing for wheel events outside [cmdk-list]', () => {
    const { list } = buildCmdkFixture();
    const otherDiv = document.createElement('div');
    document.body.appendChild(otherDiv);

    otherDiv.dispatchEvent(new Event('wheel', { bubbles: true }));

    expect(list.classList.contains('cmdk-scrolling')).toBe(false);
  });
});
