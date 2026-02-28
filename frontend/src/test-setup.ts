import '@testing-library/jest-dom/vitest';

// Radix UI (Slider) requires ResizeObserver which jsdom doesn't provide
globalThis.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};
