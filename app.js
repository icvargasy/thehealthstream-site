"use strict";

/**
 * Initializes and manages all interactive frontend states for The Healthstream.
 */
document.addEventListener("DOMContentLoaded", () => {
  initializeTheme();
  initializeSidebar();
  initializeAccordions();
  initializeJargonPopovers();
  initializeBacklogVoting();
  initializeEvidenceAccordion();
});

/**
 * Manages light/dark theme selection and synchronization.
 * Handles the click event for the theme toggle button and persists user choice.
 * @returns {void}
 */
function initializeTheme() {
  const themeToggle = document.getElementById("theme-toggle");
  if (!themeToggle) return;

  const sunIcon = themeToggle.querySelector(".sun-icon");
  const moonIcon = themeToggle.querySelector(".moon-icon");

  /**
   * Updates UI icons based on the active theme string.
   * @param {string} theme - 'dark' or 'light'.
   */
  const updateIcons = (theme) => {
    if (theme === "dark") {
      sunIcon.style.display = "block";
      moonIcon.style.display = "none";
    } else {
      sunIcon.style.display = "none";
      moonIcon.style.display = "block";
    }
  };

  // Set initial icon states
  const currentTheme = document.body.getAttribute("data-theme") || "light";
  updateIcons(currentTheme);

  themeToggle.addEventListener("click", () => {
    const activeTheme = document.body.getAttribute("data-theme") === "dark" ? "light" : "dark";
    document.body.setAttribute("data-theme", activeTheme);
    localStorage.setItem("theme", activeTheme);
    
    // Update favicon
    const favicon = document.getElementById("favicon");
    if (favicon) {
      favicon.href = `assets/favicon_${activeTheme}.png`;
    }

    updateIcons(activeTheme);
  });
}

/**
 * Manages the collapsible left sidebar layout state and aria attributes.
 * Persists the sidebar collapsed preference in localStorage.
 * @returns {void}
 */
function initializeSidebar() {
  const sidebarToggle = document.getElementById("sidebar-toggle");
  const dashboardContainer = document.getElementById("dashboard-container");
  if (!sidebarToggle || !dashboardContainer) return;

  // Restore collapsed state
  const isCollapsed = localStorage.getItem("left_sidebar_collapsed") === "true";
  if (isCollapsed) {
    document.body.classList.add("left-collapsed");
    dashboardContainer.classList.add("left-collapsed");
    sidebarToggle.setAttribute("aria-expanded", "false");
  }

  sidebarToggle.addEventListener("click", () => {
    const willCollapse = !document.body.classList.contains("left-collapsed");
    
    document.body.classList.toggle("left-collapsed", willCollapse);
    dashboardContainer.classList.toggle("left-collapsed", willCollapse);
    sidebarToggle.setAttribute("aria-expanded", willCollapse ? "false" : "true");
    
    localStorage.setItem("left_sidebar_collapsed", willCollapse ? "true" : "false");
  });
}

/**
 * Configures the collapsible category accordions inside the left sidebar.
 * Restores and persists the open/collapsed state of each category slug.
 * @returns {void}
 */
function initializeAccordions() {
  const accordionGroups = document.querySelectorAll(".accordion-group");
  
  accordionGroups.forEach((group) => {
    const trigger = group.querySelector(".accordion-trigger");
    const categoryId = group.id;
    if (!trigger || !categoryId) return;

    // Restore state (default is expanded, unless explicitly set to collapsed)
    const isCollapsed = localStorage.getItem(`cat_collapsed_${categoryId}`) === "true";
    if (isCollapsed) {
      group.classList.add("collapsed");
      trigger.setAttribute("aria-expanded", "false");
    }

    trigger.addEventListener("click", () => {
      const willCollapse = !group.classList.contains("collapsed");
      group.classList.toggle("collapsed", willCollapse);
      trigger.setAttribute("aria-expanded", willCollapse ? "false" : "true");
      localStorage.setItem(`cat_collapsed_${categoryId}`, willCollapse ? "true" : "false");
    });
  });
}

/**
 * Spawns and repositions Jargon Popovers above hover/clicked glossary words.
 * Appends a singular popover container to the DOM to prevent element bloat.
 * @returns {void}
 */
function initializeJargonPopovers() {
  const terms = document.querySelectorAll(".jargon-term");
  if (terms.length === 0) return;

  // Create single popover instance
  let popover = document.getElementById("global-popover");
  if (!popover) {
    popover = document.createElement("div");
    popover.id = "global-popover";
    popover.className = "hs-popover";
    document.body.appendChild(popover);
  }

  /**
   * Positions the popover precisely above the target element.
   * @param {HTMLElement} target - The jargon term span.
   */
  const positionPopover = (target) => {
    const rect = target.getBoundingClientRect();
    
    // Set temporary block style to calculate dimensions
    popover.style.display = "flex";
    popover.style.visibility = "hidden";
    popover.classList.add("visible");

    const popoverHeight = popover.offsetHeight;
    const popoverWidth = popover.offsetWidth;

    popover.style.visibility = "visible";
    popover.classList.remove("visible");

    const left = rect.left + window.scrollX + (rect.width / 2) - (popoverWidth / 2);
    const top = rect.top + window.scrollY - popoverHeight - 8;

    popover.style.left = `${Math.max(10, Math.min(left, window.innerWidth - popoverWidth - 10))}px`;
    popover.style.top = `${top}px`;
  };

  /**
   * Hides the global popover.
   */
  const hidePopover = () => {
    popover.classList.remove("visible");
  };

  terms.forEach((term) => {
    term.addEventListener("click", (e) => {
      e.stopPropagation();
      const definition = term.getAttribute("data-definition") || "";
      const slug = term.getAttribute("data-slug") || "";

      popover.innerHTML = `
        <div class="popover-def">${definition}</div>
        <a href="vocabulary.html#${slug}" class="popover-link">View in Glossary →</a>
      `;

      positionPopover(term);
      popover.classList.add("visible");
    });
  });

  // Dismiss on clicking outside or scrolling the reading pane
  document.addEventListener("click", (e) => {
    if (popover && !popover.contains(e.target)) {
      hidePopover();
    }
  });

  const readingPane = document.getElementById("reading-pane");
  if (readingPane) {
    readingPane.addEventListener("scroll", hidePopover);
  }
}

/**
 * Activates local voting counters for the proposed backlog list.
 * Persists the voting status of backlog items in localStorage.
 * @returns {void}
 */
function initializeBacklogVoting() {
  const backlogItems = document.querySelectorAll(".backlog-item");
  if (backlogItems.length === 0) return;

  // Retrieve votes map from local storage
  let votesMap = {};
  try {
    const stored = localStorage.getItem("backlog_votes");
    if (stored) {
      votesMap = JSON.parse(stored);
    }
  } catch (e) {
    console.error("Failed parsing backlog votes storage:", e);
  }

  backlogItems.forEach((item) => {
    const itemId = item.getAttribute("data-id");
    const voteBtn = item.querySelector(".vote-btn");
    const voteBadge = item.querySelector(".backlog-votes");
    if (!itemId || !voteBtn || !voteBadge) return;

    const baseVotes = parseInt(voteBadge.getAttribute("data-base-votes") || "0", 10);

    // Apply saved vote state
    if (votesMap[itemId]) {
      voteBadge.textContent = String(baseVotes + 1);
      voteBtn.textContent = "Voted";
      voteBtn.classList.add("voted");
      voteBtn.disabled = true;
    }

    voteBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      if (votesMap[itemId]) return;

      // Update local storage
      votesMap[itemId] = true;
      localStorage.setItem("backlog_votes", JSON.stringify(votesMap));

      // Update UI state
      voteBadge.textContent = String(baseVotes + 1);
      voteBtn.textContent = "Voted";
      voteBtn.classList.add("voted");
      voteBtn.disabled = true;
    });
  });
}

/**
 * Toggles the detailed scientific evidence and bibliography accordion.
 * @returns {void}
 */
function initializeEvidenceAccordion() {
  const section = document.querySelector(".evidence-section");
  if (!section) return;

  const trigger = section.querySelector(".evidence-trigger");
  if (!trigger) return;

  trigger.addEventListener("click", () => {
    section.classList.toggle("expanded");
    const isExpanded = section.classList.contains("expanded");
    trigger.setAttribute("aria-expanded", isExpanded ? "true" : "false");
  });
}
