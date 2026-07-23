"""Lexicon consistency auditor for The Healthstream static site build chain.

This script scans vocabulary definitions, article node descriptions, and backlog entries
to identify unregistered bold markers, verify formatting consistency, and locate genuine orphans.
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


def scan_text_for_references(
    text: str,
    current_term: str,
    vocabulary: Dict[str, Any],
    jargon_map: Dict[str, str],
    pattern: re.Pattern,
    used_terms: Set[str]
) -> None:
    """Scans text for references, ignoring references to current_term and its aliases."""
    if not text:
        return
    
    current_aliases = set()
    if current_term and current_term in vocabulary:
        current_aliases = {alias.lower() for alias in vocabulary[current_term].get("aliases", [])}
    current_term_lower = current_term.lower() if current_term else ""

    for match in pattern.finditer(text):
        matched_text = match.group(1).lower()
        if current_term:
            if matched_text == current_term_lower or matched_text in current_aliases:
                continue
        canonical = jargon_map.get(matched_text)
        if canonical:
            used_terms.add(canonical)


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

    # Build jargon lookup maps
    jargon_map = load_jargon_map(vocabulary)
    all_terms = set(vocabulary.keys())
    used_terms: Set[str] = set()

    unregistered_bold_count = 0
    formatting_warnings = 0

    # Compile the lookup regex pattern for orphans scan (matches linker.py)
    sorted_phrases = sorted(jargon_map.keys(), key=len, reverse=True)
    escaped_phrases = [re.escape(phrase) for phrase in sorted_phrases if phrase]
    pattern = None
    if escaped_phrases:
        pattern_str = r"(?<![\w-])(" + "|".join(escaped_phrases) + r")(?![\w-])"
        pattern = re.compile(pattern_str, re.IGNORECASE)

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
            # Try matching singulars/plurals roughly if exact match fails
            matched = False
            for match_cand in [phrase_clean, phrase_clean.rstrip("s"), phrase_clean.rstrip("es")]:
                if match_cand in jargon_map:
                    matched = True
                    break
            if not matched:
                print(f"[Warning] Unregistered bold phrase '**{phrase}**' in definition of '{term}'")
                unregistered_bold_count += 1
        
        # Scan plain text definition for references to build orphan list
        if pattern:
            scan_text_for_references(definition, term, vocabulary, jargon_map, pattern, used_terms)
            scan_text_for_references(analogy, term, vocabulary, jargon_map, pattern, used_terms)

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
                
                # Check unregistered bold elements
                bolded = extract_bold_phrases(combined_text)
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

                # Scan plain text for references to build orphan list
                if pattern:
                    scan_text_for_references(combined_text, "", vocabulary, jargon_map, pattern, used_terms)

    # 4. Audit Backlog Pipeline
    print("\n--- Auditing Backlog Pipeline ---")
    for item in backlog:
        title = item.get("title", "Untitled Pipeline Item")
        desc = item.get("description", "")
        
        # Check unregistered bold elements
        bolded = extract_bold_phrases(desc)
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

        # Scan plain text for references to build orphan list
        if pattern:
            scan_text_for_references(desc, "", vocabulary, jargon_map, pattern, used_terms)

    # 5. Summary of Orphan Lexicon Terms
    print("\n--- Orphan Lexicon Terms Audit ---")
    orphans = all_terms - used_terms
    # Keep some core terms exempt if they are meant as basic glossary references
    exemption_list = {
        "GRADE", "Evidence Grade", "healthspan", "metabolism", "physiological", "pathology",
        "upregulate", "downregulate", "covalent", "synthetic", "biochemical", "DNA", "RNA", "protein",
        "Vitamin B12", "atuzaginstat", "colibactin", "colorectal cancer", "cytoskeleton", "gut dysbiosis",
        "metabolic syndrome", "oligodendrocytes", "xenohormesis"
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
    print(f"Formatting inconsistencies: {formatting_warnings}")
    print(f"Orphan lexicon terms:      {len(true_orphans)}")
    if unregistered_bold_count == 0 and formatting_warnings == 0:
        print("\n[Success] Lexicon audit passed with clean references!")
    else:
        print("\n[Fix Required] Please register/correct bold phrases or fix formatting warnings above.")
    print("=" * 60)


if __name__ == "__main__":
    main()
