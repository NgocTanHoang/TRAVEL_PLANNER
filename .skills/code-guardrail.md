---
name: code-guardrail
version: 1.0.0
description: Core system gatekeeper enforced to protect source file encoding, layout constraints, and prevent regression bugs during automated refactoring sessions.
---

# Code Guardrail & Compliance Skill

## 🚫 1. STRICT ENCODING LOCKDOWN (CHẶN LỖI MÃ HÓA)
* **UTF-8 Only:** All source files, especially Django templates (`*.html`) and JavaScript assets (`*.js`), MUST be read, processed, and written strictly using **UTF-8 encoding without BOM**.
* **Zero Mojibake Tolerance:** You are completely forbidden from writing or outputting corrupted characters (e.g., `Äá»™ áº©m`, `Thi?t`, `ng??i`). All Vietnamese text must be clean, native, and properly accented.
* **Pre-Save Check:** Before finalized output generation, simulate a compiler pass to verify no string sequences have broken into raw ANSI or ISO-8859-1 text blocks.

## 📐 2. LAYOUT INTEGRITY BOUNDARIES (GIỮ VỮNG GRID)
* **Split-View Preservation:** The main container structure of `travel_plan.html` must always maintain the dynamic responsive 12-column grid (`md:grid md:grid-cols-12 md:gap-8`).
* **Component Segregation:** Form segments for Step 1, 2, 3, and 4 must expand inside their allocated `md:col-span-8` right-side zone, utilizing internal sub-grids (`grid-cols-1 sm:grid-cols-2 lg:grid-cols-3`) to prevent vertical single-column stretching.
* **No Floats/Absolute Overlaps:** Primary input blocks and operational components must remain inside the natural CSS document flow. Never use `absolute` or `fixed` coordinates that bleed into or overlap the global shared Navbar and Footer.

## 💾 3. STATE MACHINE HOOKS SAFEKEEPING (BẢO VỆ HOOK)
* Do not delete, rename, or detach any existing DOM anchor selectors, class attributes, element IDs (`id="step-x"`), or `data-step` triggers.
* The state machine loop inside `travel_plan_workflow.js` must remain backward-compatible with the backend Django views context properties.

## 📝 4. MANDATORY VERIFICATION BEFORE DELIVERING
Every code delivery block must conclude with an explicit system confirmation confirming:
1. File encoding has been double-checked and verified as 100% UTF-8.
2. Responsive scaling handles both mobile stack and desktop split-view grids with zero layout overflow.
3. Live functional Javascript callbacks/API endpoints remain untouched.
