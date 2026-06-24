"""The Healthstream Curator Workspace - Streamlit Dashboard.

Provides an interactive local web interface to review the Google Sheets staging inbox,
proactively audit literature, build lexicon definitions with direct quotes, and bootstrap
valid article drafts.
"""

import os
import sys
import datetime
import streamlit as st
import pandas as pd
from typing import List, Dict, Any

# Ensure tools/ is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compiler.utils import slugify, load_json_file, save_json_file
import curator_engine

# Path configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src")
BACKLOG_PATH = os.path.join(SRC_DIR, "backlog.json")
INBOX_PATH = os.path.join(SRC_DIR, "inbox.json")
TAGS_PATH = os.path.join(SRC_DIR, "tags.json")
VOCAB_PATH = os.path.join(SRC_DIR, "vocabulary.json")
NODES_DIR = os.path.join(SRC_DIR, "nodes", "en")
DRAFTS_DIR = os.path.join(NODES_DIR, "drafts")

# Set Page Configuration
st.set_page_config(
    page_title="The Healthstream Curator Workspace",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Premium Styling
st.markdown(
    """
    <style>
    :root {
        --accent-synapse: #DE3B49;
    }
    .main-title {
        color: #DE3B49;
        font-family: 'Fraunces', serif;
        font-size: 2.5rem;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .card {
        padding: 1.5rem;
        border-radius: 8px;
        background-color: #fcfcfc;
        border: 1px solid #eee;
        border-left: 5px solid #DE3B49;
        margin-bottom: 1rem;
    }
    .badge-human {
        background-color: #e3f2fd;
        color: #0d47a1;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .badge-agent {
        background-color: #efebe9;
        color: #4e342e;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_existing_node_slugs() -> List[str]:
    """Returns a list of all compiled article slugs."""
    if not os.path.exists(NODES_DIR):
        return []
    return [
        os.path.splitext(f)[0]
        for f in os.listdir(NODES_DIR)
        if f.endswith(".json")
    ]


# Title Header
st.markdown("<h1 class='main-title'>🌱 The Healthstream</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Curator Workspace & Interactive Research Dashboard</p>", unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.title("Navigation")
menu = st.sidebar.radio(
    "Choose Module",
    ["Inbox & Staging", "Lexicon / Vocabulary Builder", "Draft Bootstrapper"]
)

# Load tags registry
if os.path.exists(TAGS_PATH):
    TAGS_REGISTRY = load_json_file(TAGS_PATH)
else:
    TAGS_REGISTRY = {}

# ---------------------------------------------------------
# MODULE 1: Inbox & Staging Area
# ---------------------------------------------------------
if menu == "Inbox & Staging":
    st.header("📥 Inbox & Submission Staging")
    st.write(
        "Review topic submissions imported from Google Sheets. "
        "Vet and promote submissions to the active backlog queue."
    )
    
    inbox = load_json_file(INBOX_PATH, default_empty=[])
    backlog = load_json_file(BACKLOG_PATH, default_empty=[])
    
    if not inbox:
        st.info("The staging inbox is currently empty. Run `new_entry_in_pipeline.py --import` to fetch sheet responses.")
    else:
        st.subheader(f"Pending Inbox Items ({len(inbox)})")
        
        # Display list of inbox items
        for idx, item in enumerate(inbox):
            with st.container():
                st.markdown(
                    f"""
                    <div class='card'>
                        <h4>{item['title']} <span style='font-size: 0.8rem; color:#888;'>({item['category']})</span></h4>
                        <p style='font-style: italic; color:#555;'>Question: "{item['description']}"</p>
                        <p style='font-size: 0.85rem; color:#777;'>Current Votes: {item.get('votes', 1)} | Suggested Tags: {', '.join(item.get('tags', []))}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                
                col1, col2, col3 = st.columns([1, 1, 4])
                with col1:
                    promote = st.button("Promote to Backlog", key=f"promo_{idx}")
                with col2:
                    delete = st.button("Delete Item", key=f"del_{idx}")
                    
                if promote:
                    # Stash selected promotion item in session state
                    st.session_state.promoting_item = item
                    st.session_state.promoting_idx = idx
                    st.rerun()
                    
                if delete:
                    inbox.pop(idx)
                    save_json_file(INBOX_PATH, inbox)
                    st.success("Item deleted from staging inbox.")
                    st.rerun()
                    
    # Promotion Editor Form
    if "promoting_item" in st.session_state:
        st.divider()
        st.subheader("🛠️ Promote Submission & Edit Details")
        item = st.session_state.promoting_item
        idx = st.session_state.promoting_idx
        
        with st.form("promotion_form"):
            new_title = st.text_input("Vetted Title", value=item["title"])
            new_desc = st.text_area("Vetted Description (Curiosity Question)", value=item["description"])
            new_cat = st.selectbox(
                "Category", 
                ["biology", "lifestyle", "book"], 
                index=["biology", "lifestyle", "book"].index(item["category"])
            )
            
            # Multi-select tags based on tags.json registry
            default_tags = [t for t in item.get("tags", []) if t in TAGS_REGISTRY]
            new_tags = st.multiselect("Standardized Tags", list(TAGS_REGISTRY.keys()), default=default_tags)
            
            new_votes = st.number_input("Starting Votes", value=item.get("votes", 1), min_value=0)
            
            col_f1, col_f2 = st.columns([1, 5])
            with col_f1:
                submit_promotion = st.form_submit_button("Confirm Backlog Entry")
            with col_f2:
                cancel_promotion = st.form_submit_button("Cancel")
                
            if submit_promotion:
                new_slug = slugify(new_title)
                
                # Check for duplicates in backlog
                backlog = load_json_file(BACKLOG_PATH, default_empty=[])
                if any(b["id"] == new_slug for b in backlog):
                    st.error(f"A backlog item with ID '{new_slug}' already exists. Please choose a different title.")
                else:
                    new_backlog_item = {
                        "id": new_slug,
                        "title": new_title,
                        "description": new_desc,
                        "category": new_cat,
                        "votes": int(new_votes),
                        "tags": new_tags or [new_cat],
                        "created_at": datetime.date.today().isoformat() if hasattr(datetime, "date") else "2026-06-24",
                    }
                    backlog.append(new_backlog_item)
                    save_json_file(BACKLOG_PATH, backlog)
                    
                    # Remove from inbox
                    inbox.pop(idx)
                    save_json_file(INBOX_PATH, inbox)
                    
                    st.success(f"[Success] Promoted proposal '{new_slug}' to active backlog.")
                    del st.session_state.promoting_item
                    st.rerun()
                    
            if cancel_promotion:
                del st.session_state.promoting_item
                st.rerun()

# ---------------------------------------------------------
# MODULE 2: Lexicon / Vocabulary Builder
# ---------------------------------------------------------
elif menu == "Lexicon / Vocabulary Builder":
    st.header("📖 Lexicon & Vocabulary Builder")
    st.write(
        "Add or edit entries in `src/vocabulary.json`. "
        "Scan local sources in `src/sources/` to extract verbatim definitions and quotes."
    )
    
    # Load vocabulary database
    vocab = load_json_file(VOCAB_PATH, default_empty={})
    
    col_l1, col_l2 = st.columns([1, 1])
    
    with col_l1:
        st.subheader("Step 1: Extract from Local Sources")
        sources = curator_engine.list_sources()
        if not sources:
            st.warning("No PDF or text files found in `src/sources/`. Drop source documents there to begin.")
            selected_source = None
        else:
            selected_source = st.selectbox("Select Source File", sources)
            
        term_to_search = st.text_input("Enter Acronym / Term to Scan (e.g. AMPK)", value="")
        scan_button = st.button("Scan Source Document")
        
        extracted_quote = ""
        if scan_button and selected_source and term_to_search:
            with st.spinner("Parsing document and scanning text..."):
                text_content = curator_engine.get_file_content(selected_source)
                matches = curator_engine.search_text_for_definitions(text_content, term_to_search)
                
                if not matches:
                    st.info(f"No direct matches found for '{term_to_search}' in {selected_source}.")
                else:
                    st.success(f"Found {len(matches)} mentions in source file.")
                    # Select matching sentence
                    st.markdown("**Verbatim Sentences Found (Direct Quotes):**")
                    for m in matches[:6]:
                        sentence_text = m["sentence"]
                        is_def = "⭐ [Definition]" if m["is_defining"] else ""
                        st.markdown(f"> {sentence_text} {is_def}")
                        if st.button("Use this quote", key=f"use_q_{m['index']}"):
                            st.session_state.selected_quote = sentence_text
                            st.success("Selected verbatim quote.")
                            
    with col_l2:
        st.subheader("Step 2: PubMed Citation Lookup")
        query_to_search = st.text_input("Enter Paper Title or Keywords to Search", value=term_to_search)
        search_pubmed = st.button("Search PubMed")
        
        selected_citation = None
        if search_pubmed and query_to_search:
            with st.spinner("Querying Entrez PubMed E-utilities..."):
                pubmed_results = curator_engine.query_pubmed(query_to_search)
                if not pubmed_results:
                    st.info("No publication matching query found.")
                else:
                    st.markdown("**Select PubMed Reference:**")
                    for p in pubmed_results:
                        st.write(f"- **{p['author_summary']} ({p['year']})** - {p['title']}")
                        st.write(f"  *Journal*: {p['source']} | *DOI*: {p['doi']}")
                        if st.button("Select reference", key=f"ref_{p['pmid']}"):
                            st.session_state.selected_ref = p
                            st.success(f"Linked reference: {p['author_summary']}")
                            
    st.divider()
    st.subheader("Step 3: Define Lexicon Entry")
    
    # Retrieve stashed quote & reference
    quote = st.session_state.get("selected_quote", "")
    ref = st.session_state.get("selected_ref", None)
    
    with st.form("vocab_form"):
        term_name = st.text_input("Canonical Term (e.g. AMPK)", value=term_to_search)
        
        # Taxonomy mapping
        tax_options = ["protein", "molecule", "process", "concept", "organism", "condition", "framework"]
        taxonomy = st.selectbox("Taxonomy Type", tax_options)
        
        aliases_input = st.text_input("Aliases (comma-separated)", value="")
        aliases = [a.strip() for a in aliases_input.split(",") if a.strip()]
        
        definition = st.text_area(
            "Scientific Definition (HBR-style, precise, non-promotional)", 
            placeholder="An energy-sensing cellular enzyme regulating metabolic homeostasis..."
        )
        
        vulgarized_analogy = st.text_area(
            "Vulgarized Analogy (Systems analogy for lay readers)", 
            placeholder="Acts as the cellular fuel gauge, pausing cellular construction work when energy levels run low..."
        )
        
        st.markdown("**Linked Citation Details (Directly Auditable):**")
        citation_text = st.text_area("Vancouver Citation Text", value=ref["citation"] if ref else "")
        citation_link = st.text_input("Citation Link (DOI/PubMed URL)", value=ref["link"] if ref else "")
        defining_quote = st.text_area("Verbatim Defining Quote (verbatim text from source)", value=quote)
        quote_page = st.text_input("Quote Location (e.g. Page 12, Section 3)", value="")
        
        save_vocab = st.form_submit_button("Save to Lexicon Database")
        
        if save_vocab:
            if not term_name or not definition or not vulgarized_analogy or not defining_quote:
                st.error("Error: Term name, definition, vulgarized analogy, and verbatim defining quote are required.")
            else:
                citations_list = []
                if citation_text or citation_link:
                    citations_list.append({
                        "text": citation_text,
                        "link": citation_link,
                        "defining_quote": defining_quote,
                        "quote_page": quote_page
                    })
                    
                vocab[term_name] = {
                    "definition": definition,
                    "vulgarized_analogy": vulgarized_analogy,
                    "taxonomy": taxonomy,
                    "aliases": aliases,
                    "citations": citations_list,
                    "verification_status": "verified_human"
                }
                
                save_json_file(VOCAB_PATH, vocab)
                st.success(f"[Success] Lexicon entry '{term_name}' registered successfully.")
                
                # Clear session state
                if "selected_quote" in st.session_state:
                    del st.session_state.selected_quote
                if "selected_ref" in st.session_state:
                    del st.session_state.selected_ref
                st.rerun()

# ---------------------------------------------------------
# MODULE 3: Draft Bootstrapper
# ---------------------------------------------------------
elif menu == "Draft Bootstrapper":
    st.header("🚀 Draft Bootstrapper")
    st.write(
        "Select a vetted proposal from the backlog, visually map relationships to existing nodes, "
        "and bootstrap a schema-compliant JSON draft."
    )
    
    backlog = load_json_file(BACKLOG_PATH, default_empty=[])
    existing_slugs = get_existing_node_slugs()
    
    if not backlog:
        st.info("The backlog is empty. Vet submissions in the Inbox first to build the backlog queue.")
    else:
        # Selection of backlog item
        options = [f"{b['title']} ({b['category']})" for b in backlog]
        selected_backlog_str = st.selectbox("Select Backlog Item", options)
        selected_idx = options.index(selected_backlog_str)
        item = backlog[selected_idx]
        
        slug = item["id"]
        st.subheader(f"Configure Draft for: '{item['title']}'")
        st.write(f"**Curiosity Question**: {item['description']}")
        st.write(f"**Tags**: {', '.join(item.get('tags', []))}")
        
        # Configure Relationship Edges
        st.markdown("### 🕸️ Relationship Mapping (Graph Edges)")
        st.write("Link this proposed node to existing systems biology circuits:")
        
        if not existing_slugs:
            st.info("No active articles published yet. The first node will have empty edges.")
            edges = []
        else:
            edges = []
            num_edges = st.number_input("Number of relationship edges to add", min_value=0, max_value=5, value=0)
            
            for i in range(num_edges):
                col_e1, col_e2, col_e3 = st.columns([2, 1, 3])
                with col_e1:
                    target = st.selectbox(f"Target Node [{i+1}]", existing_slugs, key=f"target_{i}")
                with col_e2:
                    rel_type = st.selectbox(
                        f"Relationship [{i+1}]", 
                        ["activates", "inhibits", "requires", "implements"], 
                        key=f"rel_{i}"
                    )
                with col_e3:
                    mechanism = st.text_input(
                        f"Molecular Mechanism / Rationale [{i+1}]", 
                        placeholder="phosphorylation of residue Ser-79 pauses activity...",
                        key=f"mech_{i}"
                    )
                    
                if target:
                    edges.append({
                        "target": target,
                        "type": rel_type,
                        "mechanism": mechanism or "Biological feedback regulation."
                    })
                    
        st.divider()
        
        # Bootstrap Execution
        bootstrap_action = st.button("🚀 Bootstrap Draft JSON File")
        if bootstrap_action:
            # Create node JSON structure
            node_data = {
                "type": item["category"],
                "title": item["title"],
                "hook_question": item["description"],
                "takeaway_pill": "1-Min takeaway summary based on evidence (Actionable and direct).",
                "epistemic_rating": {
                    "grade": "Low",
                    "rationale": "GRADE-based evaluation summary of supporting literature.",
                    "debate_sides": [
                        {
                            "position": "Brief statement of Hypothesis A.",
                            "arguments": "Supporting data / trials."
                        }
                    ]
                },
                "tags": item.get("tags", [item["category"]]),
                "reading_modes": {
                    "overview_3min": "A 3-min narrative overview mapping the biological feedback loops. Use bold `**` tags for glossary terms.",
                    "deep_dive": [
                        {
                            "heading": "Molecular Feedback Loops",
                            "body": "Detailed biochemical steps (use bold `**` for vocabulary terms)."
                        }
                    ]
                },
                "edges": edges or [
                    {
                        "target": "target-slug-goes-here",
                        "type": "activates",
                        "mechanism": "How this node influences the target node."
                    }
                ],
                "evidence_table": [
                    {
                        "study": "Author et al., Year",
                        "design": "Study design (e.g., RCT, in vivo)",
                        "sample": "Cohort description (e.g., n=40 adults)",
                        "outcome": "Specific outcome data.",
                        "link": "https://pubmed.ncbi.nlm.nih.gov/XXXXX/"
                    }
                ],
                "bibliography": [
                    {
                        "id": "ref1",
                        "text": "Full Vancouver-style citation.",
                        "link": "Direct DOI or publisher link."
                    }
                ]
            }
            
            # Save file
            os.makedirs(DRAFTS_DIR, exist_ok=True)
            draft_path = os.path.join(DRAFTS_DIR, f"{slug}.json")
            save_json_file(draft_path, node_data)
            
            # Pop from backlog
            backlog.pop(selected_idx)
            save_json_file(BACKLOG_PATH, backlog)
            
            st.success(f"[Success] Generated draft JSON at: `src/nodes/en/drafts/{slug}.json`")
            st.info(f"Vetted proposal '{slug}' has been activated and removed from backlog.")
            st.rerun()
