// @vitest-environment jsdom
import { describe, it, expect, beforeEach, vi } from "vitest";
import "../app.js"; // Import once to prevent listener accumulation on global document

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
                <span class="backlog-votes" data-base-votes="124">124</span>
                <button class="vote-btn">Vote</button>
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
    const badge = item.querySelector(".backlog-votes");
    const button = item.querySelector(".vote-btn");

    expect(badge.textContent).toBe("124");
    expect(button.disabled).toBe(false);

    // Vote
    button.click();
    
    // Wait for the async fetch to finish and update UI
    await vi.waitFor(() => {
      if (badge.textContent !== "125") throw new Error("Badge not updated");
    });

    expect(badge.textContent).toBe("125");
    expect(button.disabled).toBe(true);
    expect(button.textContent).toBe("Topic Supported");
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
    expect(popover.classList.contains("visible")).toBe(false);
  });
});
