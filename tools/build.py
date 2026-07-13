"""Master static compilation orchestrator for The Healthstream content registry.

This script acts as the build entry point, coordinating data reads,
jargon reference injections, HTML page generations, and asset outputs.
"""

import os
import re
import sys
from typing import Any, Dict, List
from compiler.reader import load_json_file, load_and_validate_all_nodes
from compiler.linker import inject_jargon_links, slugify
from compiler.writer import (
    compile_base_layout,
    compile_feed_page,
    compile_detail_page,
    compile_vocabulary_page,
    compile_tag_page,
    compile_category_page,
    compile_backlog_page,
    compile_static_content_page,
    copy_static_assets,
    generate_sitemap,
    generate_robots_txt,
    generate_search_index,
)


def _build_mentions_map(
    nodes: List[Dict[str, Any]],
    backlog: List[Dict[str, Any]],
    vocabulary: Dict[str, Any],
) -> Dict[str, List[Dict[str, Any]]]:
    """Builds a mapping from each vocabulary term to all articles, backlog items, and other lexicon definitions that mention it.

    This single-pass computation replaces three separate O(N²) scans that
    previously ran independently in compile_vocabulary_page, compile_vocabulary_detail_page,
    and generate_search_index.

    Args:
        nodes: Validated article node list.
        backlog: Backlog proposal list.
        vocabulary: Jargon glossary dictionary.

    Returns:
        Dict mapping term → list of mention dicts with keys 'title', 'slug', 'type',
        and optionally 'in_pipeline' (bool, True for backlog items).
    """
    mentions: Dict[str, List[Dict[str, Any]]] = {term: [] for term in vocabulary.keys()}

    for n in nodes:
        overview_text = n["reading_modes"]["overview_3min"]
        deep_dive_text = " ".join([item["body"] for item in n["reading_modes"]["deep_dive"]])
        combined_text = f"{n['title']} {n['hook_question']} {n['takeaway_pill']} {overview_text} {deep_dive_text}"
        for term, details in vocabulary.items():
            phrases_to_check = [term] + details.get("aliases", [])
            matched = any(
                re.search(r"(?<![-\w])" + re.escape(phrase) + r"(?![-\w])", combined_text, re.IGNORECASE)
                for phrase in phrases_to_check
            )
            if matched:
                mentions[term].append({
                    "title": n["title"],
                    "slug": f"{n['slug']}.html",
                    "type": n["type"]
                })

    for item in (backlog or []):
        combined_text = f"{item['title']} {item['description']}"
        for term, details in vocabulary.items():
            phrases_to_check = [term] + details.get("aliases", [])
            matched = any(
                re.search(r"(?<![-\w])" + re.escape(phrase) + r"(?![-\w])", combined_text, re.IGNORECASE)
                for phrase in phrases_to_check
            )
            if matched:
                mentions[term].append({
                    "title": item["title"],
                    "slug": f"backlog.html#{item['id']}",
                    "type": item["category"],
                    "in_pipeline": True
                })

    # Lexicon-to-lexicon mentions
    for other_term, other_details in vocabulary.items():
        combined_text = f"{other_details.get('definition', '')} {other_details.get('vulgarized_analogy', '')}"
        for term, details in vocabulary.items():
            if term == other_term:
                continue
            phrases_to_check = [term] + details.get("aliases", [])
            matched = any(
                re.search(r"(?<![-\w])" + re.escape(phrase) + r"(?![-\w])", combined_text, re.IGNORECASE)
                for phrase in phrases_to_check
            )
            if matched:
                mentions[term].append({
                    "title": other_term,
                    "slug": f"{slugify(other_term)}.html",
                    "type": "lexicon"
                })

    return mentions


def run_build() -> None:
    """Executes the site compilation sequence.

    Loads translation matrices, proposal backlogs, and jargon definitions,
    validates all biological content nodes, compiles layouts, injects glossary
    popovers, copies assets, and writes sitemaps to the target directory.

    Raises:
        FileNotFoundError: If any critical template or file is missing.
        ValueError: If file validation checks fail.
    """
    print("==================================================")
    print("   THE HEALTHSTREAM - Compiling Static Web Hub    ")
    print("==================================================\n")

    # Define paths
    src_dir = "src"
    nodes_dir = os.path.join(src_dir, "nodes", "en")
    template_path = os.path.join(src_dir, "templates", "layout.html")
    output_dir = "en"

    vocabulary_path = os.path.join(src_dir, "vocabulary.json")
    backlog_path = os.path.join(src_dir, "backlog.json")
    translations_path = os.path.join(src_dir, "translations.json")
    tags_path = os.path.join(src_dir, "tags.json")

    # 1. Load data configurations
    try:
        print("Reading translation profiles...")
        translations = load_json_file(translations_path)

        print("Reading backlog data...")
        backlog = load_json_file(backlog_path)

        print("Reading jargon vocabulary...")
        vocabulary = load_json_file(vocabulary_path)

        print("Reading tag registry...")
        tags_registry = load_json_file(tags_path)
    except FileNotFoundError as e:
        print(f"Error: Required config data file missing: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: Malformed JSON in configuration data: {e}")
        sys.exit(1)

    # 2. Ingest and validate all articles
    try:
        print("Loading and validating content nodes...")
        nodes = load_and_validate_all_nodes(nodes_dir)
        print(f"Loaded {len(nodes)} articles successfully.")
    except FileNotFoundError as e:
        print(f"Error: Source nodes directory not found: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: Node data validation failed: {e}")
        sys.exit(1)

    # 3. Read template
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()
    except FileNotFoundError:
        print(f"Error: Master layout template file missing at: {template_path}")
        sys.exit(1)

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Pre-compute the vocabulary mention graph ONCE (avoids 3× redundant O(N²) scans)
    print("Computing vocabulary mention graph...")
    mentions = _build_mentions_map(nodes, backlog, vocabulary)

    # 4. Compile index.html (Feed Page)
    print("Compiling feed page (index.html)...")
    base_layout_feed = compile_base_layout(
        template_content=template_content,
        translations=translations,
        nodes=nodes,
        backlog=backlog,
        active_nav="feed",
    )
    feed_page_html = compile_feed_page(
        layout_html=base_layout_feed,
        nodes=nodes,
        translations=translations,
        vocabulary=vocabulary,
        backlog=backlog,
    )
    with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(feed_page_html)

    # 5. Compile vocabulary.html (Glossary Page)
    print("Compiling vocabulary page (vocabulary.html)...")
    base_layout_vocab = compile_base_layout(
        template_content=template_content,
        translations=translations,
        nodes=nodes,
        backlog=backlog,
        active_nav="vocab",
    )
    vocab_page_html = compile_vocabulary_page(
        layout_html=base_layout_vocab,
        vocabulary=vocabulary,
        translations=translations,
        nodes=nodes,
        backlog=backlog,
        mentions=mentions,
    )
    with open(os.path.join(output_dir, "vocabulary.html"), "w", encoding="utf-8") as f:
        f.write(vocab_page_html)

    # 5.5 Compile individual vocabulary term detail pages
    print("Compiling individual jargon detail pages under vocabulary/...")
    vocab_dest_dir = os.path.join(output_dir, "vocabulary")
    os.makedirs(vocab_dest_dir, exist_ok=True)
    
    from compiler.writer import compile_vocabulary_detail_page

    for term, vocab_item in vocabulary.items():
        slug = slugify(term)
        base_layout_term = compile_base_layout(
            template_content=template_content,
            translations=translations,
            nodes=nodes,
            backlog=backlog,
            active_nav="vocab",
            base_path="../",
        )
        term_html = compile_vocabulary_detail_page(
            layout_html=base_layout_term,
            term=term,
            vocab_item=vocab_item,
            mentions=mentions.get(term, []),
            translations=translations,
        )
        with open(os.path.join(vocab_dest_dir, f"{slug}.html"), "w", encoding="utf-8") as f:
            f.write(term_html)

    # 5.6 Compile vocabulary taxonomy filter pages
    print("Compiling vocabulary taxonomy pages under vocabulary/...")
    from compiler.writer import compile_vocabulary_taxonomy_page

    taxonomies = {}
    for term, vocab_item in vocabulary.items():
        tax = vocab_item.get("taxonomy", "")
        if tax:
            if tax not in taxonomies:
                taxonomies[tax] = []
            taxonomies[tax].append(term)
            
    for tax_name, tax_terms in taxonomies.items():
        tax_slug = slugify(tax_name)
        base_layout_tax = compile_base_layout(
            template_content=template_content,
            translations=translations,
            nodes=nodes,
            backlog=backlog,
            active_nav="vocab",
            base_path="../",
        )
        tax_html = compile_vocabulary_taxonomy_page(
            layout_html=base_layout_tax,
            taxonomy_name=tax_name,
            terms=tax_terms,
            vocabulary=vocabulary,
            translations=translations,
        )
        with open(os.path.join(vocab_dest_dir, f"taxonomy-{tax_slug}.html"), "w", encoding="utf-8") as f:
            f.write(tax_html)

    # 6. Compile backlog.html (Backlog Proposals Page)
    print("Compiling backlog page (backlog.html)...")
    base_layout_backlog = compile_base_layout(
        template_content=template_content,
        translations=translations,
        nodes=nodes,
        backlog=backlog,
        active_nav="backlog",
    )
    backlog_page_html = compile_backlog_page(
        layout_html=base_layout_backlog,
        backlog=backlog,
        translations=translations,
        vocabulary=vocabulary,
    )
    with open(os.path.join(output_dir, "backlog.html"), "w", encoding="utf-8") as f:
        f.write(backlog_page_html)

    # 7. Compile about.html (About Us Page)
    print("Compiling about page (about.html)...")
    base_layout_about = compile_base_layout(
        template_content=template_content,
        translations=translations,
        nodes=nodes,
        backlog=backlog,
        active_nav="about",
    )
    about_md_path = os.path.join(src_dir, "nodes", "en", "about.md")
    about_page_html = compile_static_content_page(
        layout_html=base_layout_about,
        md_filepath=about_md_path,
        title_key="nav_about",
        desc_key="site_tagline",
        translations=translations,
        vocabulary=vocabulary,
        form_type="",
    )
    with open(os.path.join(output_dir, "about.html"), "w", encoding="utf-8") as f:
        f.write(about_page_html)

    # 8. Compile contact.html (Contact Us Page)
    print("Compiling contact page (contact.html)...")
    base_layout_contact = compile_base_layout(
        template_content=template_content,
        translations=translations,
        nodes=nodes,
        backlog=backlog,
        active_nav="contact",
    )
    contact_md_path = os.path.join(src_dir, "nodes", "en", "contact.md")
    contact_page_html = compile_static_content_page(
        layout_html=base_layout_contact,
        md_filepath=contact_md_path,
        title_key="nav_contact",
        desc_key="contact_desc",
        translations=translations,
        vocabulary=vocabulary,
        form_type="contact",
    )
    with open(os.path.join(output_dir, "contact.html"), "w", encoding="utf-8") as f:
        f.write(contact_page_html)

    # 8.5. Compile submit-proposal.html (Submit Proposal Page)
    print("Compiling submit proposal page (submit-proposal.html)...")
    base_layout_proposal = compile_base_layout(
        template_content=template_content,
        translations=translations,
        nodes=nodes,
        backlog=backlog,
        active_nav="submit-proposal",
    )
    proposal_md_path = os.path.join(src_dir, "nodes", "en", "submit-proposal.md")
    proposal_page_html = compile_static_content_page(
        layout_html=base_layout_proposal,
        md_filepath=proposal_md_path,
        title_key="nav_submit_proposal",
        desc_key="submit_proposal_desc",
        translations=translations,
        vocabulary=vocabulary,
        form_type="proposal",
    )
    with open(os.path.join(output_dir, "submit-proposal.html"), "w", encoding="utf-8") as f:
        f.write(proposal_page_html)

    # 8.6. Compile terms.html (Terms of Use Page)
    print("Compiling terms of use page (terms.html)...")
    base_layout_terms = compile_base_layout(
        template_content=template_content,
        translations=translations,
        nodes=nodes,
        backlog=backlog,
        active_nav="",
    )
    terms_md_path = os.path.join(src_dir, "nodes", "en", "terms.md")
    terms_page_html = compile_static_content_page(
        layout_html=base_layout_terms,
        md_filepath=terms_md_path,
        title_key="nav_terms",
        desc_key="terms_desc",
        translations=translations,
        vocabulary=vocabulary,
        form_type="",
    )
    with open(os.path.join(output_dir, "terms.html"), "w", encoding="utf-8") as f:
        f.write(terms_page_html)

    # 8.7. Compile privacy.html (Privacy Policy Page)
    print("Compiling privacy policy page (privacy.html)...")
    base_layout_privacy = compile_base_layout(
        template_content=template_content,
        translations=translations,
        nodes=nodes,
        backlog=backlog,
        active_nav="",
    )
    privacy_md_path = os.path.join(src_dir, "nodes", "en", "privacy.md")
    privacy_page_html = compile_static_content_page(
        layout_html=base_layout_privacy,
        md_filepath=privacy_md_path,
        title_key="nav_privacy",
        desc_key="privacy_desc",
        translations=translations,
        vocabulary=vocabulary,
        form_type="",
    )
    with open(os.path.join(output_dir, "privacy.html"), "w", encoding="utf-8") as f:
        f.write(privacy_page_html)

    # 9. Compile individual detail pages (with Jargon linking)
    for node in nodes:
        print(f"Linking jargon and compiling detail page: {node['slug']}.html...")
        
        node_copy = node.copy()
        node_copy["hook_question"] = inject_jargon_links(node["hook_question"], vocabulary)
        node_copy["takeaway_pill"] = inject_jargon_links(node["takeaway_pill"], vocabulary)
        
        overview_linked = inject_jargon_links(node["reading_modes"]["overview_3min"], vocabulary)
        deep_dive_linked = [
            {
                "heading": item["heading"],
                "body": inject_jargon_links(item["body"], vocabulary)
            }
            for item in node["reading_modes"]["deep_dive"]
        ]
        evidence_table_linked = [
            {
                "study": item["study"],
                "design": item.get("design", ""),
                "sample": item.get("sample", ""),
                "outcome": inject_jargon_links(item["outcome"], vocabulary),
                "link": item["link"]
            }
            for item in node.get("evidence_table", [])
        ]
        node_copy["reading_modes"] = {
            "overview_3min": overview_linked,
            "deep_dive": deep_dive_linked
        }
        node_copy["evidence_table"] = evidence_table_linked
        
        base_layout_detail = compile_base_layout(
            template_content=template_content,
            translations=translations,
            nodes=nodes,
            backlog=backlog,
            active_nav="",
        )
        detail_page_html = compile_detail_page(
            layout_html=base_layout_detail,
            node=node_copy,
            translations=translations,
            nodes=nodes,
        )
        with open(os.path.join(output_dir, f"{node['slug']}.html"), "w", encoding="utf-8") as f:
            f.write(detail_page_html)

    # 10. Compile tag filter pages
    print("Compiling tag pages (tags/*.html)...")
    tags_output_dir = os.path.join(output_dir, "tags")
    os.makedirs(tags_output_dir, exist_ok=True)

    # Collect all unique tags across all nodes and backlog items (preserve original case from first occurrence)
    seen_tags: dict = {}
    for node in nodes:
        for t in node.get("tags", []):
            key = t.lower()
            if key not in seen_tags:
                seen_tags[key] = t
    for item in (backlog or []):
        for t in item.get("tags", []):
            key = t.lower()
            if key not in seen_tags:
                seen_tags[key] = t

    for tag_slug, tag_raw in seen_tags.items():
        base_layout_tag = compile_base_layout(
            template_content=template_content,
            translations=translations,
            nodes=nodes,
            backlog=backlog,
            active_nav="",
            base_path="../",
        )
        tag_page_html = compile_tag_page(
            layout_html=base_layout_tag,
            tag=tag_raw,
            nodes=nodes,
            translations=translations,
            backlog=backlog,
            vocabulary=vocabulary,
            tags_registry=tags_registry,
        )
        tag_out_path = os.path.join(tags_output_dir, f"{tag_slug}.html")
        with open(tag_out_path, "w", encoding="utf-8") as f:
            f.write(tag_page_html)
        print(f"  Written: tags/{tag_slug}.html ({len([n for n in nodes if any(t.lower() == tag_slug for t in n.get('tags', []))])} articles)")

    # 10.5 Compile category filter pages
    print("Compiling category pages (category-*.html)...")
    categories = ["biology", "lifestyle", "book"]
    for cat in categories:
        base_layout_cat = compile_base_layout(
            template_content=template_content,
            translations=translations,
            nodes=nodes,
            backlog=backlog,
            active_nav=f"category-{cat}",
        )
        cat_page_html = compile_category_page(
            layout_html=base_layout_cat,
            category_type=cat,
            nodes=nodes,
            translations=translations,
            vocabulary=vocabulary,
            backlog=backlog,
        )
        cat_out_path = os.path.join(output_dir, f"category-{cat}.html")
        with open(cat_out_path, "w", encoding="utf-8") as f:
            f.write(cat_page_html)
        print(f"  Written: category-{cat}.html")

    # 11. Mirror CSS, Javascript, and media assets
    print("Copying script and style assets to the output folder...")
    copy_static_assets(output_dir)

    # 12. Generate SEO Sitemap (includes tag, category, and vocabulary pages)
    print("Generating sitemap.xml...")
    site_url = translations.get("en", {}).get("site_url", "https://varga.github.io/thehealthstream").rstrip("/")
    vocab_slugs = [slugify(term) for term in vocabulary.keys()]
    generate_sitemap(output_dir, nodes, list(seen_tags.keys()), site_url, vocab_slugs=vocab_slugs)
    
    # 12. Generate robots.txt
    print("Generating robots.txt...")
    generate_robots_txt(output_dir, site_url)

    # 13. Generate Search Index
    print("Generating search_index.json...")
    generate_search_index(output_dir, nodes, vocabulary, translations, backlog, mentions=mentions)

    print("\n==================================================")
    print("   [Success] Site Compiled Successfully to en/   ")
    print("==================================================")


if __name__ == "__main__":
    run_build()
