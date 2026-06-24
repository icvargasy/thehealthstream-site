"""Static HTML compiler, asset pipeline, and sitemap writer for The Healthstream.

This module processes templates and merges structured data into final HTML files
for landing feeds, detailed decodings, the vocabulary indexes, and static pages.
"""

import os
import re
import shutil
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Dict, List, Any
import markdown
from .linker import slugify


def compile_base_layout(
    template_content: str,
    translations: Dict[str, Any],
    nodes: List[Dict[str, Any]],
    backlog: List[Dict[str, Any]],
    active_nav: str,
    base_path: str = "./",
) -> str:
    """Pre-populates the master layout shell with UI labels and navigation structures.

    Args:
        template_content: The raw HTML content of layout.html.
        translations: Dictionary of translation key-value mappings.
        nodes: Complete list of article nodes for category counting.
        backlog: List of proposed backlog items.
        active_nav: 'feed', 'vocab', 'backlog', 'about', 'contact', or 'category-*' to highlight active links.
        base_path: Relative string prefix for correct asset links.

    Returns:
        The pre-compiled HTML layout string containing content placeholders.
    """
    labels = translations.get("en", {})

    # Build complete replacement map then apply in a single regex pass
    # This avoids O(N_replacements × len(html)) repeated string scans
    replacements: Dict[str, str] = {}
    for key, value in labels.items():
        replacements[f"{{{{label_{key}}}}}"] = str(value)

    replacements["{{base_path}}"] = base_path
    replacements["{{nav_active_feed}}"] = "active" if active_nav == "feed" else ""
    replacements["{{nav_active_vocab}}"] = "active" if active_nav == "vocab" else ""
    replacements["{{nav_active_backlog}}"] = "active" if active_nav == "backlog" else ""
    replacements["{{nav_active_about}}"] = "active" if active_nav == "about" else ""
    replacements["{{nav_active_submit_proposal}}"] = "active" if active_nav == "submit-proposal" else ""
    replacements["{{nav_active_contact}}"] = "active" if active_nav == "contact" else ""
    replacements["{{nav_active_category_biology}}"] = "active" if active_nav == "category-biology" else ""
    replacements["{{nav_active_category_lifestyle}}"] = "active" if active_nav == "category-lifestyle" else ""
    replacements["{{nav_active_category_book}}"] = "active" if active_nav == "category-book" else ""
    replacements["{{count_biology}}"] = str(sum(1 for n in nodes if n.get("type") == "biology"))
    replacements["{{count_lifestyle}}"] = str(sum(1 for n in nodes if n.get("type") == "lifestyle"))
    replacements["{{count_book}}"] = str(sum(1 for n in nodes if n.get("type") == "book"))

    pattern = re.compile("|".join(re.escape(k) for k in replacements))
    html = pattern.sub(lambda m: replacements[m.group(0)], template_content)
    return html


def render_backlog_card(
    item: Dict[str, Any],
    translations: Dict[str, Any],
    is_nested: bool = False,
    vocabulary: Dict[str, Any] = None,
    as_list_item: bool = True,
) -> str:
    """Renders a backlog card HTML in unified flexbox layout format.

    Args:
        item: Backlog item dictionary.
        translations: Translation labels dictionary.
        is_nested: If True, uses '../' path prefix for nested files (e.g. tag pages).
        vocabulary: Optional glossary references dictionary.
        as_list_item: If True, wraps in a <li> element; otherwise uses <div>.

    Returns:
        The rendered HTML markup string.
    """
    labels = translations.get("en", {})
    cat = item.get("category", "")
    category_class = f"cat-{cat}" if cat else ""
    category_label = labels.get(f"category_{cat}", cat).upper()

    prefix = "../" if is_nested else ""
    category_url = f"{prefix}category-{cat}.html"
    backlog_url = f"{prefix}backlog.html"

    tag_pills = []
    for t in item.get("tags", []):
        tag_pills.append(f'<a href="{prefix}tags/{t.lower()}.html" class="tag-pill">#{t}</a>')
    tags_html = f'<div class="card-tags">{" ".join(tag_pills)}</div>' if tag_pills else ""

    created_at = item.get("created_at", "2026-06-01")
    meta_dates_html = f'<div class="card-meta-dates"><span>Proposed: {created_at}</span></div>'
    footer_html = f'<div class="card-footer-row">{tags_html}{meta_dates_html}</div>'

    desc = item["description"]
    if vocabulary:
        from compiler.linker import inject_jargon_links
        desc = inject_jargon_links(desc, vocabulary)

    tag_name = "li" if as_list_item else "div"
    card_html = (
        f'<{tag_name} class="backlog-item backlog-card-compact {category_class}" data-id="{item["id"]}" data-title="{item["title"]}" data-created="{created_at}" data-category="{cat}" data-votes="{item["votes"]}">'
        f'  <div class="backlog-header">'
        f'    <div class="backlog-title-group">'
        f'      <span class="backlog-title">{item["title"]}</span>'
        f'      <a href="{category_url}" class="category-tag">{category_label}</a>'
        f'      <a href="{backlog_url}" class="pipeline-badge">In Pipeline</a>'
        f'    </div>'
        f'    <button class="backlog-votes" data-base-votes="{item["votes"]}" aria-label="Upvote topic">'
        f'      <span class="upvote-icon">▲</span>'
        f'      <span class="vote-count">{item["votes"]}</span>'
        f'    </button>'
        f'  </div>'
        f'  <div class="backlog-desc">{desc}</div>'
        f'  {footer_html}'
        f'</{tag_name}>'
    )
    return card_html


def render_article_card(
    node: Dict[str, Any],
    translations: Dict[str, Any],
    is_nested: bool = False,
    vocabulary: Dict[str, Any] = None,
) -> str:
    """Renders a published article card HTML in unified flexbox layout format.

    Args:
        node: The article node dictionary.
        translations: Translations dictionary.
        is_nested: True if the file resides in a subdirectory (like tag pages).
        vocabulary: Optional dictionary of jargon definitions.

    Returns:
        The rendered HTML markup string.
    """
    labels = translations.get("en", {})
    cat = node.get("type", "")
    category_label = labels.get(f"category_{cat}", cat).upper()
    prefix = "../" if is_nested else ""
    category_url = f"{prefix}category-{cat}.html"
    article_url = f"{prefix}{node['slug']}.html"

    tag_pills = []
    for t in (node.get("tags") or []):
        tag_pills.append(f'<a href="{prefix}tags/{t.lower()}.html" class="tag-pill">#{t}</a>')
    tags_html = f'<div class="card-tags">{"".join(tag_pills)}</div>' if tag_pills else ""

    created_at = node.get("metadata", {}).get("created_at", "2026-06-01")
    last_audited = node.get("metadata", {}).get("last_audited", created_at)

    meta_dates_html = (
        f'<div class="card-meta-dates">'
        f'  <span>Created: {created_at}</span>'
        f'  <span>&bull;</span>'
        f'  <span>Updated: {last_audited}</span>'
        f'</div>'
    )
    footer_html = f'<div class="card-footer-row">{tags_html}{meta_dates_html}</div>'

    hook = node["hook_question"]
    takeaway = node["takeaway_pill"]
    if vocabulary:
        from compiler.linker import inject_jargon_links
        hook = inject_jargon_links(hook, vocabulary)
        takeaway = inject_jargon_links(takeaway, vocabulary)

    card_html = (
        f'<div class="feed-card cat-{cat}" data-created="{created_at}" data-title="{node["title"]}" data-category="{cat}">'
        f'  <h2 class="card-title">'
        f'    <a href="{article_url}" class="card-title-link">{node["title"]}</a>'
        f'    <a href="{category_url}" class="category-tag">{category_label}</a>'
        f'  </h2>'
        f'  <blockquote class="card-teaser-text qa-takeaway-block">'
        f'    <span class="qa-question-text">{hook}</span>'
        f'    <span class="qa-answer-text"><strong>Takeaway:</strong> {takeaway}</span>'
        f'  </blockquote>'
        f'  {footer_html}'
        f'</div>'
    )
    return card_html


def _sort_merged_cards(merged: list) -> list:
    """Sorts a merged list of (date, title, html) tuples and returns the ordered HTML list.

    Applies a stable two-key sort: alphabetical by title first, then newest-date first.
    This ensures consistent tie-breaking when dates are equal.

    Args:
        merged: List of (created_at_str, title_lower_str, card_html_str) tuples.

    Returns:
        List of rendered card HTML strings in sorted order.
    """
    merged.sort(key=lambda x: x[1])
    merged.sort(key=lambda x: x[0], reverse=True)
    return [x[2] for x in merged]


def compile_category_page(
    layout_html: str,
    category_type: str,
    nodes: List[Dict[str, Any]],
    translations: Dict[str, Any],
    vocabulary: Dict[str, Any] = None,
    backlog: List[Dict[str, Any]] = None,
) -> str:
    """Compiles a filtered category index page listing all articles and backlog pipeline items sharing a given category type.

    Args:
        layout_html: Pre-populated master layout HTML.
        category_type: The category type string (e.g. 'biology', 'lifestyle', 'book').
        nodes: Complete list of all article nodes.
        translations: Translations dictionary.
        vocabulary: Optional dictionary of jargon definitions.
        backlog: Complete list of backlog items.

    Returns:
        The complete HTML string for the category page.
    """
    labels = translations.get("en", {})
    category_label = labels.get(f"category_{category_type}", category_type)

    matching_nodes = [
        n for n in nodes
        if n.get("type") == category_type
    ]
    matching_backlog = [
        item for item in (backlog or [])
        if item.get("category") == category_type
    ]

    merged = []

    # 1. Process matching article nodes
    for n in matching_nodes:
        card_html = render_article_card(n, translations, is_nested=False, vocabulary=vocabulary)
        created_at = n.get("metadata", {}).get("created_at", "2026-06-01")
        merged.append((created_at, n["title"].lower(), card_html))

    # 2. Process matching backlog items
    for item in matching_backlog:
        card_html = render_backlog_card(item, translations, is_nested=False, vocabulary=vocabulary, as_list_item=False)
        created_at = item.get("created_at", "2026-06-01")
        merged.append((created_at, item["title"].lower(), card_html))

    # Sort: alphabetical by title first, then date descending (newest first)
    rendered_cards = _sort_merged_cards(merged)
    empty_note = (
        f'<p class="page-empty-note">'
        f'No articles or pipeline proposals in <strong>{category_label}</strong> yet.</p>'
    ) if not rendered_cards else ""

    # Count parts
    count_parts = []
    count_parts.append(f'{len(matching_nodes)} article{"s" if len(matching_nodes) != 1 else ""} published')
    if len(matching_backlog):
        count_parts.append(f'{len(matching_backlog)} in the pipeline')
    count_text = " &bull; ".join(count_parts)

    page_html = (
        f'<header class="feed-intro">'
        f'  <div class="page-intro-row">'
        f'    <h1 class="page-title">{category_label}</h1>'
        f'    <div class="feed-sort-container">'
        f'      <label for="feed-sort-select">Sort by:</label>'
        f'      <select id="feed-sort-select" class="feed-sort-select">'
        f'        <option value="newest" selected>Newest First</option>'
        f'        <option value="oldest">Oldest First</option>'
        f'        <option value="alpha-asc">Alphabetical (A-Z)</option>'
        f'        <option value="alpha-desc">Alphabetical (Z-A)</option>'
        f'      </select>'
        f'    </div>'
        f'  </div>'
        f'  <p class="page-count-text">{count_text}</p>'
        f'</header>'
        f'<div class="feed-cards" id="feed-cards-container">{" ".join(rendered_cards)}{empty_note}</div>'
    )

    page_title = f"{category_label} — The Healthstream"
    html = layout_html.replace("{{title}}", page_title)
    html = html.replace("{{meta_description}}", f"Articles in the {category_label} category on The Healthstream.")
    html = html.replace("{{content}}", page_html)
    return html


def compile_feed_page(
    layout_html: str,
    nodes: List[Dict[str, Any]],
    translations: Dict[str, Any],
    vocabulary: Dict[str, Any] = None,
    backlog: List[Dict[str, Any]] = None,
) -> str:
    """Compiles the primary feed dashboard landing page (index.html).

    Args:
        layout_html: Pre-populated master layout HTML.
        nodes: List of article nodes.
        translations: Translations dictionary.
        vocabulary: Optional dictionary of jargon definitions.
        backlog: Complete list of backlog items.

    Returns:
        The complete HTML string for the feed page.
    """
    labels = translations.get("en", {})
    merged = []

    # 1. Process article nodes
    for n in nodes:
        card_html = render_article_card(n, translations, is_nested=False, vocabulary=vocabulary)
        created_at = n.get("metadata", {}).get("created_at", "2026-06-01")
        merged.append((created_at, n["title"].lower(), card_html))

    # 2. Process backlog items
    if backlog:
        for item in backlog:
            card_html = render_backlog_card(item, translations, is_nested=False, vocabulary=vocabulary, as_list_item=False)
            created_at = item.get("created_at", "2026-06-01")
            merged.append((created_at, item["title"].lower(), card_html))

    # Sort: alphabetical by title first, then date descending (newest first)
    rendered_cards = _sort_merged_cards(merged)

    intro_html = (
        f'<header class="feed-intro">'
        f'  <div class="page-intro-row">'
        f'    <h1 class="page-title">{labels.get("feed_title", "Topics")}</h1>'
        f'    <div class="feed-sort-container">'
        f'      <label for="feed-sort-select">Sort by:</label>'
        f'      <select id="feed-sort-select" class="feed-sort-select">'
        f'        <option value="newest" selected>Newest First</option>'
        f'        <option value="oldest">Oldest First</option>'
        f'        <option value="alpha-asc">Alphabetical (A-Z)</option>'
        f'        <option value="alpha-desc">Alphabetical (Z-A)</option>'
        f'      </select>'
        f'    </div>'
        f'  </div>'
        f'  <p class="feed-tagline">{labels.get("site_tagline", "Systems Biology Content Hub")}</p>'
        f'</header>'
        f'<div class="feed-cards" id="feed-cards-container">'
        f'  {" ".join(rendered_cards)}'
        f'</div>'
    )

    # Fill in slots
    html = layout_html.replace("{{title}}", f"{labels.get('site_title', 'The Healthstream')} — Systems Biology Reference")
    html = html.replace("{{meta_description}}", labels.get("site_tagline", ""))
    html = html.replace("{{content}}", intro_html)

    # Inject Organization JSON-LD Schema
    org_schema = """<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "The Healthstream",
  "url": "https://varga.github.io/thehealthstream/",
  "logo": "https://varga.github.io/thehealthstream/assets/logo_only_light.png",
  "sameAs": []
}
</script>
"""
    html = html.replace("</head>", f"{org_schema}\n</head>")
    return html


def compile_detail_page(
    layout_html: str,
    node: Dict[str, Any],
    translations: Dict[str, Any],
    nodes: List[Dict[str, Any]] = None,
) -> str:
    """Compiles a specific detailed article node page (e.g. ampk-activation.html).

    Args:
        layout_html: Pre-populated master layout HTML.
        node: The specific article node data dictionary.
        translations: Translations dictionary.
        nodes: Complete list of all article nodes for resolving directed edge titles.

    Returns:
        The complete HTML string for the article detail page.
    """
    labels = translations.get("en", {})
    
    # 1. Takeaway Unified Block (Issue 2 revised)
    takeaway_block_html = (
        f'<blockquote class="qa-takeaway-block detail-takeaway-block">'
        f'  <span class="qa-question-text">{node["hook_question"]}</span>'
        f'  <span class="qa-answer-text"><strong>Takeaway:</strong> {node["takeaway_pill"]}</span>'
        f'</blockquote>'
    )
    
    # 2. GRADE Evidence Block & Popover details
    er = node["epistemic_rating"]
    grade = er["grade"]
    rationale = er["rationale"]
    grade_lower = grade.lower()
    
    debates_html = ""
    if er.get("debate_sides"):
        debate_items = []
        for side in er["debate_sides"]:
            item = (
                f'<li>'
                f'  <strong>Position:</strong> {side["position"]}<br>'
                f'  <strong>Arguments:</strong> {side["arguments"]}'
                f'</li>'
            )
            debate_items.append(item)
        debates_html = (
            f'<div class="grade-debates">'
            f'  <h3 class="debates-title">Key Scientific Debates</h3>'
            f'  <ul class="debates-list">'
            f'    {"".join(debate_items)}'
            f'  </ul>'
            f'</div>'
        )

    debate_link_html = ""
    if er.get("debate_sides"):
        debate_link_html = f' <a href="#evidence-section" class="popover-debate-link">debates</a>'

    grade_popover_html = (
        f'<div class="detail-grade-container">'
        f'  <span class="detail-grade-label">Evidence Grade:</span>'
        f'  <button class="detail-grade-badge grade-{grade_lower}" id="grade-trigger" aria-haspopup="true" aria-expanded="false">'
        f'    {grade}'
        f'    <svg class="info-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">'
        f'      <circle cx="12" cy="12" r="10"></circle>'
        f'      <line x1="12" y1="16" x2="12" y2="12"></line>'
        f'      <line x1="12" y1="8" x2="12.01" y2="8"></line>'
        f'    </svg>'
        f'  </button>'
        f'  <div class="grade-popover-card" id="grade-popover" role="dialog" aria-label="Evidence Grade Details">'
        f'    <div class="grade-popover-header">'
        f'      <strong>Evidence Grade: {grade}</strong>'
        f'      <button class="grade-popover-close" aria-label="Close details">&times;</button>'
        f'    </div>'
        f'    <p class="grade-popover-note">'
        f'      The GRADE system is a standardized framework for rating the quality of scientific evidence from High to Very Low.{debate_link_html}'
        f'      <a href="#evidence-section" class="popover-more-link">more...</a>'
        f'    </p>'
        f'    <div class="grade-popover-links">'
        f'      <a href="vocabulary/evidence-grade.html" class="popover-glossary-link">GRADE Rating Methodology &rarr;</a>'
        f'    </div>'
        f'  </div>'
        f'</div>'
    )

    # 3. Compile markdown content for Tabbed Reading Pane
    overview_html = markdown.markdown(node["reading_modes"]["overview_3min"])
    
    deep_dive_parts = []
    for item in node["reading_modes"]["deep_dive"]:
        heading_html = f"<h3>{item['heading']}</h3>"
        body_html = markdown.markdown(item["body"])
        deep_dive_parts.append(f"<section class='deep-dive-section'>{heading_html}{body_html}</section>")
    deep_dive_html = "\n".join(deep_dive_parts)

    body_html = (
        f'<section id="overview-section" class="detail-section overview-section">'
        f'  <h2 class="detail-section-title">Circuit Overview</h2>'
        f'  <div class="article-body-text">{overview_html}</div>'
        f'</section>'
        f'<section id="deepdive-section" class="detail-section deep-dive-section">'
        f'  <h2 class="detail-section-title">Molecular Mechanisms</h2>'
        f'  <div class="article-body-text">{deep_dive_html}</div>'
        f'</section>'
    )
    
    # 4. Evidence Row-List (Tabular Middle-Ground, Responsive)
    grade_details_card = (
        f'<div class="evidence-grade-details-card grade-{grade_lower}">'
        f'  <div class="evidence-grade-details-header">'
        f'    <strong>GRADE Evidence Rating</strong>'
        f'    <span class="detail-grade-badge grade-{grade_lower}">{grade}</span>'
        f'  </div>'
        f'  <p class="evidence-grade-rationale"><strong>Rationale:</strong> {rationale}</p>'
        f'  {debates_html}'
        f'  <div class="evidence-grade-note">'
        f'    The GRADE (Grading of Recommendations, Assessment, Development, and Evaluation) system is a standardized framework for rating the quality of scientific evidence. '
        f'    Ratings scale from High to Very Low quality.'
        f'  </div>'
        f'</div>'
    )

    evidence_items = []
    for item in node.get("evidence_table", []):
        meta_parts = []
        if item.get("design"):
            meta_parts.append(item["design"])
        if item.get("sample"):
            meta_parts.append(item["sample"])
        meta_text = ", ".join(meta_parts)
        
        outcome_desc = item.get("outcome", "")

        item_html = (
            f'<div class="evidence-item">'
            f'  <div class="evidence-meta">'
            f'    <a href="{item["link"]}" target="_blank" rel="noopener" class="evidence-study-link">{item["study"]} ↗</a>'
            f'    {f"<span class=\"evidence-design\">{meta_text}</span>" if meta_text else ""}'
            f'  </div>'
            f'  <div class="evidence-outcome">{outcome_desc}</div>'
            f'</div>'
        )
        evidence_items.append(item_html)
        
    evidence_list_html = ""
    if evidence_items:
        evidence_list_html = (
            f'<div class="evidence-list">'
            f'  <h3 class="evidence-subtitle">Primary Sources &amp; Clinical Studies</h3>'
            f'  {"".join(evidence_items)}'
            f'</div>'
        )

    accordion_html = (
        f'<section class="evidence-section detail-section" id="evidence-section">'
        f'  <h2 class="evidence-title">{labels.get("evidence_accordion_title", "Evidence, Studies &amp; Debates")}</h2>'
        f'  <div class="evidence-content">'
        f'    {grade_details_card}'
        f'    {evidence_list_html}'
        f'  </div>'
        f'</section>'
    )
    
    # 5. Directed Connections Links Block (Systemic Circuit Integration)
    connections_html = ""
    if node.get("edges") and nodes:
        slug_map = {n["slug"]: {"title": n["title"], "type": n["type"]} for n in nodes}
        conn_items = []
        for edge in node["edges"]:
            target_slug = edge["target"]
            target_info = slug_map.get(target_slug)
            if target_info:
                target_title = target_info["title"]
                conn_item = (
                    f'<li>'
                    f'  <span class="connection-type">{edge["type"]}</span>'
                    f'  <a href="{target_slug}.html" class="connection-link conn-cat-{target_info["type"]}">{target_title}</a> '
                    f'  <span class="connection-mechanism">{edge["mechanism"]}</span>'
                    f'</li>'
                )
                conn_items.append(conn_item)
        if conn_items:
            connections_html = (
                f'<section class="connections-section detail-section" id="connections-section" aria-labelledby="connections-title">'
                f'  <h2 id="connections-title" class="detail-section-title">Connected Circuits</h2>'
                f'  <ul class="connections-list">'
                f'    {"".join(conn_items)}'
                f'  </ul>'
                f'</section>'
            )

    # 5.5. Giscus Comment Widget
    giscus_html = ""

    # 6. Core content presentation
    category_label = labels.get(f"category_{node['type']}", node["type"])
    tags_html = "".join([
        f'<a href="tags/{t}.html" class="tag-pill">#{t}</a>'
        for t in node.get("tags", [])
    ])
    
    # 6.5. Sticky Table of Contents (TOC)
    has_connections = bool(connections_html)
    has_evidence = bool(evidence_items)
    
    toc_links = []
    toc_links.append('<a href="#overview-section" class="toc-link active">Circuit Overview</a>')
    toc_links.append('<a href="#deepdive-section" class="toc-link">Molecular Mechanisms</a>')
    if has_connections:
        toc_links.append('<a href="#connections-section" class="toc-link">Connected Circuits</a>')
    if has_evidence:
        toc_links.append('<a href="#evidence-section" class="toc-link">Evidence &amp; Studies</a>')
        
    toc_html = f'<nav class="article-toc" aria-label="Table of Contents">{"".join(toc_links)}</nav>'
    
    meta_row_html = (
        f'<div class="detail-header-meta">'
        f'  <div class="detail-tags">{tags_html}</div>'
        f'  {grade_popover_html}'
        f'</div>'
    )
    
    full_content = (
        f'<article class="article-detail cat-{node["type"]}">'
        f'  <header class="detail-header">'
        f'    <a href="category-{node["type"]}.html" class="category-tag">{category_label}</a>'
        f'    <h1>{node["title"]}</h1>'
        f'    {meta_row_html}'
        f'  </header>'
        f'  {takeaway_block_html}'
        f'  {toc_html}'
        f'  <section class="detail-section">'
        f'    {body_html}'
        f'  </section>'
        f'  {connections_html}'
        f'  {accordion_html}'
        f'  {giscus_html}'
        f'</article>'
    )
    
    # Combine into layout
    html = layout_html.replace("{{title}}", f"{node['title']} — The Healthstream")
    html = html.replace("{{meta_description}}", node["hook_question"])
    html = html.replace("{{content}}", full_content)
    
    # Mark specific sidebar item active in layout
    html = html.replace(f'data-slug="{node["slug"]}"', f'data-slug="{node["slug"]}" class="nav-link active"')
    
    # Inject FAQPage JSON-LD Schema
    escaped_pill = node["takeaway_pill"].replace('"', '\\"')
    faq_schema = f"""<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [{{
    "@type": "Question",
    "name": "What is the core takeaway for {node['title']}?",
    "acceptedAnswer": {{
      "@type": "Answer",
      "text": "{escaped_pill}"
    }}
  }}]
}}
</script>
"""
    html = html.replace("</head>", f"{faq_schema}\n</head>")
    return html


def compile_vocabulary_page(
    layout_html: str,
    vocabulary: Dict[str, Any],
    translations: Dict[str, Any],
    nodes: List[Dict[str, Any]],
    backlog: List[Dict[str, Any]] = None,
    mentions: Dict[str, Any] = None,
) -> str:
    """Compiles the Jargon Glossary index page (vocabulary.html).

    Args:
        layout_html: Pre-populated master layout HTML.
        vocabulary: Glossary definitions dictionary.
        translations: Translations dictionary.
        nodes: Complete list of article nodes.
        backlog: Optional list of backlog items (unused; kept for signature parity).
        mentions: Optional pre-computed mentions map from build.py. If None, computed locally.

    Returns:
        The complete HTML string for the glossary page.
    """
    labels = translations.get("en", {})
    
    # Use pre-computed mentions if provided (avoids redundant O(N²) scan)
    if mentions is None:
        local_mentions: Dict[str, List[Dict[str, str]]] = {term: [] for term in vocabulary.keys()}
        for n in nodes:
            overview_text = n["reading_modes"]["overview_3min"]
            deep_dive_text = " ".join([item["body"] for item in n["reading_modes"]["deep_dive"]])
            combined_text = f"{n['title']} {n['hook_question']} {n['takeaway_pill']} {overview_text} {deep_dive_text}"
            for term in vocabulary.keys():
                pattern = re.compile(r"(?<![-\w])" + re.escape(term) + r"(?![-\w])", re.IGNORECASE)
                if pattern.search(combined_text):
                    local_mentions[term].append({"title": n["title"], "slug": f"{n['slug']}.html"})
        mentions = local_mentions

    # Group cards by alphabetical headers
    groups = {}
    for term in sorted(vocabulary.keys()):
        first_letter = term[0].upper() if term else "#"
        if not first_letter.isalpha():
            first_letter = "#"
        if first_letter not in groups:
            groups[first_letter] = []
            
        slug = slugify(term)
        
        # Truncate definition to 100 characters + ...
        definition = vocabulary[term].get("definition", "")
        short_def = definition[:100].strip() + "..." if len(definition) > 100 else definition
            
        card_html = (
            f'<div class="vocab-card" id="{slug}">'
            f'  <h3 class="vocab-title">'
            f'    <a href="vocabulary/{slug}.html" class="vocab-card-link">{term} &rarr;</a>'
            f'  </h3>'
            f'  <p class="vocab-teaser">{short_def}</p>'
            f'</div>'
        )
        groups[first_letter].append(card_html)
        
    # Generate sticky alphabetical navigation links
    nav_links = []
    for letter in sorted(groups.keys()):
        nav_links.append(f'<a href="#{letter.lower()}" class="vocab-nav-link">{letter}</a>')
    vocab_nav_html = f'<nav class="vocab-nav" aria-label="Alphabetical Index">{"".join(nav_links)}</nav>'
        
    vocab_sections = []
    for letter in sorted(groups.keys()):
        section_html = (
            f'<section class="vocab-section" id="{letter.lower()}">'
            f'  <h2 class="vocab-letter-header">{letter}</h2>'
            f'  <div class="vocab-grid">'
            f'    {"".join(groups[letter])}'
            f'  </div>'
            f'</section>'
        )
        vocab_sections.append(section_html)
        
    vocab_html = (
        f'<header class="feed-intro vocab-feed-intro">'
        f'  <h1 class="page-title">{labels.get("vocabulary_header", "Jargon Glossary Index")}</h1>'
        f'  <p>{labels.get("vocabulary_desc", "")}</p>'
        f'</header>'
        f'{vocab_nav_html}'
        f'<div class="vocab-container">'
        f'  {"".join(vocab_sections)}'
        f'</div>'
    )
    
    html = layout_html.replace("{{title}}", f"{labels.get('nav_vocabulary', 'Jargon Glossary')} — The Healthstream")
    html = html.replace("{{meta_description}}", labels.get("vocabulary_desc", ""))
    html = html.replace("{{content}}", vocab_html)
    return html


def compile_vocabulary_detail_page(
    layout_html: str,
    term: str,
    vocab_item: Dict[str, Any],
    mentions: List[Dict[str, str]],
    translations: Dict[str, Any],
) -> str:
    """Compiles a dedicated page for a single jargon term definition.

    Args:
        layout_html: Pre-populated master layout HTML (compiled with base_path='../').
        term: Canonical jargon term string.
        vocab_item: Dictionary containing 'definition'.
        mentions: List of dictionaries with 'title' and 'slug' (root level slugs).
        translations: Translations dictionary.

    Returns:
        The complete HTML string for the term detail page.
    """
    labels = translations.get("en", {})
    definition = vocab_item.get("definition", "")
    
    mentions_links = []
    for m in sorted(mentions, key=lambda x: x["title"]):
        mentions_links.append(f'<li><a href="../{m["slug"]}" class="vocab-mention-link">{m["title"]}</a></li>')
        
    mentions_html = ""
    if mentions_links:
        mentions_html = (
            f'<div class="vocab-detail-mentions">'
            f'  <h3>Mentioned in:</h3>'
            f'  <ul class="vocab-mentions-list">'
            f'    {"".join(mentions_links)}'
            f'  </ul>'
            f'</div>'
        )

    # Verification Badge
    status = vocab_item.get("verification_status", "verified_human")
    if status == "verified_agent_grounded":
        badge_html = '<span class="vocab-status-badge badge-agent">✓ Verified Agent</span>'
    else:
        badge_html = '<span class="vocab-status-badge badge-human">✓ Verified Human</span>'

    # Vulgarized Analogy Callout
    analogy = vocab_item.get("vulgarized_analogy", "")
    analogy_html = ""
    if analogy:
        analogy_html = (
            f'<div class="vocab-analogy">'
            f'  <span class="vocab-analogy-label">Systems Analogy</span>'
            f'  <p>{analogy}</p>'
            f'</div>'
        )

    citations_html = ""
    citations = vocab_item.get("citations", [])
    if citations:
        citations_links = []
        for citation in citations:
            text = citation.get("text", "")
            link = citation.get("link", "")
            quote = citation.get("defining_quote", "")
            page = citation.get("quote_page", "")
            
            cite_item = ""
            if link:
                cite_item += f'<a href="{link}" target="_blank" rel="noopener noreferrer" class="vocab-citation-link">{text}</a>'
            else:
                cite_item += f'<span class="vocab-citation-text">{text}</span>'
                
            if page:
                cite_item += f' <span class="vocab-quote-meta">({page})</span>'
                
            if quote:
                cite_item += (
                    f'<blockquote class="vocab-quote">'
                    f'  "{quote}"'
                    f'</blockquote>'
                )
                
            citations_links.append(f'<li>{cite_item}</li>')
        citations_html = (
            f'<div class="vocab-detail-citations">'
            f'  <h4>Scientific Sources & Verbatim Definitions</h4>'
            f'  <ul>'
            f'    {"".join(citations_links)}'
            f'  </ul>'
            f'</div>'
        )

    content_html = (
        f'<article class="vocab-detail-page">'
        f'  <header>'
        f'    <a href="../vocabulary.html" class="vocab-back-link">'
        f'      &larr; Back to Lexicon'
        f'    </a>'
        f'    <div class="vocab-title-row">'
        f'      <h1>{term}</h1>'
        f'      {badge_html}'
        f'    </div>'
        f'  </header>'
        f'  {analogy_html}'
        f'  <p class="vocab-definition">{definition}</p>'
        f'  {mentions_html}'
        f'  {citations_html}'
        f'</article>'
    )
    
    html = layout_html.replace("{{title}}", f"{term} — Lexicon Glossary")
    html = html.replace("{{meta_description}}", f"Definition and details for {term} on The Healthstream.")
    html = html.replace("{{content}}", content_html)
    return html


def compile_tag_page(
    layout_html: str,
    tag: str,
    nodes: List[Dict[str, Any]],
    translations: Dict[str, Any],
    backlog: List[Dict[str, Any]] = None,
    vocabulary: Dict[str, Any] = None,
    tags_registry: Dict[str, Any] = None,
) -> str:
    """Compiles a filtered tag index page listing all articles and backlog pipeline items sharing a given tag.

    Args:
        layout_html: Pre-populated master layout HTML.
        tag: The raw tag string (e.g. 'biology', 'longevity').
        nodes: Complete list of all article nodes.
        translations: Translations dictionary.
        backlog: Complete list of backlog items.
        vocabulary: Optional dictionary of jargon definitions.
        tags_registry: Optional tag registry details mapping.

    Returns:
        The complete HTML string for the tag page.
    """
    labels = translations.get("en", {})

    tag_name = tag
    tag_desc = ""
    if tags_registry and tag.lower() in tags_registry:
        reg = tags_registry[tag.lower()]
        tag_name = reg.get("name", tag)
        tag_desc = reg.get("description", "")

    desc_html = f'<p class="tag-description">{tag_desc}</p>' if tag_desc else ""

    # Filter nodes that contain this tag (case-insensitive match)
    matching = [
        n for n in nodes
        if any(t.lower() == tag.lower() for t in n.get("tags", []))
    ]
    matching_backlog = [
        item for item in (backlog or [])
        if any(t.lower() == tag.lower() for t in item.get("tags", []))
    ]

    merged = []

    # 1. Process matching article nodes
    for n in matching:
        card_html = render_article_card(n, translations, is_nested=True, vocabulary=vocabulary)
        created_at = n.get("metadata", {}).get("created_at", "2026-06-01")
        merged.append((created_at, n["title"].lower(), card_html))

    # 2. Process matching backlog items
    for item in matching_backlog:
        card_html = render_backlog_card(item, translations, is_nested=True, vocabulary=vocabulary, as_list_item=False)
        created_at = item.get("created_at", "2026-06-01")
        merged.append((created_at, item["title"].lower(), card_html))

    # Sort: alphabetical by title first, then date descending (newest first)
    rendered_cards = _sort_merged_cards(merged)

    empty_note = (
        f'<p class="page-empty-note">'
        f'No decodings or pipeline proposals tagged with <strong>#{tag_name}</strong> yet.</p>'
    ) if not rendered_cards else ""

    # Count parts
    count_parts = []
    count_parts.append(f'{len(matching)} article{"s" if len(matching) != 1 else ""} published')
    if len(matching_backlog):
        count_parts.append(f'{len(matching_backlog)} in the pipeline')
    count_text = " &bull; ".join(count_parts)

    # Sorting dropdown
    sort_dropdown_html = (
        f'<div class="feed-sort-container">'
        f'  <label for="feed-sort-select">Sort by:</label>'
        f'  <select id="feed-sort-select" class="feed-sort-select">'
        f'    <option value="newest" selected>Newest First</option>'
        f'    <option value="oldest">Oldest First</option>'
        f'    <option value="alpha-asc">Alphabetical (A-Z)</option>'
        f'    <option value="alpha-desc">Alphabetical (Z-A)</option>'
        f'  </select>'
        f'</div>'
    )

    page_html = (
        f'<header class="feed-intro tag-header">'
        f'  <div class="page-intro-row">'
        f'    <h1 class="page-title">#{tag_name}</h1>'
        f'    {sort_dropdown_html}'
        f'  </div>'
        f'  {desc_html}'
        f'  <span class="published-count page-count-text">{count_text}</span>'
        f'</header>'
        f'<div class="feed-cards" id="feed-cards-container">{" ".join(rendered_cards)}{empty_note}</div>'
    )

    page_title = f"#{tag_name} — The Healthstream"
    html = layout_html.replace("{{title}}", page_title)
    html = html.replace("{{meta_description}}", f"Articles tagged #{tag_name} on The Healthstream.")
    html = html.replace("{{content}}", page_html)
    return html


def compile_backlog_page(
    layout_html: str,
    backlog: List[Dict[str, Any]],
    translations: Dict[str, Any],
    vocabulary: Dict[str, Any] = None,
) -> str:
    """Compiles the dedicated Backlog proposals and Google Forms submission page.

    Args:
        layout_html: Pre-populated master layout HTML.
        backlog: List of proposed backlog items.
        translations: Translations dictionary.
        vocabulary: Optional dictionary of jargon definitions.

    Returns:
        The complete HTML string for the backlog page.
    """
    labels = translations.get("en", {})
    
    backlog_items = []
    for item in backlog:
        backlog_items.append(render_backlog_card(item, translations, is_nested=False, vocabulary=vocabulary, as_list_item=True))
        
    cta_html = (
        f'<div class="backlog-propose-banner">'
        f'  <div class="backlog-propose-info">'
        f'    <strong class="backlog-propose-title">Have a systems biology pathway or protocol in mind?</strong>'
        f'    <span class="backlog-propose-subtitle">Propose a topic for our scientific backlog and citation audit.</span>'
        f'  </div>'
        f'  <a href="submit-proposal.html" class="vote-btn backlog-propose-btn">Submit a Proposal &rarr;</a>'
        f'</div>'
    )
    
    content_html = (
        f'<header class="feed-intro">'
        f'  <h1 class="page-title">{labels.get("backlog_title", "Proposed Backlog")}</h1>'
        f'  <p>{labels.get("backlog_desc", "")}</p>'
        f'</header>'
        f'{cta_html}'
        f'<ul class="backlog-list">'
        f'  {"".join(backlog_items)}'
        f'</ul>'
    )
    
    html = layout_html.replace("{{title}}", f"{labels.get('nav_backlog', 'Proposed Backlog')} — The Healthstream")
    html = html.replace("{{meta_description}}", labels.get("backlog_desc", ""))
    html = html.replace("{{content}}", content_html)
    return html


def compile_static_content_page(
    layout_html: str,
    md_filepath: str,
    title_key: str,
    desc_key: str,
    translations: Dict[str, Any],
    vocabulary: Dict[str, Any] = None,
    form_type: str = "",
) -> str:
    """Compiles a static content page (like About Us or Contact Us) from Markdown.

    Args:
        layout_html: Pre-populated master layout HTML.
        md_filepath: Path to the Markdown copy file.
        title_key: Label dictionary key representing page title.
        desc_key: Label dictionary key representing page meta description.
        translations: Translations dictionary.
        vocabulary: Optional dictionary of jargon definitions.
        form_type: "contact", "proposal", or "" to embed a specific form type.

    Returns:
        The complete HTML string for the static page.
    """
    labels = translations.get("en", {})
    
    try:
        with open(md_filepath, "r", encoding="utf-8") as f:
            md_content = f.read()
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Content Markdown file missing at: {md_filepath}") from e

    compiled_body = markdown.markdown(md_content)
    if vocabulary:
        from compiler.linker import inject_jargon_links
        compiled_body = inject_jargon_links(compiled_body, vocabulary)
    
    form_html = ""
    if form_type == "contact":
        form_html = (
            f'<div class="custom-form-container">'
            f'  <form id="contact-form" class="custom-form">'
            f'    <div class="form-group">'
            f'      <label for="form-email">Email Address <span class="required">*</span></label>'
            f'      <input type="email" id="form-email" name="emailAddress" required placeholder="your.email@example.com">'
            f'    </div>'
            f'    <div class="form-group">'
            f'      <label>What is the nature of your inquiry? <span class="required">*</span></label>'
            f'      <div class="radio-group">'
            f'        <label class="radio-label">'
            f'          <input type="radio" name="entry.941828249" value="I have a correction or scientific feedback on an existing decoding." required>'
            f'          <span>I have a correction or scientific feedback on an existing decoding.</span>'
            f'        </label>'
            f'        <label class="radio-label">'
            f'          <input type="radio" name="entry.941828249" value="I would like to suggest a new research study or primary source.">'
            f'          <span>I would like to suggest a new research study or primary source.</span>'
            f'        </label>'
            f'        <label class="radio-label">'
            f'          <input type="radio" name="entry.941828249" value="I am interested in research collaboration or editorial partnership.">'
            f'          <span>I am interested in research collaboration or editorial partnership.</span>'
            f'        </label>'
            f'        <label class="radio-label other-label">'
            f'          <input type="radio" name="entry.941828249" id="inquiry-other-radio" value="__other_option__">'
            f'          <span>Other:</span>'
            f'          <input type="text" id="inquiry-other-text" name="entry.941828249.other_option_response" placeholder="Please specify...">'
            f'        </label>'
            f'      </div>'
            f'    </div>'
            f'    <div class="form-group">'
            f'      <label for="form-message">Your Message <span class="required">*</span></label>'
            f'      <span class="field-help">Please detail your feedback, suggestion, or inquiry. If suggesting a source, please include the PubMed ID, DOI, or link.</span>'
            f'      <textarea id="form-message" name="entry.1129689218" required placeholder="Type your message here..."></textarea>'
            f'    </div>'
            f'    <div class="form-group">'
            f'      <label>Who are you? (Optional)</label>'
            f'      <span class="field-help">Helps us frame our discussion.</span>'
            f'      <div class="radio-group">'
            f'        <label class="radio-label">'
            f'          <input type="radio" name="entry.885889466" value="A researcher or academic">'
            f'          <span>A researcher or academic</span>'
            f'        </label>'
            f'        <label class="radio-label">'
            f'          <input type="radio" name="entry.885889466" value="A clinician or healthcare provider">'
            f'          <span>A clinician or healthcare provider</span>'
            f'        </label>'
            f'        <label class="radio-label">'
            f'          <input type="radio" name="entry.885889466" value="An enthusiast or information seeker">'
            f'          <span>An enthusiast or information seeker</span>'
            f'        </label>'
            f'        <label class="radio-label other-label">'
            f'          <input type="radio" name="entry.885889466" id="role-other-radio" value="__other_option__">'
            f'          <span>Other:</span>'
            f'          <input type="text" id="role-other-text" name="entry.885889466.other_option_response" placeholder="Please specify...">'
            f'        </label>'
            f'      </div>'
            f'    </div>'
            f'    <button type="submit" class="submit-btn" id="contact-submit-btn">Send Inquiry</button>'
            f'    <div id="contact-form-message" class="form-message"></div>'
            f'  </form>'
            f'</div>'
        )
    elif form_type == "proposal":
        form_html = (
            f'<div class="custom-form-container">'
            f'  <form id="proposal-form" class="custom-form">'
            f'    <div class="form-group">'
            f'      <label for="form-email">Email Address <span class="required">*</span></label>'
            f'      <input type="email" id="form-email" name="emailAddress" required placeholder="your.email@example.com">'
            f'    </div>'
            f'    <div class="form-group">'
            f'      <label for="form-question">What is the core question or problem you want to explore? <span class="required">*</span></label>'
            f'      <span class="field-help">What are you trying to understand or solve? Ask it in simple, everyday language (e.g., "Why do I crash in the afternoon?").</span>'
            f'      <textarea id="form-question" name="entry.68224125" required placeholder="Describe your question or problem..."></textarea>'
            f'    </div>'
            f'    <div class="form-group">'
            f'      <label for="form-source">Where did you read or hear about this?</label>'
            f'      <span class="field-help">Paste a link (LinkedIn post, blog, YouTube, book) or describe where you saw it.</span>'
            f'      <textarea id="form-source" name="entry.1814407461" placeholder="Paste link or details here..."></textarea>'
            f'    </div>'
            f'    <div class="form-group">'
            f'      <label>What category best describes this idea? <span class="required">*</span></label>'
            f'      <div class="radio-group">'
            f'        <label class="radio-label">'
            f'          <input type="radio" name="entry.336364410" value="How the body works (Biology, organs, cellular health, metabolism)" required>'
            f'          <span>How the body works (Biology, organs, cellular health, metabolism)</span>'
            f'        </label>'
            f'        <label class="radio-label">'
            f'          <input type="radio" name="entry.336364410" value="Daily habits & routines (Sleep, exercise, nutrition, light exposure)">'
            f'          <span>Daily habits & routines (Sleep, exercise, nutrition, light exposure)</span>'
            f'        </label>'
            f'        <label class="radio-label">'
            f'          <input type="radio" name="entry.336364410" value="A source synthesis (A book, social media post, blog post, or article summary)">'
            f'          <span>A source synthesis (A book, social media post, blog post, or article summary)</span>'
            f'        </label>'
            f'        <label class="radio-label other-label">'
            f'          <input type="radio" name="entry.336364410" id="category-other-radio" value="__other_option__">'
            f'          <span>Other:</span>'
            f'          <input type="text" id="category-other-text" name="entry.336364410.other_option_response" placeholder="Please specify...">'
            f'        </label>'
            f'      </div>'
            f'    </div>'
            f'    <div class="form-group">'
            f'      <label for="form-impact">How would understanding this change your daily life?</label>'
            f'      <span class="field-help">Why does this matter to you? What habit or decision are you hoping to improve?</span>'
            f'      <textarea id="form-impact" name="entry.1526174925" placeholder="e.g. I want to know if I should stop drinking coffee after 2 PM..."></textarea>'
            f'    </div>'
            f'    <button type="submit" class="submit-btn" id="proposal-submit-btn">Submit Proposal</button>'
            f'    <div id="proposal-form-message" class="form-message"></div>'
            f'  </form>'
            f'</div>'
        )
        
    if form_html:
        content_layout = (
            f'<div class="static-prose-container">'
            f'  <div class="article-body-text">{compiled_body}</div>'
            f'  {form_html}'
            f'</div>'
        )
        page_class = "form-page"
    else:
        content_layout = (
            f'<div class="static-prose-container">'
            f'  <div class="article-body-text">{compiled_body}</div>'
            f'</div>'
        )
        page_class = "prose-page"

    page_html = (
        f'<article class="static-page {page_class}">'
        f'  <header class="static-header">'
        f'    <h1>{labels.get(title_key, "Info")}</h1>'
        f'    {f"<p class=\"static-desc\">{labels.get(desc_key)}</p>" if labels.get(desc_key) else ""}'
        f'  </header>'
        f'  {content_layout}'
        f'</article>'
    )
    
    html = layout_html.replace("{{title}}", f"{labels.get(title_key, 'Info')} — The Healthstream")
    html = html.replace("{{meta_description}}", labels.get(desc_key, ""))
    html = html.replace("{{content}}", page_html)
    return html


def copy_static_assets(output_dir: str) -> None:
    """Copies app.js, style.css, modular styles, and assets directory into output_dir.

    Args:
        output_dir: Target directory path (e.g. 'en/').
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Copy app.js
    if os.path.exists("app.js"):
        shutil.copy2("app.js", os.path.join(output_dir, "app.js"))
        
    # 2. Copy and adjust style.css
    if os.path.exists("style.css"):
        with open("style.css", "r", encoding="utf-8") as f:
            style_content = f.read()
        # Remap modular style paths for direct flat structure
        style_content = style_content.replace("./src/styles/", "./styles/")
        with open(os.path.join(output_dir, "style.css"), "w", encoding="utf-8") as f:
            f.write(style_content)
            
    # 3. Copy modular style sheet folder
    styles_dest = os.path.join(output_dir, "styles")
    if os.path.exists(styles_dest):
        shutil.rmtree(styles_dest)
        
    src_styles = os.path.join("src", "styles")
    if os.path.exists(src_styles):
        shutil.copytree(src_styles, styles_dest)
        
    # 4. Copy assets folder
    assets_dest = os.path.join(output_dir, "assets")
    if os.path.exists(assets_dest):
        shutil.rmtree(assets_dest)
        
    if os.path.exists("assets"):
        shutil.copytree("assets", assets_dest)


def generate_sitemap(
    output_dir: str,
    nodes: List[Dict[str, Any]],
    tag_slugs: List[str] | None = None,
    site_url: str = "https://varga.github.io/thehealthstream",
    vocab_slugs: List[str] | None = None,
) -> None:
    """Generates sitemap.xml in the output directory for search engine indexing.

    Args:
        output_dir: Target directory path.
        nodes: List of article nodes.
        tag_slugs: Optional list of tag slug strings (e.g. ['biology', 'longevity']).
        site_url: Base site URL.
        vocab_slugs: Optional list of vocabulary term slugs for individual term pages.
    """
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

    # Static pages
    static_pages = ["index.html", "vocabulary.html", "backlog.html", "about.html", "contact.html"]
    for page in static_pages:
        url = ET.SubElement(urlset, "url")
        loc = ET.SubElement(url, "loc")
        loc.text = f"{site_url}/{page}"

    # Category index pages
    for cat in ["biology", "lifestyle", "book"]:
        url = ET.SubElement(urlset, "url")
        loc = ET.SubElement(url, "loc")
        loc.text = f"{site_url}/category-{cat}.html"

    # Dynamic Article pages
    for n in nodes:
        url = ET.SubElement(urlset, "url")
        loc = ET.SubElement(url, "loc")
        loc.text = f"{site_url}/{n['slug']}.html"

    # Tag filter pages
    for slug in (tag_slugs or []):
        url = ET.SubElement(urlset, "url")
        loc = ET.SubElement(url, "loc")
        loc.text = f"{site_url}/tags/{slug}.html"

    # Individual vocabulary term detail pages
    for slug in (vocab_slugs or []):
        url = ET.SubElement(urlset, "url")
        loc = ET.SubElement(url, "loc")
        loc.text = f"{site_url}/vocabulary/{slug}.html"

    # Pretty format XML
    raw_xml = ET.tostring(urlset, encoding="utf-8")
    parsed_xml = minidom.parseString(raw_xml)
    pretty_xml = parsed_xml.toprettyxml(indent="  ")

    sitemap_path = os.path.join(output_dir, "sitemap.xml")
    with open(sitemap_path, "w", encoding="utf-8") as f:
        f.write(pretty_xml)


def generate_robots_txt(
    output_dir: str,
    site_url: str = "https://varga.github.io/thehealthstream",
) -> None:
    """Generates a robots.txt allowing AI search agents alongside standard bots.

    Args:
        output_dir: Target output directory path.
        site_url: Base site URL.
    """
    content = f"""User-agent: *
Allow: /

# Allow AI Search Crawlers explicitly
User-agent: ChatGPT-User
Allow: /

User-agent: GPTBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Omgilibot
Allow: /

Sitemap: {site_url}/sitemap.xml
"""
    robots_path = os.path.join(output_dir, "robots.txt")
    with open(robots_path, "w", encoding="utf-8") as f:
        f.write(content)


def generate_search_index(
    output_dir: str,
    nodes: List[Dict[str, Any]],
    vocabulary: Dict[str, Any],
    translations: Dict[str, Any],
    backlog: List[Dict[str, Any]] = None,
    mentions: Dict[str, Any] = None,
) -> None:
    """Generates a compressed search_index.json file in the output folder.

    Args:
        output_dir: Target output directory path.
        nodes: Complete list of article nodes.
        vocabulary: Glossary definitions dictionary.
        translations: Mapped UI translations dictionary.
        backlog: Optional list of proposed backlog items.
        mentions: Optional pre-computed mentions map from build.py. If None, computed locally.

    Raises:
        IOError: If writing the search index file fails.
    """
    labels = translations.get("en", {})
    index_data = []

    # 1. Map article nodes
    for n in nodes:
        category_label = labels.get(f"category_{n['type']}", n["type"])
        index_data.append({
            "title": n["title"],
            "slug": f"{n['slug']}.html",
            "type": "article",
            "category": category_label,
            "category_type": n["type"],
            "teaser": n["hook_question"],
        })

    # 2. Map glossary terms
    for term, details in vocabulary.items():
        term_slug = slugify(term)
        phrases_to_check = [term] + details.get("aliases", [])

        # Determine mention status from pre-computed map or by scanning locally
        if mentions is not None:
            term_mentions = mentions.get(term, [])
            mentioned_in_nodes = any(not m.get("in_pipeline") for m in term_mentions)
            mentioned_in_backlog = any(m.get("in_pipeline") for m in term_mentions)
        else:
            # Fallback: local O(N²) scan when called without pre-computed map
            mentioned_in_nodes = False
            for n in nodes:
                overview_text = n["reading_modes"]["overview_3min"]
                deep_dive_text = " ".join([item["body"] for item in n["reading_modes"]["deep_dive"]])
                combined_text = f"{n['title']} {n['hook_question']} {n['takeaway_pill']} {overview_text} {deep_dive_text}"
                for phrase in phrases_to_check:
                    pattern = re.compile(r"(?<![-\w])" + re.escape(phrase) + r"(?![-\w])", re.IGNORECASE)
                    if pattern.search(combined_text):
                        mentioned_in_nodes = True
                        break
                if mentioned_in_nodes:
                    break

            mentioned_in_backlog = False
            if not mentioned_in_nodes and backlog:
                for item in backlog:
                    combined_text = f"{item['title']} {item['description']}"
                    for phrase in phrases_to_check:
                        pattern = re.compile(r"(?<![-\w])" + re.escape(phrase) + r"(?![-\w])", re.IGNORECASE)
                        if pattern.search(combined_text):
                            mentioned_in_backlog = True
                            break
                    if mentioned_in_backlog:
                        break

        term_item = {
            "title": term,
            "slug": f"vocabulary/{term_slug}.html",
            "type": "glossary",
            "category": labels.get("nav_vocabulary", "Glossary"),
            "category_type": "glossary",
            "teaser": details.get("definition", ""),
        }
        if mentioned_in_backlog and not mentioned_in_nodes:
            term_item["in_pipeline"] = True
            
        index_data.append(term_item)

    index_path = os.path.join(output_dir, "search_index.json")
    try:
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
    except IOError as e:
        raise IOError(f"Failed writing search index file at {index_path}") from e

