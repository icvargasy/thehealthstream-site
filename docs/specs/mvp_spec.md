# Spec: The Healthstream Static Hub (MVP)

## Objective
We are building a zero-runtime static content portal compiling metabolic, lifestyle, and book summaries. The target readers are Biohackers and Information Seekers. Success is defined by:
- Instant page loads and perfect SEO/GEO search indexability.
- Strict WCAG AA contrast ratio compliance using an OKLCH custom properties system.
- Fluid responsive interactions (theme toggles, collapsible sidebars, popovers, and voting counters) implemented in Vanilla JS.

## Tech Stack
- **Backend/Compiler**: Python (3.11+) with standard libraries and the `markdown` compilation package.
- **Frontend Core**: Static HTML5 and Vanilla Javascript (ES6 in Strict Mode).
- **Styling**: Modular Vanilla CSS utilizing CSS variables, Flexbox, and Grid (no Tailwind CSS).
- **Test Runners**:
  - Python: `pytest`
  - JavaScript: `vitest` + `jsdom` (simulated DOM environment)

## Commands
All terminal commands are prefixed with `rtk` (Rust Token Killer) to minimize token footprint.
- **Install JS Dependencies**: `rtk pnpm install`
- **Run JS Tests**: `rtk pnpm test`
- **Run Python Tests**: `rtk pytest`
- **Build Static Site**: `rtk python tools/build.py`
- **Preview Local Server**: `rtk npx serve en`

## Project Structure
```
thehealthstream/
├── docs/
│   └── specs/
│       └── mvp_spec.md          # Dedicated Specification file (This file)
├── src/
│   ├── templates/
│   │   └── layout.html          # Global HTML template wrapper
│   ├── nodes/
│   │   └── en/                  # Source JSON article files
│   ├── styles/                  # Modular design sheets
│   │   ├── variables.css        # Core design tokens
│   │   ├── layout.css           # Global resets and grid frameworks
│   │   └── components.css       # Widgets, popovers, card styling
│   ├── backlog.json             # Decoded nodes proposal list
│   ├── translations.json        # Static UI string labels
│   └── vocabulary.json          # Jargon glossary definitions
├── tools/
│   ├── compiler/
│   │   ├── reader.py            # Data loading & validator
│   │   ├── linker.py            # Jargon matching & link regex injector
│   │   └── writer.py            # HTML compiler, asset manager & sitemap generator
│   ├── build.py                 # Build orchestrator
│   └── new_entry.py             # CLI article bootstrapper
├── en/                          # Target compilation output directory
├── style.css                    # Master styling imports entry point
├── app.js                       # Vanilla client interaction script
├── tests/
│   ├── app.test.js              # Vitest JSDOM event tests
│   └── test_build.py            # Pytest compiler tests
```

## Code Style

### Python Conventions
- Follow PEP 8 styles.
- Include Google-style docstrings for all functions.
- Explicit Exception Handling (no bare `except:`).

```python
def load_json(path: str) -> dict:
    """Ingests a JSON file and parses it.

    Args:
        path: Path to the target file.

    Returns:
        The deserialized JSON content.

    Raises:
        FileNotFoundError: If the file is not found.
        ValueError: If parsing fails.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Missing file: {path}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"Malformed JSON: {path}") from e
```

### JavaScript Conventions
- Run under `"use strict"`.
- Use JSDoc-style comments for all functions.
- Explicit, single-responsibility event handlers.

```javascript
"use strict";

/**
 * Toggles the expanded class on the given element.
 * @param {HTMLElement} element - The target container.
 * @returns {void}
 */
function toggleAccordion(element) {
  if (!element) return;
  element.classList.toggle("is-expanded");
}
```

## Testing Strategy
- **Compiler Level**:
  - Verify that `reader.py` validates schemas correctly (rejects missing fields, validates types).
  - Verify that `linker.py` replaces words matched from `vocabulary.json` with `<span class="jargon-term">` elements only in text blocks (ignoring HTML tag structures).
  - Verify that `writer.py` generates HTML pages, copies assets, and writes `sitemap.xml`.
- **Client Level (Vitest + JSDOM)**:
  - Simulate clicks on Sidebar toggles and verify `.left-collapsed` class and storage updates.
  - Simulate jargon term clicks and verify popover insertions and position logic.
  - Simulate backlog voting clicks and verify localStorage and UI counter adjustments.

## Boundaries
- **Always**: Prefix commands with `rtk`. Run tests before planning commits. Document public interfaces.
- **Ask First**: Adding external dependencies or framework wrappers.
- **Never**: Introduce runtime backend web servers (must remain 100% static HTML/JS).

## Success Criteria
1. `rtk pytest` returns green on compiler testing.
2. `rtk pnpm test` returns green on client interactions.
3. Running `rtk python tools/build.py` constructs a valid `en/` folder containing `index.html`, `vocabulary.html`, `style.css`, `app.js`, `assets/`, `styles/`, `sitemap.xml`, and matching articles (e.g. `ampk-activation.html`).
4. Site visual interface matches styling specifications (OKLCH, responsive layout, dark/light theme, accordions, and popovers).
