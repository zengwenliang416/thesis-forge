---
version: 0.1
name: ThesisForge Desktop UI Foundation
description: Desktop UI foundation used by the V1 HTML review prototype; production desktop UI remains deferred.
colors:
  primary: "#171717"
  secondary: "#4d4d4d"
  tertiary: "#006bff"
  neutral: "#f2f2f2"
  background-100: "#ffffff"
  background-200: "#fafafa"
  gray-100: "#f2f2f2"
  gray-200: "#ebebeb"
  gray-300: "#e6e6e6"
  gray-400: "#eaeaea"
  gray-500: "#c9c9c9"
  gray-600: "#a8a8a8"
  gray-700: "#8f8f8f"
  gray-800: "#7d7d7d"
  gray-900: "#4d4d4d"
  gray-1000: "#171717"
  blue-700: "#006bff"
  red-800: "#ea001d"
  amber-700: "#ffae00"
  green-700: "#28a948"
typography:
  heading-32:
    fontFamily: Geist Sans
    fontSize: 32px
    fontWeight: 600
    lineHeight: 40px
    letterSpacing: -1.28px
  heading-24:
    fontFamily: Geist Sans
    fontSize: 24px
    fontWeight: 600
    lineHeight: 32px
    letterSpacing: -0.96px
  label-14:
    fontFamily: Geist Sans
    fontSize: 14px
    fontWeight: 500
    lineHeight: 20px
    letterSpacing: 0
  copy-14:
    fontFamily: Geist Sans
    fontSize: 14px
    fontWeight: 400
    lineHeight: 22px
    letterSpacing: 0
  button-14:
    fontFamily: Geist Sans
    fontSize: 14px
    fontWeight: 500
    lineHeight: 20px
    letterSpacing: 0
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  xxl: 40px
rounded:
  sm: 6px
  md: 12px
  lg: 16px
components:
  button-primary:
    backgroundColor: "{colors.gray-1000}"
    textColor: "{colors.background-100}"
    typography: "{typography.button-14}"
    rounded: "{rounded.sm}"
    height: 40px
  button-secondary:
    backgroundColor: "{colors.background-100}"
    textColor: "{colors.primary}"
    typography: "{typography.button-14}"
    rounded: "{rounded.sm}"
    height: 40px
  input:
    backgroundColor: "{colors.background-100}"
    textColor: "{colors.primary}"
    typography: "{typography.label-14}"
    rounded: "{rounded.sm}"
    height: 40px
---

# ThesisForge Desktop UI Foundation

## Overview

ThesisForge V1 prioritizes the deterministic offline compiler and CLI. The
`build-thesisforge-v1-core` change includes a review-only HTML prototype of the future
desktop workbench, while production PySide6 UI remains deferred. The prototype must
make the product structure reviewable without becoming a compiler dependency.

## Colors

Use tokenized colors. Describe semantic usage for primary text, secondary text,
page surfaces, borders, focus, success, warning, destructive, and disabled
states. Do not introduce ad hoc colors in feature work.

## Typography

Use typography tokens instead of hand-setting size, weight, line height, or
letter spacing. Record heading, label, copy, mono/data, and button rules here.

## Layout

Define page width, responsive breakpoints, section rhythm, panel spacing, grid
rules, and mobile behavior. Every layout requirement should be usable by a
prototype and by production implementation.

## Elevation & Depth

Define border, shadow, overlay, popover, modal, and focus depth rules. Prefer
surface and border hierarchy before heavy shadows.

## Motion

Define when motion is allowed, expected durations, easing, reduced-motion
behavior, and states where animation is forbidden.

## Shapes

Define radius families for controls, cards, menus, dialogs, avatars, and pills.
Avoid mixing unrelated radius systems in one view.

## Components

Define visual rules for buttons, inputs, tables, cards, dialogs, navigation,
empty states, toasts, tooltips, tabs, segmented controls, menus, and loading
states.

## Voice & Content

Future UI copy uses concise Simplified Chinese. Domain error codes remain stable and
language-neutral; the UI adapter maps them to Chinese labels, validation messages,
empty states, progress text, and recovery actions.

## Theme & Internationalization

- Theme capability: `light-only`.
- Theme toggle: `none`; do not show or create a theme switcher.
- Internationalization: `disabled` for V1.
- Supported locales: `zh-CN`.
- Default locale: `zh-CN`.
- Prototype rule: the V1 core change must provide desktop and mobile HTML review coverage in the light theme and `zh-CN`; theme and locale switchers are intentionally omitted.

## Do's and Don'ts

- Do use the token names above in prototypes and production code.
- Do require accessible focus states and body text contrast.
- Do record theme modes and locale coverage before starting a UI prototype.
- Do pair color state with icon or text.
- Don't add one-off colors, spacing, shadows, or radii without updating this spec.
- Don't invent dark mode, a theme toggle, i18n, or a language switcher when the project does not support it.
- Don't hide important state with color alone.
