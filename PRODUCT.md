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

#### The Curiosity Hook (Option 1)
Instead of displaying the core answer upfront, each feed card features a prominent **Curiosity Hook / Question** (e.g., *"Does constant constant snacking permanently lock our metabolic switches in storage mode?"*). This creates a strong hook that drives click-throughs and opens future community discussion.
### 3.3. Page Transition & Optimized Detail View
Clicking a feed card performs a clean page transition to the optimized static detail page, containing:
*   **1-Min Pill Takeaway Box**: Placed at the absolute start of the article page. An information icon prefix box containing the distilled, actionable conclusion.
*   **GRADE Evidence Rating Block**: Replaces the old consensus bar. Ratings are classified as *High*, *Moderate*, *Low*, or *Very Low*. Incorporates a built-in explanation of the GRADE framework to build scientific trust.
*   **Tabbed Reading Pane**: Allows users to toggle between:
    *   `[ 3-Min Overview ]`: Summarizes the biological circuit using simple analogies and outlines the justified lifestyle protocol.
    *   `[ Deep-Dive Mechanism ]`: Details the specific molecular pathway steps (maximum of 4 sections).
*   **Static Adjacency Links**: Displays directed network connection links (e.g., *Inhibits: mTOR*) generated from the entry's JSON edge schema to support lateral browsing.
*   **Interactive Jargon Popovers**: Dotted underline terms mapped in `src/vocabulary.json` trigger a mobile-friendly interactive popover on click/tap, displaying a brief definition and a link to the dedicated `/vocabulary.html` page.
*   **Evidence & Data Accordion**: A click-to-expand section at the bottom containing clinical study metrics, primary sources (PubMed/DOI links), and bibliography reference lists.

---

## 4. Lean Startup Strategy & Validation

### 4.1. Leap-of-Faith Assumptions
1.  **Value Hypothesis**: General readers and biohackers are motivated to study systems biology pathway mappings to modify their lifestyle habits.
2.  **Growth Hypothesis**: Decoded curiosity hooks will drive sharing on LinkedIn, generating organic loops alongside long-tail search indexing.
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
