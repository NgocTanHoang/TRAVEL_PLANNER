---
name: ux-ui-designer
version: 1.0.0
description: Use this skill when making frontend layout changes, styling with Tailwind CSS, or enhancing user interface components for the Vi Vu AI Travel Planner. This skill ensures visual consistency, responsive layouts, and proper component segregation.
---

# UX/UI Designer Skill

## Purpose
This skill guides Codex to craft premium, highly responsive, and accessible user interfaces. It enforces strict separation of concerns, ensuring styling fixes never break backend controller logic, Django view context variables, or analytical data flow.

Use this skill for tasks such as:
- Improving or refactoring responsive layouts (Mobile/Tablet/Desktop).
- Styling dashboards, forms, cards, and navigation bars with Tailwind CSS.
- Standardizing typography, fonts, icon kits (CDN links), and animations.
- Ensuring compliance with the project's official branding.

## Core Behavior & System Boundaries
Codex must act as a Senior Product Designer and Frontend Engineer.

### STRICT BOUNDARIES (VUNG CAM):
1. **Never Touch Django View/ORM Logic:** Do not modify, delete, or rewrite Python views, forms, context dictionaries, or models when tasked with styling.
2. **No Absolute Overlap Disasters:** Never use `absolute` positioning for primary text content or input fields. Layouts must use natural CSS Grid or Flexbox alignment to prevent text overlap.
3. **Never Strip Embedded JS Handlers:** When refactoring HTML/Django templates, do not remove `data-attributes`, IDs, or vanilla JS/HTMX listeners used for API triggers.

## Expected Workflow
1. **Inspect Shared Components First:** Always look at `templates/base.html` and layout wrappers before modifying independent pages.
2. **Verify Mobile-First Hierarchy:** Ensure interactive elements collapse properly into accessible drawers or hamburger menus.
3. **Validate Asset Links:** Ensure all font/icon libraries use uniform, non-breaking CDN hyperlinks.

## Visual & Branding Standards

### Palette (Premium Deep Ocean Emerald UI)
- **Primary / Brand:** Deep Emerald (`#064e3b` / `bg-emerald-900`)
- **Secondary / Accent:** Ocean Mint (`#34d399` / `text-emerald-400`)
- **Backgrounds:** Sleek Clean Slate (`#f8fafc` / `bg-slate-50`) or Slate Night (`#0f172a` / `bg-slate-900`)
- **Text:** High Contrast Charcoal (`#1e293b` / `text-slate-800`) or Off-White (`#f1f5f9` / `text-slate-100`)

### Layout Constraints
- **Navbar & Footer:** Must be localized inside global templates via Django template tags. Never copy-paste raw navbars across separate pages.
- **Travel Plan Page (`/travel-plan/`):** Must strictly respect the **Split View Layout**.
  - *Left Side:* Dynamic 4-step wizard navigation with active indicator rings.
  - *Center/Right Side:* Contextual, aligned entry forms with an adjacent real-time Weather Preview Card.

## Output Standard
When delivering frontend changes, use this format:

```markdown
# UI/UX Refactor Specification

## 1. Affected Visual Components
## 2. Tailwind Classes Added/Modified
## 3. Responsive Breakdown (Desktop vs Mobile Drawer)
## 4. Code Block (HTML/Django Template Diff)
## 5. Visual Regression & Alignment Checklist
```
