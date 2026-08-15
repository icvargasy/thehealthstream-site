# Brand Assets & Philosophy: The Healthstream

This document defines the brand philosophy, communication rules, visual assets, and monetization boundaries for **The Healthstream**. It is designed to align both human writers and AI coding/writing agents during copy generation.

---

## 1. Core Philosophy & Master Tenets

The core philosophy, 3-tier epistemic transparency, category-specific mapping rules, and editorial independence frameworks are fully defined in the master strategy document: **[mission_and_vision.md](file:///c:/Users/varga/thehealthstream/mission_and_vision.md)** (SSOT). 

All copy generated for **The Healthstream** is guided by the **Systems Biology Triad**:
1. **Bioenergetics & The Endosymbiotic Engine**: Framing cellular energy, substrate flux, and the evolutionary dialogue between mitochondria and the gut microbiome.
2. **Cybernetics & Dynamic Poise**: Framing biological balance as an active, oscillating rhythm between Anabolic growth (mTOR) and Catabolic recovery (AMPK/mitophagy).
3. **Compartmental Integrity & Boundary Dynamics**: Framing health through selective mucosal/endothelial barriers and continuous fluid transport (vascular, lymphatic, glymphatic).

---

## 2. Voice & Tone (The Feynman + Obama + Relational Synthesis)

Our register is precise and professional (Toastmasters/HBR level), blending relentless clarity, rhythmic pacing, and human empathy.

### 2.1 Feynman-Style Everyday Intuition (Richard Feynman)
*   **14-Year-Old Lived-Experience Standard**: Ground all high-level mental models and analogies in physical situations a 14-year-old encounters in daily life (kitchens, bicycles, garden hoses, backpacks, phones, house keys).
*   **Adolescent Readability Floor**: Maintain a **Flesch-Kincaid Grade Level 8–9** (High School / 14–16 Age Literacy) for all top-level card summaries and analogy hooks. Dense biochemical terms are reserved exclusively for deep-dive sections.
*   **Intelligent Equals**: Address the reader as an intellectually curious peer who values clear explanations and rigorous systems logic.

### 2.2 Measured & Rhetorical Cadence (Barack Obama)
*   **Inclusive Framing**: Use inclusive pronouns ("we", "our body", "our cellular health") to frame decodings as a shared scientific inquiry rather than a clinical lecture.
*   **Parallel Structure**: Use rhythmic, measured phrasing to give structural weight to conclusions.
    *   *Example*: *"To reset our circadian clock, to stabilize morning glucose, and to protect deep sleep, we must design our interaction with light."*

### 2.3 Relational Authenticity (Brené Brown)
*   **Acknowledge Behavioral Friction**: Directly address real-world challenges in maintaining protocols (e.g. maintaining fasting windows or screen boundaries in a hyper-connected environment).

---

### 2.4 The Healthstream Master Copy Standard
All content generated for **Card Teasers** (backlog proposals & summary decodings) and **Lexicon Entries** must obey the Master Copy Standard:

#### 1. Universal Execution Core (Positive Guidelines)
*   **Everyday Lived-Experience Analogy**: Use familiar, tangible real-world analogies (household tools, cooking, school halls, bicycles, gardening).
*   **Explicit Noun Subject**: Start analogies with a concrete noun subject (e.g. *"A kitchen sponge...", "A municipal traffic light...", "A household water filter..."*).
*   **Single-Sentence Economy**: Exactly 1 single, well-crafted sentence per component.
*   **Human Functional Outcomes**: Focus on direct human physiological adaptations, risk reductions, and energetic vitality.

#### 2. Component Scoping & Word-Count Ceilings

##### A. Card Teasers (Backlog Proposals & Summary Decodings)
*   **Question Hook** (`hook_question`): Curiosity-driven Title. Form: Question (`Can / Does / Could / Why`). Ceiling: **$\leq 15$ words**.
    *   *Example*: *"Can a year of regular exercise actually make your brain biologically younger?"*
*   **Systems Analogy** (`systems_analogy_hook` / `systems_analogy`): 1-sentence everyday lived-experience mental model. Ceiling: **$\leq 25$ words**.
    *   *Example*: *"A powerful water pump keeping building plumbing clean and flowing at full pressure."*
*   **Takeaway Pill** (`takeaway_pill`): Evidence-rated clinical trial verdict. Ceiling: **$\leq 25$ words**.
    *   *Example*: *"12 months of consistent exercise reduces structural brain age by 1 to 2 years on quantitative MRI scans."*

##### B. Lexicon Entries (Vocabulary Definitions)
*   **Scientific Definition** (`definition`): Objective, HBR-style 1-sentence explanation. Ceiling: **$\leq 20$ words**.
*   **Systems Analogy** (`vulgarized_analogy`): Plain-English 1-sentence everyday mental model ($\le 25$ words).
    *   *Example*: *"The brain's cleanup crew that sweeps up damaged cells and keeps the peace."*

---

## 3. Visual Identity & Design Guidelines

To build immediate brand recognition while respecting strict visual accessibility (WCAG 4.5:1 contrast ratio), our visual identity balances a single master brand color with context-responsive theme variables.

### 3.1 Color Palette & Specs

1.  **Unified Brand Color: "Synapse Coral"**
    *   **HEX**: `#DE3B49`
    *   **OKLCH**: `oklch(0.60 0.18 18)`
    *   **Usage**: Used on primary branding elements, the combined logomark assets, and visual highlights.

2.  **Context-Responsive Interactive Accents**
    *   *To guarantee text and link readability against differing backgrounds, interactive elements adapt chromatic luminosity while maintaining the exact Hue angle (18):*
    *   **Light Backgrounds**: **Oxblood Coral** (`oklch(0.45 0.16 18)` / HEX `#9C1C26`). Contrast ratio is $\geq 4.5:1$ against the paper-white page background.
    *   **Dark Backgrounds**: **Crimson Rose** (`oklch(0.65 0.17 18)` / HEX `#F76A76`). Contrast ratio is $\geq 4.5:1$ against the warm charcoal background.

### 3.2 Typography Guidelines

*   **Display / Heading Font**: `Fraunces` (Google Fonts). Variable serif with organic weight. Expresses literary authority and depth.
*   **Body / UI Font**: `DM Sans` (Google Fonts). Geometric, high legibility.
*   **Type Hierarchy**:
    *   **H1**: `clamp(1.9rem, 3.2vw, 2.5rem)` (Letter-spacing: `-0.03em`)
    *   **H2**: `clamp(1.35rem, 2.3vw, 1.8rem)` (Letter-spacing: `-0.03em`)
    *   **H3**: `1.25rem` (Weight: `400`)
    *   **Body Text**: `1rem` (Line-height: `1.65`, maximum line length: `68ch`)
    *   **Labels/Metadata**: `0.75rem` (Weight: `600`, tracking: `0.05em`, uppercase)

### 3.3 Catalog of Assets

All brand assets reside in the `assets/` directory as high-resolution transparent PNG files.

1.  **Icon-Only Logo**: [logo_only_light.png](file:///c:/Users/varga/thehealthstream/assets/logo_only_light.png) / [logo_only_dark.png](file:///c:/Users/varga/thehealthstream/assets/logo_only_dark.png).
    *   *Consistency Note*: The light version is rendered in Oxblood Coral to ensure high contrast on light backgrounds. The dark version is rendered in Crimson Rose to ensure glow and visibility on dark surfaces. For unified print or offline contexts, use the core **Synapse Coral** (`#DE3B49`).
2.  **Typography Logo**: [brandname_light.png](file:///c:/Users/varga/thehealthstream/assets/brandname_light.png) / [brandname_dark.png](file:///c:/Users/varga/thehealthstream/assets/brandname_dark.png).
3.  **Combined Logo**: [both_together_light.png](file:///c:/Users/varga/thehealthstream/assets/both_together_light.png) / [both_together_dark.png](file:///c:/Users/varga/thehealthstream/assets/both_together_dark.png).
4.  **Favicon**: [favicon_light.png](file:///c:/Users/varga/thehealthstream/assets/favicon_light.png) / [favicon_dark.png](file:///c:/Users/varga/thehealthstream/assets/favicon_dark.png).

### 3.4 Display Contexts & Layout
*   **Sidebar Navigation**: Place the typography `brandname` logo variants in the upper left header area.
*   **Mobile Top-Bar / Headers**: Use the monogram `logo_only` variants for visual compactness.
*   **Social & Meta Graph Previews**: Use the combined logo `both_together` variants for high brand recognition.
*   **Theme Reactivity**: JavaScript inside `layout.html` matches the image source to the user's active theme selection (`light` or `dark`).

---

## 4. Monetization Boundaries & Independence

To ensure The Healthstream remains an unbiased and trusted reference while keeping monetization opportunities open:

1.  **Independent Diagnostics Registry**: We may recommend raw ingredient formulations or third-party diagnostic services (e.g., metabolic testing, blood panels) but we maintain a policy of complete disclosure.
2.  **Premium Memberships**: We do not lock primary reading panes behind paywalls. Instead, premium tiers grant early access to frontier decodings, exclusive community forums, and advanced backlog prioritization rights.
3.  **Value-Added Tools**: In the future backend phase, dynamic tools (e.g., personalized biometric schedule builders, interactive circuit simulators) may be charged as premium features.

---

## 5. Reference Documentation Links

To see how the brand philosophy maps to product structure, visual stylesheets, and content templates, refer to:
*   **Design Tokens & CSS Variables**: [DESIGN.md](file:///c:/Users/varga/thehealthstream/DESIGN.md) mapping core colors (Synapse Coral, Oxblood, Crimson) to active CSS rules.
*   **Product Definition & Features**: [PRODUCT.md](file:///c:/Users/varga/thehealthstream/PRODUCT.md) outlining user stories, target personas, and validation metrics.
*   **Engineering Conventions**: [gemini.md](file:///c:/Users/varga/thehealthstream/gemini.md) defining the static compilation flow, Python/JS standards, and test environments.
*   **Content Blueprint**: [docs/content_recipe.md](file:///c:/Users/varga/thehealthstream/docs/content_recipe.md) detailing structural templates and tone register enforcement during article drafting.
*   **Strategic Roadmap**: [mission_and_vision.md](file:///c:/Users/varga/thehealthstream/mission_and_vision.md) outlining the long-term vision and email notification integrations.
