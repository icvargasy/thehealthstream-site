"use strict";

const safeStorage = {
  getItem: (key) => {
    try {
      return window.localStorage ? window.localStorage.getItem(key) : null;
    } catch (e) {
      return null;
    }
  },
  setItem: (key, value) => {
    try {
      if (window.localStorage) {
        window.localStorage.setItem(key, value);
      }
    } catch (e) {
      // Ignore
    }
  }
};

/**
 * Initializes and manages all interactive frontend states for The Healthstream.
 */
document.addEventListener("DOMContentLoaded", () => {
  initializeTheme();
  initializeSidebar();
  initializeJargonPopovers();
  initializeBacklogVoting();
  initializeSearch();
  initializeFeedSorting();
  initializeProposalSubmission();
  initializeContactSubmission();
  initializeBackToTop();
  initializeTocNavigation();
  initializeGradePopover();
  initializeScrollingAndHash();
  initializeFeedToggle();
  initializeCardClicks();
  initializeLexiconVerification();
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
    safeStorage.setItem("theme", activeTheme);
    
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

  // Restore collapsed state (default to collapsed on mobile <= 768px if no preference stored)
  const isMobile = window.innerWidth <= 768;
  const storedState = safeStorage.getItem("left_sidebar_collapsed");
  const isCollapsed = storedState !== null ? storedState === "true" : isMobile;
  
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
    
    safeStorage.setItem("left_sidebar_collapsed", willCollapse ? "true" : "false");
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
    popover.setAttribute("role", "dialog");
    popover.setAttribute("aria-label", "Jargon glossary definition");
    popover.setAttribute("tabindex", "-1");
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

    const left = rect.left + (rect.width / 2) - (popoverWidth / 2);
    
    const headerHeight = parseInt(
      getComputedStyle(document.documentElement).getPropertyValue("--header-height") || "56",
      10
    );
    const spaceAbove = rect.top - headerHeight;
    let top;
    
    if (spaceAbove < popoverHeight + 10) {
      // Position below the target word
      top = rect.bottom + 8;
      popover.classList.remove("popover-above");
      popover.classList.add("popover-below");
    } else {
      // Position above the target word
      top = rect.top - popoverHeight - 8;
      popover.classList.remove("popover-below");
      popover.classList.add("popover-above");
    }

    popover.style.left = `${Math.max(10, Math.min(left, window.innerWidth - popoverWidth - 10))}px`;
    popover.style.top = `${top}px`;
  };

  /**
   * Hides the global popover.
   */
  const hidePopover = () => {
    popover.classList.remove("visible");
  };

  const handleTermActivation = (term, e) => {
    e.stopPropagation();
    const definition = term.getAttribute("data-definition") || "";
    const slug = term.getAttribute("data-slug") || "";
    const canonicalKey = term.getAttribute("data-term") || "";
    const matchedText = term.getAttribute("data-matched-text") || term.innerText || "";
    const basePath = typeof window.BASE_PATH !== "undefined" ? window.BASE_PATH : "";
    const href = `${basePath}vocabulary/${slug}.html`;

    const parsedDefinition = definition.replace(/\{\{BASE_PATH\}\}|%7B%7BBASE_PATH%7D%7D/gi, basePath);

    let aliasHtml = "";
    if (canonicalKey && matchedText && matchedText.trim().toLowerCase() !== canonicalKey.trim().toLowerCase()) {
      aliasHtml = `
        <div class="popover-alias-badge" style="font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; background-color: var(--selected-bg); color: var(--accent-synapse); border: 1px solid var(--selected-border); padding: 2px 6px; border-radius: var(--radius-pill); align-self: flex-start; margin-top: calc(-1 * var(--space-1)); margin-bottom: var(--space-1);">
          Alias: ${matchedText}
        </div>
      `;
    }

    popover.innerHTML = `
      <div class="popover-term-title" style="font-weight: 700; color: var(--accent-synapse); font-size: 0.95rem; margin-bottom: var(--space-1);">${canonicalKey}</div>
      ${aliasHtml}
      <div class="popover-def">${parsedDefinition}</div>
      <a href="${href}" class="popover-link">View in Glossary &rarr;</a>
    `;

    positionPopover(term);
    popover.classList.add("visible");
  };

  // Delegated event listening for jargon popover activation
  document.addEventListener("click", (e) => {
    const term = e.target.closest(".jargon-term");
    if (term) {
      handleTermActivation(term, e);
    } else if (popover && !popover.contains(e.target)) {
      hidePopover();
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      const term = e.target.closest && e.target.closest(".jargon-term");
      if (term) {
        e.preventDefault();
        handleTermActivation(term, e);
      }
    } else if (e.key === "Escape") {
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
  const backlogItems = document.querySelectorAll(".backlog-item, .pipeline-card-merged");
  if (backlogItems.length === 0) return;

  // Retrieve votes map from local storage
  let votesMap = {};
  try {
    const stored = safeStorage.getItem("backlog_votes");
    if (stored) {
      votesMap = JSON.parse(stored);
    }
  } catch (e) {
    console.error("Failed parsing backlog votes storage:", e);
  }

  backlogItems.forEach((item) => {
    const itemId = item.getAttribute("data-id");
    const itemTitle = item.getAttribute("data-title");
    const itemCategory = item.getAttribute("data-category");
    const voteBadge = item.querySelector(".backlog-votes");
    if (!itemId || !voteBadge) return;

    const baseVotes = parseInt(voteBadge.getAttribute("data-base-votes") || "0", 10);
    const voteCountSpan = voteBadge.querySelector(".vote-count");

    const updateVoteUI = (voted) => {
      const displayVotes = voted ? baseVotes + 1 : baseVotes;
      if (voteCountSpan) {
        voteCountSpan.textContent = String(displayVotes);
      } else {
        voteBadge.textContent = String(displayVotes);
      }
      if (voted) {
        voteBadge.classList.add("voted");
        voteBadge.disabled = true;
        item.classList.add("voted");
      } else {
        voteBadge.classList.remove("voted");
        voteBadge.disabled = false;
        item.classList.remove("voted");
      }
    };

    // Apply saved vote state
    if (votesMap[itemId]) {
      updateVoteUI(true);
    }

    const submitVote = (email) => {
      const formUrl = "https://docs.google.com/forms/d/e/1FAIpQLScvE2_p-3PEjrJFZZiemtzs7RJ7DGFt-i4Q2PZQgMK1mMmHrA/formResponse";
      const bodyData = new URLSearchParams({
        "emailAddress": email,
        "entry.1511979281": itemTitle,
        "entry.557600625": itemCategory,
        "entry.20589093": "Vote cast from Healthstream website"
      });

      fetch(formUrl, {
        method: "POST",
        mode: "no-cors",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded"
        },
        body: bodyData.toString()
      })
      .then(() => {
        votesMap[itemId] = true;
        safeStorage.setItem("backlog_votes", JSON.stringify(votesMap));
        updateVoteUI(true);
      })
      .catch((err) => {
        console.error("Failed to submit vote:", err);
        alert("We could not register your support at this moment. Please check your network connection and try again.");
      });
    };

    const triggerVoteFlow = () => {
      if (votesMap[itemId]) return;

      const voterEmail = safeStorage.getItem("voter_email");
      if (voterEmail) {
        submitVote(voterEmail);
        return;
      }
      
      const showModal = () => {
        const existing = document.querySelector(".vote-modal-overlay");
        if (existing) existing.remove();

        const modal = document.createElement("div");
        modal.className = "vote-modal-overlay";
        modal.style.cssText = "position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 10000;";
        
        const itemAccent = getComputedStyle(item).getPropertyValue("--backlog-accent") || "var(--accent-synapse)";

        modal.innerHTML = `
          <div class="vote-modal-content" role="dialog" aria-modal="true" aria-labelledby="vote-modal-title" style="background: var(--bg-paper); border: 1px solid var(--border-color); border-radius: var(--radius-card); padding: var(--space-4); max-width: 400px; width: 90%; box-shadow: var(--shadow-lg); display: flex; flex-direction: column; gap: var(--space-3); animation: modalFadeIn 0.2s ease-out;">
            <h3 id="vote-modal-title" style="margin: 0; font-family: var(--font-display); font-size: 1.2rem; color: var(--text-ink);">Support Topic Proposal</h3>
            <p style="margin: 0; font-size: 0.9rem; color: var(--text-ink-muted); line-height: 1.5;">
              Verify your identity to support <strong>"${itemTitle}"</strong>. We only use this email to validate community voting.
            </p>
            <div style="display: flex; flex-direction: column; gap: var(--space-1);">
              <label for="vote-modal-email" style="font-size: 0.8rem; font-weight: 600; color: var(--text-ink-muted);">Email Address</label>
              <input type="email" id="vote-modal-email" style="padding: 10px 12px; border: 1px solid var(--border-color); border-radius: var(--radius-button); background: var(--bg-surface-alt); color: var(--text-ink); font-family: var(--font-system); font-size: 0.95rem; outline: none; width: 100%; box-sizing: border-box;" placeholder="your.email@example.com" required>
            </div>
            <div style="display: flex; justify-content: flex-end; gap: var(--space-2); margin-top: var(--space-1);">
              <button class="vote-modal-cancel" style="background: transparent; border: 1px solid var(--border-color); color: var(--text-ink-muted); padding: 8px 16px; border-radius: var(--radius-button); font-weight: 600; font-size: 0.85rem; cursor: pointer; transition: background var(--transition-fast);">Cancel</button>
              <button class="vote-modal-submit" style="background: ${itemAccent}; border: 1px solid transparent; color: var(--bg-paper); padding: 8px 20px; border-radius: var(--radius-button); font-weight: 700; font-size: 0.85rem; cursor: pointer; text-transform: uppercase; letter-spacing: 0.05em; transition: opacity var(--transition-fast);">Confirm Support</button>
            </div>
          </div>
        `;

        document.body.appendChild(modal);

        const emailInput = modal.querySelector("#vote-modal-email");
        const cancelBtn = modal.querySelector(".vote-modal-cancel");
        const submitBtn = modal.querySelector(".vote-modal-submit");

        setTimeout(() => emailInput.focus(), 50);

        const handleKeydown = (evt) => {
          if (evt.key === "Escape") {
            closeModal();
          }
        };

        const closeModal = () => {
          document.removeEventListener("keydown", handleKeydown);
          modal.remove();
        };

        document.addEventListener("keydown", handleKeydown);

        cancelBtn.addEventListener("click", closeModal);
        modal.addEventListener("click", (evt) => {
          if (evt.target === modal) closeModal();
        });

        const performSubmit = () => {
          const emailVal = emailInput.value.trim();
          if (!emailVal || !emailVal.includes("@")) {
            emailInput.style.borderColor = "oklch(0.55 0.18 15)";
            return;
          }
          safeStorage.setItem("voter_email", emailVal);
          closeModal();
          submitVote(emailVal);
        };

        submitBtn.addEventListener("click", performSubmit);
        emailInput.addEventListener("keydown", (evt) => {
          if (evt.key === "Enter") {
            evt.preventDefault();
            performSubmit();
          }
        });
      };

      showModal();
    };

    voteBadge.addEventListener("click", (e) => {
      e.stopPropagation();
      triggerVoteFlow();
    });
  });
}



/**
 * Configures and lazy-loads the client-side global autocomplete search bar.
 * Enables keyboard navigation (Up/Down arrows, Enter to confirm, Escape to close).
 * @returns {void}
 */
function initializeSearch() {
  const searchInput = document.getElementById("global-search");
  const searchResults = document.getElementById("search-results");
  const searchContainer = document.getElementById("header-search");
  if (!searchInput || !searchResults || !searchContainer) return;

  let searchIndex = null;
  let activeIndex = -1;
  let currentMatches = [];

  const loadSearchIndex = async () => {
    if (searchIndex) return;
    try {
      const basePath = typeof window.BASE_PATH !== "undefined" ? window.BASE_PATH : "";
      const response = await fetch(basePath + "search_index.json");
      if (!response.ok) throw new Error("Network response error");
      searchIndex = await response.json();
    } catch (e) {
      console.error("Failed loading search index payload:", e);
    }
  };

  const closeDropdown = () => {
    searchResults.style.display = "none";
    searchInput.setAttribute("aria-expanded", "false");
    activeIndex = -1;
  };

  const renderResults = () => {
    if (currentMatches.length === 0) {
      searchResults.innerHTML = '<div class="search-no-results">No matching biological decodings or terms found.</div>';
      searchResults.style.display = "block";
      searchInput.setAttribute("aria-expanded", "true");
      return;
    }

    const itemsHtml = currentMatches.map((item, index) => {
      const catType = item.category_type || (item.type === "glossary" ? "glossary" : "article");
      const badgeClass = `cat-${catType}`;
      const itemClass = `search-result-item cat-${catType}`;
      const basePath = typeof window.BASE_PATH !== "undefined" ? window.BASE_PATH : "";
      
      let pipelineBadgeHtml = "";
      if (item.in_pipeline || item.type === "backlog") {
        pipelineBadgeHtml = `<span class="result-category-badge pipeline-badge-search" style="margin-right: var(--space-1);">In Pipeline</span>`;
      }

      return `
        <a href="${basePath}${item.slug}" class="${itemClass}" role="option" id="search-opt-${index}" data-index="${index}">
          <div class="result-meta">
            <span class="result-title">${item.title}</span>
            <div style="display: flex; gap: var(--space-1); align-items: center;">
              ${pipelineBadgeHtml}
              <span class="result-category-badge ${badgeClass}">${item.category}</span>
            </div>
          </div>
          <p class="result-teaser">${item.teaser}</p>
        </a>
      `;
    }).join("");

    searchResults.innerHTML = itemsHtml;
    searchResults.style.display = "block";
    searchInput.setAttribute("aria-expanded", "true");
    updateActiveItem();
  };

  const updateActiveItem = () => {
    const items = searchResults.querySelectorAll(".search-result-item");
    items.forEach((item, index) => {
      if (index === activeIndex) {
        item.classList.add("active");
        searchInput.setAttribute("aria-activedescendant", item.id);
        if (typeof item.scrollIntoView === "function") {
          item.scrollIntoView({ block: "nearest" });
        }
      } else {
        item.classList.remove("active");
      }
    });
  };

  // Lazy load on focus
  searchInput.addEventListener("focus", async () => {
    await loadSearchIndex();
    if (searchInput.value.trim().length > 0) {
      handleSearchInput();
    }
  });

  const handleSearchInput = () => {
    const query = searchInput.value.toLowerCase().trim();
    if (!query) {
      closeDropdown();
      return;
    }

    if (!searchIndex) return;

    currentMatches = searchIndex.filter((item) => {
      return (
        item.title.toLowerCase().includes(query) ||
        item.category.toLowerCase().includes(query) ||
        item.teaser.toLowerCase().includes(query)
      );
    }).slice(0, 8);

    activeIndex = -1;
    renderResults();
  };

  searchInput.addEventListener("input", handleSearchInput);

  // Keyboard navigation
  searchInput.addEventListener("keydown", (e) => {
    if (searchResults.style.display === "none") return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      activeIndex = (activeIndex + 1) % currentMatches.length;
      updateActiveItem();
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      activeIndex = activeIndex - 1;
      if (activeIndex < 0) activeIndex = currentMatches.length - 1;
      updateActiveItem();
    } else if (e.key === "Enter") {
      if (activeIndex >= 0 && activeIndex < currentMatches.length) {
        e.preventDefault();
        window.location.href = currentMatches[activeIndex].slug;
      }
    } else if (e.key === "Escape") {
      e.preventDefault();
      closeDropdown();
    }
  });

  // Close and clear when a search result link is clicked
  searchResults.addEventListener("click", (e) => {
    const link = e.target.closest(".search-result-item");
    if (link) {
      closeDropdown();
      searchInput.value = "";
    }
  });

  // Close dropdown on click outside
  document.addEventListener("click", (e) => {
    if (!searchContainer.contains(e.target)) {
      closeDropdown();
    }
  });
}



/**
 * Intercepts submission of the topic proposal form and sends it asynchronously to Google Forms.
 * Shows a loading indicator, then replaces form with a custom confirmation block.
 * @returns {void}
 */
function initializeProposalSubmission() {
  const form = document.getElementById("proposal-form");
  if (!form) return;

  // Pre-fill email if already saved
  const savedEmail = safeStorage.getItem("voter_email");
  if (savedEmail) {
    const emailInput = form.querySelector("#form-email");
    if (emailInput) emailInput.value = savedEmail;
  }

  // Handle custom dynamic behaviour for the "Other" category text box
  const otherRadio = form.querySelector("#category-other-radio");
  const otherText = form.querySelector("#category-other-text");
  const allRadios = form.querySelectorAll('input[name="entry.336364410"]');

  if (otherRadio && otherText) {
    otherText.disabled = true;
    allRadios.forEach((radio) => {
      radio.addEventListener("change", () => {
        otherText.disabled = !otherRadio.checked;
        if (otherRadio.checked) {
          otherText.focus();
        }
      });
    });
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();

    const submitBtn = document.getElementById("proposal-submit-btn");
    const messageContainer = document.getElementById("proposal-form-message");

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = "Submitting...";
    }

    const email = form.querySelector("#form-email").value.trim();
    const question = form.querySelector("#form-question").value.trim();
    const source = form.querySelector("#form-source").value.trim();

    const categoryRadio = form.querySelector('input[name="entry.336364410"]:checked');
    if (!categoryRadio) {
      alert("Please select a category.");
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = "Submit Proposal";
      }
      return;
    }

    let category = categoryRadio.value;
    let otherResponse = "";
    if (category === "__other_option__") {
      otherResponse = otherText.value.trim();
      if (!otherResponse) {
        alert("Please specify the other category name.");
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = "Submit Proposal";
        }
        otherText.focus();
        return;
      }
    }

    const impact = form.querySelector("#form-impact").value.trim();

    // Cache email locally
    safeStorage.setItem("voter_email", email);

    const formUrl = "https://docs.google.com/forms/d/e/1FAIpQLSemSavDnZAVNnZ321Mpnhyc99eVLBqvlQVSrVs745qL7jfx9w/formResponse";
    const bodyData = new URLSearchParams({
      "emailAddress": email,
      "entry.68224125": question,
      "entry.1814407461": source,
      "entry.336364410": category,
      "entry.336364410.other_option_response": otherResponse,
      "entry.1526174925": impact
    });

    fetch(formUrl, {
      method: "POST",
      mode: "no-cors",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded"
      },
      body: bodyData.toString()
    })
    .then(() => {
      form.innerHTML = `
        <div class="form-confirmation-card">
          <div class="confirmation-icon-wrapper">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
          </div>
          <h2>Proposal Registered</h2>
          <p>We have received your suggestion. Every proposal helps us map out a more complete layout of our shared biological circuits. Our team will review how this integrates with existing pathways shortly.</p>
          <a href="index.html" class="submit-btn back-explore-btn">&larr; Back to Explore</a>
        </div>
      `;
    })
    .catch((err) => {
      console.error("Proposal submission error:", err);
      if (messageContainer) {
        messageContainer.style.display = "block";
        messageContainer.className = "form-message error";
        messageContainer.textContent = "We could not register your proposal at this moment. Please check your network connection and try again.";
      }
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = "Submit Proposal";
      }
    });
  });
}

/**
 * Intercepts contact inquiry submissions and executes background AJAX form posts to Google Forms.
 * @returns {void}
 */
function initializeContactSubmission() {
  const form = document.getElementById("contact-form");
  if (!form) return;

  // Pre-fill cached email if exists
  const cachedEmail = safeStorage.getItem("voter_email");
  const emailInput = form.querySelector("#form-email");
  if (cachedEmail && emailInput) {
    emailInput.value = cachedEmail;
  }

  // Handle other text inputs enabling/disabling
  const inquiryOtherRadio = form.querySelector("#inquiry-other-radio");
  const inquiryOtherText = form.querySelector("#inquiry-other-text");
  const inquiryRadios = form.querySelectorAll('input[name="entry.941828249"]');

  if (inquiryOtherRadio && inquiryOtherText) {
    inquiryOtherText.disabled = true;
    inquiryRadios.forEach((radio) => {
      radio.addEventListener("change", () => {
        inquiryOtherText.disabled = !inquiryOtherRadio.checked;
        if (inquiryOtherRadio.checked) inquiryOtherText.focus();
      });
    });
  }

  const roleOtherRadio = form.querySelector("#role-other-radio");
  const roleOtherText = form.querySelector("#role-other-text");
  const roleRadios = form.querySelectorAll('input[name="entry.885889466"]');

  if (roleOtherRadio && roleOtherText) {
    roleOtherText.disabled = true;
    roleRadios.forEach((radio) => {
      radio.addEventListener("change", () => {
        roleOtherText.disabled = !roleOtherRadio.checked;
        if (roleOtherRadio.checked) roleOtherText.focus();
      });
    });
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();

    const submitBtn = document.getElementById("contact-submit-btn");
    const messageContainer = document.getElementById("contact-form-message");

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = "Sending...";
    }

    const email = form.querySelector("#form-email").value.trim();
    const message = form.querySelector("#form-message").value.trim();

    const inquiryRadio = form.querySelector('input[name="entry.941828249"]:checked');
    if (!inquiryRadio) {
      alert("Please select the nature of your inquiry.");
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = "Send Inquiry";
      }
      return;
    }

    let inquiry = inquiryRadio.value;
    let inquiryOther = "";
    if (inquiry === "__other_option__") {
      inquiryOther = inquiryOtherText.value.trim();
      if (!inquiryOther) {
        alert("Please specify the other inquiry nature.");
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = "Send Inquiry";
        }
        inquiryOtherText.focus();
        return;
      }
    }

    const roleRadio = form.querySelector('input[name="entry.885889466"]:checked');
    let role = roleRadio ? roleRadio.value : "";
    let roleOther = "";
    if (role === "__other_option__") {
      roleOther = roleOtherText.value.trim();
      if (!roleOther) {
        alert("Please specify your role.");
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = "Send Inquiry";
        }
        roleOtherText.focus();
        return;
      }
    }

    // Cache email locally
    safeStorage.setItem("voter_email", email);

    const formUrl = "https://docs.google.com/forms/d/e/1FAIpQLScnY0-A9rXKikkqJOqWRFgC32kns-ShE56xZ8lW9WMSBvnMHw/formResponse";
    const bodyData = new URLSearchParams({
      "emailAddress": email,
      "entry.941828249": inquiry,
      "entry.941828249.other_option_response": inquiryOther,
      "entry.1129689218": message,
      "entry.885889466": role,
      "entry.885889466.other_option_response": roleOther
    });

    fetch(formUrl, {
      method: "POST",
      mode: "no-cors",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded"
      },
      body: bodyData.toString()
    })
    .then(() => {
      form.innerHTML = `
        <div class="form-confirmation-card">
          <div class="confirmation-icon-wrapper">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
          </div>
          <h2>Message Registered</h2>
          <p>We have successfully registered your inquiry. Our engineering and editorial team will review your feedback shortly. Thank you for helping us refine our decodings.</p>
          <a href="index.html" class="submit-btn back-explore-btn">&larr; Back to Explore</a>
        </div>
      `;
    })
    .catch((err) => {
      console.error("Contact submission error:", err);
      if (messageContainer) {
        messageContainer.style.display = "block";
        messageContainer.className = "form-message error";
        messageContainer.textContent = "We could not register your inquiry at this moment. Please check your network connection and try again.";
      }
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = "Send Inquiry";
      }
    });
  });
}

/**
 * Configures the floating Back to Top button scroll visibility and trigger actions.
 * @returns {void}
 */
function initializeBackToTop() {
  const readingPane = document.getElementById("reading-pane");
  const backToTopBtn = document.getElementById("back-to-top");
  if (!readingPane || !backToTopBtn) return;

  readingPane.addEventListener("scroll", () => {
    if (readingPane.scrollTop > 300) {
      backToTopBtn.classList.add("visible");
    } else {
      backToTopBtn.classList.remove("visible");
    }
  });

  backToTopBtn.addEventListener("click", () => {
    readingPane.scrollTo({ top: 0, behavior: "smooth" });
  });
}

/**
 * Controls active state highlighting and smooth navigation scrolling for the detail page TOC.
 * @returns {void}
 */
function initializeTocNavigation() {
  const readingPane = document.getElementById("reading-pane");
  const tocLinks = document.querySelectorAll(".toc-link");
  const sections = document.querySelectorAll(".detail-section");
  if (!readingPane || tocLinks.length === 0) return;

  // Handle click scroll events
  tocLinks.forEach((link) => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      const targetId = link.getAttribute("href");
      const targetEl = document.querySelector(targetId);
      if (targetEl) {
        // Calculate the target offset relative to the reading pane
        const targetOffsetTop = targetEl.offsetTop;
        // Scroll with a smooth transition, adjusting slightly for scroll padding
        readingPane.scrollTo({
          top: targetOffsetTop - 16,
          behavior: "smooth"
        });

        targetEl.setAttribute("tabindex", "-1");
        if (typeof targetEl.focus === "function") {
          targetEl.focus({ preventScroll: true });
        }

        // Set active class
        tocLinks.forEach((l) => l.classList.remove("active"));
        link.classList.add("active");
      }
    });
  });

  // Track active section on scroll
  readingPane.addEventListener("scroll", () => {
    let currentActiveId = "";
    const paneScrollTop = readingPane.scrollTop;
    
    sections.forEach((section) => {
      const sectionTop = section.offsetTop;
      if (paneScrollTop >= (sectionTop - 120)) {
        currentActiveId = "#" + section.id;
      }
    });

    if (currentActiveId) {
      tocLinks.forEach((link) => {
        if (link.getAttribute("href") === currentActiveId) {
          link.classList.add("active");
        } else {
          link.classList.remove("active");
        }
      });
    }
  });
}

/**
 * Toggles the GRADE evidence rating popover card and manages click dismissal.
 * @returns {void}
 */
function initializeGradePopover() {
  const trigger = document.getElementById("grade-trigger");
  const popover = document.getElementById("grade-popover");
  const readingPane = document.getElementById("reading-pane");
  if (!trigger || !popover || !readingPane) return;

  const toggle = (show) => {
    const willShow = show !== undefined ? show : (trigger.getAttribute("aria-expanded") !== "true");
    trigger.setAttribute("aria-expanded", willShow ? "true" : "false");
    popover.classList.toggle("visible", willShow);
  };

  trigger.addEventListener("click", (e) => {
    e.stopPropagation();
    toggle();
  });

  const closeBtn = popover.querySelector(".grade-popover-close");
  if (closeBtn) {
    closeBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      toggle(false);
    });
  }

  // Handle smooth scroll when clicking more... link inside the popover (delegated)
  popover.addEventListener("click", (e) => {
    const moreLink = e.target.closest(".popover-more-link");
    if (moreLink) {
      e.preventDefault();
      e.stopPropagation();
      toggle(false); // Close popover
      const target = document.getElementById("evidence-section");
      if (target) {
        if (typeof readingPane.scrollTo === "function") {
          readingPane.scrollTo({
            top: target.offsetTop - 16,
            behavior: "smooth"
          });
        }
      }
    }
  });

  // Dismiss when clicking outside
  document.addEventListener("click", (e) => {
    if (!popover.contains(e.target) && !trigger.contains(e.target)) {
      toggle(false);
    }
  });

  // Dismiss on ESC key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      toggle(false);
    }
  });

  // Dismiss on reading pane scroll
  readingPane.addEventListener("scroll", () => toggle(false));
}

/**
 * Handles real-time client-side sorting of feed cards (by time or lexical ordering, ascending or descending).
 * @returns {void}
 */
function initializeFeedSorting() {
  // Feed sorting (Explore / Category / Tag pages)
  const sortSelect = document.getElementById("feed-sort-select");
  const container = document.getElementById("feed-cards-container");
  if (sortSelect && container) {
    sortSelect.addEventListener("change", () => {
      const value = sortSelect.value;
      const cards = Array.from(container.querySelectorAll(".feed-card, .backlog-item"));
      
      cards.sort((a, b) => {
        const dateA = a.getAttribute("data-created") || "";
        const dateB = b.getAttribute("data-created") || "";
        const titleA = (a.getAttribute("data-title") || "").toLowerCase().trim();
        const titleB = (b.getAttribute("data-title") || "").toLowerCase().trim();

        if (value === "newest") {
          if (dateA !== dateB) return dateB.localeCompare(dateA); // newest first
          return titleA.localeCompare(titleB);
        } else if (value === "oldest") {
          if (dateA !== dateB) return dateA.localeCompare(dateB); // oldest first
          return titleA.localeCompare(titleB);
        } else if (value === "alpha-asc") {
          return titleA.localeCompare(titleB);
        } else if (value === "alpha-desc") {
          return titleB.localeCompare(titleA);
        }
        return 0;
      });

      // Re-append to DOM in new sorted order
      cards.forEach((card) => {
        container.appendChild(card);
      });
    });
  }

  // Backlog page sorting
  const backlogSelect = document.getElementById("backlog-sort-select");
  const backlogContainer = document.getElementById("backlog-list-container");
  if (backlogSelect && backlogContainer) {
    backlogSelect.addEventListener("change", () => {
      const value = backlogSelect.value;
      const items = Array.from(backlogContainer.querySelectorAll(".backlog-item"));

      items.sort((a, b) => {
        const votesA = parseInt(a.getAttribute("data-votes") || "0", 10);
        const votesB = parseInt(b.getAttribute("data-votes") || "0", 10);
        const dateA = a.getAttribute("data-created") || "";
        const dateB = b.getAttribute("data-created") || "";
        const titleA = (a.getAttribute("data-title") || "").toLowerCase().trim();
        const titleB = (b.getAttribute("data-title") || "").toLowerCase().trim();

        if (value === "votes") {
          if (votesA !== votesB) return votesB - votesA; // highest votes first
          return titleA.localeCompare(titleB);
        } else if (value === "newest") {
          if (dateA !== dateB) return dateB.localeCompare(dateA); // newest first
          return titleA.localeCompare(titleB);
        } else if (value === "oldest") {
          if (dateA !== dateB) return dateA.localeCompare(dateB); // oldest first
          return titleA.localeCompare(titleB);
        } else if (value === "alpha-asc") {
          return titleA.localeCompare(titleB);
        } else if (value === "alpha-desc") {
          return titleB.localeCompare(titleA);
        }
        return 0;
      });

      // Re-append to DOM in new sorted order
      items.forEach((item) => {
        backlogContainer.appendChild(item);
      });
    });
  }
}

/**
 * Locks main window scroll to (0, 0) and handles routing/hash navigation within #reading-pane.
 * @returns {void}
 */
function initializeScrollingAndHash() {
  try {
    const readingPane = document.getElementById("reading-pane");
    if (!readingPane) return;

    // 1. Lock window/body scroll to (0,0) so browser's native target element focus / hash jumps
    // don't scroll the body off-screen, cutting off the global header.
    window.addEventListener("scroll", () => {
      if (window.scrollY !== 0 || window.scrollX !== 0) {
        if (typeof window.scrollTo === "function") {
          window.scrollTo(0, 0);
        }
      }
    });

    // 2. Intercept click events on local hash anchor links (where href starts with #),
    // smooth scroll #reading-pane to target, and update history hash without scrolling the window.
    // Skip TOC links and popover-more links because they are handled separately or we want custom behavior.
    document.addEventListener("click", (e) => {
        const freshReadingPane = document.getElementById("reading-pane");
        if (!freshReadingPane) return;

        const anchor = e.target.closest("a");
        if (!anchor) return;
        
        const href = anchor.getAttribute("href");
        if (href && href.startsWith("#")) {
          // Ignore table of contents navigation links and popover-more links
          if (anchor.classList.contains("toc-link") || anchor.classList.contains("popover-more-link")) {
            return;
          }
          
          const targetId = href.substring(1);
          if (!targetId) return;
          
          const targetElement = document.getElementById(targetId);
          if (targetElement) {
            e.preventDefault();
            if (typeof freshReadingPane.scrollTo === "function") {
              freshReadingPane.scrollTo({
                top: targetElement.offsetTop - 16,
                behavior: "smooth"
              });
            }
            // Update hash in address bar without scrolling window
            history.pushState(null, null, href);
          }
        }
      });

    // 3. Inspect window.location.hash on page load, reset window scroll, and scroll #reading-pane to the target element.
    if (window.location.hash) {
      const targetId = window.location.hash.substring(1);
      const targetElement = document.getElementById(targetId);
      if (targetElement) {
        // Force scroll layout lock immediately
        if (typeof window.scrollTo === "function") {
          window.scrollTo(0, 0);
        }
        
        // Delay slightly to allow page layout/content to settle
        setTimeout(() => {
          if (typeof window.scrollTo === "function") {
            window.scrollTo(0, 0);
          }
          const freshReadingPane = document.getElementById("reading-pane");
          if (freshReadingPane && typeof freshReadingPane.scrollTo === "function") {
            freshReadingPane.scrollTo({
              top: targetElement.offsetTop - 16,
              behavior: "auto"
            });
          }
        }, 150);
      }
    }
  } catch (err) {
    console.error("Error in initializeScrollingAndHash:", err);
  }
}


/**
 * Handles client-side filtering toggle buttons for Explore and Category feeds.
 * @returns {void}
 */
function initializeFeedToggle() {
  const toggleButtons = document.querySelectorAll(".feed-toggle-btn");
  const feedCards = document.querySelectorAll(".feed-card");
  
  if (toggleButtons.length === 0) return;
  
  const filterFeed = (filterValue) => {
    feedCards.forEach((card) => {
      const isPipeline = card.classList.contains("pipeline-card-merged");
      
      if (filterValue === "all") {
        card.style.display = "";
      } else if (filterValue === "decoded") {
        card.style.display = isPipeline ? "none" : "";
      } else if (filterValue === "pipeline") {
        card.style.display = isPipeline ? "" : "none";
      }
    });
  };

  // Restore saved filter preference from localStorage
  const savedFilter = safeStorage.getItem("feed_filter") || "all";
  
  toggleButtons.forEach((btn) => {
    const filterValue = btn.getAttribute("data-filter");
    if (filterValue === savedFilter) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });
  
  filterFeed(savedFilter);

  toggleButtons.forEach((button) => {
    button.addEventListener("click", () => {
      toggleButtons.forEach((btn) => btn.classList.remove("active"));
      button.classList.add("active");
      
      const filterValue = button.getAttribute("data-filter");
      safeStorage.setItem("feed_filter", filterValue);
      filterFeed(filterValue);
    });
  });
}


/**
 * Makes the entire .feed-card clickable for published articles,
 * directing navigation to the article link if click is not on other interactive elements.
 * @returns {void}
 */
function initializeCardClicks() {
  document.addEventListener("click", (e) => {
    const card = e.target.closest(".feed-card");
    if (!card) return;

    // Pipeline cards don't lead to a page, so they shouldn't trigger redirection
    if (card.classList.contains("pipeline-card-merged")) return;

    // Do not redirect if clicking on interactive elements (links, buttons, popovers, upvote, jargon definitions)
    if (e.target.closest("a, button, input, select, label, .jargon-term, .backlog-votes")) {
      return;
    }

    const titleLink = card.querySelector(".card-title-link");
    if (titleLink) {
      const href = titleLink.getAttribute("href");
      if (href) {
        window.location.href = href;
      }
    }
  });
}

/**
 * Handles interactive human-verification toggles for jargon lexicon terms.
 * Allows users to click 'Verify' or outline tick icons to mark AI-generated terms as Human Verified.
 * @returns {void}
 */
function initializeLexiconVerification() {
  document.addEventListener("click", (e) => {
    const btn = e.target.closest(".unverified-tick-btn");
    if (!btn) return;
    e.preventDefault();
    e.stopPropagation();

    const term = btn.getAttribute("data-term") || "Term";
    const blueTickHtml = `
      <span class="verified-human-tick" title="Verified Human" aria-label="Verified Human">
        <svg class="verified-tick-svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-left: 4px;">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
          <polyline points="22 4 12 14.01 9 11.01"></polyline>
        </svg>
      </span>
    `;

    const wrapper = document.createElement("span");
    wrapper.innerHTML = blueTickHtml;
    if (btn.parentNode) {
      btn.parentNode.replaceChild(wrapper.firstElementChild, btn);
    }

    try {
      const verified = JSON.parse(localStorage.getItem("verified_terms") || "[]");
      if (!verified.includes(term)) {
        verified.push(term);
        localStorage.setItem("verified_terms", JSON.stringify(verified));
      }
    } catch (err) {
      console.warn("Could not save verification state:", err);
    }
  });
}

