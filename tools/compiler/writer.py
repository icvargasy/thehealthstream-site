"""Static HTML compiler, asset pipeline, and sitemap writer for The Healthstream.

This module processes templates and merges structured data into final HTML files
for landing feeds, detailed decodings, and the vocabulary indexes.
"""

import os
import shutil
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
        nodes: Complete list of article nodes for sidebar links.
        backlog: List of proposed backlog items for sidebar voting.
        active_nav: 'feed' or 'vocab' to assign the active tab class.
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

    # Group sidebar links by category
    bio_links = []
    life_links = []
    book_links = []

    for n in sorted(nodes, key=lambda x: x["title"]):
        link_html = (
            f'<li><a href="{base_path}{n["slug"]}.html" class="nav-link" '
            f'data-slug="{n["slug"]}">{n["title"]}</a></li>'
        )
        if n["type"] == "biology":
            bio_links.append(link_html)
        elif n["type"] == "lifestyle":
            life_links.append(link_html)
        elif n["type"] == "book":
            book_links.append(link_html)

    html = html.replace("{{sidebar_links_biology}}", "\n".join(bio_links))
    html = html.replace("{{sidebar_links_lifestyle}}", "\n".join(life_links))
    html = html.replace("{{sidebar_links_book}}", "\n".join(book_links))

    # Compile Backlog widget
    backlog_items = []
    for item in backlog:
        item_html = (
            f'<li class="backlog-item" data-id="{item["id"]}">'
            f'  <div class="backlog-header">'
            f'    <span class="backlog-title">{item["title"]}</span>'
            f'    <span class="backlog-votes" data-base-votes="{item["votes"]}">{item["votes"]}</span>'
            f'  </div>'
            f'  <div class="backlog-desc">{item["description"]}</div>'
            f'  <button class="vote-btn">Vote</button>'
            f'</li>'
        )
        backlog_items.append(item_html)

    html = html.replace("{{sidebar_backlog}}", "\n".join(backlog_items))
    return html


def compile_feed_page(
    layout_html: str,
    nodes: List[Dict[str, Any]],
    translations: Dict[str, Any],
) -> str:
    """Compiles the primary feed dashboard landing page (index.html).

    Args:
        layout_html: Pre-populated master layout HTML.
        nodes: List of article nodes.
        translations: Translations dictionary.

    Returns:
        The complete HTML string for the feed page.
    """
    labels = translations.get("en", {})
    
    # Generate chronological cards (sorted by title/slug for determinism in MVP)
    sorted_nodes = sorted(nodes, key=lambda x: x["title"])
    cards = []
    
    for n in sorted_nodes:
        # Category boundary configuration
        category_label = labels.get(f"category_{n['type']}", n["type"])
        card_html = (
            f'<a href="{n["slug"]}.html" class="feed-card cat-{n["type"]}">'
            f'  <div class="card-header">'
            f'    <span class="category-tag">{category_label}</span>'
            f'  </div>'
            f'  <h2 class="card-title">{n["title"]}</h2>'
            f'  <blockquote class="card-teaser-text">{n["hook_question"]}</blockquote>'
            f'</a>'
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
    html = layout_html.replace("{{title}}", labels.get("site_title", "The Healthstream"))
    html = html.replace("{{meta_description}}", labels.get("site_tagline", ""))
    html = html.replace("{{content}}", intro_html)
    return html


def compile_detail_page(
    layout_html: str,
    node: Dict[str, Any],
    translations: Dict[str, Any],
) -> str:
    """Compiles a specific detailed article node page (e.g. ampk-activation.html).

    Args:
        layout_html: Pre-populated master layout HTML.
        node: The specific article node data dictionary.
        translations: Translations dictionary.

    Returns:
        The complete HTML string for the article detail page.
    """
    labels = translations.get("en", {})
    
    # 1. Takeaway Pill Box
    pill_html = (
        f'<section class="pill-box" aria-labelledby="pill-title">'
        f'  <svg class="pill-icon" width="24" height="24" viewBox="0 0 24 24">'
        f'    <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"></circle>'
        f'    <line x1="12" y1="16" x2="12" y2="12" stroke="currentColor" stroke-width="2"></line>'
        f'    <line x1="12" y1="8" x2="12.01" y2="8" stroke="currentColor" stroke-width="2"></line>'
        f'  </svg>'
        f'  <div class="pill-content">'
        f'    <h2 id="pill-title" class="pill-title">{labels.get("takeaway_pill_title", "1-Min Takeaway")}</h2>'
        f'    <p class="pill-text">{node["takeaway_pill"]}</p>'
        f'  </div>'
        f'</section>'
    )
    
    # 2. Epistemic Consensus Scale
    status = node["epistemic_status"]
    pos_map = {"consensus": "80%", "developing": "50%", "high-controversy": "20%"}
    indicator_left = pos_map.get(status, "50%")
    
    consensus_html = (
        f'<section class="epistemic-section" aria-label="{labels.get("consensus_level", "Epistemic Status")}">'
        f'  <div class="epistemic-title">{labels.get("consensus_level", "Epistemic Consensus Scale")}</div>'
        f'  <div class="epistemic-bar-wrapper">'
        f'    <div class="epistemic-bar">'
        f'      <div class="epistemic-indicator" style="left: {indicator_left};" aria-hidden="true"></div>'
        f'    </div>'
        f'  </div>'
        f'  <div class="epistemic-labels">'
        f'    <span class="epistemic-label {"active" if status == "high-controversy" else ""}">{labels.get("consensus_controversial", "Controversy")}</span>'
        f'    <span class="epistemic-label {"active" if status == "developing" else ""}">{labels.get("consensus_developing", "Developing")}</span>'
        f'    <span class="epistemic-label {"active" if status == "consensus" else ""}">{labels.get("consensus_established", "Consensus")}</span>'
        f'  </div>'
        f'</section>'
    )

    # 3. Compile markdown content
    body_html = markdown.markdown(node["content"])
    
    # 4. Evidence & Data Accordion
    evidence_rows = []
    for item in node.get("evidence_table", []):
        row = (
            f'<tr>'
            f'  <td>{item["study"]}</td>'
            f'  <td>{item["design"]}</td>'
            f'  <td>{item["sample"]}</td>'
            f'  <td>{item["outcome"]}</td>'
            f'  <td><a href="{item["link"]}" target="_blank" rel="noopener">Source ↗</a></td>'
            f'</tr>'
        )
        evidence_rows.append(row)
        
    evidence_table_html = ""
    if evidence_rows:
        evidence_table_html = (
            f'<div class="table-wrapper">'
            f'  <table class="evidence-table">'
            f'    <thead>'
            f'      <tr>'
            f'        <th>{labels.get("evidence_study", "Study")}</th>'
            f'        <th>{labels.get("evidence_design", "Design")}</th>'
            f'        <th>{labels.get("evidence_sample", "Sample")}</th>'
            f'        <th>{labels.get("evidence_outcome", "Outcome")}</th>'
            f'        <th>Link</th>'
            f'      </tr>'
            f'    </thead>'
            f'    <tbody>'
            f'      {"".join(evidence_rows)}'
            f'    </tbody>'
            f'  </table>'
            f'</div>'
        )

    bib_items = []
    for bib in node.get("bibliography", []):
        li = (
            f'<li class="bib-item" id="{bib["id"]}">'
            f'  {bib["text"]} <a href="{bib["link"]}" target="_blank" rel="noopener">Link ↗</a>'
            f'</li>'
        )
        bib_items.append(li)
        
    bib_list_html = ""
    if bib_items:
        bib_list_html = f'<ul class="bib-list">{"".join(bib_items)}</ul>'

    accordion_html = (
        f'<section class="evidence-section">'
        f'  <button class="evidence-trigger" aria-expanded="false">'
        f'    <span>{labels.get("evidence_accordion_title", "Evidence & Data Accordion")}</span>'
        f'    <svg class="chevron" width="16" height="16" viewBox="0 0 24 24">'
        f'      <path d="M7 10l5 5 5-5z"></path>'
        f'    </svg>'
        f'  </button>'
        f'  <div class="evidence-content">'
        f'    {evidence_table_html}'
        f'    {bib_list_html}'
        f'  </div>'
        f'</section>'
    )
    
    # 5. Core content presentation
    category_label = labels.get(f"category_{node['type']}", node["type"])
    tags_html = "".join([f'<span class="tag-pill">#{t}</span>' for t in node.get("tags", [])])
    
    full_content = (
        f'<article class="article-detail">'
        f'  <header class="detail-header">'
        f'    <span class="category-tag" style="display:inline-block; margin-bottom:var(--space-2);">{category_label}</span>'
        f'    <h1>{node["title"]}</h1>'
        f'    <div class="detail-tags">{tags_html}</div>'
        f'  </header>'
        f'  {pill_html}'
        f'  {consensus_html}'
        f'  <div class="article-body-text">{body_html}</div>'
        f'  {accordion_html}'
        f'</article>'
    )
    
    # Combine into layout and highlight active sidebar link
    html = layout_html.replace("{{title}}", node["title"])
    html = html.replace("{{meta_description}}", node["hook_question"])
    html = html.replace("{{content}}", full_content)
    
    # Mark specific sidebar item active in layout
    html = html.replace(f'data-slug="{node["slug"]}"', f'data-slug="{node["slug"]}" class="nav-link active"')
    
    return html


def compile_vocabulary_page(
    layout_html: str,
    vocabulary: Dict[str, Any],
    translations: Dict[str, Any],
) -> str:
    """Compiles the Jargon Glossary index page (vocabulary.html).

    Args:
        layout_html: Pre-populated master layout HTML.
        vocabulary: Glossary definitions dictionary.
        translations: Translations dictionary.

    Returns:
        The complete HTML string for the glossary page.
    """
    labels = translations.get("en", {})
    
    # Build list of glossary terms sorted alphabetically
    cards = []
    for term in sorted(vocabulary.keys()):
        slug = slugify(term)
        card_html = (
            f'<div class="vocab-card" id="{slug}">'
            f'  <h3 style="font-family: var(--font-body); font-weight:700; margin-top:0; color:var(--accent-synapse);">{term}</h3>'
            f'  <p style="margin-top:var(--space-1); line-height:1.5;">{vocabulary[term].get("definition", "")}</p>'
            f'</div>'
        )
        cards.append(card_html)
        
    vocab_html = (
        f'<header class="feed-intro">'
        f'  <h1>{labels.get("vocabulary_header", "Jargon Glossary Index")}</h1>'
        f'  <p>{labels.get("vocabulary_desc", "")}</p>'
      f'</header>'
      f'<div class="vocab-grid">'
      f'  {"".join(cards)}'
      f'</div>'
    )
    
    html = layout_html.replace("{{title}}", labels.get("nav_vocabulary", "Jargon Glossary"))
    html = html.replace("{{meta_description}}", labels.get("vocabulary_desc", ""))
    html = html.replace("{{content}}", vocab_html)
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


def generate_sitemap(output_dir: str, nodes: List[Dict[str, Any]]) -> None:
    """Generates sitemap.xml in the output directory for search engine indexing.

    Args:
        output_dir: Target directory path.
        nodes: List of article nodes.
    """
    # Create XML Structure
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    
    # Standard site pages
    static_pages = ["index.html", "vocabulary.html"]
    for page in static_pages:
        url = ET.SubElement(urlset, "url")
        loc = ET.SubElement(url, "loc")
        loc.text = f"https://varga.github.io/thehealthstream/{page}"
        
    # Dynamic Article pages
    for n in nodes:
        url = ET.SubElement(urlset, "url")
        loc = ET.SubElement(url, "loc")
        loc.text = f"https://varga.github.io/thehealthstream/{n['slug']}.html"

    # Pretty format XML
    raw_xml = ET.tostring(urlset, encoding="utf-8")
    parsed_xml = minidom.parseString(raw_xml)
    pretty_xml = parsed_xml.toprettyxml(indent="  ")
    
    sitemap_path = os.path.join(output_dir, "sitemap.xml")
    with open(sitemap_path, "w", encoding="utf-8") as f:
        f.write(pretty_xml)
