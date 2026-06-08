"""Master static compilation orchestrator for The Healthstream content registry.

This script acts as the build entry point, coordinating data reads,
jargon reference injections, HTML page generations, and asset outputs.
"""

import os
import sys
from compiler.reader import load_json_file, load_and_validate_all_nodes
from compiler.linker import inject_jargon_links
from compiler.writer import (
    compile_base_layout,
    compile_feed_page,
    compile_detail_page,
    compile_vocabulary_page,
    compile_backlog_page,
    compile_static_content_page,
    copy_static_assets,
    generate_sitemap,
    generate_robots_txt,
)


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

    # 1. Load data configurations
    try:
        print("Reading translation profiles...")
        translations = load_json_file(translations_path)

        print("Reading backlog data...")
        backlog = load_json_file(backlog_path)

        print("Reading jargon vocabulary...")
        vocabulary = load_json_file(vocabulary_path)
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
    )
    with open(os.path.join(output_dir, "vocabulary.html"), "w", encoding="utf-8") as f:
        f.write(vocab_page_html)

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
        has_contact_form=False,
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
        has_contact_form=True,
    )
    with open(os.path.join(output_dir, "contact.html"), "w", encoding="utf-8") as f:
        f.write(contact_page_html)

    # 9. Compile individual detail pages (with Jargon linking)
    for node in nodes:
        print(f"Linking jargon and compiling detail page: {node['slug']}.html...")
        linked_content = inject_jargon_links(node["content"], vocabulary)
        
        node_copy = node.copy()
        node_copy["content"] = linked_content
        
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
        )
        with open(os.path.join(output_dir, f"{node['slug']}.html"), "w", encoding="utf-8") as f:
            f.write(detail_page_html)

    # 10. Mirror CSS, Javascript, and media assets
    print("Copying script and style assets to the output folder...")
    copy_static_assets(output_dir)

    # 11. Generate SEO Sitemap
    print("Generating sitemap.xml...")
    generate_sitemap(output_dir, nodes)

    # 12. Generate robots.txt
    print("Generating robots.txt...")
    generate_robots_txt(output_dir)

    print("\n==================================================")
    print("   [Success] Site Compiled Successfully to en/   ")
    print("==================================================")


if __name__ == "__main__":
    run_build()
