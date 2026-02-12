# 🏔️ Nordlig Design System

**Nordisches Design für moderne Apps**

**Version:** 1.0.0-alpha  
**Status:** 📋 Planning Phase  
**Repository:** `@nordlig/design-system` (npm package)  
**Last Updated:** 2026-02-12

---

## 🎯 Vision & Mission

### Vision
Ein professionelles, skalierbares Design System das nordische Design-Prinzipien in moderne App-Entwicklung überträgt.

### Mission
- **Minimalismus** - Weniger ist mehr
- **Klarheit** - Funktion vor Form
- **Konsistenz** - Wiederverwendbar über Projekte
- **Accessibility** - Inklusiv by design
- **Standards** - W3C compliant, MCP ready

---

## 🎨 Design Prinzipien

### 1. Nordische Ästhetik
**Inspiration:** Skandinavisches Möbeldesign
- ❄️ **Minimalismus** - Reduziert auf das Wesentliche
- 📐 **Klare Linien** - Geometrisch, strukturiert
- 🔆 **Weißraum** - Viel Breathing Room
- 🌲 **Natürliche Akzente** - Erdtöne, dezente Farben
- 🎨 **Gedämpfte Palette** - Nicht grell oder peppig

### 2. Funktionalität
- **Form follows Function** - Design dient Usability
- **Intuitive Interaktion** - Selbsterklärend
- **Performance** - Leichtgewichtig, schnell

### 3. Zugänglichkeit
- **WCAG 2.1 AA** minimum (AAA where possible)
- **Keyboard Navigation** - Vollständig tastatursteuerbar
- **Screen Reader** - Semantisches HTML
- **Color Contrast** - Mindestens 4.5:1 für Text

### 4. Konsistenz
- **Atomic Design** - Komponenten-Hierarchie
- **Design Tokens** - Single Source of Truth
- **Pattern Library** - Dokumentierte Patterns

---

## 🏗️ Architektur

### Token-Hierarchie (4 Layers)

```
┌─────────────────────────────────────────┐
│ Level 4: SEMANTIC                       │
│ Component-specific tokens               │
│ (btn-primary-bg, input-border-focus)   │
└──────────────┬──────────────────────────┘
               │ References Level 3 only
┌──────────────▼──────────────────────────┐
│ Level 3: ROLES                          │
│ Functional tokens                       │
│ (bg-primary, border-default, text-base)│
└──────────────┬──────────────────────────┘
               │ References Level 2 only
┌──────────────▼──────────────────────────┐
│ Level 2: GLOBAL                         │
│ Theme colors (Primary, Secondary, etc.) │
│ (primary-1-500, accent-3-200)          │
└──────────────┬──────────────────────────┘
               │ References Level 1 only
┌──────────────▼──────────────────────────┐
│ Level 1: BASE                           │
│ Raw color palettes                      │
│ (slate-100, sky-500, emerald-900)      │
│ → Only layer with Hex codes!           │
└─────────────────────────────────────────┘
```

### Atomic Design Structure

```
Atoms (Basic building blocks)
  └─ Button, Input, Label, Icon, Badge
       ↓
Molecules (Simple combinations)
  └─ InputField (Label + Input + Error)
  └─ IconButton (Icon + Button)
       ↓
Organisms (Complex components)
  └─ Form, Card, Navigation, Table
       ↓
Templates (Page layouts)
  └─ DashboardTemplate, DetailTemplate
       ↓
Pages (Actual implementations)
  └─ SessionDetail, UploadPage
```

---

## 🎨 Design Tokens Specification

### Level 1: BASE (Primitive Tokens)

**Purpose:** Raw values, Tailwind-style palettes  
**Format:** `--color-{palette}-{shade}`  
**Contains:** Only Hex codes

```css
/* Neutral Palettes (Grays) */
--color-slate-50: #f8fafc;
--color-slate-100: #f1f5f9;
--color-slate-200: #e2e8f0;
--color-slate-300: #cbd5e1;
--color-slate-400: #94a3b8;
--color-slate-500: #64748b;
--color-slate-600: #475569;
--color-slate-700: #334155;
--color-slate-800: #1e293b;
--color-slate-900: #0f172a;
--color-slate-950: #020617;

--color-stone-50: #fafaf9;
/* ... stone palette ... */

/* Cool Tones (Blues, Teals) - Nordic inspired */
--color-sky-50: #f0f9ff;
--color-sky-100: #e0f2fe;
--color-sky-200: #bae6fd;
--color-sky-300: #7dd3fc;
--color-sky-400: #38bdf8;
--color-sky-500: #0ea5e9;
--color-sky-600: #0284c7;
--color-sky-700: #0369a1;
--color-sky-800: #075985;
--color-sky-900: #0c4a6e;
--color-sky-950: #082f49;

--color-cyan-50: #ecfeff;
/* ... cyan palette ... */

--color-teal-50: #f0fdfa;
/* ... teal palette ... */

/* Warm Accents (Earth tones) */
--color-amber-50: #fffbeb;
/* ... amber palette ... */

--color-orange-50: #fff7ed;
/* ... orange palette ... */

/* Nature Greens */
--color-emerald-50: #ecfdf5;
/* ... emerald palette ... */

--color-green-50: #f0fdf4;
/* ... green palette ... */

/* Status Colors */
--color-red-50: #fef2f2;
/* ... red palette ... */

--color-yellow-50: #fefce8;
/* ... yellow palette ... */

--color-blue-50: #eff6ff;
/* ... blue palette ... */
```

**Complete Base Palettes (Suggested):**
- **Neutrals:** slate, stone, zinc, gray
- **Cool:** sky, cyan, teal, blue, indigo
- **Warm:** amber, orange, red
- **Nature:** emerald, green, lime
- **Status:** yellow (warning), red (error), green (success), blue (info)

---

### Level 2: GLOBAL (Theme Tokens)

**Purpose:** Theme-specific color assignments  
**Format:** `--color-{type}-{index}-{shade}`  
**References:** Only Level 1  
**No Hex codes!**

```css
/* PRIMARY Colors (2 palettes standard) */
--color-primary-1-50: var(--color-sky-50);
--color-primary-1-100: var(--color-sky-100);
--color-primary-1-200: var(--color-sky-200);
--color-primary-1-300: var(--color-sky-300);
--color-primary-1-400: var(--color-sky-400);
--color-primary-1-500: var(--color-sky-500);   /* Main primary */
--color-primary-1-600: var(--color-sky-600);
--color-primary-1-700: var(--color-sky-700);
--color-primary-1-800: var(--color-sky-800);
--color-primary-1-900: var(--color-sky-900);
--color-primary-1-950: var(--color-sky-950);

--color-primary-2-50: var(--color-indigo-50);
--color-primary-2-100: var(--color-indigo-100);
/* ... full indigo palette ... */
--color-primary-2-500: var(--color-indigo-500);  /* Alt primary */

/* SECONDARY Colors (2 palettes standard) */
--color-secondary-1-50: var(--color-slate-50);
--color-secondary-1-100: var(--color-slate-100);
/* ... full slate palette ... */
--color-secondary-1-500: var(--color-slate-500);  /* Main secondary */

--color-secondary-2-50: var(--color-stone-50);
/* ... full stone palette ... */
--color-secondary-2-500: var(--color-stone-500);  /* Alt secondary */

/* ACCENT Colors (5+ palettes, numbered neutrally) */
--color-accent-1-50: var(--color-emerald-50);
/* ... emerald palette (Success) ... */
--color-accent-1-500: var(--color-emerald-500);

--color-accent-2-50: var(--color-amber-50);
/* ... amber palette (Warning) ... */
--color-accent-2-500: var(--color-amber-500);

--color-accent-3-50: var(--color-red-50);
/* ... red palette (Error) ... */
--color-accent-3-500: var(--color-red-500);

--color-accent-4-50: var(--color-blue-50);
/* ... blue palette (Info) ... */
--color-accent-4-500: var(--color-blue-500);

--color-accent-5-50: var(--color-teal-50);
/* ... teal palette (Custom accent) ... */
--color-accent-5-500: var(--color-teal-500);

/* NEUTRAL Palettes (Grays for UI) */
--color-neutral-1-50: var(--color-slate-50);
/* ... slate palette ... */
--color-neutral-1-500: var(--color-slate-500);

--color-neutral-2-50: var(--color-zinc-50);
/* ... zinc palette (cooler gray) ... */
--color-neutral-2-500: var(--color-zinc-500);
```

**Theming Example:**
```css
/* Light Theme (Default) */
:root {
  --color-primary-1-500: var(--color-sky-500);
  --color-secondary-1-500: var(--color-slate-500);
  /* ... */
}

/* Dark Theme */
[data-theme="dark"] {
  --color-primary-1-500: var(--color-sky-400);  /* Lighter for dark bg */
  --color-secondary-1-500: var(--color-slate-400);
  /* ... */
}

/* Alternative Theme (e.g., "Forest") */
[data-theme="forest"] {
  --color-primary-1-500: var(--color-emerald-600);
  --color-secondary-1-500: var(--color-stone-600);
  /* ... */
}
```

---

### Level 3: ROLES (Functional Tokens)

**Purpose:** UI function assignments  
**Format:** `--color-{function}-{variant}`  
**References:** Only Level 2  
**No direct base colors!**

```css
/* BACKGROUNDS */
--color-bg-base: var(--color-neutral-1-50);           /* Page background */
--color-bg-surface: var(--color-neutral-1-100);       /* Cards, panels */
--color-bg-elevated: var(--color-neutral-1-50);       /* Modals, dropdowns */
--color-bg-overlay: rgba(0, 0, 0, 0.5);               /* Modal backdrop */

--color-bg-primary: var(--color-primary-1-500);       /* Primary actions */
--color-bg-primary-hover: var(--color-primary-1-600); /* Hover state */
--color-bg-primary-active: var(--color-primary-1-700);/* Active state */

--color-bg-secondary: var(--color-secondary-1-500);
--color-bg-secondary-hover: var(--color-secondary-1-600);

--color-bg-success: var(--color-accent-1-500);
--color-bg-warning: var(--color-accent-2-500);
--color-bg-error: var(--color-accent-3-500);
--color-bg-info: var(--color-accent-4-500);

/* TEXT */
--color-text-base: var(--color-neutral-1-900);        /* Primary text */
--color-text-muted: var(--color-neutral-1-600);       /* Secondary text */
--color-text-disabled: var(--color-neutral-1-400);    /* Disabled text */
--color-text-inverse: var(--color-neutral-1-50);      /* Text on dark bg */

--color-text-primary: var(--color-primary-1-600);     /* Links, emphasis */
--color-text-success: var(--color-accent-1-700);
--color-text-warning: var(--color-accent-2-700);
--color-text-error: var(--color-accent-3-700);
--color-text-info: var(--color-accent-4-700);

/* BORDERS */
--color-border-default: var(--color-neutral-1-300);   /* Standard border */
--color-border-muted: var(--color-neutral-1-200);     /* Subtle border */
--color-border-strong: var(--color-neutral-1-400);    /* Emphasized border */

--color-border-focus: var(--color-primary-1-500);     /* Focus ring */
--color-border-error: var(--color-accent-3-500);      /* Error state */
--color-border-success: var(--color-accent-1-500);    /* Success state */

/* INTERACTIVE STATES */
--color-interactive-primary: var(--color-primary-1-500);
--color-interactive-primary-hover: var(--color-primary-1-600);
--color-interactive-primary-active: var(--color-primary-1-700);
--color-interactive-primary-disabled: var(--color-neutral-1-300);

--color-interactive-secondary: var(--color-secondary-1-500);
--color-interactive-secondary-hover: var(--color-secondary-1-600);
--color-interactive-secondary-active: var(--color-secondary-1-700);

/* SEMANTIC FEEDBACK */
--color-success-bg-subtle: var(--color-accent-1-50);
--color-success-bg: var(--color-accent-1-100);
--color-success-border: var(--color-accent-1-500);
--color-success-text: var(--color-accent-1-700);

--color-warning-bg-subtle: var(--color-accent-2-50);
--color-warning-bg: var(--color-accent-2-100);
--color-warning-border: var(--color-accent-2-500);
--color-warning-text: var(--color-accent-2-700);

--color-error-bg-subtle: var(--color-accent-3-50);
--color-error-bg: var(--color-accent-3-100);
--color-error-border: var(--color-accent-3-500);
--color-error-text: var(--color-accent-3-700);

--color-info-bg-subtle: var(--color-accent-4-50);
--color-info-bg: var(--color-accent-4-100);
--color-info-border: var(--color-accent-4-500);
--color-info-text: var(--color-accent-4-700);
```

---

### Level 4: SEMANTIC (Component Tokens)

**Purpose:** Component-specific tokens  
**Format:** `--color-{component}-{property}-{variant}`  
**References:** Only Level 3  
**No references to Level 1 or 2!**

```css
/* BUTTON */
--color-btn-primary-bg: var(--color-bg-primary);
--color-btn-primary-bg-hover: var(--color-bg-primary-hover);
--color-btn-primary-bg-active: var(--color-bg-primary-active);
--color-btn-primary-text: var(--color-text-inverse);
--color-btn-primary-border: var(--color-bg-primary);

--color-btn-secondary-bg: var(--color-bg-surface);
--color-btn-secondary-bg-hover: var(--color-neutral-1-200);
--color-btn-secondary-text: var(--color-text-base);
--color-btn-secondary-border: var(--color-border-default);

--color-btn-ghost-bg: transparent;
--color-btn-ghost-bg-hover: var(--color-neutral-1-100);
--color-btn-ghost-text: var(--color-text-primary);
--color-btn-ghost-border: transparent;

--color-btn-disabled-bg: var(--color-interactive-primary-disabled);
--color-btn-disabled-text: var(--color-text-disabled);

/* INPUT */
--color-input-bg: var(--color-bg-base);
--color-input-bg-disabled: var(--color-neutral-1-100);
--color-input-text: var(--color-text-base);
--color-input-text-placeholder: var(--color-text-muted);
--color-input-border: var(--color-border-default);
--color-input-border-hover: var(--color-border-strong);
--color-input-border-focus: var(--color-border-focus);
--color-input-border-error: var(--color-border-error);

/* CARD */
--color-card-bg: var(--color-bg-surface);
--color-card-border: var(--color-border-muted);
--color-card-shadow: rgba(0, 0, 0, 0.1);

/* BADGE */
--color-badge-success-bg: var(--color-success-bg);
--color-badge-success-text: var(--color-success-text);
--color-badge-success-border: var(--color-success-border);

--color-badge-warning-bg: var(--color-warning-bg);
--color-badge-warning-text: var(--color-warning-text);
--color-badge-warning-border: var(--color-warning-border);

--color-badge-error-bg: var(--color-error-bg);
--color-badge-error-text: var(--color-error-text);
--color-badge-error-border: var(--color-error-border);

--color-badge-info-bg: var(--color-info-bg);
--color-badge-info-text: var(--color-info-text);
--color-badge-info-border: var(--color-info-border);

--color-badge-neutral-bg: var(--color-neutral-1-100);
--color-badge-neutral-text: var(--color-text-muted);
--color-badge-neutral-border: var(--color-border-muted);

/* TABLE */
--color-table-header-bg: var(--color-neutral-1-100);
--color-table-header-text: var(--color-text-base);
--color-table-row-bg: var(--color-bg-base);
--color-table-row-bg-hover: var(--color-neutral-1-50);
--color-table-row-bg-selected: var(--color-primary-1-50);
--color-table-border: var(--color-border-muted);

/* MODAL */
--color-modal-bg: var(--color-bg-elevated);
--color-modal-overlay: var(--color-bg-overlay);
--color-modal-border: var(--color-border-default);
--color-modal-shadow: rgba(0, 0, 0, 0.2);
```

---

## 📏 Other Token Types

### Spacing Tokens (Similar 4-Layer)

**Level 1: BASE**
```css
--spacing-0: 0px;
--spacing-0-5: 2px;
--spacing-1: 4px;
--spacing-1-5: 6px;
--spacing-2: 8px;
--spacing-2-5: 10px;
--spacing-3: 12px;
--spacing-3-5: 14px;
--spacing-4: 16px;
--spacing-5: 20px;
--spacing-6: 24px;
--spacing-7: 28px;
--spacing-8: 32px;
--spacing-9: 36px;
--spacing-10: 40px;
--spacing-11: 44px;
--spacing-12: 48px;
--spacing-14: 56px;
--spacing-16: 64px;
--spacing-20: 80px;
--spacing-24: 96px;
--spacing-28: 112px;
--spacing-32: 128px;
```

**Level 2: GLOBAL (Semantic Sizes)**
```css
--spacing-xs: var(--spacing-2);     /* 8px */
--spacing-sm: var(--spacing-3);     /* 12px */
--spacing-md: var(--spacing-4);     /* 16px */
--spacing-lg: var(--spacing-6);     /* 24px */
--spacing-xl: var(--spacing-8);     /* 32px */
--spacing-2xl: var(--spacing-12);   /* 48px */
--spacing-3xl: var(--spacing-16);   /* 64px */
```

**Level 3: ROLES**
```css
--spacing-component-padding-sm: var(--spacing-sm);
--spacing-component-padding-md: var(--spacing-md);
--spacing-component-padding-lg: var(--spacing-lg);

--spacing-component-gap-sm: var(--spacing-xs);
--spacing-component-gap-md: var(--spacing-sm);
--spacing-component-gap-lg: var(--spacing-md);

--spacing-layout-gutter: var(--spacing-lg);
--spacing-layout-section: var(--spacing-2xl);
```

**Level 4: SEMANTIC**
```css
--spacing-btn-padding-x: var(--spacing-component-padding-md);
--spacing-btn-padding-y: var(--spacing-component-padding-sm);
--spacing-btn-gap: var(--spacing-component-gap-sm);

--spacing-input-padding-x: var(--spacing-component-padding-md);
--spacing-input-padding-y: var(--spacing-component-padding-sm);

--spacing-card-padding: var(--spacing-component-padding-lg);
--spacing-card-gap: var(--spacing-component-gap-md);
```

---

### Typography Tokens

**Level 1: BASE**
```css
/* Font Families */
--font-family-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
--font-family-serif: 'Merriweather', Georgia, serif;
--font-family-mono: 'JetBrains Mono', 'Fira Code', monospace;

/* Font Sizes */
--font-size-xs: 0.75rem;    /* 12px */
--font-size-sm: 0.875rem;   /* 14px */
--font-size-base: 1rem;     /* 16px */
--font-size-lg: 1.125rem;   /* 18px */
--font-size-xl: 1.25rem;    /* 20px */
--font-size-2xl: 1.5rem;    /* 24px */
--font-size-3xl: 1.875rem;  /* 30px */
--font-size-4xl: 2.25rem;   /* 36px */
--font-size-5xl: 3rem;      /* 48px */

/* Font Weights */
--font-weight-light: 300;
--font-weight-normal: 400;
--font-weight-medium: 500;
--font-weight-semibold: 600;
--font-weight-bold: 700;

/* Line Heights */
--line-height-tight: 1.25;
--line-height-normal: 1.5;
--line-height-relaxed: 1.75;
--line-height-loose: 2;

/* Letter Spacing */
--letter-spacing-tight: -0.025em;
--letter-spacing-normal: 0em;
--letter-spacing-wide: 0.025em;
```

**Level 2: GLOBAL (Text Styles)**
```css
--text-display: var(--font-size-4xl) var(--font-weight-bold);
--text-h1: var(--font-size-3xl) var(--font-weight-bold);
--text-h2: var(--font-size-2xl) var(--font-weight-semibold);
--text-h3: var(--font-size-xl) var(--font-weight-semibold);
--text-h4: var(--font-size-lg) var(--font-weight-medium);
--text-body: var(--font-size-base) var(--font-weight-normal);
--text-small: var(--font-size-sm) var(--font-weight-normal);
--text-caption: var(--font-size-xs) var(--font-weight-normal);
```

**Level 3: ROLES**
```css
--text-heading-primary: var(--text-h1);
--text-heading-secondary: var(--text-h2);
--text-body-primary: var(--text-body);
--text-body-secondary: var(--text-small);
--text-label: var(--text-small);
```

**Level 4: SEMANTIC**
```css
--text-btn-label: var(--text-body-primary);
--text-input-value: var(--text-body-primary);
--text-input-placeholder: var(--text-body-secondary);
--text-card-title: var(--text-heading-secondary);
--text-card-description: var(--text-body-secondary);
```

---

### Border Radius Tokens

**Level 1: BASE**
```css
--radius-none: 0px;
--radius-sm: 0.125rem;   /* 2px */
--radius-base: 0.25rem;  /* 4px */
--radius-md: 0.375rem;   /* 6px */
--radius-lg: 0.5rem;     /* 8px */
--radius-xl: 0.75rem;    /* 12px */
--radius-2xl: 1rem;      /* 16px */
--radius-3xl: 1.5rem;    /* 24px */
--radius-full: 9999px;   /* Pill shape */
```

**Level 2-4:** Similar pattern as above

---

### Shadow Tokens

**Level 1: BASE**
```css
--shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.05);
--shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06);
--shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07), 0 2px 4px rgba(0, 0, 0, 0.06);
--shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.05);
--shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.1), 0 10px 10px rgba(0, 0, 0, 0.04);
--shadow-2xl: 0 25px 50px rgba(0, 0, 0, 0.25);
```

**Level 2-4:** Mapped to component needs

---

## 🛠️ Technical Implementation

### Tech Stack

**Design Tokens:**
- ✅ **Style Dictionary** - Token transformation
- ✅ **DTCG Format** - W3C Community Group standard
- ✅ **Multi-platform** - CSS, SCSS, JS, iOS, Android

**Component Library:**
- ✅ **React + TypeScript** - Component framework
- ✅ **Tailwind CSS** - Utility-first styling (with custom tokens)
- ✅ **Radix UI** - Headless primitives (accessibility)
- ✅ **CVA** (class-variance-authority) - Component variants

**Documentation:**
- ✅ **Storybook** - Component playground
- ✅ **Zero** (or similar) - Token documentation
- ✅ **MDX** - Rich documentation

**Quality:**
- ✅ **ESLint + Prettier** - Code quality
- ✅ **Vitest** - Testing
- ✅ **Chromatic** - Visual regression
- ✅ **Axe** - Accessibility testing

---

## 📦 Repository Structure

```
@nordlig/design-system/
├── packages/
│   ├── tokens/                      # Design Tokens
│   │   ├── src/
│   │   │   ├── base/               # Level 1: Base tokens
│   │   │   │   ├── colors.json
│   │   │   │   ├── spacing.json
│   │   │   │   ├── typography.json
│   │   │   │   └── ...
│   │   │   ├── global/             # Level 2: Global tokens
│   │   │   │   ├── colors.json     # primary-1, secondary-1, etc.
│   │   │   │   └── ...
│   │   │   ├── roles/              # Level 3: Role tokens
│   │   │   │   ├── colors.json     # bg-primary, text-base, etc.
│   │   │   │   └── ...
│   │   │   └── semantic/           # Level 4: Component tokens
│   │   │       ├── button.json
│   │   │       ├── input.json
│   │   │       └── ...
│   │   ├── style-dictionary.config.js
│   │   └── package.json
│   │
│   ├── components/                  # React Components
│   │   ├── src/
│   │   │   ├── atoms/
│   │   │   │   ├── Button/
│   │   │   │   │   ├── Button.tsx
│   │   │   │   │   ├── Button.stories.tsx
│   │   │   │   │   ├── Button.test.tsx
│   │   │   │   │   └── index.ts
│   │   │   │   ├── Input/
│   │   │   │   ├── Badge/
│   │   │   │   └── ...
│   │   │   ├── molecules/
│   │   │   │   ├── InputField/
│   │   │   │   └── ...
│   │   │   ├── organisms/
│   │   │   │   ├── Card/
│   │   │   │   ├── Table/
│   │   │   │   └── ...
│   │   │   └── index.ts
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   └── styles/                      # Generated CSS
│       ├── dist/
│       │   ├── tokens.css          # All tokens as CSS vars
│       │   ├── tailwind.config.js  # Tailwind config
│       │   └── themes/             # Theme variants
│       │       ├── light.css
│       │       ├── dark.css
│       │       └── ...
│       └── package.json
│
├── apps/
│   ├── storybook/                  # Storybook app
│   │   ├── .storybook/
│   │   ├── stories/
│   │   └── package.json
│   │
│   └── docs/                       # Documentation site
│       ├── src/
│       │   ├── pages/
│       │   │   ├── index.mdx
│       │   │   ├── tokens/
│       │   │   │   ├── colors.mdx
│       │   │   │   ├── spacing.mdx
│       │   │   │   └── ...
│       │   │   └── components/
│       │   │       ├── button.mdx
│       │   │       └── ...
│       │   └── components/
│       └── package.json
│
├── .github/
│   └── workflows/
│       ├── release.yml             # NPM publish
│       ├── chromatic.yml           # Visual tests
│       └── test.yml                # Unit tests
│
├── package.json
├── pnpm-workspace.yaml
├── turbo.json                      # Monorepo build
└── README.md
```

---

## 🎨 Style Dictionary Configuration

```javascript
// packages/tokens/style-dictionary.config.js

module.exports = {
  source: [
    'src/base/**/*.json',
    'src/global/**/*.json',
    'src/roles/**/*.json',
    'src/semantic/**/*.json',
  ],
  platforms: {
    // CSS Variables
    css: {
      transformGroup: 'css',
      buildPath: '../styles/dist/',
      files: [{
        destination: 'tokens.css',
        format: 'css/variables',
        options: {
          outputReferences: true  // Keep var() references
        }
      }]
    },
    
    // Tailwind Config
    tailwind: {
      transformGroup: 'js',
      buildPath: '../styles/dist/',
      files: [{
        destination: 'tailwind.config.js',
        format: 'tailwind/config'
      }]
    },
    
    // TypeScript
    ts: {
      transformGroup: 'js',
      buildPath: '../components/src/tokens/',
      files: [{
        destination: 'tokens.ts',
        format: 'javascript/es6'
      }]
    },
    
    // JSON (for MCP, Figma, etc.)
    json: {
      transformGroup: 'js',
      buildPath: 'dist/',
      files: [{
        destination: 'tokens.json',
        format: 'json/flat'
      }]
    }
  }
};
```

---

## 📖 Token File Example (DTCG Format)

```json
// packages/tokens/src/base/colors.json
{
  "color": {
    "base": {
      "sky": {
        "50": {
          "$type": "color",
          "$value": "#f0f9ff",
          "$description": "Sky color palette - Lightest shade"
        },
        "100": {
          "$type": "color",
          "$value": "#e0f2fe"
        },
        "500": {
          "$type": "color",
          "$value": "#0ea5e9",
          "$description": "Sky color palette - Main shade"
        }
      }
    }
  }
}
```

```json
// packages/tokens/src/global/colors.json
{
  "color": {
    "primary": {
      "1": {
        "50": {
          "$type": "color",
          "$value": "{color.base.sky.50}",
          "$description": "Primary color palette 1 - based on sky"
        },
        "500": {
          "$type": "color",
          "$value": "{color.base.sky.500}"
        }
      }
    }
  }
}
```

```json
// packages/tokens/src/roles/backgrounds.json
{
  "color": {
    "bg": {
      "primary": {
        "$type": "color",
        "$value": "{color.primary.1.500}",
        "$description": "Primary background color for main actions"
      },
      "surface": {
        "$type": "color",
        "$value": "{color.neutral.1.100}",
        "$description": "Surface background for cards and panels"
      }
    }
  }
}
```

```json
// packages/tokens/src/semantic/button.json
{
  "color": {
    "btn": {
      "primary": {
        "bg": {
          "$type": "color",
          "$value": "{color.bg.primary}",
          "$description": "Button primary background"
        },
        "text": {
          "$type": "color",
          "$value": "{color.text.inverse}"
        }
      }
    }
  }
}
```

---

## 🧩 Component Example

```typescript
// packages/components/src/atoms/Button/Button.tsx

import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../utils/cn';

const buttonVariants = cva(
  // Base styles (applies to all variants)
  'inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        primary: 'bg-[var(--color-btn-primary-bg)] text-[var(--color-btn-primary-text)] border border-[var(--color-btn-primary-border)] hover:bg-[var(--color-btn-primary-bg-hover)] active:bg-[var(--color-btn-primary-bg-active)]',
        secondary: 'bg-[var(--color-btn-secondary-bg)] text-[var(--color-btn-secondary-text)] border border-[var(--color-btn-secondary-border)] hover:bg-[var(--color-btn-secondary-bg-hover)]',
        ghost: 'bg-[var(--color-btn-ghost-bg)] text-[var(--color-btn-ghost-text)] hover:bg-[var(--color-btn-ghost-bg-hover)]',
      },
      size: {
        sm: 'h-9 px-3 text-sm',
        md: 'h-10 px-4 py-2',
        lg: 'h-11 px-8',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);

Button.displayName = 'Button';

export { Button, buttonVariants };
```

```typescript
// packages/components/src/atoms/Button/Button.stories.tsx

import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './Button';

const meta: Meta<typeof Button> = {
  title: 'Atoms/Button',
  component: Button,
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['primary', 'secondary', 'ghost'],
    },
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg'],
    },
  },
};

export default meta;
type Story = StoryObj<typeof Button>;

export const Primary: Story = {
  args: {
    variant: 'primary',
    children: 'Primary Button',
  },
};

export const Secondary: Story = {
  args: {
    variant: 'secondary',
    children: 'Secondary Button',
  },
};

export const Ghost: Story = {
  args: {
    variant: 'ghost',
    children: 'Ghost Button',
  },
};

export const AllSizes: Story = {
  render: () => (
    <div className="flex gap-4 items-center">
      <Button size="sm">Small</Button>
      <Button size="md">Medium</Button>
      <Button size="lg">Large</Button>
    </div>
  ),
};
```

---

## 🎭 MCP Integration

### Figma → Code Workflow

```
┌─────────────┐
│   Figma     │
│  UI Kit     │
└──────┬──────┘
       │ Figma MCP Server
       │ (Design tokens export)
       ↓
┌─────────────┐
│  Claude AI  │
│  (via MCP)  │
└──────┬──────┘
       │ Interprets tokens
       │ Maps to Nordlig DS
       ↓
┌─────────────┐
│  React Code │
│  Components │
└─────────────┘
```

**Token Export Format (MCP-ready JSON):**
```json
{
  "figma": {
    "colors": {
      "primary": "#0ea5e9",
      "background": "#f8fafc"
    },
    "typography": {
      "heading": "32px/bold",
      "body": "16px/regular"
    },
    "spacing": {
      "sm": "8px",
      "md": "16px"
    }
  },
  "nordlig": {
    "mapping": {
      "figma.colors.primary": "color.primary.1.500",
      "figma.colors.background": "color.bg.base"
    }
  }
}
```

**Code Connect Example:**
```typescript
// Figma Code Connect config
figma.connect(Button, {
  variant: {
    Primary: { variant: 'primary' },
    Secondary: { variant: 'secondary' },
  },
  size: {
    Small: { size: 'sm' },
    Medium: { size: 'md' },
    Large: { size: 'lg' },
  },
});
```

---

## 📅 Implementation Roadmap

### Phase 1: Foundation (Week 1-2) 🔴 CRITICAL
**Goal:** Setup infrastructure & core tokens

**Tasks:**
- [ ] Setup monorepo (pnpm + Turbo)
- [ ] Configure Style Dictionary
- [ ] Define Level 1 (Base) tokens
  - [ ] Colors (all palettes)
  - [ ] Spacing
  - [ ] Typography
  - [ ] Shadows
  - [ ] Radii
- [ ] Define Level 2 (Global) tokens
  - [ ] Primary 1-2
  - [ ] Secondary 1-2
  - [ ] Accent 1-5
  - [ ] Neutral 1-2
- [ ] Generate CSS variables
- [ ] Setup Tailwind config
- [ ] Create documentation structure

**Deliverables:**
- ✅ NPM package structure
- ✅ Token JSON files (DTCG format)
- ✅ Generated CSS vars
- ✅ Tailwind config

---

### Phase 2: Core Components (Week 3-4) 🟠 HIGH
**Goal:** Build atomic components for Training Analyzer

**Tasks:**
- [ ] Define Level 3 (Roles) tokens
- [ ] Define Level 4 (Semantic) tokens for core components
- [ ] Build Atoms:
  - [ ] Button (primary, secondary, ghost)
  - [ ] Input (text, number, date)
  - [ ] Label
  - [ ] Badge (success, warning, error, info, neutral)
  - [ ] Icon (wrapper)
- [ ] Build Molecules:
  - [ ] InputField (Label + Input + Error)
  - [ ] Select (Dropdown)
- [ ] Setup Storybook
- [ ] Write component tests

**Deliverables:**
- ✅ 6-8 core components
- ✅ Storybook documentation
- ✅ Unit tests >80%

---

### Phase 3: Integration (Week 5) 🟠 HIGH
**Goal:** Integrate into Training Analyzer

**Tasks:**
- [ ] Install `@nordlig/design-system` in Training Analyzer
- [ ] Replace existing components with Nordlig components
- [ ] Apply theme tokens
- [ ] Test responsive behavior
- [ ] Accessibility audit

**Deliverables:**
- ✅ Training Analyzer using Nordlig DS
- ✅ WCAG 2.1 AA compliance

---

### Phase 4: Advanced Components (Week 6-8) 🟡 MEDIUM
**Goal:** Build organisms & templates

**Tasks:**
- [ ] Build Organisms:
  - [ ] Card
  - [ ] Table
  - [ ] Modal
  - [ ] Toast/Notification
- [ ] Build Templates:
  - [ ] DashboardTemplate
  - [ ] DetailTemplate
- [ ] Add component variants
- [ ] Documentation improvements

---

### Phase 5: Theming & Customization (Week 9-10) 🟡 MEDIUM
**Goal:** Multi-theme support

**Tasks:**
- [ ] Dark theme implementation
- [ ] Alternative themes (Forest, Ocean, etc.)
- [ ] Theme switcher component
- [ ] Theme documentation

---

### Phase 6: Figma Integration (Week 11-12) ⏳ PLANNED
**Goal:** Design ↔ Code sync

**Tasks:**
- [ ] Create Figma UI Kit
- [ ] Map components to Figma
- [ ] Setup Code Connect
- [ ] MCP server for token export
- [ ] Bidirectional sync testing

---

## 📊 Success Metrics

### Quality Metrics
- ✅ **Token Coverage:** 100% of colors through 4 layers
- ✅ **Component Coverage:** All Training Analyzer needs
- ✅ **Test Coverage:** >80% unit tests
- ✅ **Accessibility:** WCAG 2.1 AA minimum
- ✅ **Performance:** <50kb bundle size

### Process Metrics
- ✅ **Documentation:** Every token & component documented
- ✅ **Storybook:** All components with stories
- ✅ **MCP Ready:** Token JSON exports
- ✅ **Figma Sync:** Code Connect working

---

## 🚀 Getting Started (After Setup)

### Installation
```bash
npm install @nordlig/design-system
```

### Usage
```typescript
// Import tokens CSS
import '@nordlig/design-system/tokens.css';

// Import components
import { Button, Input, Badge } from '@nordlig/design-system';

function App() {
  return (
    <div>
      <Button variant="primary" size="md">
        Click me
      </Button>
      <Input placeholder="Enter text..." />
      <Badge variant="success">Active</Badge>
    </div>
  );
}
```

### Tailwind Config
```javascript
// tailwind.config.js
import nordligConfig from '@nordlig/design-system/tailwind.config';

export default {
  presets: [nordligConfig],
  content: [
    './src/**/*.{ts,tsx}',
    './node_modules/@nordlig/design-system/**/*.{js,ts,jsx,tsx}',
  ],
};
```

---

## 📚 Documentation Structure

```
docs.nordlig.design/
├── Getting Started
│   ├── Installation
│   ├── Quick Start
│   └── Migration Guide
├── Design Tokens
│   ├── Overview
│   ├── Colors
│   │   ├── Base Palettes
│   │   ├── Global Theme Colors
│   │   ├── Role Colors
│   │   └── Semantic Colors
│   ├── Spacing
│   ├── Typography
│   ├── Shadows
│   └── Radii
├── Components
│   ├── Atoms
│   │   ├── Button
│   │   ├── Input
│   │   └── Badge
│   ├── Molecules
│   └── Organisms
├── Patterns
│   ├── Forms
│   ├── Navigation
│   └── Data Display
├── Theming
│   ├── Creating Themes
│   ├── Dark Mode
│   └── Custom Themes
├── Accessibility
│   ├── Guidelines
│   ├── Testing
│   └── Keyboard Navigation
└── Figma Integration
    ├── UI Kit Setup
    ├── Code Connect
    └── MCP Server
```

---

## ✅ Next Steps

### Immediate (This Week):
1. Create GitHub repo: `nordlig-design-system`
2. Setup monorepo structure (pnpm + Turbo)
3. Configure Style Dictionary
4. Define Level 1 Base tokens (colors, spacing, typography)
5. Generate first CSS variables

### Short Term (Next 2 Weeks):
1. Define Level 2-4 tokens
2. Build Button, Input, Badge components
3. Setup Storybook
4. Write tests

### Medium Term (Month 1-2):
1. Integrate into Training Analyzer
2. Build remaining components
3. Theme support
4. Documentation site

### Long Term (Month 3+):
1. Figma UI Kit
2. Code Connect integration
3. MCP server
4. Multi-project usage

---

**Status:** 📋 Ready for Implementation  
**Next Action:** Create repo & setup monorepo structure

---

**Dieses Dokument ist lebendig - wird mit Design System weiterentwickelt!** 🎨
