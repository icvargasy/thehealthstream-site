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
    active_category: str = "",
    base_path: str = "./",
) -> str:
    """Pre-populates the master layout shell with UI labels and navigation structures.

    Args:
        template_content: The raw HTML content of layout.html.
        translations: Dictionary of translation key-value mappings.
        nodes: Complete list of article nodes for sidebar links.
        backlog: List of proposed backlog items.
        active_nav: 'feed', 'vocab', 'backlog', 'about', or 'contact' to highlight active links.
        active_category: 'biology', 'lifestyle', or 'book' to keep that accordion expanded.
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
    html = html.replace("{{nav_active_contact}}", "active" if active_nav == "contact" else "")

    # Set accordion states based on active_category
    categories = ["biology", "lifestyle", "book"]
    for cat in categories:
        if cat == active_category:
            html = html.replace(f"{{{{accordion_collapsed_{cat}}}}}", "")
            html = html.replace(f"{{{{accordion_expanded_{cat}}}}}", "true")
        else:
            html = html.replace(f"{{{{accordion_collapsed_{cat}}}}}", "collapsed")
            html = html.replace(f"{{{{accordion_expanded_{cat}}}}}", "false")

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
        f'    <span class="active epistemic-label {"active" if status == "consensus" else ""}">{labels.get("consensus_established", "Consensus")}</span>'
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
        bib_title = labels.get("evidence_bibliography", "References & Citations")
        bib_list_html = (
            f'<div class="bib-section-title" style="margin-top: var(--space-4); margin-bottom: var(--space-2); font-family: var(--font-body); font-weight: 700; font-size: var(--font-size-label); text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-ink-muted);">'
            f'  {bib_title}'
            f'</div>'
            f'<ul class="bib-list">{"".join(bib_items)}</ul>'
        )

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
    
    # Combine into layout
    html = layout_html.replace("{{title}}", node["title"])
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
        for term in vocabulary.keys():
            pattern = re.compile(r"(?<![\w-])" + re.escape(term) + r"(?![\w-])", re.IGNORECASE)
            if pattern.search(n["content"]):
                mentions[term].append({
                    "title": n["title"],
                    "slug": f"{n['slug']}.html"
                })
    
    cards = []
    for term in sorted(vocabulary.keys()):
        slug = slugify(term)
        
        # Build mentions HTML
        term_mentions = mentions.get(term, [])
        mentions_html = ""
        if term_mentions:
            links = []
            for m in sorted(term_mentions, key=lambda x: x["title"]):
                links.append(f'<a href="{m["slug"]}" class="vocab-mention-link">{m["title"]}</a>')
            mentions_html = (
                f'<div class="vocab-mentions" style="margin-top: var(--space-3); padding-top: var(--space-2); border-top: 1px dashed var(--border-color); font-size: 0.85rem; color: var(--text-ink-muted);">'
                f'  <span style="font-weight: 600;">Mentioned in:</span> {", ".join(links)}'
                f'</div>'
            )

        card_html = (
            f'<div class="vocab-card" id="{slug}">'
            f'  <h3 style="font-family: var(--font-body); font-weight:700; margin-top:0; color:var(--accent-synapse);">{term}</h3>'
            f'  <p style="margin-top:var(--space-1); line-height:1.5;">{vocabulary[term].get("definition", "")}</p>'
            f'  {mentions_html}'
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


def compile_backlog_page(
    layout_html: str,
    backlog: List[Dict[str, Any]],
    translations: Dict[str, Any],
) -> str:
    """Compiles the dedicated Backlog proposals and Google Forms submission page.

    Args:
        layout_html: Pre-populated master layout HTML.
        backlog: List of proposed backlog items.
        translations: Translations dictionary.

    Returns:
        The complete HTML string for the backlog page.
    """
    labels = translations.get("en", {})
    
    backlog_items = []
    for item in backlog:
        item_html = (
            f'<li class="backlog-item" data-id="{item["id"]}" style="background-color: var(--bg-surface-alt); border: 1px solid var(--border-color); padding: var(--space-3); border-radius: var(--radius-card); display: flex; flex-direction: column; gap: var(--space-2);">'
            f'  <div class="backlog-header" style="display: flex; align-items: center; justify-content: space-between;">'
            f'    <span class="backlog-title" style="font-weight: 700; font-size: 1.1rem; color: var(--text-ink);">{item["title"]}</span>'
            f'    <span class="backlog-votes" data-base-votes="{item["votes"]}" style="background-color: var(--selected-bg); color: var(--accent-synapse); border: 1px solid var(--selected-border); border-radius: var(--radius-pill); padding: 2px 10px; font-weight: 700; font-size: 0.85rem;">{item["votes"]}</span>'
            f'  </div>'
            f'  <div class="backlog-desc" style="color: var(--text-ink-muted); line-height: 1.5;">{item["description"]}</div>'
            f'  <button class="vote-btn" style="align-self: flex-start; padding: 6px 16px;">Vote</button>'
            f'</li>'
        )
        backlog_items.append(item_html)
        
    form_url = labels.get("form_backlog_url", "")
    form_title = labels.get("form_submit_theme_title", "Submit Proposal")
    
    form_html = (
        f'<section class="submit-theme-section" style="margin-top: var(--space-5); border-top: 1px solid var(--border-color); padding-top: var(--space-4);">'
        f'  <h2>{form_title}</h2>'
        f'  <p style="color: var(--text-ink-muted); margin-bottom: var(--space-3);">{labels.get("backlog_desc", "")}</p>'
        f'  <div class="form-container">'
        f'    <iframe class="form-iframe" src="{form_url}" title="{form_title}" sandbox="allow-forms allow-scripts allow-same-origin">Loading...</iframe>'
        f'  </div>'
        f'</section>'
    )
    
    content_html = (
        f'<header class="feed-intro">'
        f'  <h1>{labels.get("backlog_title", "Proposed Backlog")}</h1>'
        f'</header>'
        f'<ul class="backlog-list" style="display: flex; flex-direction: column; gap: var(--space-3); list-style: none; padding: 0;">'
        f'  {"".join(backlog_items)}'
        f'</ul>'
        f'{form_html}'
    )
    
    html = layout_html.replace("{{title}}", labels.get("nav_backlog", "Proposed Backlog"))
    html = html.replace("{{meta_description}}", labels.get("backlog_desc", ""))
    html = html.replace("{{content}}", content_html)
    return html


def compile_static_content_page(
    layout_html: str,
    md_filepath: str,
    title_key: str,
    desc_key: str,
    translations: Dict[str, Any],
    has_contact_form: bool = False,
) -> str:
    """Compiles a static content page (like About Us or Contact Us) from Markdown.

    Args:
        layout_html: Pre-populated master layout HTML.
        md_filepath: Path to the Markdown copy file.
        title_key: Label dictionary key representing page title.
        desc_key: Label dictionary key representing page meta description.
        translations: Translations dictionary.
        has_contact_form: True if a Google Form iframe embed is required.

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
    
    form_html = ""
    if has_contact_form:
        form_url = labels.get("form_contact_url", "")
        form_title = labels.get("form_submit_contact_title", "Contact Inquiry")
        form_html = (
            f'<div class="form-container" style="margin-top: var(--space-4);">'
            f'  <iframe class="form-iframe" src="{form_url}" title="{form_title}" sandbox="allow-forms allow-scripts allow-same-origin">Loading...</iframe>'
            f'</div>'
        )
        
    page_html = (
        f'<article class="static-page">'
        f'  <header class="feed-intro" style="margin-bottom: var(--space-4);">'
        f'    <h1>{labels.get(title_key, "Info")}</h1>'
        f'    {f"<p>{labels.get(desc_key)}</p>" if labels.get(desc_key) else ""}'
        f'  </header>'
        f'  <div class="article-body-text">{compiled_body}</div>'
        f'  {form_html}'
        f'</article>'
    )
    
    html = layout_html.replace("{{title}}", labels.get(title_key, "Info"))
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


def generate_sitemap(output_dir: str, nodes: List[Dict[str, Any]]) -> None:
    """Generates sitemap.xml in the output directory for search engine indexing.

    Args:
        output_dir: Target directory path.
        nodes: List of article nodes.
    """
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    
    # Static and custom pages
    static_pages = ["index.html", "vocabulary.html", "backlog.html", "about.html", "contact.html"]
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


def generate_robots_txt(output_dir: str) -> None:
    """Generates a robots.txt allowing AI search agents alongside standard bots.

    Args:
        output_dir: Target output directory path.
    """
    content = """User-agent: *
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

Sitemap: https://varga.github.io/thehealthstream/sitemap.xml
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

