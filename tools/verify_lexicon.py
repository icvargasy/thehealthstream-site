"""Lexicon consistency auditor for The Healthstream static site build chain.

This script scans vocabulary definitions, article node descriptions, and backlog entries
to identify unregistered bold markers, missing lexicon references, and potential candidates.
"""

import os
import json
import re
from typing import Dict, Any, List, Set


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

    # Build jargon lookup maps
    jargon_map = load_jargon_map(vocabulary)
    all_terms = set(vocabulary.keys())
    used_terms: Set[str] = set()

    unregistered_bold_count = 0
    candidate_links_count = 0

    print(f"Loaded {len(vocabulary)} active lexicon terms.")
    print(f"Loaded {len(backlog)} backlog pipeline items.")

    # 2. Audit Vocabulary Definitions
    print("\n--- Auditing Glossary Definitions ---")
    for term, details in vocabulary.items():
        definition = details.get("definition", "")
        analogy = details.get("vulgarized_analogy", "")
        
        # Check bold elements in definition
        bolded = extract_bold_phrases(definition) + extract_bold_phrases(analogy)
        for phrase in bolded:
            phrase_clean = phrase.strip().lower()
            # Try matching singulars/plurals roughly if exact match fails
            matched = False
            for match_cand in [phrase_clean, phrase_clean.rstrip("s"), phrase_clean.rstrip("es")]:
                if match_cand in jargon_map:
                    canonical = jargon_map[match_cand]
                    used_terms.add(canonical)
                    matched = True
                    break
            if not matched:
                print(f"[Warning] Unregistered bold phrase '**{phrase}**' in definition of '{term}'")
                unregistered_bold_count += 1

    # 3. Audit Article Content Nodes
    print("\n--- Auditing Article Content Nodes ---")
    if os.path.exists(nodes_dir):
        for file_name in os.listdir(nodes_dir):
            if file_name.endswith(".json"):
                file_path = os.path.join(nodes_dir, file_name)
                with open(file_path, "r", encoding="utf-8") as f:
                    node = json.load(f)
                
                title = node.get("title", file_name)
                # Combine all text fields in reading modes
                rm = node.get("reading_modes", {})
                overview = rm.get("overview_3min", "")
                deep_dive_text = ""
                for section in rm.get("deep_dive", []):
                    deep_dive_text += " " + section.get("body", "")
                
                combined_text = overview + deep_dive_text
                bolded = extract_bold_phrases(combined_text)
                
                for phrase in bolded:
                    phrase_clean = phrase.strip().lower()
                    matched = False
                    for match_cand in [phrase_clean, phrase_clean.rstrip("s"), phrase_clean.rstrip("es")]:
                        if match_cand in jargon_map:
                            canonical = jargon_map[match_cand]
                            used_terms.add(canonical)
                            matched = True
                            break
                    if not matched:
                        print(f"[Warning] Unregistered bold phrase '**{phrase}**' in article '{title}' ({file_name})")
                        unregistered_bold_count += 1

    # 4. Audit Backlog Pipeline
    print("\n--- Auditing Backlog Pipeline ---")
    for item in backlog:
        title = item.get("title", "Untitled Pipeline Item")
        desc = item.get("description", "")
        bolded = extract_bold_phrases(desc)
        
        for phrase in bolded:
            phrase_clean = phrase.strip().lower()
            matched = False
            for match_cand in [phrase_clean, phrase_clean.rstrip("s"), phrase_clean.rstrip("es")]:
                if match_cand in jargon_map:
                    canonical = jargon_map[match_cand]
                    used_terms.add(canonical)
                    matched = True
                    break
            if not matched:
                print(f"[Warning] Unregistered bold phrase '**{phrase}**' in pipeline item '{title}'")
                unregistered_bold_count += 1

    # 5. Summary of Orphan Lexicon Terms
    print("\n--- Orphan Lexicon Terms Audit ---")
    orphans = all_terms - used_terms
    # Keep some core terms exempt if they are meant as basic glossary references
    exemption_list = {
        "GRADE", "Evidence Grade", "healthspan", "metabolism", "physiological", "pathology",
        "upregulate", "downregulate", "covalent", "synthetic", "biochemical", "DNA", "RNA", "protein"
    }
    true_orphans = orphans - exemption_list
    if true_orphans:
        print(f"Found {len(true_orphans)} orphan glossary terms (defined but never referenced inside other definitions/articles):")
        for term in sorted(true_orphans):
            print(f"  - {term}")
    else:
        print("No non-exempt orphan lexicon terms found.")

    print("\n" + "=" * 60)
    print("                     AUDIT RESULT SUMMARY                    ")
    print("=" * 60)
    print(f"Unregistered bold phrases: {unregistered_bold_count}")
    print(f"Orphan lexicon terms:      {len(true_orphans)}")
    if unregistered_bold_count == 0:
        print("\n[Success] Lexicon audit passed with clean references!")
    else:
        print("\n[Fix Required] Please register or correct the unregistered bold phrases above.")
    print("=" * 60)


if __name__ == "__main__":
    main()
