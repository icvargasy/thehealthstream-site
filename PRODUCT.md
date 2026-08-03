# Product Context: The Healthstream

## 1. Core Brand & Systems Biology Philosophy

Our core systems biology tenets, communication rules (measured rhetoric paired with relational storytelling), visual asset guidelines, and monetization boundaries are fully defined in **[BRAND.md](file:///c:/Users/varga/thehealthstream/BRAND.md)**. 

### Design Identity Integration
Our visual identity is anchored in the **Synapse & Ink Strategy** (coral/rose accents against deep slate-charcoal and warm alabaster backgrounds) detailed in **[DESIGN.md](file:///c:/Users/varga/thehealthstream/DESIGN.md)**.

*   **Anti-patterns**: Avoid generic healthcare/SaaS blue; avoid clickbait/sensationalized headlines; avoid over-rounding (>12px card corners); never use placeholder text or mock metrics.

---

## 2. Target User Personas

*   **Information Seekers (Quick Scan)**: Need an immediate, actionable protocol (1-minute takeaway) without reading details.
*   **Knowledge Mapping Seekers (Systems Map)**: Biohackers and physiology enthusiasts looking to understand mechanical connections (3-minute map) and study metrics evidence.

---

## 3. Core Product Feature Set (Lean MVP)

### 3.1. English Edition & Static Target
To preserve SEO/GEO performance and maximize initial validation speed, the platform is compiled statically and targets the English (`en/`) language edition. Hosted directly on GitHub Pages with zero server-side runtime dependencies.

### 3.2. Unified Feed & Card System
The landing page displays a chronological stream of content cards categorized by color-coded left borders:
*   **Biology/Science (Rose Border)**: Decoded metabolic and biological pathway networks.
*   **Lifestyle/Behavior (Sage Border)**: Actionable sleep, exercise, and circadian habits.
*   **Book Summaries (Gold Border)**: Synthesis of scientific books and curated longevity texts.

#### Hook Question (`hook_question`)
Each feed card title is a **Hook Question**: a plain-language interrogative sentence (FK Grade 8–9, 12–18 words) that gestures toward a specific, counterintuitive outcome without disclosing the answer upfront. The same `hook_question` field is used identically for published Summary cards and unpublished Pipeline cards, ensuring display consistency across the unified feed. Science and Lifestyle cards follow the 7-principle Hook Question Standard (see `GEMINI.md §5.7`). Book cards use `"[Title] (Author)"` format.
### 3.3. Page Transition & Optimized Detail View
Clicking a feed card performs a clean page transition to the optimized static detail page, containing:
*   **1-Min Pill Takeaway Box**: Placed at the absolute start of the article page. An information icon prefix box containing the distilled, actionable conclusion.
*   **GRADE Evidence Rating Block**: Replaces the old consensus bar. Ratings are classified as *High*, *Moderate*, *Low*, or *Very Low*. Incorporates a built-in explanation of the GRADE framework to build scientific trust.
*   **Tabbed Reading Pane**: Allows users to toggle between:
    *   `[ 3-Min Overview ]`: Summarizes the biological circuit using simple analogies and outlines the justified lifestyle protocol.
    *   `[ Deep-Dive Mechanism ]`: Details the specific molecular pathway steps (maximum of 4 sections).
*   **Interactive Jargon Popovers**: Dotted underline terms mapped in `src/vocabulary.json` trigger a mobile-friendly interactive popover on click/tap, displaying a brief definition and a link to the dedicated `/vocabulary.html` page.
*   **Evidence & Data Accordion**: A click-to-expand section at the bottom containing clinical study metrics, primary sources (PubMed/DOI links), and bibliography reference lists.

### 3.4. Circuit Graph Topology & Related Circuits Widget
The platform builds an in-memory directed graph ($G = (V, E)$) during static compilation, laying database-ready foundations for future graph database migrations:
*   **3-Directional Schema**: Each entry frontmatter declares directed edges:
    `related_circuits: { upstream: [...], downstream: [...], similar: [...] }`.
*   **Frontier Expansion Heuristics**:
    1.  *Broad Domain Scope*: Decodes pathways across biological mechanisms, lifestyle protocols, and frontier/emerging science (longevity models, pre-prints).
    2.  *Hard Caps & Edge Pruning*: Max 5 directional connections per category per node to preserve high signal-to-noise ratio. New entries displace weaker links based on effect size.
    3.  *Tiered Render UI*:
        *   **Tier 1 (Curated / Established)**: 1–2 line format with directional badge (`Upstream`, `Downstream`, `Similar`), title link, and mechanistic summary.
        *   **Tier 2 (Frontier / Hypothesized)**: Compact 1-line format with `Emerging Hypothesis` badge and an **`Endorse Connection →`** link.
    4.  *Pre-filled Community Submissions*: Clicking `Endorse Connection →` routes to `./submit-proposal.html?source={id}&target={target}&type={type}`, pre-filling form inputs via client-side `URLSearchParams`.

---

## 4. Lean Startup Strategy & Validation

### 4.1. Leap-of-Faith Assumptions
1.  **Value Hypothesis**: General readers and biohackers are motivated to study systems biology pathway mappings to modify their lifestyle habits.
2.  **Growth Hypothesis**: Decoded hook questions will drive sharing on LinkedIn and organic search indexing by surfacing counterintuitive scientific outcomes in an immediately scannable format.
3.  **Retention Hypothesis**: Readers will return to the site regularly as a structured, non-commercial reference registry.

### 4.2. Engine of Growth
*   **Primary Focus**: **Sticky Engine of Growth**.
*   **Rationale**: Because health protocols require habit formation, we prioritize repeat visit cohort retention over bulk customer acquisition.

### 4.3. Actionable vs. Vanity Metrics
*   **Actionable (Tracked)**:
    *   **Cohort Return Rate**: The percentage of unique readers returning in weeks 2, 4, and 8.
    *   **Vocabulary Popover Tap Rate**: Indicates active reader onboarding and text engagement.
    *   **Pill Accordion Expansion Rate**: Indicates deep research engagement.
*   **Vanity (Ignored)**:
    *   **Total Cumulative Pageviews**.
    *   **Total Feed Scroll Depth**.

### 4.4. Pivot vs. Persevere Triggers
*   **Persevere**: Continue iteration if Week 4 Cohort Return Rate exceeds 20% and Vocabulary popover taps exceed 1.5 per session.
*   **Pivot**: If retention falls below 10% after 5 content iterations, pivot the content complexity lower or refocus on pure book summaries over pathway diagrams.

---

## 5. Telemetry, Accessibility & Inclusion

*   **Telemetry**: Privacy-first, client-side lightweight proxy tracking (e.g. Plausible) tracking clicks, card transitions, and accordion states.
*   **Contrast**: Strict WCAG AA contrast (≥ 4.5:1 for body copy; ≥ 3:1 for large display elements).
*   **Reduced Motion**: Respects `prefers-reduced-motion` media queries by bypassing slide transitions in favor of instant displays.

---

## 6. Reference Documentation Links

To facilitate developer and agent navigation, refer to these master documentation files:
*   **Strategic Roadmap & Master Tenets**: [mission_and_vision.md](file:///c:/Users/varga/thehealthstream/mission_and_vision.md) (SSOT for core philosophy, GRADE tiers, and monetization boundaries).
*   **Brand, Voice & Style Guidelines**: [BRAND.md](file:///c:/Users/varga/thehealthstream/BRAND.md) (SSOT for Feynman + Obama + Relational tone and color specs).
*   **Engineering Guidelines**: [gemini.md](file:///c:/Users/varga/thehealthstream/gemini.md) outlining coding standards, test runners, and static build pipelines.
