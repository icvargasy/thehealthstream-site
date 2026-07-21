// @vitest-environment jsdom
import { describe, it, expect, beforeEach, vi, beforeAll } from "vitest";

// Mock localStorage
const localStorageStore = {};
const localStorageMock = {
  getItem: vi.fn((key) => localStorageStore[key] || null),
  setItem: vi.fn((key, value) => {
    localStorageStore[key] = String(value);
  }),
  removeItem: vi.fn((key) => {
    delete localStorageStore[key];
  }),
  clear: vi.fn(() => {
    for (const key in localStorageStore) {
      delete localStorageStore[key];
    }
  }),
};
Object.defineProperty(window, "localStorage", { value: localStorageMock });

// Mock scrollTo
if (!window.Element.prototype.scrollTo) {
  window.Element.prototype.scrollTo = vi.fn();
}
if (!window.scrollTo) {
  window.scrollTo = vi.fn();
}

beforeAll(async () => {
  await import("../app.js");
});

describe("Client Interaction - app.js", () => {
  beforeEach(() => {
    // Clean mock storage
    localStorageMock.clear();
    vi.clearAllMocks();

    // Mock search_index.json fetch
    const mockSearchIndex = [
      { title: "AMPK Energy Activation", slug: "ampk-activation.html", type: "article", category: "Biology & Science", teaser: "Fasting activates AMPK." },
      { title: "mTOR Growth regulation", slug: "vocabulary.html#mtor", type: "glossary", category: "Jargon Glossary", teaser: "mTOR details." }
    ];
    window.fetch = vi.fn().mockImplementation(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockSearchIndex),
      })
    );

    // Reset DOM and apply default theme (representing layout.html inline script behavior)
    document.body.innerHTML = `
      <header class="global-header">
        <button id="sidebar-toggle" aria-expanded="true">Toggle</button>
        <button id="theme-toggle">
          <span class="sun-icon">Sun</span>
          <span class="moon-icon">Moon</span>
        </button>
        <div class="header-search-container" id="header-search">
          <input type="search" id="global-search" placeholder="Search..." aria-label="Search content">
          <div id="search-results" class="search-results-dropdown" role="listbox" style="display: none;"></div>
        </div>
      </header>
      
      <div id="dashboard-container">
        <aside id="sidebar">
          <nav class="sidebar-section">
            <div class="sidebar-title">Topics</div>
            <ul class="nav-list">
              <li>
                <a href="category-biology.html" class="nav-link category-link cat-biology" data-category="biology">
                  Biological Circuits <span class="category-count">(1)</span>
                </a>
              </li>
            </ul>
          </nav>
          
          <div class="sidebar-section">
            <ul class="backlog-list">
              <li class="backlog-item" data-id="autophagy-kinetics">
                <button class="backlog-votes" data-base-votes="124" aria-label="Upvote topic">
                  <span class="upvote-icon">▲</span>
                  <span class="vote-count">124</span>
                </button>
              </li>
            </ul>
          </div>
        </aside>
        
        <main id="reading-pane">
          <div class="content-container">
            <div class="detail-grade-container">
              <button class="detail-grade-badge grade-high" id="grade-trigger" aria-haspopup="true" aria-expanded="false">
                High
              </button>
              <div class="grade-popover-card" id="grade-popover" role="dialog">
                <button class="grade-popover-close">&times;</button>
                <p class="grade-popover-rationale">Consensus is supported.</p>
              </div>
            </div>
            <p>
              Let's test <span class="jargon-term" data-term="AMPK" data-definition="Energy enzyme" data-slug="ampk">AMPK</span>.
            </p>
            <section class="evidence-section">
              <h2 class="evidence-title">Evidence</h2>
              <div class="evidence-content">
                <p>Deep scientific evidence.</p>
              </div>
            </section>
          </div>
        </main>
      </div>
    `;
    document.body.setAttribute("data-theme", "light");

    // Trigger initialization
    document.dispatchEvent(new Event("DOMContentLoaded"));
  });

  it("should toggle theme between light and dark modes and persist preference", () => {
    const themeBtn = document.getElementById("theme-toggle");
    
    // Default is light
    expect(document.body.getAttribute("data-theme")).toBe("light");
    
    // Toggle to dark
    themeBtn.click();
    expect(document.body.getAttribute("data-theme")).toBe("dark");
    expect(localStorageMock.setItem).toHaveBeenCalledWith("theme", "dark");
    
    // Toggle back to light
    themeBtn.click();
    expect(document.body.getAttribute("data-theme")).toBe("light");
    expect(localStorageMock.setItem).toHaveBeenCalledWith("theme", "light");
  });

  it("should collapse/expand sidebar and persist preference", () => {
    const sidebarBtn = document.getElementById("sidebar-toggle");
    const container = document.getElementById("dashboard-container");

    expect(document.body.classList.contains("left-collapsed")).toBe(false);
    expect(sidebarBtn.getAttribute("aria-expanded")).toBe("true");

    // Click collapse
    sidebarBtn.click();
    expect(document.body.classList.contains("left-collapsed")).toBe(true);
    expect(container.classList.contains("left-collapsed")).toBe(true);
    expect(sidebarBtn.getAttribute("aria-expanded")).toBe("false");
    expect(localStorageMock.setItem).toHaveBeenCalledWith("left_sidebar_collapsed", "true");

    // Click expand
    sidebarBtn.click();
    expect(document.body.classList.contains("left-collapsed")).toBe(false);
    expect(sidebarBtn.getAttribute("aria-expanded")).toBe("true");
    expect(localStorageMock.setItem).toHaveBeenCalledWith("left_sidebar_collapsed", "false");
  });

  it("should display popover definitions when clicking jargon terms", () => {
    const term = document.querySelector(".jargon-term");
    
    // Before click, popover doesn't exist or is not visible
    let popover = document.getElementById("global-popover");
    if (popover) {
      expect(popover.classList.contains("visible")).toBe(false);
    }

    // Click jargon term
    term.click();
    
    popover = document.getElementById("global-popover");
    expect(popover).not.toBeNull();
    expect(popover.classList.contains("visible")).toBe(true);
    expect(popover.querySelector(".popover-def").textContent).toBe("Energy enzyme");
    expect(popover.querySelector("a").getAttribute("href")).toBe("vocabulary/ampk.html");

    // Click outside to dismiss
    document.body.click();
    expect(popover.classList.contains("visible")).toBe(false);
  });

  it("should record backlog votes in localStorage and disable button", async () => {
    // Pre-populate email in localStorage to bypass prompt
    localStorageStore["voter_email"] = "test@example.com";

    const item = document.querySelector(".backlog-item");
    const button = item.querySelector(".backlog-votes");
    const voteCount = button.querySelector(".vote-count");

    expect(voteCount.textContent).toBe("124");
    expect(button.disabled).toBe(false);

    // Vote
    button.click();
    
    // Wait for the async fetch to finish and update UI
    await vi.waitFor(() => {
      if (voteCount.textContent !== "125") throw new Error("Badge not updated");
    });

    expect(voteCount.textContent).toBe("125");
    expect(button.disabled).toBe(true);
    expect(button.classList.contains("voted")).toBe(true);
    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      "backlog_votes",
      JSON.stringify({ "autophagy-kinetics": true })
    );
  });



  it("should fetch search index on focus, filter results on input, and support keyboard navigation", async () => {
    const searchInput = document.getElementById("global-search");
    const searchResults = document.getElementById("search-results");

    expect(searchResults.style.display).toBe("none");

    // Focus input (should trigger fetch)
    searchInput.dispatchEvent(new Event("focus"));
    expect(window.fetch).toHaveBeenCalledWith("search_index.json");

    // Give fetch a tick to resolve
    await new Promise(resolve => setTimeout(resolve, 0));

    // Type "ampk"
    searchInput.value = "ampk";
    searchInput.dispatchEvent(new Event("input"));

    expect(searchResults.style.display).toBe("block");
    const items = searchResults.querySelectorAll(".search-result-item");
    expect(items.length).toBe(1);
    expect(items[0].querySelector(".result-title").textContent).toBe("AMPK Energy Activation");

    // Arrow Down keyboard event
    searchInput.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowDown" }));
    expect(items[0].classList.contains("active")).toBe(true);

    // Escape key to close
    searchInput.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
    expect(searchResults.style.display).toBe("none");
  });



  it("should toggle the GRADE evidence rating popover on click and dismiss correctly", () => {
    const trigger = document.getElementById("grade-trigger");
    const popover = document.getElementById("grade-popover");
    const closeBtn = popover.querySelector(".grade-popover-close");

    expect(trigger.getAttribute("aria-expanded")).toBe("false");
    expect(popover.classList.contains("visible")).toBe(false);

    // Click trigger to show
    trigger.click();
    expect(trigger.getAttribute("aria-expanded")).toBe("true");
    expect(popover.classList.contains("visible")).toBe(true);

    // Click close button to hide
    closeBtn.click();
    expect(trigger.getAttribute("aria-expanded")).toBe("false");
    expect(popover.classList.contains("visible")).toBe(false);

    // Click trigger to show again
    trigger.click();
    expect(popover.classList.contains("visible")).toBe(true);

    // Click outside to dismiss
    document.body.click();
    expect(trigger.getAttribute("aria-expanded")).toBe("false");
  });

  it("should close the search dropdown and clear input when a search result is clicked", async () => {
    const searchInput = document.getElementById("global-search");
    const searchResults = document.getElementById("search-results");

    // Trigger focus and fetch
    searchInput.dispatchEvent(new Event("focus"));
    await new Promise(resolve => setTimeout(resolve, 0));

    // Input text
    searchInput.value = "ampk";
    searchInput.dispatchEvent(new Event("input"));
    expect(searchResults.style.display).toBe("block");

    // Click result item
    const item = searchResults.querySelector(".search-result-item");
    item.addEventListener("click", (e) => e.preventDefault());
    item.click();

    expect(searchResults.style.display).toBe("none");
    expect(searchInput.value).toBe("");
  });

  it("should dynamically sort cards based on select change", () => {
    // Add sorting UI to document
    document.body.innerHTML += `
      <select id="feed-sort-select">
        <option value="newest">Newest</option>
        <option value="oldest">Oldest</option>
        <option value="alpha-asc">A-Z</option>
        <option value="alpha-desc">Z-A</option>
      </select>
      <div id="feed-cards-container">
        <div class="feed-card" data-created="2026-06-12" data-title="Beta Card">Beta</div>
        <div class="feed-card" data-created="2026-06-14" data-title="Alpha Card">Alpha</div>
        <div class="feed-card" data-created="2026-06-10" data-title="Gamma Card">Gamma</div>
      </div>
    `;

    // Re-initialize theme and other features so the listener gets bound to the new elements
    document.dispatchEvent(new Event("DOMContentLoaded"));

    const sortSelect = document.getElementById("feed-sort-select");
    const container = document.getElementById("feed-cards-container");

    const getTitles = () => Array.from(container.querySelectorAll(".feed-card")).map(c => c.textContent.trim());

    // Sort newest
    sortSelect.value = "newest";
    sortSelect.dispatchEvent(new Event("change"));
    expect(getTitles()).toEqual(["Alpha", "Beta", "Gamma"]); // 14, 12, 10

    // Sort oldest
    sortSelect.value = "oldest";
    sortSelect.dispatchEvent(new Event("change"));
    expect(getTitles()).toEqual(["Gamma", "Beta", "Alpha"]); // 10, 12, 14

    // Sort A-Z
    sortSelect.value = "alpha-asc";
    sortSelect.dispatchEvent(new Event("change"));
    expect(getTitles()).toEqual(["Alpha", "Beta", "Gamma"]); // Alpha, Beta, Gamma

    // Sort Z-A
    sortSelect.value = "alpha-desc";
    sortSelect.dispatchEvent(new Event("change"));
    expect(getTitles()).toEqual(["Gamma", "Beta", "Alpha"]); // Gamma, Beta, Alpha
  });

  it("should close popover and scroll to evidence-section when popover-more-link is clicked", () => {
    const popover = document.getElementById("grade-popover");
    
    // Add more-link non-destructively
    const p = document.createElement("p");
    p.className = "grade-popover-rationale";
    p.innerHTML = 'Consensus is supported. <a href="#evidence-section" class="popover-more-link">more...</a>';
    popover.appendChild(p);
    
    const container = document.querySelector(".content-container");
    const section = document.createElement("section");
    section.id = "evidence-section";
    section.textContent = "Evidence Section";
    container.appendChild(section);

    const trigger = document.getElementById("grade-trigger");
    const moreLink = popover.querySelector(".popover-more-link");
    const readingPane = document.getElementById("reading-pane");

    readingPane.scrollTo = vi.fn();

    // Open popover
    trigger.click();
    expect(popover.classList.contains("visible")).toBe(true);

    // Click more... link (calling preventDefault to bypass JSDOM async navigation)
    moreLink.addEventListener("click", (e) => e.preventDefault());
    moreLink.click();

    expect(popover.classList.contains("visible")).toBe(false);
    expect(readingPane.scrollTo).toHaveBeenCalled();
  });

  it("should intercept local hash links and scroll reading pane", () => {
    const container = document.querySelector(".content-container");
    
    // Add elements non-destructively
    const anchor = document.createElement("a");
    anchor.href = "#test-section";
    anchor.id = "test-anchor";
    anchor.textContent = "Go to Test Section";
    container.appendChild(anchor);
    
    const targetDiv = document.createElement("div");
    targetDiv.id = "test-section";
    targetDiv.textContent = "Test Section";
    container.appendChild(targetDiv);

    const readingPane = document.getElementById("reading-pane");
    readingPane.scrollTo = vi.fn();

    // Click anchor link (calling preventDefault to bypass JSDOM async navigation)
    anchor.addEventListener("click", (e) => e.preventDefault());
    anchor.click();

    expect(readingPane.scrollTo).toHaveBeenCalled();
  });

  it("should toggle visibility of feed cards when filter buttons are clicked", () => {
    const container = document.querySelector(".content-container");
    const toggleRow = document.createElement("div");
    toggleRow.innerHTML = `
      <div class="feed-toggle-container">
        <button class="feed-toggle-btn active" data-filter="all">All</button>
        <button class="feed-toggle-btn" data-filter="decoded">Articles</button>
        <button class="feed-toggle-btn" data-filter="pipeline">Pipeline</button>
      </div>
      <div id="feed-cards-container">
        <div class="feed-card cat-biology" id="card-article">Article Content</div>
        <div class="feed-card pipeline-card-merged cat-biology" id="card-pipeline">Pipeline Content</div>
      </div>
    `;
    container.appendChild(toggleRow);

    // Trigger DOMContentLoaded initialization
    document.dispatchEvent(new window.Event("DOMContentLoaded"));

    const btnAll = document.querySelector('.feed-toggle-btn[data-filter="all"]');
    const btnDecoded = document.querySelector('.feed-toggle-btn[data-filter="decoded"]');
    const btnPipeline = document.querySelector('.feed-toggle-btn[data-filter="pipeline"]');
    const cardArticle = document.getElementById("card-article");
    const cardPipeline = document.getElementById("card-pipeline");

    // Click "decoded" filter
    btnDecoded.click();
    expect(btnDecoded.classList.contains("active")).toBe(true);
    expect(btnAll.classList.contains("active")).toBe(false);
    expect(cardArticle.style.display).toBe("");
    expect(cardPipeline.style.display).toBe("none");

    // Click "pipeline" filter
    btnPipeline.click();
    expect(btnPipeline.classList.contains("active")).toBe(true);
    expect(btnDecoded.classList.contains("active")).toBe(false);
    expect(cardArticle.style.display).toBe("none");
    expect(cardPipeline.style.display).toBe("");

    // Click "all" filter
    btnAll.click();
    expect(btnAll.classList.contains("active")).toBe(true);
    expect(cardArticle.style.display).toBe("");
    expect(cardPipeline.style.display).toBe("");
  });

  it("should handle proposal form submission and toggle '__other_option__' custom input", async () => {
    const container = document.querySelector(".content-container");
    const formDiv = document.createElement("div");
    formDiv.innerHTML = `
      <form id="proposal-form">
        <input type="email" id="form-email" value="test@example.com" required>
        <input type="text" id="form-question" value="Does EGCG boost AMPK?" required>
        <input type="text" id="form-source" value="PubMed">
        <input type="radio" name="entry.336364410" value="biology" checked>
        <input type="radio" name="entry.336364410" id="category-other-radio" value="__other_option__">
        <input type="text" id="category-other-text" disabled>
        <input type="text" id="form-impact" value="High impact">
        <button type="submit" id="proposal-submit-btn">Submit Proposal</button>
        <div id="proposal-form-message"></div>
      </form>
    `;
    container.appendChild(formDiv);

    document.dispatchEvent(new window.Event("DOMContentLoaded"));

    const otherRadio = document.getElementById("category-other-radio");
    const otherText = document.getElementById("category-other-text");

    window.alert = vi.fn();

    // Radio toggle enables text input
    otherRadio.checked = true;
    otherRadio.dispatchEvent(new Event("change"));
    expect(otherText.disabled).toBe(false);
    otherText.value = "Custom Category";

    window.fetch = vi.fn().mockResolvedValue({ ok: true });

    const form = document.getElementById("proposal-form");
    form.dispatchEvent(new Event("submit", { cancelable: true }));

    await vi.waitFor(() => {
      expect(document.querySelector(".form-confirmation-card")).not.toBeNull();
    });
    expect(localStorageMock.setItem).toHaveBeenCalledWith("voter_email", "test@example.com");
  });

  it("should open email verification modal when voting on backlog item without cached email", async () => {
    const voteBtn = document.querySelector(".backlog-votes");
    voteBtn.click();

    const modal = document.querySelector(".vote-modal-overlay");
    expect(modal).not.toBeNull();

    const emailInput = modal.querySelector("#vote-modal-email");
    emailInput.value = "community@example.com";

    window.fetch = vi.fn().mockResolvedValue({ ok: true });
    const submitBtn = modal.querySelector(".vote-modal-submit");
    submitBtn.click();

    await vi.waitFor(() => {
      expect(document.querySelector(".vote-modal-overlay")).toBeNull();
    });
    expect(localStorageMock.setItem).toHaveBeenCalledWith("voter_email", "community@example.com");
  });
});

