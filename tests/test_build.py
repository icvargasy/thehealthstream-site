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
        "<html><head><title>{{title}}</title></head><body>{{label_nav_home}} count:{{count_biology_total}} "
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
        "AMPK": {"definition": "An energy sensing enzyme."},
        "SIRT1": {"definition": "A sirtuin enzyme."}
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
    backlog = [
        {
            "id": "ampk-booster-protocol",
            "title": "AMPK Booster Protocol",
            "description": "How does AMPK get boosted?",
            "category": "lifestyle",
            "votes": 5,
        },
        {
            "id": "sirt1-activators",
            "title": "SIRT1 Activators",
            "description": "How does SIRT1 get boosted?",
            "category": "lifestyle",
            "votes": 3,
        }
    ]
    from tools.compiler.writer import compile_vocabulary_page
    compiled = compile_vocabulary_page(layout, vocabulary, translations, nodes, backlog)
    assert "Glossary" in compiled
    assert "vocabulary/ampk.html" in compiled
    assert "AMPK" in compiled
    assert "Mentioned in:" not in compiled
    assert "ampk-activation.html" not in compiled
    assert "backlog.html#ampk-booster-protocol" not in compiled
    assert "In Pipeline" not in compiled

def test_generate_search_index_in_pipeline(tmp_path) -> None:
    """Verifies that glossary terms only in backlog receive in_pipeline: true in search index."""
    vocabulary = {
        "AMPK": {"definition": "An energy sensing enzyme."},
        "EGCG": {"definition": "A polyphenol in tea."}
    }
    nodes = [
        {
            "slug": "ampk-activation",
            "title": "AMPK Activation",
            "type": "biology",
            "hook_question": "Does snacking block energy?",
            "takeaway_pill": "Fasting activates AMPK.",
            "epistemic_rating": {"grade": "High", "rationale": "Supported.", "debate_sides": []},
            "tags": [],
            "reading_modes": {"overview_3min": "This activates AMPK.", "deep_dive": []},
            "edges": [], "evidence_table": [], "bibliography": []
        }
    ]
    backlog = [
        {
            "id": "tea-metabolic-effects",
            "title": "Tea metabolic effects",
            "description": "Modulation of metabolism via EGCG.",
            "category": "biology",
            "votes": 10
        }
    ]
    translations = {"en": {"nav_vocabulary": "Glossary"}}
    import json
    import os
    from tools.compiler.writer import generate_search_index
    
    generate_search_index(str(tmp_path), nodes, vocabulary, translations, backlog)
    
    with open(os.path.join(tmp_path, "search_index.json"), "r", encoding="utf-8") as f:
        data = json.load(f)
        
    ampk_item = next(item for item in data if item["title"] == "AMPK")
    egcg_item = next(item for item in data if item["title"] == "EGCG")
    
    assert "in_pipeline" not in ampk_item  # AMPK has a node mention, so not only in pipeline
    assert egcg_item.get("in_pipeline") is True  # EGCG has only backlog mentions

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
    assert "Mentioned In" in compiled
    assert "../ampk-activation.html" in compiled
    assert "AMPK Activation" in compiled


def test_compile_vocabulary_detail_page_with_citations() -> None:
    """Verifies compilation of individual jargon detail page when citations are provided."""
    layout = "<html><body>{{title}} {{meta_description}} {{content}}</body></html>"
    term = "SIRT1"
    vocab_item = {
        "definition": "A cellular maintenance sirtuin.",
        "citations": [
            {
                "text": "Cantó et al., 2009",
                "link": "https://doi.org/10.1016/j.tem.2009.03.008"
            }
        ]
    }
    mentions = []
    translations = {"en": {"nav_vocabulary": "Glossary"}}
    from tools.compiler.writer import compile_vocabulary_detail_page
    compiled = compile_vocabulary_detail_page(layout, term, vocab_item, mentions, translations)
    assert "SIRT1" in compiled
    assert "A cellular maintenance sirtuin" in compiled
    assert "Scientific Sources & Verbatim Definitions" in compiled
    assert "Cantó et al., 2009" in compiled
    assert "https://doi.org/10.1016/j.tem.2009.03.008" in compiled



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
    assert "GRADE Rating Methodology &rarr;" in compiled
    assert "popover-debate-link" not in compiled
    assert "popover-more-link" in compiled
    assert "more..." in compiled
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
    assert data[1]["slug"] == "vocabulary/ampk.html"
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
    assert "biology" in compiled.lower()
    assert "AMPK Activation" in compiled
    assert "Circadian Sleep Protocol" not in compiled
    assert 'href="../ampk-activation.html"' in compiled

    # Tag with tags registry
    tags_registry = {
        "biology": {
            "name": "Biological Circuits",
            "dimension": "biology",
            "description": "Custom description of biology circuit processes."
        }
    }
    compiled_with_registry = compile_tag_page(layout, "biology", nodes, translations, tags_registry=tags_registry)
    assert "Biology" in compiled_with_registry
    assert "Custom description of biology" in compiled_with_registry

    # Tag with no matching articles
    compiled_empty = compile_tag_page(layout, "longevity", nodes, translations)
    assert "No decodings or pipeline proposals tagged" in compiled_empty


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
    assert "No articles or pipeline proposals in" in compiled_empty


def test_card_structure_and_backlog_buttons() -> None:
    """Verifies category badges and presence/absence of Vote button on backlog cards across pages."""
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
            "tags": ["biology"],
            "reading_modes": {
                "overview_3min": "Overview text",
                "deep_dive": []
            },
            "edges": [],
            "evidence_table": [],
            "bibliography": []
        }
    ]
    backlog = [
        {
            "id": "autophagy-kinetics",
            "title": "Autophagy Kinetics",
            "description": "Fasting trigger",
            "category": "biology",
            "tags": ["biology"],
            "votes": 124,
        }
    ]
    translations = {
        "en": {
            "category_biology": "Biology",
            "nav_backlog": "Backlog",
            "backlog_title": "Backlog Title",
            "feed_title": "Feed Title",
        }
    }

    # 1. Feed Page: Backlog card should NOT contain a separate "Vote" button, but should have the category tag, "In Pipeline" badge, and "backlog-votes" button
    compiled_feed = compile_feed_page(layout, nodes, translations, backlog=backlog)
    assert "Autophagy Kinetics" in compiled_feed
    assert "Proposed" in compiled_feed
    assert "BIOLOGY" in compiled_feed
    assert '<button class="vote-btn">' not in compiled_feed
    assert "backlog-votes" in compiled_feed

    # 2. Category Page: Backlog card should NOT contain a separate "Vote" button, but should have the category tag, "In Pipeline" badge, and "backlog-votes" button
    compiled_cat = compile_category_page(layout, "biology", nodes, translations, backlog=backlog)
    assert "Autophagy Kinetics" in compiled_cat
    assert "Proposed" in compiled_cat
    assert "BIOLOGY" in compiled_cat
    assert '<button class="vote-btn">' not in compiled_cat
    assert "backlog-votes" in compiled_cat

    # 3. Tag Page: Backlog card should NOT contain a separate "Vote" button, but should have the category tag, "In Pipeline" badge, and "backlog-votes" button
    compiled_tag = compile_tag_page(layout, "biology", nodes, translations, backlog=backlog)
    assert "Autophagy Kinetics" in compiled_tag
    assert "Proposed" in compiled_tag
    assert "BIOLOGY" in compiled_tag
    assert '<button class="vote-btn">' not in compiled_tag
    assert "backlog-votes" in compiled_tag

    # 4. Backlog Page: Backlog card should NOT contain a separate "Vote" button, but should have the category tag, "In the Pipeline" badge, and "backlog-votes" button
    compiled_backlog = compile_backlog_page(layout, backlog, translations)
    assert "Autophagy Kinetics" in compiled_backlog
    assert "In the Pipeline" in compiled_backlog
    assert "BIOLOGY" in compiled_backlog
    assert '<button class="vote-btn">' not in compiled_backlog
    assert "backlog-votes" in compiled_backlog


def test_validate_vocabulary_schema() -> None:
    """Verifies that validate_vocabulary_schema correctly identifies valid and invalid configurations."""
    import os
    import json
    from tools.pipeline_helper import validate_vocabulary_schema

    # 1. Valid vocabulary dictionary
    valid_vocab = {
        "AMPK": {
            "definition": "An energy-sensing cellular enzyme regulating metabolic homeostasis.",
            "vulgarized_analogy": "Acts as the cellular fuel gauge, pausing construction when fuel is low.",
            "taxonomy": "protein",
            "aliases": ["AMP-activated protein kinase"],
            "citations": [
                {
                    "text": "Hardie DG. AMPK. J Cell Sci. 2004;117:5479-5487.",
                    "link": "https://doi.org/10.1242/jcs.01540",
                    "defining_quote": "AMPK acts as a cellular energy sensor.",
                    "quote_page": "Page 5479"
                }
            ],
            "verification_status": "verified_human"
        }
    }

    # Write temporary file
    temp_path = "tests/temp_vocabulary.json"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(valid_vocab, f)

    try:
        errors = validate_vocabulary_schema(temp_path)
        assert not errors, f"Expected no errors, got: {errors}"

        # 2. Invalid vocabulary dictionary (missing defining_quote)
        invalid_vocab = {
            "AMPK": {
                "definition": "An energy-sensing cellular enzyme.",
                "vulgarized_analogy": "Acts as a fuel gauge.",
                "taxonomy": "protein",
                "aliases": [],
                "citations": [
                    {
                        "text": "Hardie DG. AMPK.",
                        "link": "https://doi.org/10.1242/jcs.01540",
                        # "defining_quote" is missing!
                        "quote_page": "Page 5479"
                    }
                ],
                "verification_status": "verified_human"
            }
        }
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(invalid_vocab, f)

        errors = validate_vocabulary_schema(temp_path)
        assert len(errors) == 1
        assert "missing or empty 'defining_quote'" in errors[0]
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_repo_vocabulary_compliance() -> None:
    """Verifies that the actual repository vocabulary.json file conforms to the new strict schema."""
    import os
    from tools.pipeline_helper import validate_vocabulary_schema

    vocab_path = "src/vocabulary.json"
    assert os.path.exists(vocab_path)
    errors = validate_vocabulary_schema(vocab_path)
    assert not errors, f"Repository vocabulary.json contains schema violations: {errors}"


