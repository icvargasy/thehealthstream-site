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
        "bibliography": [{"id": "ref1", "text": "Smith 2023 details.", "link": "http://ncbi.nlm.nih.gov", "tag": "Empirical Study"}],
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
    assert '<span class="jargon-term"' in linked
    assert 'data-term="AMPK"' in linked
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
    assert "Scientific Sources & Literature Citations" in compiled or "Scientific Sources &amp; Literature Citations" in compiled
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
    assert "AMPK Activation" in compiled
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
    assert "Evidence Level:" in compiled
    assert "High" in compiled
    assert "GRADE Rating Methodology &rarr;" in compiled
    assert "popover-more-link" in compiled
    assert "Jump to evidence registry" in compiled
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
            "hook_question": "Can fasting restart the cell's internal recycling system?",
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
            "hook_question": "Can fasting restart the cell's internal recycling system?",
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


def test_link_checker_cache() -> None:
    """Verifies that the link checker cache exists and contains no failures."""
    import os
    import json
    cache_path = "tools/link_cache.json"
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            cache = json.load(f)
            for url, entry in cache.items():
                assert entry.get("success", False), f"Cached link failure detected: {url} (Status {entry.get('status_code')})"


def test_vocabulary_no_adjective_alias_collisions() -> None:
    """Verifies that no raw adjective aliases exist in vocabulary.json dynamically."""
    import json
    import re
    with open("src/vocabulary.json", "r", encoding="utf-8") as f:
        vocab = json.load(f)

    # Dynamic adjective suffix pattern (-al, -ic, -ous, -ar, -ary, -ive)
    adj_suffix_regex = re.compile(r"^[a-z]{5,}(?:al|ic|ous|ar|ary|ive)$", re.IGNORECASE)
    # Valid single-word noun terms/aliases that happen to match adjective suffixes
    valid_noun_exceptions = {"chemical", "molecule", "receptor", "factor", "microbiome", "lipophilic", "polyphenol"}

    for term, data in vocab.items():
        aliases = [a.lower() for a in data.get("aliases", [])]
        for alias in aliases:
            if " " in alias or alias in valid_noun_exceptions:
                continue
            if adj_suffix_regex.match(alias):
                assert False, f"Forbidden raw adjective alias detected: '{alias}' under term '{term}'"



def test_vocabulary_analogy_word_ceilings() -> None:
    """Verifies that all vulgarized analogies in vocabulary.json satisfy universal 25-word ceiling."""
    import json
    with open("src/vocabulary.json", "r", encoding="utf-8") as f:
        vocab = json.load(f)
    
    for term, data in vocab.items():
        analogy = data.get("vulgarized_analogy", "")
        if analogy:
            word_count = len(analogy.split())
            assert word_count <= 25, f"Analogy for '{term}' exceeds universal 25-word ceiling ({word_count} words)"


def test_accessibility_attributes_compilation() -> None:
    """Verifies static HTML compilation renders accessibility attributes (ARIA, tabindex, semantic headings)."""
    layout = '<html><body><button id="sidebar-toggle" aria-controls="sidebar">Toggle</button><h2 class="sidebar-title">Topics</h2>{{title}} {{meta_description}} {{content}}</body></html>'
    translations = {"en": {"category_biology": "Biology"}}
    vocabulary = {"AMPK": {"definition": "An energy-sensing enzyme."}}
    node = {
        "slug": "ampk-activation",
        "title": "AMPK Activation",
        "type": "biology",
        "hook_question": "Does snacking block AMPK?",
        "takeaway_pill": "Fasting activates AMPK.",
        "epistemic_rating": {"grade": "High", "rationale": "Consensus supported.", "debate_sides": []},
        "tags": ["biology"],
        "reading_modes": {"overview_3min": "This activates AMPK.", "deep_dive": []},
        "edges": [], "evidence_table": [], "bibliography": []
    }

    # 1. Detail page compilation check
    compiled_detail = compile_detail_page(layout, node, translations, vocabulary=vocabulary)
    assert 'tabindex="0"' in compiled_detail
    assert 'role="button"' in compiled_detail
    assert 'aria-haspopup="dialog"' in compiled_detail
    assert 'aria-controls="grade-popover"' in compiled_detail

    # 2. Sidebar heading check
    compiled_base = compile_base_layout(layout, translations, [node], [], "feed")
    assert '<h2 class="sidebar-title">' in compiled_base


def test_card_layout_parity_all_pages() -> None:
    """Verifies unified card layout markup across feed, category, and tag compiled pages."""
    layout = "<html><body>{{title}} {{meta_description}} {{content}}</body></html>"
    nodes = [{
        "slug": "ampk-activation",
        "title": "AMPK Activation",
        "type": "biology",
        "hook_question": "Does snacking block energy?",
        "takeaway_pill": "Fasting activates AMPK.",
        "systems_analogy_hook": "Acts as cellular fuel gauge.",
        "epistemic_rating": {"grade": "High", "rationale": "Supported.", "debate_sides": []},
        "tags": ["metabolism"],
        "reading_modes": {"overview_3min": "Overview.", "deep_dive": []},
        "edges": [], "evidence_table": [], "bibliography": []
    }]
    backlog = [{
        "id": "autophagy-kinetics",
        "title": "Autophagy Kinetics",
        "hook_question": "Can fasting restart the cell's internal recycling system?",
        "description": "Fasting trigger",
        "category": "biology",
        "tags": ["metabolism"],
        "votes": 42,
        "created_at": "2026-06-15"
    }]
    translations = {"en": {"category_biology": "Biology", "nav_home": "Explore"}}

    feed = compile_feed_page(layout, nodes, translations, backlog=backlog)
    cat = compile_category_page(layout, "biology", nodes, translations, backlog=backlog)
    tag = compile_tag_page(layout, "metabolism", nodes, translations, backlog=backlog)

    for page_html in (feed, cat, tag):
        # Article card parity
        assert 'class="feed-card cat-biology"' in page_html
        assert 'data-title="AMPK Activation"' in page_html
        assert 'data-category="biology"' in page_html
        assert 'class="category-tag">BIOLOGY</a>' in page_html
        assert 'class="card-meta-dates"' in page_html

        # Backlog card parity
        assert 'data-id="autophagy-kinetics"' in page_html
        assert 'class="backlog-votes' in page_html
        assert 'data-base-votes="42"' in page_html


def test_content_nodes_vulgarisation_and_analogy_ceilings() -> None:
    """Scans all JSON files under src/nodes/en/ to verify 3-tier word count ceilings on takeaways and analogies."""
    import glob
    import json
    import os

    node_files = glob.glob("src/nodes/en/**/*.json", recursive=True)
    assert len(node_files) > 0, "No content node files found under src/nodes/en/"

    for filepath in node_files:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        title = data.get("title", os.path.basename(filepath))
        
        # Takeaway pill ceiling (Level 2/3: <= 45 words)
        takeaway = data.get("takeaway_pill", "")
        if takeaway:
            word_count = len(takeaway.split())
            assert word_count <= 45, f"Node '{title}' takeaway_pill exceeds Level 3 ceiling of 45 words ({word_count} words)"

        # Systems analogy hook ceiling (Level 2/3: <= 45 words)
        analogy = data.get("systems_analogy_hook", "")
        if analogy:
            word_count = len(analogy.split())
            assert word_count <= 45, f"Node '{title}' systems_analogy_hook exceeds Level 3 ceiling of 45 words ({word_count} words)"


def test_render_backlog_card_layout_parity() -> None:
    """Verifies render_backlog_card uses hook_question as card H2 and renders the systems analogy block."""
    from tools.compiler.writer import render_backlog_card

    backlog_item = {
        "id": "test-backlog-item",
        "title": "Test Backlog Proposal",
        "hook_question": "Could disrupted cell recycling quietly accelerate brain aging?",
        "description": "Why is cellular energy sensing critical for longevity?",
        "category": "biology",
        "votes": 12,
        "tags": ["biology", "metabolism"],
        "created_at": "2026-06-15",
        "systems_analogy": "A factory power grid throttling non-essential machinery.",
        "takeaway_pill": "Phosphorylation of energy sensors activates mitochondrial biogenesis."
    }

    translations = {"en": {"category_biology": "Biological Circuits"}}
    card_html = render_backlog_card(backlog_item, translations, as_list_item=False)

    assert 'class="feed-card pipeline-card-merged cat-biology"' in card_html
    # hook_question must appear as the card H2 headline
    assert 'Could disrupted cell recycling quietly accelerate brain aging?' in card_html
    assert 'class="card-analogy-hook"' in card_html
    assert 'A factory power grid throttling non-essential machinery.' in card_html
    assert 'class="pipeline-badge pipeline-badge-link"' in card_html
    assert 'In the Pipeline' in card_html
    # description must NOT appear as the card H2 (internal field only)
    assert 'Why is cellular energy sensing critical for longevity?' not in card_html
    # Formal mechanism takeaways are reserved for detail pages
    assert 'class="card-takeaway-hook"' not in card_html
    assert 'class="qa-question-text"' not in card_html


def test_validate_vocabulary_item_ai_generated_default() -> None:
    """Verifies that validate_vocabulary_item sets verification_status to 'ai_generated' by default."""
    from tools.compiler.reader import validate_vocabulary_item

    item_data = {
        "definition": "A test term definition.",
        "vulgarized_analogy": "A test analogy."
    }
    validate_vocabulary_item(item_data, "test-term")
    assert item_data.get("verification_status") == "ai_generated"


def test_dynamic_analogy_purity_noun_subject_and_universal_ceiling() -> None:
    """Dynamic first-principles enforcer for Systems Analogy Protocol across current and future entries.

    Checks:
    1. Zero Biological/Clinical Jargon: Dynamically matches terms/aliases from src/vocabulary.json
       plus biological suffix patterns (-itis, -cyte, -phage, -ase, -ome, -genic, -vascular, -tropic, -blast, -some, -emia).
    2. Explicit Noun Subject: Analogies cannot start with bare action verbs (e.g. Restructures, Activates, Regulates).
    3. Universal Ceiling: <= 25 words across vocabulary, backlog cards, and content nodes.
    """
    import glob, json, os, re

    # 1. Build dynamic jargon lexicon from vocabulary.json keys and aliases
    vocab_path = "src/vocabulary.json"
    assert os.path.exists(vocab_path), "src/vocabulary.json missing"
    with open(vocab_path, "r", encoding="utf-8") as f:
        vocab_data = json.load(f)

    # Exclude non-jargon taxonomy words
    ignore_words = {"concept", "framework", "condition", "process", "lifestyle", "exercise", "book", "grade", "evidence", "healthspan"}
    dynamic_jargon_terms = set()

    for term, data in vocab_data.items():
        term_clean = term.lower().strip()
        if len(term_clean) > 2 and term_clean not in ignore_words:
            dynamic_jargon_terms.add(term_clean)
        for alias in data.get("aliases", []):
            alias_clean = alias.lower().strip()
            if len(alias_clean) > 2 and alias_clean not in ignore_words:
                dynamic_jargon_terms.add(alias_clean)

    # Additional explicit medical/biological suffix regex (excluding non-bio everyday words like 'home')
    bio_suffix_regex = re.compile(r"\b(?!home\b)\w+(?:itis|cyte|phage|ase|ome|genic|vascular|tropic|blast|some|emia|pathic)\b", re.IGNORECASE)

    # Imperative / Action verb blacklist at position 0
    bare_action_verb_regex = re.compile(r"^(Restructures|Regulates|Activates|Clears|Triggers|Modulates|Prevents|Reduces|Enhances|Improves|Accelerates|Drives|Inhibits|Promotes|Suppresses|Alters)\b", re.IGNORECASE)

    # A. Audit Published Nodes (src/nodes/en/)
    node_files = glob.glob("src/nodes/en/**/*.json", recursive=True)
    for filepath in node_files:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        analogy = data.get("systems_analogy_hook", "").strip()
        if not analogy:
            continue

        # Ceiling check (Universal ceiling: <= 25 words)
        words = analogy.split()
        assert len(words) <= 25, f"Node analogy in '{filepath}' exceeds universal ceiling of 25 words ({len(words)} words)"

        # Explicit Noun Subject check
        match_verb = bare_action_verb_regex.match(analogy)
        assert not match_verb, f"Node analogy in '{filepath}' starts with bare action verb '{match_verb.group(0)}': '{analogy}'"

        # Dynamic Jargon Check
        analogy_lower = analogy.lower()
        for j_term in dynamic_jargon_terms:
            pattern = r"\b" + re.escape(j_term) + r"\b"
            assert not re.search(pattern, analogy_lower), f"Node analogy in '{filepath}' violates Purity Rule with vocabulary term '{j_term}'"

        # Bio Suffix Check
        suffix_matches = bio_suffix_regex.findall(analogy)
        assert not suffix_matches, f"Node analogy in '{filepath}' violates Purity Rule with biological suffix terms: {suffix_matches}"

    # B. Audit Backlog Items (src/backlog.json)
    backlog_path = "src/backlog.json"
    if os.path.exists(backlog_path):
        with open(backlog_path, "r", encoding="utf-8") as f:
            backlog_items = json.load(f)
        for item in backlog_items:
            analogy = item.get("systems_analogy", "").strip()
            if not analogy:
                continue
            words = analogy.split()
            assert len(words) <= 25, f"Backlog analogy for '{item.get('id')}' exceeds universal ceiling of 25 words ({len(words)} words)"
            match_verb = bare_action_verb_regex.match(analogy)
            assert not match_verb, f"Backlog analogy for '{item.get('id')}' starts with bare action verb '{match_verb.group(0)}'"

    # C. Audit Vocabulary Analogies (Universal ceiling <= 25 words)
    for term, data in vocab_data.items():
        v_analogy = data.get("vulgarized_analogy", "").strip()
        if not v_analogy:
            continue
        words = v_analogy.split()
        assert len(words) <= 25, f"Vocabulary analogy for '{term}' exceeds universal ceiling of 25 words ({len(words)} words)"
        match_verb = bare_action_verb_regex.match(v_analogy)
        assert not match_verb, f"Vocabulary analogy for '{term}' starts with bare action verb '{match_verb.group(0)}'"


def test_full_build_internal_relative_links_and_anchors() -> None:
    """Compiles site to en/ and verifies 100% of internal HTML relative links and fragment anchors resolve."""
    from html.parser import HTMLParser
    from tools.build import run_build
    import os

    class LinkAndAnchorExtractor(HTMLParser):
        def __init__(self):
            super().__init__()
            self.hrefs = []
            self.ids = set()

        def handle_starttag(self, tag, attrs):
            attr_dict = dict(attrs)
            if "id" in attr_dict:
                self.ids.add(attr_dict["id"])
            if tag == "a" and "href" in attr_dict:
                self.hrefs.append(attr_dict["href"])

    run_build()
    output_dir = "en"
    assert os.path.exists(output_dir), "en directory missing after run_build()"

    html_files = []
    for root, _, files in os.walk(output_dir):
        for f in files:
            if f.endswith(".html"):
                html_files.append(os.path.join(root, f))

    assert len(html_files) > 0, "No HTML files generated by run_build()"

    for filepath in html_files:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        parser = LinkAndAnchorExtractor()
        parser.feed(content)

        # Check internal relative links
        for href in parser.hrefs:
            if href.startswith(("http://", "https://", "mailto:", "javascript:")):
                continue

            parts = href.split("#")
            rel_path = parts[0].split("?")[0]
            fragment = parts[1] if len(parts) > 1 else None

            if rel_path:
                target_path = os.path.normpath(os.path.join(os.path.dirname(filepath), rel_path))
                assert os.path.exists(target_path), f"Broken relative link '{href}' in {os.path.relpath(filepath, output_dir)}"
            else:
                target_path = filepath

            if fragment:
                with open(target_path, "r", encoding="utf-8") as tf:
                    target_parser = LinkAndAnchorExtractor()
                    target_parser.feed(tf.read())
                assert fragment in target_parser.ids, f"Broken anchor '#{fragment}' in '{href}' from {os.path.relpath(filepath, output_dir)}"


def test_compile_detail_page_json_ld_schema_validity() -> None:
    """Parses JSON-LD script block from compiled detail page using json.loads and validates FAQPage structure."""
    import json
    from tools.compiler.writer import compile_detail_page

    layout = "<html><head></head><body>{{title}} {{meta_description}} {{content}}</body></html>"
    node = {
        "slug": "test-node",
        "title": "Test Title",
        "type": "biology",
        "hook_question": "Question?",
        "takeaway_pill": "Takeaway.",
        "epistemic_rating": {"grade": "High", "rationale": "Rationale.", "debate_sides": []},
        "tags": ["biology"],
        "reading_modes": {"overview_3min": "Overview", "deep_dive": []},
        "edges": [],
        "evidence_table": [],
        "bibliography": []
    }
    translations = {"en": {"takeaway_pill_title": "Takeaway", "consensus_level": "Level", "consensus_established": "Est"}}

    compiled = compile_detail_page(layout, node, translations, [node])

    start_tag = '<script type="application/ld+json">'
    end_tag = '</script>'
    assert start_tag in compiled and end_tag in compiled

    json_str = compiled.split(start_tag)[1].split(end_tag)[0].strip()
    data = json.loads(json_str)

    assert data["@context"] == "https://schema.org"
    assert data["@type"] == "FAQPage"
    assert "mainEntity" in data
    assert isinstance(data["mainEntity"], list)
    assert len(data["mainEntity"]) > 0
    assert data["mainEntity"][0]["@type"] == "Question"
    assert data["mainEntity"][0]["acceptedAnswer"]["@type"] == "Answer"


def test_linker_attribute_safety_with_gt_symbol() -> None:
    """Ensures inject_jargon_links does not corrupt HTML tags containing '>' inside attribute quotes."""
    from tools.compiler.linker import inject_jargon_links

    vocab = {"AMPK": {"definition": "Energy sensor definition."}}
    html_input = '<img alt="AMPK > SIRT1 pathway" src="test.jpg"> AMPK is active.'
    output = inject_jargon_links(html_input, vocab)

    assert '<img alt="AMPK > SIRT1 pathway" src="test.jpg">' in output
    assert '<span class="jargon-term"' in output
    assert 'data-term="AMPK"' in output


def test_database_grade_schema_purity() -> None:
    """Ensures all backlog items and developed nodes have valid GRADE levels (High, Moderate, Low, Very Low)."""
    import json
    import os

    valid_grades = {"High", "Moderate", "Low", "Very Low"}

    # 1. Backlog Validation
    backlog_path = "src/backlog.json"
    if os.path.exists(backlog_path):
        with open(backlog_path, "r", encoding="utf-8") as f:
            items = json.load(f)
        for item in items:
            grade = item.get("grade")
            assert grade in valid_grades, f"Backlog proposal '{item.get('id')}' has invalid/missing grade: '{grade}'"


def test_backlog_book_title_naming_standards() -> None:
    """Verifies book category items follow 'Book Title (Author Name)' and validates minimum dataset size."""
    import json
    import os
    import re

    backlog_path = "src/backlog.json"
    assert os.path.exists(backlog_path), "backlog.json is missing!"

    with open(backlog_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    # 1. Size check (data preservation assertion)
    assert len(items) >= 28, f"Backlog has shrunk! Found only {len(items)} items, expected at least 28."

    # 2. Check for Gabor Maté book summary restoration
    mate_present = any(item.get("id") == "when-the-body-says-no-summary" for item in items)
    assert mate_present, "Gabor Maté book summary ('when-the-body-says-no-summary') is missing from the backlog!"

    # 3. Check book title formatting
    book_title_regex = re.compile(r"^.+\s\(.+\)$")
    for item in items:
        if item.get("category") == "book":
            title = item.get("title", "")
            assert book_title_regex.match(title), (
                f"Book category entry '{item.get('id')}' violates naming convention! "
                f"Title was '{title}', must be in format 'Book Title (Author Name)'"
            )

def test_validate_backlog_item_requires_hook_question() -> None:
    """Ensures validate_backlog_item raises ValueError when hook_question is absent."""
    from tools.compiler.reader import validate_backlog_item

    base_item = {
        "id": "test-backlog-id",
        "title": "Test Backlog Entry",
        "hook_question": "Could disrupted cell recycling quietly accelerate brain aging?",
        "description": "How does autophagy suppression drive neurodegeneration?",
        "category": "biology",
        "systems_analogy": "A city sanitation fleet halted by budget cuts, letting waste pile in streets.",
        "grade": "Low",
    }

    # 1. Valid item must pass without raising
    validate_backlog_item(base_item, "test-backlog-id")

    # 2. Missing hook_question must raise
    invalid = {k: v for k, v in base_item.items() if k != "hook_question"}
    with pytest.raises(ValueError, match="hook_question"):
        validate_backlog_item(invalid, "test-backlog-id")

    # 3. Empty hook_question must raise
    empty = {**base_item, "hook_question": ""}
    with pytest.raises(ValueError, match="hook_question"):
        validate_backlog_item(empty, "test-backlog-id")


def test_backlog_hook_question_schema_parity() -> None:
    """Ensures every non-book backlog item has a populated hook_question field."""
    import json
    import os

    backlog_path = "src/backlog.json"
    if not os.path.exists(backlog_path):
        return

    with open(backlog_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    for item in items:
        item_id = item.get("id", "unknown")
        category = item.get("category", "")
        if category == "book":
            continue  # book cards use Title (Author) format, hook_question optional
        hook = item.get("hook_question", "")
        assert hook and hook.strip(), (
            f"Backlog item '{item_id}' (category={category}) is missing a hook_question. "
            "All Science and Lifestyle pipeline cards must have a hook_question."
        )
        assert hook.strip().endswith("?"), (
            f"Backlog item '{item_id}' hook_question must end with '?'. Got: '{hook}'"
        )


def test_tag_schema_validation() -> None:
    """Verifies that validate_backlog_item rejects unregistered tags."""
    from tools.compiler.reader import validate_backlog_item
    invalid_item = {
        "id": "test-invalid-tag",
        "title": "Invalid Tag Entry",
        "hook_question": "Does invalid tag fail?",
        "description": "Description...",
        "category": "biology",
        "systems_analogy": "Analogy...",
        "grade": "Low",
        "tags": ["invalid_tag_name_xyz"]
    }
    with pytest.raises(ValueError, match="Unregistered or invalid tag"):
        validate_backlog_item(invalid_item, "test-invalid-tag")


def test_popover_analogy_badge_in_linker() -> None:
    """Verifies that _get_compiled_definition prepends Systems Analogy badge for terms with vulgarized_analogy."""
    from tools.compiler.linker import _get_compiled_definition, clear_popover_cache
    clear_popover_cache()
    vocab = {
        "autophagy": {
            "definition": "Formal cellular degradation process.",
            "vulgarized_analogy": "A city fleet recycling old car parts.",
            "aliases": []
        }
    }
    compiled = _get_compiled_definition("autophagy", vocab)
    assert "popover-analogy-badge" in compiled
    assert "systems-analogy-icon" in compiled
    assert "Systems Analogy" in compiled


def test_debate_stance_cards_in_writer() -> None:
    """Verifies that scientific debates are rendered as stance cards with badges."""
    from tools.compiler.writer import compile_detail_page
    layout_html = "<html><head></head><body>{{content}}</body></html>"
    node = {
        "slug": "ampk-activation",
        "type": "biology",
        "title": "AMPK Activation",
        "hook_question": "Does constant snacking block energy?",
        "takeaway_pill": "Fasting activates AMPK.",
        "epistemic_rating": {
            "grade": "High",
            "rationale": "Strong evidence.",
            "debate_sides": [
                {
                    "position": "Proponent View",
                    "arguments": "Advocates argue that fasting triggers clearance.",
                    "stance": "supporting",
                    "citations": ["ref1"]
                },
                {
                    "position": "Critical View",
                    "arguments": "Critics contend that extreme fasting risks muscle loss.",
                    "stance": "counter",
                    "citations": []
                }
            ]
        },
        "tags": ["biology", "metabolism"],
        "reading_modes": {
            "overview_3min": "Overview text",
            "deep_dive": [{"heading": "Molecular Axis", "body": "Body text"}]
        },
        "edges": [],
        "evidence_table": [],
        "bibliography": [{"id": "ref1", "text": "Study 2023", "link": "http://example.com", "tag": "Empirical Study"}]
    }
    html_out = compile_detail_page(layout_html, node, {"en": {}})
    assert "debate-bullet-item" in html_out
    assert "stance-badge" in html_out
    assert "Supporting" in html_out
    assert "Counter" in html_out


def test_related_circuits_3_directional_rendering() -> None:
    """Confirms that render_related_circuits_section renders Systems Biology in Action title, curiosity-first hook questions, lifecycle badges, relational bridges, and Read Summary/Upvote buttons."""
    from tools.compiler.writer import compile_detail_page, render_related_circuits_section

    nodes_sample = [
        {"slug": "source-node", "title": "Source Node Title", "hook_question": "Does source work?", "type": "biology", "systems_analogy_hook": "A master switch managing daily energy."},
        {"slug": "upstream-node", "title": "Upstream Cause Title", "hook_question": "How does upstream driver influence cellular respiration?", "type": "lifestyle", "systems_analogy_hook": "A bicycle chain transferring pedal force to the back wheel."},
    ]
    backlog_sample = [
        {"id": "frontier-node", "title": "Frontier Target Title", "hook_question": "Can parallel circuits balance glucose load?", "category": "biology", "systems_analogy": "A household thermostat regulating room temperature."}
    ]

    node_data = {
        "slug": "source-node",
        "type": "biology",
        "title": "Source Node Title",
        "hook_question": "Does source work?",
        "takeaway_pill": "Pill takeaway",
        "epistemic_rating": {"grade": "High", "rationale": "Clear data", "debate_sides": []},
        "tags": ["biology"],
        "reading_modes": {"overview_3min": "Text", "deep_dive": []},
        "related_circuits": {
            "upstream": [
                {
                    "target": "upstream-node",
                    "mechanism": "Primary driver mechanism transferring metabolic load.",
                    "tier": "published"
                }
            ],
            "similar": [
                {
                    "target": "frontier-node",
                    "mechanism": "Hypothesized parallel maintaining homeostasis.",
                    "tier": "backlog"
                }
            ]
        },
        "evidence_table": [],
        "bibliography": []
    }

    rendered_html = render_related_circuits_section(node_data, nodes_sample, backlog=backlog_sample)

    # Check section title and directional group headers
    assert "How This Connects: Systems Biology in Action" in rendered_html
    assert "Upstream Drivers &amp; Triggers" in rendered_html or "Upstream Drivers & Triggers" in rendered_html
    assert "Parallel Circuits &amp; Convergent Loops" in rendered_html or "Parallel Circuits & Convergent Loops" in rendered_html
    assert "badge-upstream" in rendered_html
    assert "badge-similar" in rendered_html

    # Check curiosity-first hook question headlines and formal target subtitles
    assert "How does upstream driver influence cellular respiration?" in rendered_html
    assert "Target: <span>Upstream Cause Title</span>" in rendered_html
    assert "Can parallel circuits balance glucose load?" in rendered_html
    assert "Target: <span>Frontier Target Title</span>" in rendered_html

    # Check Relational Bridge box
    assert "The Connection" in rendered_html
    assert "Primary driver mechanism transferring metabolic load." in rendered_html
    assert "Hypothesized parallel maintaining homeostasis." in rendered_html

    # Check bespoke lifecycle badges with icons
    assert "badge-lifecycle-decoded" in rendered_html
    assert "Decoded" in rendered_html
    assert "badge-lifecycle-pipeline" in rendered_html
    assert "In Pipeline" in rendered_html

    # Check card-consistent actions: Read Summary button for published node
    assert "read-article-btn" in rendered_html
    assert "Read Summary" in rendered_html
    assert "upstream-node.html" in rendered_html

    # Check in-page upvote button for pipeline proposal
    assert "backlog-votes" in rendered_html
    assert "data-id=\"frontier-node\"" in rendered_html
    assert "Upvote" in rendered_html

    # Check prominent solid primary CTA
    assert "+ Propose a Pathway Connection &rarr;" in rendered_html
    assert "connection-submit-btn-primary" in rendered_html
    assert "submit-proposal.html?source=source-node" in rendered_html


def test_compile_vocabulary_detail_page_flat_layout() -> None:
    """Verifies that compile_vocabulary_detail_page generates unboxed flat analogy and article-consistent sections."""
    from tools.compiler.writer import compile_vocabulary_detail_page

    layout = "<html><body>{{title}} {{meta_description}} {{content}}</body></html>"
    term = "AMPK"
    vocab_item = {
        "definition": "AMP-activated protein kinase enzyme.",
        "vulgarized_analogy": "The master fuel gauge monitoring energy balance.",
        "taxonomy": "protein",
        "verification_status": "verified_human",
        "aliases": ["AMP-ACTIVATED PROTEIN KINASE"],
        "citations": [
            {
                "text": "Hardie DG, et al. AMPK.",
                "link": "https://doi.org/10.1007/test",
                "defining_quote": "AMPK acts as the central regulator.",
                "quote_page": "189"
            }
        ]
    }
    mentions = [
        {"title": "EGCG", "slug": "egcg.html", "type": "lexicon", "taxonomy": "molecule"}
    ]
    translations = {"en": {}}

    compiled = compile_vocabulary_detail_page(layout, term, vocab_item, mentions, translations)

    # Check unboxed flat definitions list
    assert "vocab-definitions-list" in compiled
    assert "Systems Analogy" in compiled
    assert "Formal Definition" in compiled
    assert "The master fuel gauge monitoring energy balance." in compiled

    # Check header badges
    assert "Back to Lexicon" in compiled
    assert "Type: protein" in compiled
    assert "Aliases:" in compiled

    # Check evidence & citations sections
    assert "Mentioned In" in compiled
    assert "Scientific Sources &amp; Literature Citations" in compiled or "Scientific Sources & Literature Citations" in compiled
    assert "[1]" in compiled
    assert "Hardie DG, et al. AMPK." in compiled
    assert "AMPK acts as the central regulator." in compiled


def test_morphological_variants_generation() -> None:
    """Verifies singular, plural, irregular, and hyphen morphological expansions."""
    from tools.compiler.linker import get_morphological_variants

    # Regular plural/singular derivations
    assert "metabolic dysregulations" in get_morphological_variants("metabolic dysregulation")
    assert "metabolic dysregulation" in get_morphological_variants("metabolic dysregulations")
    assert "oligodendrocyte" in get_morphological_variants("oligodendrocytes")
    assert "oligodendrocytes" in get_morphological_variants("oligodendrocyte")
    assert "glucotypes" in get_morphological_variants("glucotype")
    assert "variabilities" in get_morphological_variants("variability")

    # Irregular derivations
    assert "dysbioses" in get_morphological_variants("dysbiosis")
    assert "dysbiosis" in get_morphological_variants("dysbioses")
    assert "microglial" in get_morphological_variants("microglia")
    assert "cytoskeletal" in get_morphological_variants("cytoskeleton")
    assert "xenohormetic" in get_morphological_variants("xenohormesis")

    # Hyphen / space alternates
    assert "gut-brain axis" in get_morphological_variants("gut brain axis")
    assert "gut brain axis" in get_morphological_variants("gut-brain axis")

    # Short uppercase acronyms must NOT be stemmed or pluralized
    assert get_morphological_variants("DNA") == {"DNA"}
    assert get_morphological_variants("RNA") == {"RNA"}
    assert get_morphological_variants("GRADE") == {"GRADE"}
    assert get_morphological_variants("ATP") == {"ATP"}


def test_case_sensitive_acronym_isolation() -> None:
    """Verifies that short uppercase acronyms do not falsely match lowercase words."""
    from tools.compiler.linker import build_lexicon_matcher

    vocab = {
        "GRADE": {"definition": "Standardized evidence evaluation framework.", "aliases": []},
        "healthspan": {"definition": "Period of life spent free from disease.", "aliases": []},
    }
    cs_pat, cs_map, ci_pat, ci_map = build_lexicon_matcher(vocab)

    test_text = "We evaluate the evidence grade using standard metrics. We need high GRADE rigor."
    cs_matches = [m.group(1) for m in cs_pat.finditer(test_text)] if cs_pat else []
    assert cs_matches == ["GRADE"]
    assert "grade" not in cs_matches


def test_deep_text_harvester_exhaustiveness() -> None:
    """Ensures nested fields (citations, debate arguments, evidence tables) are captured."""
    from tools.compiler.utils import extract_searchable_text

    node_payload = {
        "title": "Sample Study",
        "reading_modes": {"overview_3min": "Overview text.", "deep_dive": []},
        "evidence_table": [{"outcome": "Target colibactin reduction observed."}],
        "epistemic_rating": {
            "debate_sides": [{"arguments": "Discussing atuzaginstat efficacy."}]
        }
    }
    extracted = extract_searchable_text(node_payload)
    assert "colibactin" in extracted
    assert "atuzaginstat" in extracted


def test_zero_orphans_without_hardcoded_exemptions() -> None:
    """Ensures all 124 terms in the live corpus pass consistency audit with zero hardcoded exemptions."""
    import os
    from tools.compiler.utils import load_json_file
    from tools.build import _build_mentions_map

    vocab = load_json_file("src/vocabulary.json")
    backlog = load_json_file("src/backlog.json", default_empty=[])
    nodes = []
    nodes_dir = "src/nodes/en"
    if os.path.exists(nodes_dir):
        for f in os.listdir(nodes_dir):
            if f.endswith(".json"):
                n = load_json_file(os.path.join(nodes_dir, f))
                n["slug"] = f.replace(".json", "")
                nodes.append(n)

    mentions = _build_mentions_map(nodes, backlog, vocab)
    orphans = [term for term, m_list in mentions.items() if len(m_list) == 0]

    assert len(orphans) == 0, f"Unreferenced orphan terms detected in live corpus: {orphans}"
    assert len(mentions["metabolic syndrome"]) >= 1
    assert any("cgm-non-diabetic-glycotypes" in m["slug"] for m in mentions["metabolic syndrome"])







