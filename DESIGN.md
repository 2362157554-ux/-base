---
version: alpha
name: base-design-system
description: "-base is a cinematic short-video editing workbench: dark canvas, real preview as the hero, compact production controls, hairline borders, and one scarce electric-blue action color."

colors:
  primary: "#58a6ff"
  primary-hover: "#79b8ff"
  on-primary: "#ffffff"
  success: "#5ee0b5"
  danger: "#ff7b72"
  warning: "#f2cc60"
  canvas: "#07080a"
  canvas-preview: "#000000"
  surface: "#101319"
  surface-raised: "#161a22"
  surface-soft: "#1d2330"
  hairline: "#252b36"
  hairline-strong: "#3a4658"
  ink: "#f4f7fb"
  ink-muted: "#a7b0be"
  ink-subtle: "#717b8a"

typography:
  app-title:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, PingFang SC, Microsoft YaHei, sans-serif"
    fontSize: 16px
    fontWeight: 650
    lineHeight: 1.25
    letterSpacing: 0
  section-label:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, PingFang SC, Microsoft YaHei, sans-serif"
    fontSize: 12px
    fontWeight: 650
    lineHeight: 1.3
    letterSpacing: 0.08em
    textTransform: uppercase
  body:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, PingFang SC, Microsoft YaHei, sans-serif"
    fontSize: 13px
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: 0
  body-small:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, PingFang SC, Microsoft YaHei, sans-serif"
    fontSize: 12px
    fontWeight: 400
    lineHeight: 1.45
    letterSpacing: 0
  mono:
    fontFamily: "SFMono-Regular, Menlo, Monaco, Consolas, Liberation Mono, monospace"
    fontSize: 11px
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: 0

rounded:
  xs: 4px
  sm: 6px
  md: 8px
  lg: 12px
  frame: 16px
  pill: 9999px

spacing:
  xs: 4px
  sm: 8px
  md: 12px
  lg: 16px
  xl: 24px
  panel: 18px

components:
  app-shell:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    layout: "header plus three-pane editor"
  top-bar:
    backgroundColor: "{colors.surface}"
    border: "1px solid {colors.hairline}"
    height: 56px
  side-panel:
    backgroundColor: "{colors.surface}"
    border: "1px solid {colors.hairline}"
    width: 360px
  preview-stage:
    backgroundColor: "{colors.canvas-preview}"
    rounded: "{rounded.frame}"
    border: "1px solid {colors.hairline-strong}"
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "9px 14px"
  button-secondary:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.ink}"
    border: "1px solid {colors.hairline}"
    rounded: "{rounded.md}"
    padding: "9px 14px"
  input:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    border: "1px solid {colors.hairline}"
    rounded: "{rounded.sm}"
    padding: "8px 10px"
  capability-card:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.ink}"
    border: "1px solid {colors.hairline}"
    rounded: "{rounded.md}"
    padding: "10px 12px"
---

# -base Design System

## 1. Visual Theme & Atmosphere

`-base` should feel like a compact editing bay for short-video production. The preview is the protagonist; controls should frame it quietly. Borrow the useful idea from `awesome-design-md`: write the design language as a plain `DESIGN.md` contract so AI agents and humans can make later UI changes without drifting.

The visual direction borrows methods, not brand identity:

- Runway: actual video/imagery should carry the drama; chrome stays restrained.
- Linear/Raycast: dark surface ladder, compact panels, hairline borders, scarce accent color.
- Mintlify: structured tokens and component entries that agents can reference directly.

## 2. Color Rules

Use near-black `canvas` for the app background and pure black `canvas-preview` for the video stage. Build hierarchy with `surface`, `surface-raised`, and `surface-soft`; do not add decorative gradients or glow backgrounds.

`primary` is only for the main generation action, focus states, and key active controls. `success`, `danger`, and `warning` are semantic states only. Do not use accent colors as large card fills or body text.

## 3. Typography Rules

Use one sans stack for UI prose and one mono stack for job ids, keyboard hints, and technical metadata. Labels are small, uppercase, and tracked. Body text stays compact but readable: 13px/1.5 for controls, 12px/1.45 for helper text.

Do not use hero-scale marketing type inside the app shell. This is an operational editor, not a landing page.

## 4. Component Rules

### App Shell

Keep the three-pane workflow visible on desktop: assets and canvas settings on the left, preview and capability cards in the center, script and output actions on the right. On narrow screens, collapse to a single-column stack in this order: preview, assets/settings, script/actions, capabilities.

### Preview Stage

The video preview is the primary visual asset. Give it a black stage, a 16px frame radius, and a hairline border. Avoid heavy drop shadows; depth should come from the surrounding dark surfaces and the actual video.

### Panels

Panels use `surface` with hairline separators. Cards inside panels use `surface-raised`. Avoid nested decorative cards; use spacing and borders for grouping.

### Buttons

Primary buttons use `primary` with white text and 8px radius. Secondary and ghost buttons use dark surfaces and hairline borders. Avoid pill CTAs except for compact status tags.

### Inputs

Inputs and selects use the darkest canvas fill, 6px radius, and a hairline border. Focus uses `primary`; errors use `danger`; success uses `success`.

### Capability Cards

Capability cards should be dense and scan-friendly. Tool names are high-emphasis; summaries are muted and truncated. Disabled cards fade but keep layout dimensions stable.

## 5. Layout & Responsive Behavior

Desktop target: fixed 360px side panels with a flexible center preview. Tablet target: left panel, center preview, and right panel may stack. Mobile target: one column with no horizontal overflow, 44px minimum tap targets where possible.

Use an 8px rhythm for gaps and a 16px to 24px rhythm for panel padding. Keep repeated tool cards in stable grid tracks so toggling parameters does not resize unrelated areas.

## 6. Do's and Don'ts

Do:

- Let uploaded footage, Remotion preview, and generated MP4 output define the visual personality.
- Keep all production controls compact, dark, and predictable.
- Use one primary action color per viewport.
- Use `DESIGN.md` tokens when asking an AI agent to add UI.

Don't:

- Do not turn the editor into a marketing page.
- Do not add gradients, decorative blobs, bokeh, or oversized hero sections.
- Do not use strong shadows on cards.
- Do not introduce extra accent palettes for individual tools.
- Do not make controls shift layout when a checkbox is toggled.

## 7. Agent Prompt Guide

When adding UI, tell the agent:

> Follow `DESIGN.md`. Build a dark cinematic editing workbench: black preview stage, compact side panels, hairline borders, one electric-blue primary action, muted helper text, and responsive one-column mobile layout. Keep the actual video preview as the hero.

