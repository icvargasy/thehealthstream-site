"""Compiler unit test suite for The Healthstream static site builder.

Validates article readers, Jargon auto-linking regex replacements, and page compilers.
"""

import pytest
from tools.compiler.reader import validate_node
from tools.compiler.linker import inject_jargon_links, slugify
from tools.compiler.writer import (
    compile_base_layout,
    compile_feed_page,
    compile_detail_page,
    compile_backlog_page,
    compile_static_content_page,
    compile_tag_page,
    compile_category_page,
    generate_search_index,
)


def test_validate_node_valid() -> None:
    """Confirms that a perfectly formatted node dictionary passes validation."""
    valid_node = {
        "type": "biology",
        "title": "AMPK Energy Activation",
        "hook_question": "Does constant snacking block energy?",
        "takeaway_pill": "Fasting activates AMPK for cellular clearance.",
        "epistemic_rating": {
            "grade": "High",
            "rationale": "Consensus is supported by extensive mammalian studies.",
            "debate_sides": []
        },
        "tags": ["biology", "metabolism"],
        "reading_modes": {
            "overview_3min": "Fasting activates AMPK for cellular clearance.",
            "deep_dive": [
                {
                    "heading": "The AMPK-mTOR Reciprocal Axis",
                    "body": "At the molecular level..."
                }
            ]
        },
        "edges": [
            {
                "target": "circadian-sleep-protocol",
                "type": "requires",
                "mechanism": "Details..."
            }
        ],
        "evidence_table": [
            {
                "study": "Smith 2023",
                "design": "RCT",
                "sample": "n=10",
                "outcome": "Clearance",
                "link": "http://ncbi.nlm.nih.gov",
            }
        ],
        "bibliography": [{"id": "ref1", "text": "Smith 2023 details.", "link": "http://ncbi.nlm.nih.gov"}],
    }
    # Should run without raising any exceptions
    validate_node(valid_node, "test_file.json")


def test_validate_node_missing_fields() -> None:
    """Ensures validation fails if a required key is missing."""
    invalid_node = {
        "type": "biology",
        "title": "AMPK Activation",
        # "hook_question" is missing!
        "takeaway_pill": "Fasting activates AMPK.",
        "epistemic_rating": {
            "grade": "High",
            "rationale": "Consensus is supported.",
            "debate_sides": []
        },
        "tags": ["biology"],
        "reading_modes": {
            "overview_3min": "Fasting activates AMPK.",
            "deep_dive": []
        },
        "edges": [],
        "evidence_table": [],
        "bibliography": [],
    }
    with pytest.raises(ValueError, match="Missing required field 'hook_question'"):
        validate_node(invalid_node, "test_file.json")


def test_validate_node_invalid_types() -> None:
    """Ensures validation fails if a field contains an incorrect data type."""
    invalid_node = {
        "type": "invalid_type",  # Must be biology, lifestyle, or book
        "title": "AMPK Activation",
        "hook_question": "Snacking?",
        "takeaway_pill": "Fasting activates AMPK.",
        "epistemic_rating": {
            "grade": "High",
            "rationale": "Consensus is supported.",
            "debate_sides": []
        },
        "tags": ["biology"],
        "reading_modes": {
            "overview_3min": "Fasting activates AMPK.",
            "deep_dive": []
        },
        "edges": [],
        "evidence_table": [],
        "bibliography": [],
    }
    with pytest.raises(ValueError, match="Invalid type 'invalid_type'"):
        validate_node(invalid_node, "test_file.json")


def test_slugify() -> None:
    """Validates raw text conversion to url-safe slugs."""
    assert slugify("AMPK Activation Pathway!") == "ampk-activation-pathway"
    assert slugify("   Zone 2 Strength  ") == "zone-2-strength"


def test_inject_jargon_links() -> None:
    """Verifies that jargon words are replaced case-insensitively and tags/links are ignored."""
    vocabulary = {
        "AMPK": {"definition": "An energy sensing enzyme."},
        "metabolic flexibility": {"definition": "Ability to switch fuels."},
    }

    # Standard replacement
    text_content = "This activates AMPK and metabolic flexibility."
    linked = inject_jargon_links(text_content, vocabulary)
    assert '<span class="jargon-term" data-term="AMPK"' in linked
    assert "data-term=\"metabolic flexibility\"" in linked

    # Case insensitivity
    text_content_caps = "We study METABOLIC FLEXIBILITY."
    linked_caps = inject_jargon_links(text_content_caps, vocabulary)
    assert "data-term=\"metabolic flexibility\"" in linked_caps
    assert "METABOLIC FLEXIBILITY" in linked_caps

    # Avoid replacement inside HTML tags
    tag_content = '<img src="ampk.jpg" alt="AMPK image">'
    linked_tag = inject_jargon_links(tag_content, vocabulary)
    assert linked_tag == tag_content  # No replacement inside attributes/tags

    # Avoid replacement inside anchor links
    anchor_content = '<a href="ampk.html">Read about AMPK here</a>'
    linked_anchor = inject_jargon_links(anchor_content, vocabulary)
    assert linked_anchor == anchor_content


def test_compile_base_layout() -> None:
    """Verifies layout template slot substitutions and static feed/navigation flags."""
    template = (
        "<html><head><title>{{title}}</title></head><body>{{label_nav_home}} count:{{count_biology}} "
        "active-feed:{{nav_active_feed}} active-bio:{{nav_active_category_biology}} {{content}}</body></html>"
    )
    translations = {"en": {"nav_home": "Feed"}}
    nodes = [{"slug": "ampk-activation", "title": "AMPK Activation", "type": "biology"}]
    backlog = []

    compiled = compile_base_layout(template, translations, nodes, backlog, "category-biology")
    assert "Feed" in compiled
    assert "count:1" in compiled
    assert "active-bio:active" in compiled
    assert "active-feed:" in compiled




def test_compile_vocabulary_page() -> None:
    """Verifies vocabulary page compiles jargon glossary and builds cross-references/mentions."""
    layout = "<html><body>{{title}} {{meta_description}} {{content}}</body></html>"
    vocabulary = {
        "AMPK": {"definition": "An energy sensing enzyme."}
    }
    translations = {"en": {"nav_vocabulary": "Glossary"}}
    nodes = [
        {
            "slug": "ampk-activation",
            "title": "AMPK Activation",
            "type": "biology",
            "hook_question": "Does snacking block energy?",
            "takeaway_pill": "Fasting activates AMPK.",
            "epistemic_rating": {
                "grade": "High",
                "rationale": "Consensus is supported.",
                "debate_sides": []
            },
            "tags": [],
            "reading_modes": {
                "overview_3min": "This activates AMPK.",
                "deep_dive": []
            },
            "edges": [],
            "evidence_table": [],
            "bibliography": []
        }
    ]
    from tools.compiler.writer import compile_vocabulary_page
    compiled = compile_vocabulary_page(layout, vocabulary, translations, nodes)
    assert "Glossary" in compiled
    assert "vocabulary/ampk.html" in compiled
    assert "AMPK" in compiled

def test_compile_vocabulary_detail_page() -> None:
    """Verifies compilation of individual jargon detail page."""
    layout = "<html><body>{{title}} {{meta_description}} {{content}}</body></html>"
    term = "AMPK"
    vocab_item = {"definition": "An energy sensing enzyme."}
    mentions = [
        {"title": "AMPK Activation", "slug": "ampk-activation.html"}
    ]
    translations = {"en": {"nav_vocabulary": "Glossary"}}
    from tools.compiler.writer import compile_vocabulary_detail_page
    compiled = compile_vocabulary_detail_page(layout, term, vocab_item, mentions, translations)
    assert "AMPK" in compiled
    assert "An energy sensing enzyme" in compiled
    assert "Mentioned in:" in compiled
    assert "../ampk-activation.html" in compiled
    assert "AMPK Activation" in compiled


def test_compile_feed_page() -> None:
    """Verifies index feed card content compilation."""
    layout = "<html><body>{{title}} {{meta_description}} {{content}}</body></html>"
    nodes = [
        {
            "slug": "ampk-activation",
            "title": "AMPK Activation",
            "type": "biology",
            "hook_question": "Snacking switch?",
            "takeaway_pill": "Fasting activates AMPK.",
            "epistemic_rating": {
                "grade": "High",
                "rationale": "Consensus is supported.",
                "debate_sides": []
            },
            "tags": [],
            "reading_modes": {
                "overview_3min": "Overview text",
                "deep_dive": []
            },
            "edges": [],
            "evidence_table": [],
            "bibliography": []
        }
    ]
    translations = {"en": {"site_title": "The Healthstream", "site_tagline": "Hub", "feed_title": "Feed"}}

    compiled = compile_feed_page(layout, nodes, translations)
    assert "The Healthstream" in compiled
    assert "Hub" in compiled
    assert "Snacking switch?" in compiled
    assert 'href="ampk-activation.html"' in compiled


def test_compile_detail_page() -> None:
    """Verifies that individual detailed pages are properly compiled."""
    layout = "<html><head></head><body>{{title}} {{meta_description}} {{content}}</body></html>"
    node = {
        "slug": "ampk-activation",
        "title": "AMPK Activation",
        "type": "biology",
        "hook_question": "Does constant snacking block energy?",
        "takeaway_pill": "Fasting pill",
        "epistemic_rating": {
            "grade": "High",
            "rationale": "Consensus is supported.",
            "debate_sides": []
        },
        "tags": ["metabolism"],
        "reading_modes": {
            "overview_3min": "Body narrative.",
            "deep_dive": []
        },
        "edges": [],
        "evidence_table": [],
        "bibliography": [],
    }
    translations = {
        "en": {
            "takeaway_pill_title": "1-Min Takeaway",
            "consensus_level": "GRADE Evidence Rating",
            "consensus_established": "Established",
        }
    }

    compiled = compile_detail_page(layout, node, translations, [node])
    assert "AMPK Activation" in compiled
    assert "Fasting pill" in compiled
    assert "Evidence Grade:" in compiled
    assert "High" in compiled
    # Verify Schema.org FAQPage injection
    assert 'application/ld+json' in compiled
    assert '"@type": "FAQPage"' in compiled


def test_compile_backlog_page() -> None:
    """Verifies that the dedicated Backlog page renders backlog cards and redirect button."""
    layout = "<html><body>{{title}} {{meta_description}} {{content}}</body></html>"
    backlog = [
        {
            "id": "autophagy-kinetics",
            "title": "Autophagy Kinetics",
            "description": "Fasting trigger",
            "votes": 124,
        }
    ]
    translations = {
        "en": {
            "nav_backlog": "Backlog List",
            "backlog_title": "Proposed Backlog",
            "backlog_desc": "Vote to decide.",
        }
    }

    compiled = compile_backlog_page(layout, backlog, translations)
    assert "Backlog List" in compiled
    assert "Autophagy Kinetics" in compiled
    assert "124" in compiled
    assert "submit-proposal.html" in compiled
    assert "Submit a Proposal" in compiled


def test_compile_static_content_page(tmp_path) -> None:
    """Verifies parsing of Markdown copy files into final themed static HTML pages."""
    layout = "<html><body>{{title}} {{meta_description}} {{content}}</body></html>"
    md_file = tmp_path / "about.md"
    md_file.write_text("### Our Mission\nSystems biology feedback loop mapping.", encoding="utf-8")

    translations = {
        "en": {
            "nav_about": "About Us",
            "site_tagline": "Static biological reference hub.",
        }
    }

    compiled = compile_static_content_page(
        layout_html=layout,
        md_filepath=str(md_file),
        title_key="nav_about",
        desc_key="site_tagline",
        translations=translations,
    )
    assert "About Us" in compiled
    assert "Systems biology feedback loop mapping" in compiled
    assert "Our Mission" in compiled


def test_generate_search_index(tmp_path) -> None:
    """Verifies compilation of search_index.json payload."""
    nodes = [{
        "slug": "ampk-activation",
        "title": "AMPK Activation",
        "type": "biology",
        "hook_question": "Does snacking block energy?",
        "takeaway_pill": "Fasting activates AMPK.",
        "epistemic_rating": {
            "grade": "High",
            "rationale": "Consensus is supported.",
            "debate_sides": []
        },
        "tags": [],
        "reading_modes": {
            "overview_3min": "Overview text",
            "deep_dive": []
        },
        "edges": [],
        "evidence_table": [],
        "bibliography": []
    }]
    vocabulary = {"AMPK": {"definition": "An energy sensing enzyme."}}
    translations = {"en": {"category_biology": "Biology & Science", "nav_vocabulary": "Glossary"}}
    
    import json
    import os
    
    generate_search_index(str(tmp_path), nodes, vocabulary, translations)
    
    index_file = tmp_path / "search_index.json"
    assert os.path.exists(index_file)
    
    with open(index_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert len(data) == 2
    # Check article mapping
    assert data[0]["title"] == "AMPK Activation"
    assert data[0]["slug"] == "ampk-activation.html"
    assert data[0]["type"] == "article"
    assert data[0]["category"] == "Biology & Science"
    assert data[0]["teaser"] == "Does snacking block energy?"
    
    # Check glossary mapping
    assert data[1]["title"] == "AMPK"
    assert data[1]["slug"] == "vocabulary.html#ampk"
    assert data[1]["type"] == "glossary"
    assert data[1]["category"] == "Glossary"
    assert data[1]["teaser"] == "An energy sensing enzyme."


def test_compile_tag_page() -> None:
    """Verifies that tag filter pages render matching articles and handle empty tags."""
    from tools.compiler.writer import compile_tag_page

    layout = "<html><body>{{title}} {{meta_description}} {{content}}</body></html>"
    nodes = [
        {
            "slug": "ampk-activation",
            "title": "AMPK Activation",
            "type": "biology",
            "hook_question": "Does snacking block energy?",
            "takeaway_pill": "Fasting activates AMPK.",
            "epistemic_rating": {
                "grade": "High",
                "rationale": "Consensus is supported.",
                "debate_sides": []
            },
            "tags": ["biology", "metabolism"],
            "reading_modes": {
                "overview_3min": "Overview text",
                "deep_dive": []
            },
            "edges": [],
            "evidence_table": [],
            "bibliography": []
        },
        {
            "slug": "circadian-sleep",
            "title": "Circadian Sleep Protocol",
            "type": "lifestyle",
            "hook_question": "How does light reset the clock?",
            "takeaway_pill": "Fasting activates AMPK.",
            "epistemic_rating": {
                "grade": "High",
                "rationale": "Consensus is supported.",
                "debate_sides": []
            },
            "tags": ["lifestyle", "sleep"],
            "reading_modes": {
                "overview_3min": "Overview text",
                "deep_dive": []
            },
            "edges": [],
            "evidence_table": [],
            "bibliography": []
        },
    ]
    translations = {"en": {"category_biology": "Biology & Science", "category_lifestyle": "Lifestyle"}}

    # Tag with matching articles
    compiled = compile_tag_page(layout, "biology", nodes, translations)
    assert "#biology" in compiled
    assert "AMPK Activation" in compiled
    assert "Circadian Sleep Protocol" not in compiled
    assert 'href="../ampk-activation.html"' in compiled

    # Tag with no matching articles
    compiled_empty = compile_tag_page(layout, "longevity", nodes, translations)
    assert "No published articles tagged" in compiled_empty


def test_compile_category_page() -> None:
    """Verifies that category index streams compile correctly with type-based filtration."""
    layout = "<html><body>{{title}} {{meta_description}} {{content}}</body></html>"
    nodes = [
        {
            "slug": "ampk-activation",
            "title": "AMPK Activation",
            "type": "biology",
            "hook_question": "Does snacking block energy?",
            "takeaway_pill": "Fasting activates AMPK.",
            "epistemic_rating": {
                "grade": "High",
                "rationale": "Consensus is supported.",
                "debate_sides": []
            },
            "tags": [],
            "reading_modes": {
                "overview_3min": "Overview text",
                "deep_dive": []
            },
            "edges": [],
            "evidence_table": [],
            "bibliography": []
        },
        {
            "slug": "circadian-sleep",
            "title": "Circadian Sleep Protocol",
            "type": "lifestyle",
            "hook_question": "How does light reset the clock?",
            "takeaway_pill": "Fasting activates AMPK.",
            "epistemic_rating": {
                "grade": "High",
                "rationale": "Consensus is supported.",
                "debate_sides": []
            },
            "tags": [],
            "reading_modes": {
                "overview_3min": "Overview text",
                "deep_dive": []
            },
            "edges": [],
            "evidence_table": [],
            "bibliography": []
        },
    ]
    translations = {"en": {"category_biology": "Biological Circuits"}}

    # Biology category
    compiled = compile_category_page(layout, "biology", nodes, translations)
    assert "Biological Circuits" in compiled
    assert "AMPK Activation" in compiled
    assert "Circadian Sleep Protocol" not in compiled
    assert 'href="ampk-activation.html"' in compiled

    # Empty category
    compiled_empty = compile_category_page(layout, "book", nodes, translations)
    assert "No articles in" in compiled_empty

