"""Compiler unit test suite for The Healthstream static site builder.

Validates article readers, Jargon auto-linking regex replacements, and page compilers.
"""

import pytest
from tools.compiler.reader import validate_node
from tools.compiler.linker import inject_jargon_links, slugify
from tools.compiler.writer import compile_base_layout, compile_feed_page, compile_detail_page


def test_validate_node_valid() -> None:
    """Confirms that a perfectly formatted node dictionary passes validation."""
    valid_node = {
        "type": "biology",
        "title": "AMPK Energy Activation",
        "hook_question": "Does constant snacking block energy?",
        "takeaway_pill": "Fasting activates AMPK for cellular clearance.",
        "epistemic_status": "consensus",
        "tags": ["biology", "metabolism"],
        "content": "This is AMPK content.",
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
        "epistemic_status": "consensus",
        "tags": ["biology"],
        "content": "Content...",
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
        "epistemic_status": "consensus",
        "tags": ["biology"],
        "content": "Content...",
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
    """Verifies layout template slot substitutions."""
    template = "<html><head><title>{{title}}</title></head><body>{{label_nav_home}} {{sidebar_links_biology}} {{content}}</body></html>"
    translations = {"en": {"nav_home": "Feed"}}
    nodes = [{"slug": "ampk-activation", "title": "AMPK Activation", "type": "biology"}]
    backlog = []

    compiled = compile_base_layout(template, translations, nodes, backlog, "feed")
    assert "<title>{{title}}</title>" in compiled  # Detail placeholder preserved for now
    assert "Feed" in compiled
    assert 'data-slug="ampk-activation"' in compiled


def test_compile_feed_page() -> None:
    """Verifies index feed card content compilation."""
    layout = "<html><body>{{title}} {{meta_description}} {{content}}</body></html>"
    nodes = [
        {
            "slug": "ampk-activation",
            "title": "AMPK Activation",
            "type": "biology",
            "hook_question": "Snacking switch?",
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
    layout = "<html><body>{{title}} {{meta_description}} {{content}}</body></html>"
    node = {
        "slug": "ampk-activation",
        "title": "AMPK Activation",
        "type": "biology",
        "hook_question": "Does constant snacking block energy?",
        "takeaway_pill": "Fasting pill",
        "epistemic_status": "consensus",
        "tags": ["metabolism"],
        "content": "Body narrative.",
        "evidence_table": [],
        "bibliography": [],
    }
    translations = {
        "en": {
            "takeaway_pill_title": "1-Min Takeaway",
            "consensus_level": "Consensus Scale",
            "consensus_established": "Established",
        }
    }

    compiled = compile_detail_page(layout, node, translations)
    assert "AMPK Activation" in compiled
    assert "Fasting pill" in compiled
    assert "Consensus Scale" in compiled
    assert "left: 80%" in compiled  # Consensus position
