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

    // Reset DOM and apply default theme (representing layout.html inline script behavior)
    document.body.innerHTML = `
      <header class="global-header">
        <button id="sidebar-toggle" aria-expanded="true">Toggle</button>
        <button id="theme-toggle">
          <span class="sun-icon">Sun</span>
          <span class="moon-icon">Moon</span>
        </button>
      </header>
      
      <div id="dashboard-container">
        <aside id="sidebar">
          <div class="accordion-group" id="group-biology">
            <button class="accordion-trigger" aria-controls="content-biology" aria-expanded="true">
              <span>Biology</span>
              <svg class="chevron"></svg>
            </button>
            <div class="accordion-content" id="content-biology">
              <!-- Links -->
            </div>
          </div>
          
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
            <p>
              Let's test <span class="jargon-term" data-term="AMPK" data-definition="Energy enzyme" data-slug="ampk">AMPK</span>.
            </p>
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

  it("should toggle category accordions inside sidebar", () => {
    const group = document.getElementById("group-biology");
    const trigger = group.querySelector(".accordion-trigger");

    expect(group.classList.contains("collapsed")).toBe(false);

    // Toggle collapse
    trigger.click();
    expect(group.classList.contains("collapsed")).toBe(true);
    expect(localStorageMock.setItem).toHaveBeenCalledWith("cat_collapsed_group-biology", "true");

    // Toggle expand
    trigger.click();
    expect(group.classList.contains("collapsed")).toBe(false);
    expect(localStorageMock.setItem).toHaveBeenCalledWith("cat_collapsed_group-biology", "false");
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
    expect(popover.querySelector("a").getAttribute("href")).toBe("vocabulary.html#ampk");

    // Click outside to dismiss
    document.body.click();
    expect(popover.classList.contains("visible")).toBe(false);
  });

  it("should record backlog votes in localStorage and disable button", () => {
    const item = document.querySelector(".backlog-item");
    const badge = item.querySelector(".backlog-votes");
    const button = item.querySelector(".vote-btn");

    expect(badge.textContent).toBe("124");
    expect(button.disabled).toBe(false);

    // Vote
    button.click();
    expect(badge.textContent).toBe("125");
    expect(button.disabled).toBe(true);
    expect(button.textContent).toBe("Voted");
    expect(button.classList.contains("voted")).toBe(true);
    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      "backlog_votes",
      JSON.stringify({ "autophagy-kinetics": true })
    );
  });
});
