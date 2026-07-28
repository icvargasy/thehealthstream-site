# Mission and Vision: The Healthstream

Long-term objectives, roadmap phasing, and validation milestones for the static systems biology content hub.

---

## 1. Core Mission

**The Healthstream** compiles objective, systems-aligned decodings of the underlying feedback loops that govern human health, longevity, daily habits, and scientific literature. Our aim is to present biology, lifestyle protocols, and emerging health research in a precise, non-commercial, and highly accessible format.

### Core Architecture & Curation Principles
*   **Zero-Runtime Framework**: Keep client page loads instantaneous and fully indexable for search engines (SEO/GEO) by compiling all pages statically. Hosted on GitHub Pages without server execution.
*   **Zero-Cost Hybrid Backend**: Leverage Google Forms + Sheets for silent background submissions (proposals, votes) and Giscus (GitHub Discussions API) for static comments. This avoids server hosting costs and platform lock-in.
*   **14-Year-Old (Adolescent) Visuality Principle**: Systems analogies must map 1:1 to everyday physical/mechanical dynamics (plumbing, car engines, traffic lights, factory assembly lines) that a 14-year-old high school student can picture in under 5 seconds. Technical biological or chemical jargon (e.g. *kinase, phosphorylation, upregulate, transducer*) is strictly forbidden in analogy blocks and reserved exclusively for clinical deep dives.
*   **3-Tier Epistemic Transparency**: Rather than ignoring unproven research, entries are categorized into three constructive data confidence tiers: Consensus Core (Tier 1: High/Moderate GRADE), Emerging Frontier (Tier 2: Low GRADE preliminary human/animal models), and Exploratory Sandbox (Tier 3: Very Low GRADE pre-clinical/biofeedback tools).
*   **Community Co-Creation**: Readers actively participate in library curation via pipeline topic upvoting, pathway proposal submissions, and jargon lexicon human verification.
*   **Dual-Lens Framework (Systems Analogy + Clinical Mechanism)**: Every entry presents two complementary perspectives:
    1.  **Systems Analogy**: An intuitive mental model matching biological dynamics 1:1 across multi-domain physical systems.
    2.  **Clinical Mechanism**: Empirical proof, GRADE evidence ratings, RCT metrics, and exact molecular feedback loops.
*   **3-Tier Metaphor & Complexity Ceilings**:
    - *Level 1 (Single Molecule / State)*: Max 20 words.
    - *Level 2 (Dual Interaction / Process)*: Max 35 words (Card teaser ceiling).
    - *Level 3 (Multi-System Loop / Disease)*: Max 45 words (Popover ceiling).
*   **Independent Subagent Verification Protocol**: Every content decoding, schema change, or metaphor addition must be independently audited by task-specific subagent panels evaluating scientific precision, cognitive accessibility, domain matching, and UI/UX layout footprints.
*   **Separation of Concerns**: Product behaviors live in `PRODUCT.md`; styling tokens live in `DESIGN.md`; brand guidelines live in `BRAND.md`; engineering rules live in `gemini.md`. Strategy and milestones live here.

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

