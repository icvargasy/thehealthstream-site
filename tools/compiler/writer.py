"""Static HTML compiler, asset pipeline, and sitemap writer for The Healthstream.

This module processes templates and merges structured data into final HTML files
for landing feeds, detailed decodings, the vocabulary indexes, and static pages.
"""

import os
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
    html = template_content

    # Swap basic UI translation slots
    for key, value in labels.items():
        html = html.replace(f"{{{{label_{key}}}}}", str(value))

    # Set base path
    html = html.replace("{{base_path}}", base_path)

    # Set navigation active flags
    html = html.replace("{{nav_active_feed}}", "active" if active_nav == "feed" else "")
    html = html.replace("{{nav_active_vocab}}", "active" if active_nav == "vocab" else "")
    html = html.replace("{{nav_active_backlog}}", "active" if active_nav == "backlog" else "")
    html = html.replace("{{nav_active_about}}", "active" if active_nav == "about" else "")
    html = html.replace("{{nav_active_submit_proposal}}", "active" if active_nav == "submit-proposal" else "")
    html = html.replace("{{nav_active_contact}}", "active" if active_nav == "contact" else "")

    # Set category active flags
    html = html.replace("{{nav_active_category_biology}}", "active" if active_nav == "category-biology" else "")
    html = html.replace("{{nav_active_category_lifestyle}}", "active" if active_nav == "category-lifestyle" else "")
    html = html.replace("{{nav_active_category_book}}", "active" if active_nav == "category-book" else "")

    # Calculate category counts
    count_bio = sum(1 for n in nodes if n.get("type") == "biology")
    count_life = sum(1 for n in nodes if n.get("type") == "lifestyle")
    count_book = sum(1 for n in nodes if n.get("type") == "book")

    html = html.replace("{{count_biology}}", str(count_bio))
    html = html.replace("{{count_lifestyle}}", str(count_life))
    html = html.replace("{{count_book}}", str(count_book))

    return html


def compile_category_page(
    layout_html: str,
    category_type: str,
    nodes: List[Dict[str, Any]],
    translations: Dict[str, Any],
    vocabulary: Dict[str, Any] = None,
) -> str:
    """Compiles a filtered category index page listing all articles sharing a given category type.

    Args:
        layout_html: Pre-populated master layout HTML.
        category_type: The category type string (e.g. 'biology', 'lifestyle', 'book').
        nodes: Complete list of all article nodes.
        translations: Translations dictionary.
        vocabulary: Optional dictionary of jargon definitions.

    Returns:
        The complete HTML string for the category page.
    """
    labels = translations.get("en", {})
    category_label = labels.get(f"category_{category_type}", category_type)

    # Filter nodes by type
    matching = [
        n for n in nodes
        if n.get("type") == category_type
    ]

    cards = []
    for n in sorted(matching, key=lambda x: x["title"]):
        tag_pills = []
        for t in n.get("tags", []):
            tag_pills.append(f'<a href="tags/{t.lower()}.html" class="tag-pill">#{t}</a>')
        tags_html = f'<div class="card-tags">{"".join(tag_pills)}</div>' if tag_pills else ""

        hook = n["hook_question"]
        takeaway = n["takeaway_pill"]
        if vocabulary:
            from compiler.linker import inject_jargon_links
            hook = inject_jargon_links(hook, vocabulary)
            takeaway = inject_jargon_links(takeaway, vocabulary)

        card_html = (
            f'<div class="feed-card cat-{n["type"]}">'
            f'  <div class="card-header">'
            f'    <span class="category-tag">{category_label}</span>'
            f'  </div>'
            f'  <h2 class="card-title">'
            f'    <a href="{n["slug"]}.html" class="card-title-link">{n["title"]}</a>'
            f'  </h2>'
            f'  <blockquote class="card-teaser-text qa-takeaway-block">'
            f'    <span class="qa-question-text">{hook}</span>'
            f'    <span class="qa-answer-text"><strong>Takeaway:</strong> {takeaway}</span>'
            f'  </blockquote>'
            f'  {tags_html}'
            f'</div>'
        )
        cards.append(card_html)

    empty_note = (
        f'<p style="color: var(--text-ink-muted); margin-top: var(--space-4);">'
        f'No articles in <strong>{category_label}</strong> yet.</p>'
    ) if not cards else ""

    page_html = (
        f'<header class="feed-intro">'
        f'  <h1>{category_label}</h1>'
        f'  <p>{len(matching)} article{"s" if len(matching) != 1 else ""} published</p>'
        f'</header>'
        f'<div class="feed-cards">{"".join(cards)}{empty_note}</div>'
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
) -> str:
    """Compiles the primary feed dashboard landing page (index.html).

    Args:
        layout_html: Pre-populated master layout HTML.
        nodes: List of article nodes.
        translations: Translations dictionary.
        vocabulary: Optional dictionary of jargon definitions.

    Returns:
        The complete HTML string for the feed page.
    """
    labels = translations.get("en", {})
    
    # Generate chronological cards (sorted by title/slug for determinism in MVP)
    sorted_nodes = sorted(nodes, key=lambda x: x["title"])
    cards = []
    
    for n in sorted_nodes:
        category_label = labels.get(f"category_{n['type']}", n["type"])
        tag_pills = []
        for t in n.get("tags", []):
            tag_pills.append(f'<a href="tags/{t.lower()}.html" class="tag-pill">#{t}</a>')
        tags_html = f'<div class="card-tags">{"".join(tag_pills)}</div>' if tag_pills else ""

        hook = n["hook_question"]
        takeaway = n["takeaway_pill"]
        if vocabulary:
            from compiler.linker import inject_jargon_links
            hook = inject_jargon_links(hook, vocabulary)
            takeaway = inject_jargon_links(takeaway, vocabulary)

        card_html = (
            f'<div class="feed-card cat-{n["type"]}">'
            f'  <div class="card-header">'
            f'    <span class="category-tag">{category_label}</span>'
            f'  </div>'
            f'  <h2 class="card-title">'
            f'    <a href="{n["slug"]}.html" class="card-title-link">{n["title"]}</a>'
            f'  </h2>'
            f'  <blockquote class="card-teaser-text qa-takeaway-block">'
            f'    <span class="qa-question-text">{hook}</span>'
            f'    <span class="qa-answer-text"><strong>Takeaway:</strong> {takeaway}</span>'
            f'  </blockquote>'
            f'  {tags_html}'
            f'</div>'
        )
        cards.append(card_html)
        
    intro_html = (
        f'<header class="feed-intro">'
        f'  <h1>{labels.get("feed_title", "Chronological Stream")}</h1>'
        f'  <p>{labels.get("site_tagline", "Systems Biology Content Hub")}</p>'
        f'</header>'
        f'<div class="feed-cards">'
        f'  {"".join(cards)}'
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
    
    # 2. GRADE Evidence Block (Replacing compact inline strip)
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
            f'  <span class="debates-title">Key Scientific Debates</span>'
            f'  <ul class="debates-list">'
            f'    {"".join(debate_items)}'
            f'  </ul>'
            f'</div>'
        )

    grade_popover_html = (
        f'<div class="detail-grade-container">'
        f'  <span class="detail-grade-label">Evidence Grade:</span>'
        f'  <button class="detail-grade-badge grade-{grade_lower}" id="grade-trigger" aria-haspopup="true" aria-expanded="false">'
        f'    {grade}'
        f'    <svg class="info-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="margin-left: 3px; vertical-align: middle;">'
        f'      <circle cx="12" cy="12" r="10"></circle>'
        f'      <line x1="12" y1="16" x2="12" y2="12"></line>'
        f'      <line x1="12" y1="8" x2="12.01" y2="8"></line>'
        f'    </svg>'
        f'  </button>'
        f'  <div class="grade-popover-card" id="grade-popover" role="dialog" aria-label="Evidence Grade Details">'
        f'    <div class="grade-popover-header" style="display:flex; align-items:center; justify-content:space-between; border-bottom: 1px solid var(--border-color); padding-bottom:var(--space-1); margin-bottom:var(--space-2);">'
        f'      <strong style="color:var(--text-ink);">Evidence Grade: {grade}</strong>'
        f'      <button class="grade-popover-close" aria-label="Close details" style="background:none; border:none; color:var(--text-ink-muted); font-size:1.2rem; cursor:pointer; padding:0; line-height:1;">&times;</button>'
        f'    </div>'
        f'    <p class="grade-popover-rationale" style="margin:0 0 var(--space-2) 0;"><strong>Rationale:</strong> {rationale}</p>'
        f'    {debates_html}'
        f'    <div class="grade-popover-note" style="font-size:0.75rem; color:var(--text-ink-muted); border-top:1px dashed var(--border-color); padding-top:var(--space-2); margin-top:var(--space-2);">'
        f'      The GRADE (Grading of Recommendations, Assessment, Development, and Evaluation) system is a standardized framework for rating the quality of scientific evidence. '
        f'      Ratings scale from High to Very Low quality.'
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
            f'  {"".join(evidence_items)}'
            f'</div>'
        )

    accordion_html = ""
    if evidence_list_html:
        accordion_html = (
            f'<section class="evidence-section detail-section" id="evidence-section">'
            f'  <h2 class="evidence-title">{labels.get("evidence_accordion_title", "Evidence & Studies")}</h2>'
            f'  <div class="evidence-content">'
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
                    f'  <a href="{target_slug}.html" class="connection-link">{target_title}</a> '
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

    # 5.5. Giscus Comment Widget (Disabled globally)
    giscus_html = ""
    giscus_repo = None
    giscus_repo_id = ""
    giscus_category = ""
    giscus_category_id = ""

    if giscus_repo:
        giscus_html = (
            f'<section class="comments-section detail-section" id="comments-section" style="margin-top: var(--space-8); border-top: 1px solid var(--border-color); padding-top: var(--space-6);">'
            f'  <h2 class="comments-header" style="font-family: var(--font-heading); font-size: var(--font-size-h2); margin-bottom: var(--space-4);">Discussions</h2>'
            f'  <script src="https://giscus.app/client.js"'
            f'          data-repo="{giscus_repo}"'
            f'          data-repo-id="{giscus_repo_id}"'
            f'          data-category="{giscus_category}"'
            f'          data-category-id="{giscus_category_id}"'
            f'          data-mapping="pathname"'
            f'          data-strict="0"'
            f'          data-reactions-enabled="1"'
            f'          data-emit-metadata="0"'
            f'          data-input-position="bottom"'
            f'          data-theme="preferred_color_scheme"'
            f'          data-lang="en"'
            f'          crossorigin="anonymous"'
            f'          async>'
            f'  </script>'
            f'</section>'
        )

    # 6. Core content presentation
    category_label = labels.get(f"category_{node['type']}", node["type"])
    tags_html = "".join([
        f'<a href="tags/{t}.html" class="tag-pill">#{t}</a>'
        for t in node.get("tags", [])
    ])
    
    # 6.5. Sticky Table of Contents (TOC)
    has_connections = bool(connections_html)
    has_evidence = bool(evidence_items)
    has_discussions = False
    
    toc_links = []
    toc_links.append('<a href="#overview-section" class="toc-link active">Circuit Overview</a>')
    toc_links.append('<a href="#deepdive-section" class="toc-link">Molecular Mechanisms</a>')
    if has_connections:
        toc_links.append('<a href="#connections-section" class="toc-link">Connected Circuits</a>')
    if has_evidence:
        toc_links.append('<a href="#evidence-section" class="toc-link">Evidence &amp; Studies</a>')
        
    toc_html = f'<nav class="article-toc" aria-label="Table of Contents">{"".join(toc_links)}</nav>'
    
    meta_row_html = (
        f'<div class="detail-header-meta" style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:var(--space-2); margin-top:var(--space-2);">'
        f'  <div class="detail-tags" style="margin-top:0;">{tags_html}</div>'
        f'  {grade_popover_html}'
        f'</div>'
    )
    
    full_content = (
        f'<article class="article-detail cat-{node["type"]}">'
        f'  <header class="detail-header">'
        f'    <span class="category-tag" style="display:inline-block; margin-bottom:var(--space-2);">{category_label}</span>'
        f'    <h1>{node["title"]}</h1>'
        f'    {meta_row_html}'
        f'  </header>'
        f'  {takeaway_block_html}'
        f'  {toc_html}'
        f'  <section id="reading-pane-tab" class="detail-section">'
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
    
    # Inject FAQPage JSON-LD Schema (SEO/GEO Optimization)
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
) -> str:
    """Compiles the Jargon Glossary index page (vocabulary.html).

    Args:
        layout_html: Pre-populated master layout HTML.
        vocabulary: Glossary definitions dictionary.
        translations: Translations dictionary.
        nodes: Complete list of article nodes.

    Returns:
        The complete HTML string for the glossary page.
    """
    import re
    labels = translations.get("en", {})
    
    # Calculate mentions map
    mentions: Dict[str, List[Dict[str, str]]] = {term: [] for term in vocabulary.keys()}
    for n in nodes:
        overview_text = n["reading_modes"]["overview_3min"]
        deep_dive_text = " ".join([item["body"] for item in n["reading_modes"]["deep_dive"]])
        combined_text = f"{n['title']} {n['hook_question']} {n['takeaway_pill']} {overview_text} {deep_dive_text}"
        
        for term in vocabulary.keys():
            pattern = re.compile(r"(?<![\w-])" + re.escape(term) + r"(?![\w-])", re.IGNORECASE)
            if pattern.search(combined_text):
                mentions[term].append({
                    "title": n["title"],
                    "slug": f"{n['slug']}.html"
                })
    
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
        if len(definition) > 100:
            short_def = definition[:100].strip() + "..."
        else:
            short_def = definition
            
        card_html = (
            f'<div class="vocab-card" id="{slug}">'
            f'  <h3 class="vocab-title" style="font-family: var(--font-body); font-weight:700; margin:0; font-size: 1.1rem;">'
            f'    <a href="vocabulary/{slug}.html" class="vocab-card-link">{term} &rarr;</a>'
            f'  </h3>'
            f'  <p class="vocab-teaser" style="margin-top:var(--space-1); margin-bottom:0; font-size:0.9rem; line-height:1.45; color:var(--text-ink-muted);">{short_def}</p>'
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
        f'  <h1>{labels.get("vocabulary_header", "Jargon Glossary Index")}</h1>'
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
        mentions_links.append(f'<li style="margin-bottom:var(--space-1);"><a href="../{m["slug"]}" class="vocab-mention-link" style="font-weight:600; color:var(--accent-synapse); text-decoration:none;">{m["title"]}</a></li>')
        
    mentions_html = ""
    if mentions_links:
        mentions_html = (
            f'<div class="vocab-detail-mentions" style="margin-top: var(--space-5); padding-top: var(--space-4); border-top: 1px dashed var(--border-color);">'
            f'  <h3 style="font-family: var(--font-body); font-size: var(--font-size-label); text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-ink-muted); margin-bottom: var(--space-2);">Mentioned in:</h3>'
            f'  <ul class="vocab-mentions-list" style="padding-left: var(--space-3); line-height: 1.6; list-style-type: square; color: var(--text-ink-muted);">'
            f'    {"".join(mentions_links)}'
            f'  </ul>'
            f'</div>'
        )

    content_html = (
        f'<article class="vocab-detail-page" style="padding: var(--space-2) 0;">'
        f'  <header style="margin-bottom: var(--space-4);">'
        f'    <a href="../vocabulary.html" class="vocab-back-link" style="font-size: 0.85rem; font-weight: 600; display: inline-flex; align-items: center; gap: 4px; color: var(--accent-synapse); margin-bottom: var(--space-3); text-decoration: none;">'
        f'      &larr; Back to Lexicon'
        f'    </a>'
        f'    <h1 style="font-family: var(--font-display); font-size: var(--font-size-h1); font-weight: 800; margin: 0; color: var(--text-ink);">{term}</h1>'
        f'  </header>'
        f'  <p style="font-size: 1.1rem; line-height: 1.65; color: var(--text-ink); max-width: 68ch; margin-top: var(--space-3);">{definition}</p>'
        f'  {mentions_html}'
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
) -> str:
    """Compiles a filtered tag index page listing all articles and backlog pipeline items sharing a given tag.

    Args:
        layout_html: Pre-populated master layout HTML.
        tag: The raw tag string (e.g. 'biology', 'longevity').
        nodes: Complete list of all article nodes.
        translations: Translations dictionary.
        backlog: Complete list of backlog items.
        vocabulary: Optional dictionary of jargon definitions.

    Returns:
        The complete HTML string for the tag page.
    """
    labels = translations.get("en", {})

    # Filter nodes that contain this tag (case-insensitive match)
    matching = [
        n for n in nodes
        if any(t.lower() == tag.lower() for t in n.get("tags", []))
    ]

    cards = []
    for n in sorted(matching, key=lambda x: x["title"]):
        category_label = labels.get(f"category_{n['type']}", n["type"])
        tag_pills = []
        for t in n.get("tags", []):
            tag_pills.append(f'<a href="{t.lower()}.html" class="tag-pill">#{t}</a>')
        tags_html = f'<div class="card-tags">{"".join(tag_pills)}</div>' if tag_pills else ""

        hook = n["hook_question"]
        takeaway = n["takeaway_pill"]
        if vocabulary:
            from compiler.linker import inject_jargon_links
            hook = inject_jargon_links(hook, vocabulary)
            takeaway = inject_jargon_links(takeaway, vocabulary)

        card_html = (
            f'<div class="feed-card cat-{n["type"]}">'
            f'  <div class="card-header">'
            f'    <span class="category-tag">{category_label}</span>'
            f'  </div>'
            f'  <h2 class="card-title">'
            f'    <a href="../{n["slug"]}.html" class="card-title-link">{n["title"]}</a>'
            f'  </h2>'
            f'  <blockquote class="card-teaser-text qa-takeaway-block">'
            f'    <span class="qa-question-text">{hook}</span>'
            f'    <span class="qa-answer-text"><strong>Takeaway:</strong> {takeaway}</span>'
            f'  </blockquote>'
            f'  {tags_html}'
            f'</div>'
        )
        cards.append(card_html)

    # Filter backlog items that contain this tag (case-insensitive match)
    matching_backlog = [
        item for item in (backlog or [])
        if any(t.lower() == tag.lower() for t in item.get("tags", []))
    ]

    backlog_cards = []
    for item in sorted(matching_backlog, key=lambda x: x["title"]):
        category_class = f'cat-{item.get("category", "")}' if item.get("category") else ""
        
        tag_pills = []
        for t in item.get("tags", []):
            tag_pills.append(f'<a href="{t.lower()}.html" class="tag-pill">#{t}</a>')
        tags_html = f'<div class="card-tags">{"".join(tag_pills)}</div>' if tag_pills else ""

        desc = item["description"]
        if vocabulary:
            from compiler.linker import inject_jargon_links
            desc = inject_jargon_links(desc, vocabulary)

        card_html = (
            f'<div class="backlog-item backlog-card-compact {category_class}" data-id="{item["id"]}" data-title="{item["title"]}" data-category="{item.get("category", "")}">'
            f'  <div class="backlog-header">'
            f'    <div style="display: flex; align-items: center; gap: var(--space-2); flex-wrap: wrap;">'
            f'      <span class="backlog-title">{item["title"]}</span>'
            f'      <span class="pipeline-badge">In Pipeline</span>'
            f'    </div>'
            f'    <span class="backlog-votes" data-base-votes="{item["votes"]}">{item["votes"]}</span>'
            f'  </div>'
            f'  <div class="backlog-desc">{desc}</div>'
            f'  {tags_html}'
            f'  <button class="vote-btn">Vote</button>'
            f'</div>'
        )
        backlog_cards.append(card_html)

    empty_note = (
        f'<p style="color: var(--text-ink-muted); margin-top: var(--space-4);">'
        f'No published articles tagged with <strong>#{tag}</strong> yet.</p>'
    ) if not cards else ""

    pipeline_html = ""
    if backlog_cards:
        pipeline_html = (
            f'<section id="pipeline-section" class="detail-section pipeline-section">'
            f'  <h2 class="detail-section-title">In the Pipeline</h2>'
            f'  <div class="backlog-list" style="display: flex; flex-direction: column; gap: var(--space-3); list-style: none; padding: 0;">'
            f'    {"".join(backlog_cards)}'
            f'  </div>'
            f'</section>'
        )

    toc_html = ""
    if cards and backlog_cards:
        toc_html = (
            f'<nav class="article-toc" aria-label="Table of Contents">'
            f'  <a href="#published-section" class="toc-link active">Published Articles</a>'
            f'  <a href="#pipeline-section" class="toc-link">In the Pipeline</a>'
            f'</nav>'
        )

    page_html = (
        f'<header class="feed-intro tag-header">'
        f'  <h1>#{tag}</h1>'
        f'  <span class="published-count">{len(matching)} article{"s" if len(matching) != 1 else ""} published</span>'
        f'</header>'
        f'{toc_html}'
        f'<section id="published-section" class="detail-section">'
        f'  <h2 class="detail-section-title">Published Articles</h2>'
        f'  <div class="feed-cards">{"".join(cards)}{empty_note}</div>'
        f'</section>'
        f'{pipeline_html}'
    )

    page_title = f"#{tag} — The Healthstream"
    html = layout_html.replace("{{title}}", page_title)
    html = html.replace("{{meta_description}}", f"Articles tagged #{tag} on The Healthstream.")
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
        category_class = f'cat-{item.get("category", "")}' if item.get("category") else ""
        tag_pills = []
        for t in item.get("tags", []):
            tag_pills.append(f'<a href="tags/{t.lower()}.html" class="tag-pill">#{t}</a>')
        tags_html = f'<div class="card-tags" style="margin-top: var(--space-2);">{"".join(tag_pills)}</div>' if tag_pills else ""

        desc = item["description"]
        if vocabulary:
            from compiler.linker import inject_jargon_links
            desc = inject_jargon_links(desc, vocabulary)

        item_html = (
            f'<li class="backlog-item {category_class}" data-id="{item["id"]}" data-title="{item["title"]}" data-category="{item.get("category", "")}">'
            f'  <div class="backlog-header">'
            f'    <span class="backlog-title">{item["title"]}</span>'
            f'    <span class="backlog-votes" data-base-votes="{item["votes"]}">{item["votes"]}</span>'
            f'  </div>'
            f'  <div class="backlog-desc">{desc}</div>'
            f'  {tags_html}'
            f'  <button class="vote-btn">Vote</button>'
            f'</li>'
        )
        backlog_items.append(item_html)
        
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
        f'  <h1>{labels.get("backlog_title", "Proposed Backlog")}</h1>'
        f'  <p>{labels.get("backlog_desc", "")}</p>'
        f'</header>'
        f'{cta_html}'
        f'<ul class="backlog-list" style="display: flex; flex-direction: column; gap: var(--space-3); list-style: none; padding: 0;">'
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
            f'    <div id="contact-form-message" class="form-message" style="display: none;"></div>'
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
            f'    <div id="proposal-form-message" class="form-message" style="display: none;"></div>'
            f'  </form>'
            f'</div>'
        )
        
    if form_html:
        content_layout = (
            f'<div class="static-prose-container">'
            f'  <div class="article-body-text" style="margin-bottom: var(--space-4);">{compiled_body}</div>'
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
) -> None:
    """Generates sitemap.xml in the output directory for search engine indexing.

    Args:
        output_dir: Target directory path.
        nodes: List of article nodes.
        tag_slugs: Optional list of tag slug strings (e.g. ['biology', 'longevity']).
        site_url: Base site URL.
    """
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

    # Static and custom pages
    static_pages = ["index.html", "vocabulary.html", "backlog.html", "about.html", "contact.html"]
    for page in static_pages:
        url = ET.SubElement(urlset, "url")
        loc = ET.SubElement(url, "loc")
        loc.text = f"{site_url}/{page}"

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
) -> None:
    """Generates a compressed search_index.json file in the output folder.

    Args:
        output_dir: Target output directory path.
        nodes: Complete list of article nodes.
        vocabulary: Glossary definitions dictionary.
        translations: Mapped UI translations dictionary.

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
            "teaser": n["hook_question"],
        })

    # 2. Map glossary terms
    for term, details in vocabulary.items():
        index_data.append({
            "title": term,
            "slug": f"vocabulary.html#{slugify(term)}",
            "type": "glossary",
            "category": labels.get("nav_vocabulary", "Glossary"),
            "teaser": details.get("definition", ""),
        })

    index_path = os.path.join(output_dir, "search_index.json")
    try:
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
    except IOError as e:
        raise IOError(f"Failed writing search index file at {index_path}") from e

