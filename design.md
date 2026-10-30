---
version: alpha
name: Sarvam AI

description: Design system for Sarvam AI — a confident, culturally rooted Indian AI platform. The visual language blends warm saffron-orange gradients with a professional light aesthetic, anchored by proprietary variable typefaces and a clean, enterprise-grade layout.

colors:
  # Core text colors (from --color-tx-* :root vars)
  on-surface: "#1f1f1f"
  on-surface-secondary: "#3d3d3d"
  on-surface-tertiary: "#666666"
  on-surface-inverse: "#faf8f5"
  on-surface-brand: "#29211d"
  on-surface-accent: "#c4733d"

  # Surface colors (from --color-sf-* :root vars)
  surface: "#fcfcfc"
  surface-secondary: "#f5f5f5"
  surface-tertiary: "#f0f0f0"
  surface-quaternary: "#e6e6e6"

  # Stroke/border colors (from --color-st-* :root vars)
  stroke: "#e6e6e6"
  stroke-secondary: "#f0f0f0"

  # Brand palette (from --color-br-* :root vars)
  primary: "#2a2c33"
  on-primary: "#ffffff"
  secondary: "#393cc1"
  on-secondary: "#ffffff"
  tertiary: "#d5650f"
  on-tertiary: "#ffffff"

  # Semantic SR palettes — indigo scale
  sr-indigo-50: "#fafcff"
  sr-indigo-100: "#e8effc"
  sr-indigo-200: "#d2dff9"
  sr-indigo-300: "#a7c0f1"
  sr-indigo-400: "#81a0e9"
  sr-indigo-500: "#6a88e2"
  sr-indigo-600: "#556adc"
  sr-indigo-700: "#4250d5"
  sr-indigo-800: "#3333cc"
  sr-indigo-900: "#212191"
  sr-indigo-950: "#11115b"

  # SR orange scale
  sr-orange-50: "#fffbfa"
  sr-orange-100: "#feede6"
  sr-orange-200: "#fddcce"
  sr-orange-300: "#f9bb9e"
  sr-orange-400: "#f59970"
  sr-orange-500: "#f38858"
  sr-orange-600: "#ee7944"
  sr-orange-700: "#e96c2f"
  sr-orange-800: "#e6651b"
  sr-orange-900: "#a5460f"
  sr-orange-950: "#682906"

  # SR green scale
  sr-green-50: "#f2f8eb"
  sr-green-100: "#e3f1d8"
  sr-green-200: "#c8e4b0"
  sr-green-300: "#acd587"
  sr-green-400: "#90c85b"
  sr-green-500: "#83c040"
  sr-green-600: "#6ea335"
  sr-green-700: "#496d21"
  sr-green-800: "#385418"
  sr-green-900: "#263d0e"

  # SR grey scale
  sr-grey-50: "#f9f9f9"
  sr-grey-100: "#f5f5f5"
  sr-grey-200: "#f0f0f0"
  sr-grey-300: "#e6e6e6"
  sr-grey-400: "#cccccc"
  sr-grey-500: "#b3b3b3"
  sr-grey-600: "#999999"
  sr-grey-700: "#666666"
  sr-grey-800: "#525252"
  sr-grey-900: "#3d3d3d"
  sr-grey-950: "#292929"

  # SR red scale
  sr-red-400: "#c43d2b"
  sr-red-500: "#b81514"

  # SR yellow scale
  sr-yellow-300: "#ffcb79"
  sr-yellow-500: "#feb12b"

  # SR pink scale
  sr-pink-400: "#d4508e"
  sr-pink-500: "#b12060"

  # Neutrals
  neutral: "#141414"
  error: "#b81514"
  on-error: "#ffffff"

  # Link
  link: "#4250d5"

typography:
  headline-display:
    fontFamily: Season Mix
    fontFallback: Playfair Display
    fontSize: 64px
    fontWeight: "425"
    lineHeight: 67.2px
    letterSpacing: -0.025em

  headline-lg:
    fontFamily: Season Mix
    fontFallback: Playfair Display
    fontSize: 56px
    fontWeight: "425"
    lineHeight: 1.2
    letterSpacing: -0.02em

  headline-md:
    fontFamily: Season Mix
    fontFallback: Playfair Display
    fontSize: 40px
    fontWeight: "425"
    lineHeight: 1.2

  headline-sm:
    fontFamily: Season Mix
    fontFallback: Playfair Display
    fontSize: 28px
    fontWeight: "500"
    lineHeight: 1.2

  title-lg:
    fontFamily: Matter
    fontFallback: Inter
    fontSize: 20px
    fontWeight: "525"
    lineHeight: 1.4

  body-lg:
    fontFamily: Matter
    fontFallback: Inter
    fontSize: 18px
    fontWeight: "400"
    lineHeight: 1.6

  body-md:
    fontFamily: Matter
    fontFallback: Inter
    fontSize: 16px
    fontWeight: "400"
    lineHeight: 1.5
    letterSpacing: 0.025em

  body-sm:
    fontFamily: Matter
    fontFallback: Inter
    fontSize: 15px
    fontWeight: "400"
    lineHeight: 1.65

  label-lg:
    fontFamily: Matter
    fontFallback: Inter
    fontSize: 14px
    fontWeight: "525"
    lineHeight: 1.5

  label-md:
    fontFamily: Matter
    fontFallback: Inter
    fontSize: 12px
    fontWeight: "425"
    lineHeight: 1.5

  label-sm:
    fontFamily: Matter Mono
    fontFallback: JetBrains Mono
    fontSize: 10px
    fontWeight: "400"
    lineHeight: 1.4

  code:
    fontFamily: Matter Mono
    fontFallback: JetBrains Mono
    fontSize: 14px
    fontWeight: "400"
    lineHeight: 1.5

rounded:
  none: 0px
  sm: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  2xl: 1rem
  3xl: 1.5rem
  card: 1rem
  card-lg: 32px
  full: 9999px

spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 32px
  xl: 48px
  2xl: 96px
  3xl: 128px
  gutter: 16px
  margin: 32px

shadows:
  sm: "0 1px 3px rgba(0,0,0,0.08)"
  md: "0 4px 24px rgba(0,0,0,0.12)"
  lg: "0 12px 40px -8px rgba(0,0,0,0.12)"
  xl: "0px 0px 40px 0px rgba(0,0,0,0.06)"
  card: "0px 6px 70px 44px rgba(0,0,0,0.10), 0px 0px 18.6px 0px rgba(20,20,20,0.08)"
  button-filled: "inset 0 0 12px #ffffff, 0px 0px 2px 0 rgba(0,0,0,0.10)"
  button-outline: "inset 0 0 12px rgba(0,0,0,0.09), 0px 0px 1px rgba(0,0,0,0.20)"

components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label-lg}"
    rounded: "{rounded.full}"
    padding: "8px 20px"

  button-primary-hover:
    backgroundColor: "{colors.sr-grey-950}"
    textColor: "{colors.on-primary}"

  button-secondary:
    backgroundColor: "{colors.surface-tertiary}"
    textColor: "{colors.on-surface}"
    typography: "{typography.label-lg}"
    rounded: "{rounded.full}"
    padding: "8px 20px"

  button-secondary-hover:
    backgroundColor: "{colors.stroke}"
    textColor: "{colors.on-surface}"

  card:
    backgroundColor: "{colors.on-primary}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.card}"
    padding: "{spacing.lg}"

  badge:
    backgroundColor: "{colors.sr-green-100}"
    textColor: "{colors.sr-green-800}"
    typography: "{typography.label-md}"
    rounded: "{rounded.full}"
    padding: "0px 8px"

  badge-orange:
    backgroundColor: "{colors.sr-orange-100}"
    textColor: "{colors.sr-orange-900}"
    typography: "{typography.label-md}"
    rounded: "{rounded.full}"
    padding: "0px 8px"

  nav-link:
    textColor: "{colors.on-surface}"
    typography: "{typography.body-md}"

  nav-link-hover:
    textColor: "{colors.on-surface-tertiary}"

  link:
    textColor: "{colors.link}"

  link-hover:
    textColor: "{colors.on-surface-tertiary}"

  table-header:
    backgroundColor: "{colors.surface-secondary}"
    textColor: "{colors.on-surface}"
    typography: "{typography.label-lg}"
    padding: "6px 12px"

  input-field:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body-md}"
    rounded: "{rounded.lg}"

  code-block:
    backgroundColor: "{colors.sr-grey-50}"
    textColor: "{colors.on-surface}"
    typography: "{typography.code}"
    rounded: "{rounded.xl}"
---

## Overview

Sarvam AI is a confident, culturally rooted Indian AI platform built for enterprise-grade audiences. The design system reflects this duality: professional precision paired with warm, energetic accents drawn from saffron and indigo — colors that carry deep cultural resonance.

The overall design voice is **clean and purposeful**. The interface relies on generous whitespace, a restrained neutral palette for surfaces, and focused accent usage to communicate intelligence and reliability. The typographic system pairs the variable display font **Season Mix** (for editorial impact in headlines) with **Matter** (for crisp, legible UI body copy), creating a hierarchy that feels both human and technical.

The design is light-mode only, with no dark mode overrides detected.

## Colors

The color system is organized around functional roles: text (on-surface), backgrounds (surface), borders (stroke), brand accents, and full semantic palettes for status communication.

- **Primary:** {colors.primary} — a near-black slate used for primary interactive elements (buttons, high-emphasis UI). Conveys authority and precision.
- **Secondary:** {colors.secondary} — deep indigo used for links, interactive accents, and brand identity moments.
- **Tertiary:** {colors.tertiary} — a warm saffron-orange used for badges, gradient anchors, and cultural warmth. Never use as a primary button background.
- **Surface:** {colors.surface} — near-white page background at 99% lightness. Keeps content legible and light.
- **On-Surface:** {colors.on-surface} — primary text at near-black for maximum contrast on light surfaces.
- **On-Surface Secondary/Tertiary:** {colors.on-surface-secondary} and {colors.on-surface-tertiary} — used for supporting text, captions, and metadata to establish clear typographic hierarchy.
- **Stroke:** {colors.stroke} — neutral border color used for dividers, card outlines, and form field borders.
- **Error:** {colors.error} — the sr-red-500 token, used exclusively for error states and destructive actions.
- **SR Indigo Scale:** A custom semantic indigo ramp from {colors.sr-indigo-50} through {colors.sr-indigo-950} used for interactive, informational, and brand-blue contexts.
- **SR Orange Scale:** A custom warm orange ramp from {colors.sr-orange-50} through {colors.sr-orange-950} used for brand accent gradients and warm badges.
- **SR Green Scale:** A custom green ramp used for success badges and positive indicators.
- **SR Grey Scale:** A full neutral ramp from {colors.sr-grey-50} through {colors.sr-grey-950} used for all structural neutrals, disabled states, and backgrounds.

## Typography

This system employs two proprietary variable typefaces that are not available on Google Fonts. Fallback substitutions are specified below.

- **Season Mix** — A variable serif/mixed-axis display typeface used exclusively for headline levels. It brings editorial character and cultural distinctiveness to large-scale text. Google Font fallback: **Playfair Display**.
- **Matter** — A variable sans-serif used for all UI body copy, labels, navigation, and interactive text. It is clean, highly legible, and neutral at body sizes while remaining expressive at display weights. Google Font fallback: **Inter**.
- **Matter Mono** — A monospaced variant of Matter used for code blocks and technical content. Google Font fallback: **JetBrains Mono**.

Note: Because Season Mix and Matter are proprietary fonts served from self-hosted WOFF2 files, any reproduction of this system should use the listed Google Font fallbacks. The visual character will differ slightly in weight distribution and axis feel.

**Type Scale:**

- **headline-display** ({typography.headline-display.fontSize}): Season Mix at weight ~425. Used for hero section titles and primary marketing statements. Letter-spacing tightened to -0.025em.
- **headline-lg** ({typography.headline-lg.fontSize}): Season Mix. Used for page-level section headings.
- **headline-md** ({typography.headline-md.fontSize}): Season Mix. Used for card or subsection headings.
- **headline-sm** ({typography.headline-sm.fontSize}): Season Mix. Used for minor headings and large labels.
- **title-lg** ({typography.title-lg.fontSize}): Matter at weight ~525. Used for card titles and prominent UI labels.
- **body-lg** ({typography.body-lg.fontSize}): Matter at weight 400. Used for lead paragraphs and prominent descriptions.
- **body-md** ({typography.body-md.fontSize}): Matter at weight 400. Standard paragraph text.
- **body-sm** ({typography.body-sm.fontSize}): Matter at weight 400. Dense UI text, table cells.
- **label-lg** ({typography.label-lg.fontSize}): Matter at weight ~525. Button labels, form labels.
- **label-md** ({typography.label-md.fontSize}): Matter at weight ~425. Badge text, metadata, captions.
- **label-sm** ({typography.label-sm.fontSize}): Matter Mono. Micro labels, timestamps, secondary metadata.
- **code** ({typography.code.fontSize}): Matter Mono. All code and technical string content.

## Layout & Spacing

The spacing system is built on a **4px base unit** (`--spacing-base: 4px`), following a standard 4-point grid. All spacing increments are multiples of this unit.

- **xs:** {spacing.xs} — tight internal padding, icon gaps.
- **sm:** {spacing.sm} — intra-component spacing, badge padding.
- **md:** {spacing.md} — standard element spacing, list gaps.
- **lg:** {spacing.lg} — card internal padding, form field heights.
- **xl:** {spacing.xl} — section inner padding (`--spacing-section-inner: 48px`).
- **2xl:** {spacing.2xl} — smaller section-to-section gaps (`--spacing-section-gap-sm: 96px`).
- **3xl:** {spacing.3xl} — full section separation (`--spacing-section-gap: 128px`).
- **gutter:** {spacing.gutter} — column gutter width.
- **margin:** {spacing.margin} — page-level horizontal margin.

The maximum content width is 1400px (`--spacing-width-mx`), and the maximum height for key content panels is 1080px (`--spacing-height-mx`). Container sizes follow a standard ramp from `20rem` (xs) to `80rem` (7xl).

The layout uses a fluid grid approach typical of Tailwind-configured sites, centering content with horizontal margins and a fixed max-width clamp.

## Elevation & Depth

Elevation is communicated through a family of ambient shadows, avoiding harsh drop shadows in favor of soft, diffused layers that preserve the light, clean aesthetic.

- **sm:** {shadows.sm} — subtle lift for interactive states on small elements.
- **md:** {shadows.md} — standard card and panel elevation.
- **lg:** {shadows.lg} — modal dialogs, dropdown menus, popovers.
- **xl:** {shadows.xl} — full-screen overlay panels, feature cards.
- **card:** {shadows.card} — the primary card shadow combining a broad ambient halo with a tight proximity shadow for depth without weight.
- **button-filled:** {shadows.button-filled} — inset highlight glow plus a tight perimeter stroke for filled buttons, creating a premium tactile feel.
- **button-outline:** {shadows.button-outline} — inset dark glow plus a perimeter stroke for outline/secondary buttons.

Inset shadows (glow-white, glow-dark, glow-indigo) and focus rings (ring-indigo, ring-red) are used for interactive feedback and accessibility. Focus states use a 3px indigo ring with low opacity.

## Shapes

The shape language uses **rounded corners** at a moderate to generous radius, creating a professional yet approachable interface. Sharp (zero) radius is never used on interactive surfaces.

- **sm** ({rounded.sm}) — minor radius for tags and internal UI chips.
- **md** ({rounded.md}) — small interactive elements, table cell badges.
- **lg** ({rounded.lg}) — form inputs and select fields.
- **xl** ({rounded.xl}) — content chips, info blocks.
- **card** ({rounded.card} = 1rem) — standard card container radius, directly aliased from `--radius-2xl`.
- **card-lg** ({rounded.card-lg} = 32px) — large feature cards and hero panels.
- **full** ({rounded.full}) — all pill-style buttons (primary and secondary) and status badges. This is a signature shape element of the Sarvam AI brand.

## Components

### Buttons

Both primary and secondary buttons use a pill shape ({rounded.full}), which is the definitive brand button signature. Pill radius must never be reduced on CTAs.

The **button-primary** uses {colors.primary} (near-black slate) with white text and an inset gloss shadow ({shadows.button-filled}) for a premium, tactile quality. Padding is compact at `8px 20px` with {typography.label-lg} typography.

The **button-secondary** uses {colors.surface-tertiary} background with {colors.on-surface} text and the outline glow shadow ({shadows.button-outline}). It sits at the same height as the primary button for consistent alignment.

### Cards

The **card** component uses a pure white ({colors.on-primary}) background against the near-white page surface, with a 1px {colors.stroke} border and a generous compound box shadow ({shadows.card}) to create a clearly elevated, floating appearance. Corner radius is {rounded.card}.

Large feature cards use {rounded.card-lg} (32px) for a more expressive, editorial panel feel.

### Badges

Two badge variants are defined by semantic intent:

- **badge** (green): {colors.sr-green-100} background with {colors.sr-green-800} text — used for success, availability, and positive status.
- **badge-orange**: {colors.sr-orange-100} background with {colors.sr-orange-900} text — used for warm accent states, promotional tags, or beta indicators.

All badges use {rounded.full} and {typography.label-md}.

### Navigation

**nav-link** uses {typography.body-md} at standard weight with {colors.on-surface} text. On hover, text shifts to {colors.on-surface-tertiary} for a subtle fade effect that communicates interactivity without heavy visual change.

### Links

Inline **link** uses {colors.link} (sr-indigo-700) with an underline decoration. On hover, color transitions to {colors.on-surface-tertiary} at 80% opacity.

### Table Headers

**table-header** uses {colors.surface-secondary} background with {colors.on-surface} text, {typography.label-lg} weight, and `6px 12px` padding. Letter-spacing is slightly tightened for dense tabular contexts.

### Inputs

**input-field** uses the base {colors.surface} background with {colors.on-surface} text and {rounded.lg} corner radius, keeping form fields visually lighter than cards.

### Code Blocks

**code-block** uses {colors.sr-grey-50} background with {colors.on-surface} text and {typography.code} (Matter Mono). Line highlight backgrounds use `#eef0fd` with an indigo left-bar accent.

## Do's and Don'ts

**Do's**

- Use {colors.primary} for all primary CTA buttons and high-emphasis interactive elements to maintain consistent brand authority.
- Use {rounded.full} for all pill-style buttons — this is the primary brand shape signature and must not be altered on CTAs.
- Use Season Mix (fallback: Playfair Display) exclusively for headline levels; never use it for body or label text.
- Use Matter (fallback: Inter) for all body, label, navigation, and UI copy at appropriate weight stops (400, ~425, ~525).
- Apply {shadows.card} to all card components to maintain the characteristic floating-panel elevation of the Sarvam AI UI.
- Use the SR Indigo scale ({colors.sr-indigo-50} through {colors.sr-indigo-950}) for all informational, interactive, and link-adjacent color contexts.
- Use {spacing.3xl} (128px) for major section-to-section vertical separation to maintain the generous, enterprise-grade whitespace rhythm.
- Pair {colors.tertiary} exclusively as a gradient anchor (saffron-orange); never use it as a solid button background color.

**Don'ts**

- Do not use Season Mix below 28px — at small sizes the display axis of the font degrades legibility; use Matter instead.
- Do not reduce button border-radius below {rounded.full} for primary or secondary CTAs — doing so breaks the pill-button brand signature.
- Do not place {colors.on-surface-tertiary} text on {colors.surface-tertiary} backgrounds without verifying contrast — the pairing can fall below 3:1 at small sizes.
- Do not use raw oklch color values from the Tailwind utility variables (--color-red-*, --color-blue-*, etc.) as brand tokens — these are utility defaults, not semantic brand colors.
- Do not mix {colors.surface} and {colors.surface-tertiary} as adjacent card backgrounds within the same section — always pick one tonal level per visual grouping.
- Do not apply {shadows.card} to inline elements or badges — this shadow is reserved for elevated panel containers only.
- Do not use font weights below 400 or above 700 in the Matter variable range for UI text — the designed weight stops are 400 (regular), ~425 (text), ~525 (medium), and 600–700 (bold/semibold) for special emphasis.
