"""Lexicon consistency auditor for The Healthstream static site build chain.

This script scans vocabulary definitions, article node descriptions, and backlog entries
to identify unregistered bold markers, verify formatting consistency, and locate genuine orphans.
"""

import os
import json
import re
import sys
from typing import Dict, Any, List, Set, Tuple

_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

from compiler.utils import extract_searchable_text
from compiler.linker import build_lexicon_matcher


def extract_bold_phrases(text: str) -> List[str]:
    """Finds all phrases formatted as **phrase** in markdown text."""
    if not text:
        return []
    return re.findall(r"\*\*([^*]+)\*\*", text)


def load_jargon_map(vocabulary: Dict[str, Any]) -> Dict[str, str]:
    """Builds a case-insensitive map from phrase/alias to canonical term key."""
    jargon_map = {}
    for term, details in vocabulary.items():
        jargon_map[term.lower()] = term
        for alias in details.get("aliases", []):
            jargon_map[alias.lower()] = term
    return jargon_map


def check_formatting(term: str, details: Dict[str, Any]) -> int:
    """Enforces strict consistent formatting on vocabulary items.

    Returns:
        The count of formatting warnings/errors found.
    """
    warnings = 0
    required_fields = ["definition", "vulgarized_analogy", "taxonomy", "aliases", "citations", "verification_status"]
    for field in required_fields:
        if field not in details:
            print(f"[Warning] Vocabulary term '{term}' is missing required field '{field}'")
            warnings += 1

    definition = details.get("definition", "")
    if definition:
        def_stripped = definition.strip("*_`\"' ")
        if def_stripped:
            if not def_stripped[0].isupper() and def_stripped[0].isalpha():
                print(f"[Warning] Definition for '{term}' should start with a capital letter: '{definition[:30]}...'")
                warnings += 1
            if not def_stripped.endswith(".") and not def_stripped.endswith("?"):
                print(f"[Warning] Definition for '{term}' should end with a period: '{definition[-15:]}'")
                warnings += 1

    analogy = details.get("vulgarized_analogy", "")
    if analogy:
        anal_stripped = analogy.strip("*_`\"' ")
        if anal_stripped:
            if not anal_stripped[0].isupper() and anal_stripped[0].isalpha():
                print(f"[Warning] Analogy for '{term}' should start with a capital letter: '{analogy[:30]}...'")
                warnings += 1
            if not anal_stripped.endswith("."):
                print(f"[Warning] Analogy for '{term}' should end with a period: '{analogy[-15:]}'")
                warnings += 1

    citations = details.get("citations", [])
    for idx, cit in enumerate(citations):
        if not isinstance(cit, dict):
            print(f"[Warning] Citation {idx} in '{term}' must be a dictionary")
            warnings += 1
            continue
        text = cit.get("text", "")
        link = cit.get("link", "")
        if not text:
            print(f"[Warning] Citation {idx} in '{term}' is missing 'text'")
            warnings += 1
        if not link:
            print(f"[Warning] Citation {idx} in '{term}' is missing 'link'")
            warnings += 1
        elif not (link.startswith("http://") or link.startswith("https://")):
            print(f"[Warning] Citation {idx} link in '{term}' is not a valid HTTP URL: '{link}'")
            warnings += 1

    return warnings


def main() -> None:
    print("=" * 60)
    print("        THE HEALTHSTREAM - LEXICON CONSISTENCY AUDIT        ")
    print("=" * 60)

    # 1. Load data
    vocab_path = "src/vocabulary.json"
    backlog_path = "src/backlog.json"
    nodes_dir = "src/nodes/en"

    if not os.path.exists(vocab_path):
        print(f"[Error] Vocabulary file not found at: {vocab_path}")
        return

    with open(vocab_path, "r", encoding="utf-8") as f:
        vocabulary = json.load(f)

    backlog = []
    if os.path.exists(backlog_path):
        with open(backlog_path, "r", encoding="utf-8") as f:
            backlog = json.load(f)

    # Build jargon lookup maps and compiled dual-matcher
    jargon_map = load_jargon_map(vocabulary)
    all_terms = set(vocabulary.keys())
    used_terms: Set[str] = set()

    unregistered_bold_count = 0
    formatting_warnings = 0

    matcher = build_lexicon_matcher(vocabulary)

    def scan_text_for_terms(text: str, current_term: str = "") -> None:
        if not text:
            return
        if current_term:
            t_matcher = build_lexicon_matcher(vocabulary, exclude_term=current_term)
            matched = t_matcher.search_in_text(text)
        else:
            matched = matcher.search_in_text(text)
        used_terms.update(matched)

    print(f"Loaded {len(vocabulary)} active lexicon terms.")
    print(f"Loaded {len(backlog)} backlog pipeline items.")

    # 2. Audit Vocabulary Definitions & Format
    print("\n--- Auditing Glossary Definitions & Formatting ---")
    for term, details in vocabulary.items():
        definition = details.get("definition", "")
        analogy = details.get("vulgarized_analogy", "")

        # Format Check
        formatting_warnings += check_formatting(term, details)

        # Check bold elements in definition (unregistered bold check)
        bolded = extract_bold_phrases(definition) + extract_bold_phrases(analogy)
        for phrase in bolded:
            phrase_clean = phrase.strip().lower()
            matched = False
            for match_cand in [phrase_clean, phrase_clean.rstrip("s"), phrase_clean.rstrip("es")]:
                if match_cand in jargon_map:
                    matched = True
                    break
            if not matched:
                print(f"[Warning] Unregistered bold phrase '**{phrase}**' in definition of '{term}'")
                unregistered_bold_count += 1

        # Scan plain text definition and citations for references
        full_vocab_text = extract_searchable_text(details)
        scan_text_for_terms(full_vocab_text, current_term=term)

    # 3. Audit Article Content Nodes
    print("\n--- Auditing Article Content Nodes ---")
    if os.path.exists(nodes_dir):
        for file_name in os.listdir(nodes_dir):
            if file_name.endswith(".json"):
                file_path = os.path.join(nodes_dir, file_name)
                with open(file_path, "r", encoding="utf-8") as f:
                    node = json.load(f)

                title = node.get("title", file_name)
                full_node_text = extract_searchable_text(node)

                # Check unregistered bold elements
                bolded = extract_bold_phrases(full_node_text)
                for phrase in bolded:
                    phrase_clean = phrase.strip().lower()
                    matched = False
                    for match_cand in [phrase_clean, phrase_clean.rstrip("s"), phrase_clean.rstrip("es")]:
                        if match_cand in jargon_map:
                            matched = True
                            break
                    if not matched:
                        print(f"[Warning] Unregistered bold phrase '**{phrase}**' in article '{title}' ({file_name})")
                        unregistered_bold_count += 1

                # Scan text for references
                scan_text_for_terms(full_node_text)

    # 4. Audit Backlog Pipeline
    print("\n--- Auditing Backlog Pipeline ---")
    for item in backlog:
        title = item.get("title", "Untitled Pipeline Item")
        full_item_text = extract_searchable_text(item)

        # Check unregistered bold elements
        bolded = extract_bold_phrases(full_item_text)
        for phrase in bolded:
            phrase_clean = phrase.strip().lower()
            matched = False
            for match_cand in [phrase_clean, phrase_clean.rstrip("s"), phrase_clean.rstrip("es")]:
                if match_cand in jargon_map:
                    matched = True
                    break
            if not matched:
                print(f"[Warning] Unregistered bold phrase '**{phrase}**' in pipeline item '{title}'")
                unregistered_bold_count += 1

        # Scan text for references
        scan_text_for_terms(full_item_text)

    # 5. Summary of Orphan Lexicon Terms (Zero-Tolerance Policy: No Exemption Lists)
    print("\n--- Orphan Lexicon Terms Audit ---")
    orphans = all_terms - used_terms
    if orphans:
        print(f"Found {len(orphans)} orphan glossary terms (defined but never referenced inside other definitions/articles):")
        for term in sorted(orphans):
            print(f"  - {term}")
    else:
        print("No orphan lexicon terms found. All 124 terms have active references.")

    print("\n" + "=" * 60)
    print("                     AUDIT RESULT SUMMARY                    ")
    print("=" * 60)
    print(f"Unregistered bold phrases: {unregistered_bold_count}")
    print(f"Formatting inconsistencies: {formatting_warnings}")
    print(f"Orphan lexicon terms:      {len(orphans)}")
    if unregistered_bold_count == 0 and formatting_warnings == 0 and len(orphans) == 0:
        print("\n[Success] Lexicon audit passed with clean references!")
    else:
        print("\n[Fix Required] Please register/correct bold phrases, fix formatting, or link orphan terms above.")
    print("=" * 60)


if __name__ == "__main__":
    main()
