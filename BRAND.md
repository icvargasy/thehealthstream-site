# Brand Assets & Philosophy: The Healthstream

This document defines the brand philosophy, communication rules, visual assets, and monetization boundaries for **The Healthstream**. It is designed to align both human writers and AI coding/writing agents during copy generation.

---

## 1. Core Philosophy

### 1.1 The Systems Biology Lens
We treat the human body as an interconnected circuit board of biological feedback loops rather than a collection of isolated symptoms. Every entry—whether a biochemical pathway or a daily protocol—must trace the chemical and electrical signals upstream and downstream. 
*   **Do not describe actions in isolation**: Always explain the cascading inputs and outputs (e.g., how insulin suppression phosphorylation activates AMPK, which in turn pauses mTORC1 and up-regulates autophagy).

### 1.2 Epistemic Transparency & Frontier Mapping
We do not limit the registry to established, conservative consensus. We actively explore the "frontier quests" of health—speculative, incoming biological research. However, we maintain absolute honesty:
*   **Clear Classification**: All articles are graded using the GRADE evidence framework (`High`, `Moderate`, `Low`, `Very Low`).
*   **Consensus vs. Frontier**: Decoded pathways with clinical trial backings are marked as **Established Consensus**. Emerging ideas (e.g., early rodent model longevity trials) are explicitly marked as **Frontier Hypotheses** with a `Very Low` or `Low` GRADE rating, and their debate angles must be explicitly outlined in the "Key Scientific Debates" block.

---

## 2. Voice & Tone (The Obama & Brené Brown Synthesis)

Our register is precise and professional (HBR/Toastmasters level), but it communicates with unique cadence and empathy.

### 2.1 Measured & Rhetorical Pacing (Barack Obama)
*   **Inclusive Rhetoric**: Use inclusive pronouns ("we", "our body", "our health") to frame content as a collaborative scientific exploration rather than a lecture.
*   **Parallel Structure**: Use the "rule of three" or parallel phrasing to give paragraphs a rhythmic, measured cadence.
    *   *Example*: *"To reset our circadian clock, to stabilize our morning glucose, and to protect our deep sleep cycles, we must design our interaction with light."*
*   **Deliberate Simplicity**: Avoid over-complex sentences when explaining mechanisms; build step-by-step logic.

### 2.2 Relational Authenticity & Storytelling (Brené Brown)
*   **Empathy for Human Friction**: Acknowledge that lifestyle modifications are hard. Ground dry, mechanical instructions in the reality of human behavior (e.g., acknowledge the emotional craving during a fast, or the social challenges of avoiding blue screens).
*   **The Narrative Bridge**: Explain chemical switches as stories of adaptation, survival, and cellular balance.
    *   *Example*: *"Autophagy is not just a biological label; it is the cell’s internal recycling crew, sweeping away the damage of yesterday to clear a path for tomorrow’s growth."*

### 2.3 Mechanical Precision
*   Use direct, active verbs. Avoid weak helper constructs:
    *   **Prohibited**: *"AMPK serves to regulate cellular energy."*
    *   **Approved**: *"AMPK regulates cellular energy."*
*   Never use clickbait headlines, sensationalized generalizations, or supplement/product endorsements.

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
