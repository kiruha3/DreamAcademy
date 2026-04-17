# DreamDocs Design System — Master Tokens

**Source:** https://dreamdocs.ru + existing portal codebase  
**Date:** 2026-04-16  
**Status:** MVP baseline for Academy portal

---

## Color Palette

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-primary` | `#0096cc` | Primary brand, buttons, links |
| `--color-primary-light` | `#00b0f0` | Gradients, hover accents |
| `--color-dark` | `#313647` | Headings, strong text |
| `--color-text` | `#464d66` | Body text, paragraphs |
| `--color-bg` | `#ffffff` | Page background |
| `--color-bg-light` | `#f0f0f0` | Section backgrounds, auth page |
| `--color-black` | `#111111` | Logo, high-contrast text |

---

## Typography

| Token | Value | Usage |
|-------|-------|-------|
| `--font-family` | `Segoe UI, system-ui, -apple-system, sans-serif` | Body, UI text |
| `--font-size-hero` | `48px` | Landing H1 |
| `--font-size-h2` | `36px` | Section titles |
| `--font-size-h3` | `20px` | Card titles |
| `--font-size-body` | `16px` | Body text |
| `--font-size-small` | `14px` | Buttons, captions, hints |
| `--line-height` | `1.6` | Body paragraphs |

---

## Spacing & Layout

| Token | Value | Usage |
|-------|-------|-------|
| `--container-max-width` | `1200px` | Max content width |
| `--container-padding` | `20px` | Horizontal page padding |
| `--section-padding-y` | `60px`–`100px` | Vertical section spacing |
| `--card-padding` | `24px` | Card internal padding |
| `--grid-gap` | `24px` | Grid/column gaps |

---

## Components

### Buttons
- Background: `--color-primary`
- Text: `#ffffff`
- Padding: `10px 20px` (standard), `14px 32px` (large)
- Border-radius: `6px`
- Hover: darken to `#007aa8`

### Cards
- Background: `#ffffff`
- Border-radius: `12px`
- Shadow: `0 2px 8px rgba(0,0,0,0.06)` (subtle), `0 4px 12px rgba(0,0,0,0.08)` (elevated)

### Forms
- Input border: `1px solid #ddd`
- Input border-radius: `6px`
- Focus border: `--color-primary`
- Label font-weight: `500`

---

## Responsive Strategy

- Mobile-first CSS
- Grid uses `repeat(auto-fit, minmax(260px, 1fr))` for flexible layouts
- Container centers with max-width and side padding

---

## Assets

- **Logo:** `DreamDocs_logo_1.png` (Tilda CDN)
- **Favicon:** `public/favicon.ico`
- **Hero gradient:** `linear-gradient(135deg, #0096cc 0%, #00b0f0 100%)`
