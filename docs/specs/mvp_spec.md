# Spec: The Healthstream Static Hub (MVP)

## Objective
We are building a zero-runtime static content portal compiling metabolic, lifestyle, and book summaries. The target readers are Biohackers and Information Seekers. Success is defined by:
- Instant page loads and perfect SEO/GEO search indexability (including robots.txt and sitemap entries).
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
│   │   └── en/                  # Source JSON article files and static Markdown pages
│   │       ├── about.md         # About page narrative
│   │       └── contact.md       # Contact page narrative
│   ├── styles/                  # Modular design sheets
│   │   ├── variables.css        # Core design tokens
│   │   ├── layout.css           # Global resets and grid frameworks
│   │   └── components.css       # Widgets, popovers, card styling, and iframe boxes
│   ├── backlog.json             # Decoded nodes proposal list
│   ├── translations.json        # Static UI string labels and Google Form URLs
│   └── vocabulary.json          # Jargon glossary definitions
├── tools/
│   ├── compiler/
│   │   ├── reader.py            # Data loading & validator
│   │   ├── linker.py            # Jargon matching & link regex injector
│   │   └── writer.py            # HTML compiler, static MD parser, sitemap & robots writer
│   ├── build.py                 # Build orchestrator
│   └── new_entry.py             # CLI article bootstrapper
├── en/                          # Target compilation output directory
│   ├── index.html               # Homepage feed
│   ├── vocabulary.html          # Jargon Glossary page
│   ├── backlog.html             # Topic proposals and submission page
│   ├── about.html               # About page
│   ├── contact.html             # Contact page
│   ├── style.css                # Compiled stylesheet
│   ├── app.js                   # Client interactions script
│   ├── robots.txt               # Bot accessibility configuration
│   └── sitemap.xml              # SEO mapping
```

## Security & Data Operations
- **Serverless Form Processing**: To preserve privacy, all forms (Inquiries and Backlog topic submissions) route through secure external Google Forms.
- **Iframe Sandboxing**: Any embedded Google Form must utilize strict iframe sandbox parameters:
  ```html
  sandbox="allow-forms allow-scripts allow-same-origin"
  ```
  This isolates form executions and prevents clickjacking or window redirects.

## SEO/GEO Optimization Mappings
- **robots.txt**: Explicitly allows crawler access to AI search engine bots (`ChatGPT-User`, `GPTBot`, `PerplexityBot`, `ClaudeBot`) to maximize citation opportunities in AI search graphs.
- **JSON-LD Schema**:
  - Hompage (`index.html`) embeds `Organization` schema.
  - Detail articles embed `FAQPage` schema dynamically mapped from article takeaway pills.

## Code Style

### Python Conventions
- Follow PEP 8 styles.
- Include Google-style docstrings for all functions.
- Explicit Exception Handling (no bare `except:`).

### JavaScript Conventions
- Run under `"use strict"`.
- Use JSDoc-style comments for all functions.
- Explicit, single-responsibility event handlers.

## Testing Strategy
- **Compiler Level**:
  - Validate schema types and required fields.
  - Verify case-insensitive jargon linker ignores HTML tags, attributes, and existing links.
  - Verify static Markdown page compilations, robots.txt outputs, sitemaps, and JSON-LD injections.
- **Client Level (Vitest + JSDOM)**:
  - Verify dark/light toggles and layout collapsed persistences.
  - Verify click-to-open jargon popovers and backlog votes increment logic.
