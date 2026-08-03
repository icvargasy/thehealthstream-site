# Mission and Vision: The Healthstream

Long-term objectives, roadmap phasing, and validation milestones for the static systems biology content hub.

---

## 1. Core Mission & Master SSOT Tenets

**The Healthstream** compiles objective, systems-aligned decodings of the underlying feedback loops that govern human health, longevity, daily habits, and scientific literature. Our aim is to present biology, lifestyle protocols, and emerging health research in a precise, non-commercial, and highly accessible format.

### Master SSOT Core Tenets

*   **Pillar 1: Epistemic Transparency & GRADE Alignment**:
    *   Classify all decoded entries into three constructive data confidence tiers: **Consensus Core** (Tier 1: High/Moderate GRADE), **Emerging Frontier** (Tier 2: Low GRADE preliminary human/animal models), and **Exploratory Sandbox** (Tier 3: Very Low GRADE pre-clinical hypotheses).
    *   Symmetrical Scientific Debates: Require cited opposing perspectives in `epistemic_rating.debate_sides` for lower-tier evidence topics.
*   **Pillar 2: Category-Tailored Context Mapping**:
    *   *Biology Nodes*: Trace inputs, cellular transducers, and physiological outcomes where evidence permits.
    *   *Lifestyle Nodes*: Trace behavioral triggers, physiological adaptations, and functional outcomes.
    *   *Book Nodes*: Trace core thesis, supporting arguments, and practical implications.
    *   *Exploratory Sandbox*: Highlight early-stage hypotheses and open research questions transparently.
*   **Pillar 3: Adolescent Readability Benchmark (Flesch-Kincaid Grade 8–9)**:
    *   Translate complex mechanisms into familiar everyday mental models (fuel gauges, traffic signals, factory assembly lines) pictureable in < 5 seconds.
    *   Enforce a **Flesch-Kincaid Grade Level 8–9 (High School / 14–16 Age Literacy)** reading floor for analogy blocks. Biological or chemical textbook jargon (*kinase, phosphorylation, upregulate, transducer*) is strictly forbidden in analogy blocks and reserved exclusively for clinical deep dives.
    *   *Good vs. Bad Rubric*:
        *   ❌ **Bad (Jargon Overload)**: *"AMPK suppresses mTORC1 via phosphorylation under low ATP."*
        *   ✅ **Good (Feynman Mental Model)**: *"Think of AMPK as the cell's main fuel gauge, pausing construction projects when energy reserves drop."*
*   **Pillar 4: Strategic Monetization & Editorial Independence**:
    *   *Decoupled Core*: All decoded pathways, jargon definitions, and GRADE evidence reviews remain 100% free, open-access, and paywall-free under Creative Commons/MIT.
    *   *Strategic Monetization Boundaries*: Future monetization is restricted to value-add utilities (biometric protocol calculators), third-party lab diagnostic referrals, and community supporters (GitHub Sponsors).
    *   *Mandatory Disclosure*: Editorial choices and evidence grades are 100% decoupled from financial incentives. Any commercial partner or affiliate link carries explicit visual disclosure tags (`[Partner Referral]`).
*   **Pillar 5: Systems Analogy Rule (3-Element Structural Mapping)**:
    *   Enforce a mandatory 3-element mapping for all analogy blocks across biological, lifestyle, and frontier entries:
        `[Target Mechanism/System]` → `[Everyday Systems Parallel]` → `[Behavior / Failure Mode]`.
    *   Ensure the everyday system is instantly recognizable without domain-specific technical knowledge.
*   **Pillar 6: Frontier Science & Content Expansion Vision**:
    *   Expand content reach across three systemic domains: *Biological Pathways*, *Lifestyle Protocols*, and *Frontier / Emerging Science* (pre-clinical longevity research, early human trials, systems biology paradigms).
    *   Maintain epistemic transparency by dual-tiering graph connections:
        *   **Tier 1 (Curated / Established)**: Supported by High/Moderate GRADE certainty. Rendered in 1–2 line format with directional badges.
        *   **Tier 2 (Frontier / Emerging Hypotheses)**: Early-stage research or speculative connections. Rendered as 1-line entries with an `Emerging Hypothesis` tag and an **`Endorse Connection →`** link pre-filling community proposals.
*   **Zero-Runtime & Zero-Cost Architecture**: Compiles statically to GitHub Pages without server execution. Uses Google Forms/Sheets for background backlog upvoting (`no-cors`) and Giscus for static comments.
*   **3-Tier Metaphor & Complexity Ceilings**:
    *   *Level 1 (Single Molecule / State)*: Max 20 words.
    *   *Level 2 (Dual Interaction / Process)*: Max 35 words (Card teaser ceiling).
    *   *Level 3 (Multi-System Loop / Disease)*: Max 45 words (Popover ceiling).
*   **Separation of Concerns**: Strategy and core tenets live here in `mission_and_vision.md` (SSOT). Voice and style live in `BRAND.md`; functional specs and metrics live in `PRODUCT.md`; visual design tokens live in `DESIGN.md`; AI agent rules and compiler build pipelines live in `GEMINI.md`.

---

## 2. Future Vision Phases & Roadmap

```
PHASE 1: Static MVP ──(Weekly Return >20%)──→ PHASE 2: Curation & Discussion Loops
                                                              │
                                                              ▼
PHASE 4: Expert Cryptographic Sign-offs ←── PHASE 3: Dynamic Graph & Custom DB
```

### Phase 1: Static MVP (Current Phase)
*   **Objective**: Validate audience interest in decoded systems biology content.
*   **Features**:
    *   Unified feed of color-coded cards (Science, Lifestyle, Books).
    *   Card detail pages featuring a 1-Min Pill Answer at the top.
    *   Static controversy index slider.
    *   Interactive client jargon popovers (click-to-open).
    *   Local HTML builder script.

### Phase 2: Curation, Voting & Discussion Loops
*   **Objective**: Automate curation and collect reader feedback with zero hosting cost.
*   **Proposed Scope**:
    *   **Silent Backlog Voting & Proposals**: Custom JavaScript forms that post data asynchronously to a Google Form linked to a Google Sheet (using `fetch` in `no-cors` mode).
    *   **Static Comments Widget**: Integration of Giscus at the bottom of article pages. Comments are stored as GitHub Discussions, avoiding database costs and platform lock-in.
    *   **Scheduled Rebuild Action**: An automated GitHub Action that fetches Google Sheet votes/proposals on a daily schedule, runs `tools/new_entry_in_pipeline.py --import` to update `backlog.json`, and rebuilds the static pages.
*   **Google Apps Script Notification Integration**:
    *   *Paste this script in Google Sheet Extensions > Apps Script and set up an 'On Form Submit' trigger to receive immediate notifications at `icvargasy@gmail.com` when new entries are registered:*
    ```javascript
    /**
     * Sends an email notification to the site administrator when new topic proposals 
     * or votes are submitted to the Google Sheet.
     */
    function sendNewSubmissionEmail(e) {
      var recipient = "icvargasy@gmail.com";
      var subject = "🌱 The Healthstream: New Entry Proposal or Vote Submitted";
      var details = "";
      
      if (e && e.values) {
        details = "\n\nSubmission Details:\n" + e.values.map(function(val, idx) {
          return "Field [" + idx + "]: " + val;
        }).join("\n");
      } else {
        try {
          var sheet = SpreadsheetApp.getActiveSheet();
          var lastRow = sheet.getLastRow();
          var lastColumn = sheet.getLastColumn();
          if (lastRow > 1) {
            var rowData = sheet.getRange(lastRow, 1, 1, lastColumn).getValues()[0];
            details = "\n\nLast Sheet Row Details:\n" + rowData.map(function(val, idx) {
              return "Column " + (idx + 1) + ": " + val;
            }).join("\n");
          }
        } catch (err) {
          details = "\n(Could not retrieve row details: " + err.message + ")";
        }
      }
      
      var body = "Hello,\n\nA new entry suggestion or backlog vote was submitted on " + new Date().toLocaleString() + "." + details + "\n\nThis submission will be ingested in the next scheduled build run.\n\n-- The Healthstream Pipeline Automaton";
      
      GmailApp.sendEmail(recipient, subject, body);
    }
    ```
*   **Transition Gate to Phase 2**:
    *   [ ] Week 4 Cohort Return Rate ≥ 20% on the Static MVP.
    *   [ ] Popover activation rate ≥ 1.5 clicks per session.

### Phase 3: Dynamic Content Graph & Custom Database
*   **Objective**: Move off static files to support dynamic network queries and advanced user tools.
*   **Proposed Scope**:
    *   **Database Decision**: Select a database framework suited for highly-connected biological nodes. Options include Graph Databases (e.g., Neo4j/Memgraph) or lightweight Relational Databases (e.g., SQLite/PostgreSQL) with a dedicated edge connection table.
    *   **Technology Stack Pathways**: Detailed route for both Python (FastAPI + SQLModel) and TypeScript (Next.js/Express + Prisma) to avoid architectural bottlenecks.
    *   **Personalization Engine**: Allow users to compile customized lifestyle protocol schedules based on their personal biometric goals.
*   **Transition Gate to Phase 3**:
    *   [ ] Total backlog vote count ≥ 500 votes.
    *   [ ] Article count exceeds 40 unique decoded nodes.

### Phase 4: Expert Cryptographic Sign-offs
*   **Objective**: Establish peer review and trust authority.
*   **Proposed Scope**:
    *   Verified clinicians and researchers sign off on content revisions using public-key cryptography.
    *   Display digital signatures on article cards to verify factual integrity and scientific consensus.

---

## Reference Documentation Links

To see how the long-term vision maps to product features, brand design, and static compilation, refer to:
*   **Product Definition & Features**: [PRODUCT.md](file:///c:/Users/varga/thehealthstream/PRODUCT.md) outlining user stories, target personas, and MVP validation metrics.
*   **Brand Identity & Assets**: [BRAND.md](file:///c:/Users/varga/thehealthstream/BRAND.md) containing the logomarks catalog and Synapse & Ink strategy foundations.
*   **Engineering Conventions**: [gemini.md](file:///c:/Users/varga/thehealthstream/gemini.md) defining the static compilation flow, Python/JS standards, and test environments.

