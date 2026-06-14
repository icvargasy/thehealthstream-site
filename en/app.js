"use strict";

/**
 * Initializes and manages all interactive frontend states for The Healthstream.
 */
document.addEventListener("DOMContentLoaded", () => {
  initializeTheme();
  initializeSidebar();
  initializeJargonPopovers();
  initializeBacklogVoting();
  initializeSearch();
  initializeProposalSubmission();
  initializeContactSubmission();
  initializeBackToTop();
  initializeTocNavigation();
  initializeGradePopover();
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

  // Restore collapsed state (default to collapsed on mobile <= 768px if no preference stored)
  const isMobile = window.innerWidth <= 768;
  const storedState = localStorage.getItem("left_sidebar_collapsed");
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
    
    localStorage.setItem("left_sidebar_collapsed", willCollapse ? "true" : "false");
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
      const isSubdir = window.location.pathname.includes("/tags/") || window.location.pathname.includes("/vocabulary/");
      const href = isSubdir ? `../vocabulary/${slug}.html` : `vocabulary/${slug}.html`;

      popover.innerHTML = `
        <div class="popover-def">${definition}</div>
        <a href="${href}" class="popover-link">View in Glossary &rarr;</a>
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
    const itemTitle = item.getAttribute("data-title");
    const itemCategory = item.getAttribute("data-category");
    const voteBtn = item.querySelector(".vote-btn");
    const voteBadge = item.querySelector(".backlog-votes");
    if (!itemId || !voteBtn || !voteBadge) return;

    const baseVotes = parseInt(voteBadge.getAttribute("data-base-votes") || "0", 10);

    // Apply saved vote state
    if (votesMap[itemId]) {
      voteBadge.textContent = String(baseVotes + 1);
      voteBtn.textContent = "Topic Supported";
      voteBtn.classList.add("voted");
      voteBtn.disabled = true;
    }

    const submitVote = (email) => {
      voteBtn.disabled = true;
      voteBtn.textContent = "Sending...";

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
        localStorage.setItem("backlog_votes", JSON.stringify(votesMap));

        voteBadge.textContent = String(baseVotes + 1);
        voteBtn.textContent = "Topic Supported";
        voteBtn.classList.add("voted");
        voteBtn.disabled = true;
      })
      .catch((err) => {
        console.error("Failed to submit vote:", err);
        voteBtn.disabled = false;
        voteBtn.textContent = "Support";
        alert("We could not register your support at this moment. Please check your network connection and try again.");
      });
    };

    voteBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      if (votesMap[itemId]) return;

      const voterEmail = localStorage.getItem("voter_email");
      if (voterEmail) {
        submitVote(voterEmail);
      } else {
        if (item.querySelector(".vote-email-input-wrapper")) return;

        const wrapper = document.createElement("div");
        wrapper.className = "vote-email-input-wrapper";
        wrapper.innerHTML = `
          <label for="vote-email-${itemId}">Before we count your support, we need to verify who you are. Please enter your email:</label>
          <input type="email" id="vote-email-${itemId}" class="vote-email-input" placeholder="your.email@example.com" required>
          <div class="vote-email-actions">
            <button class="vote-confirm-btn">Confirm My Support</button>
            <button class="vote-cancel-btn">Cancel</button>
          </div>
        `;

        item.appendChild(wrapper);

        const confirmBtn = wrapper.querySelector(".vote-confirm-btn");
        const cancelBtn = wrapper.querySelector(".vote-cancel-btn");
        const emailInput = wrapper.querySelector(".vote-email-input");

        cancelBtn.addEventListener("click", (evt) => {
          evt.stopPropagation();
          wrapper.remove();
        });

        confirmBtn.addEventListener("click", (evt) => {
          evt.stopPropagation();
          const emailVal = emailInput.value.trim();
          if (!emailVal || !emailVal.includes("@")) {
            emailInput.style.borderColor = "oklch(0.55 0.18 15)";
            return;
          }
          localStorage.setItem("voter_email", emailVal);
          wrapper.remove();
          submitVote(emailVal);
        });
      }
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
      const response = await fetch("search_index.json");
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
      const badgeClass = item.type === "glossary" ? "cat-glossary" : "cat-article";
      return `
        <a href="${item.slug}" class="search-result-item" role="option" id="search-opt-${index}" data-index="${index}">
          <div class="result-meta">
            <span class="result-title">${item.title}</span>
            <span class="result-category-badge ${badgeClass}">${item.category}</span>
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
  const savedEmail = localStorage.getItem("voter_email");
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
    localStorage.setItem("voter_email", email);

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
  const cachedEmail = localStorage.getItem("voter_email");
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
    localStorage.setItem("voter_email", email);

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
  if (!trigger || !popover) return;

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
  const readingPane = document.getElementById("reading-pane");
  if (readingPane) {
    readingPane.addEventListener("scroll", () => toggle(false));
  }
}
