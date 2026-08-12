"""Dynamic Master Copy Quality Linter for The Healthstream (Minimalist Edition).

Scans all article JSON nodes, backlog proposal items, and vocabulary entries to verify
that all card teasers and lexicon copy satisfy The Healthstream Master Copy Standard:
- Hard word count ceilings (Hook <= 15, Analogy <= 20, Pill <= 25, Definition <= 20)
- Single-sentence constraint (no semicolons or multiple sentences)
- Dynamic Lexicon Jargon Inspection (extracts acronyms & long terms from src/vocabulary.json)
- 1-line biological suffix regex
"""

import glob
import json
import os
import re
import sys
from typing import List, Set

# 1-line biological suffix regex (excluding non-bio everyday words)
BIO_SUFFIX_REGEX = re.compile(
    r"\b(?!(?:home|disease|release|database|metronome|increase|decrease|phase|base|case)\b)\w+(?:itis|cyte|phage|lase|nase|tase|dase|rase|sase|genic|vascular|tropic|blast|emia|pathic)\b",
    re.IGNORECASE,
)

# Common general terms to skip if present in vocabulary keys
COMMON_EXCLUSIONS = {
    "healthspan", "lifestyle", "exercise", "nutrition", "aging", "dementia",
    "grade", "antioxidant", "polyphenol", "pathology", "disease",
}


def load_vocab_jargon() -> Set[str]:
    """Extracts uppercase acronyms and long scientific terms from vocabulary.json dynamically."""
    jargon_set = set()
    vocab_path = "src/vocabulary.json"
    if not os.path.exists(vocab_path):
        return jargon_set

    with open(vocab_path, "r", encoding="utf-8") as f:
        vocab = json.load(f)

    for term_name in vocab:
        t_clean = term_name.strip()
        t_lower = t_clean.lower()
        if t_lower in COMMON_EXCLUSIONS:
            continue

        # Add uppercase acronyms (AMPK, DHA, SCFA) or long scientific single-words (>= 8 chars)
        if t_clean.isupper() or (len(t_clean) >= 8 and " " not in t_clean):
            jargon_set.add(t_lower)

        # Add aliases that fit the same rule
        for alias in vocab[term_name].get("aliases", []):
            a_clean = alias.strip()
            a_lower = a_clean.lower()
            if a_lower not in COMMON_EXCLUSIONS:
                if a_clean.isupper() or (len(a_clean) >= 8 and " " not in a_clean):
                    jargon_set.add(a_lower)

    return jargon_set


def audit_copy_component(
    text: str,
    label: str,
    max_words: int,
    jargon_set: Set[str],
    check_jargon: bool = True,
) -> List[str]:
    """Audits a copy string for word limits, 1-sentence rule, and dynamic science jargon."""
    issues = []
    if not text:
        return issues

    raw_text = text.strip()
    words = raw_text.split()

    # 1. Single Sentence Check (no semicolons or multiple sentence endings)
    if ";" in raw_text:
        issues.append(f"Contains semicolon in {label}")
    sentence_delimiters = re.findall(r"[.!?]+", raw_text)
    if len(sentence_delimiters) > 1 and not raw_text.endswith("..."):
        issues.append(f"Contains multiple sentences in {label}")

    # 2. Hard Word Count Ceiling
    if len(words) > max_words:
        issues.append(f"Word count ({len(words)}) exceeds ceiling for {label} (<= {max_words} words)")

    # 3. Dynamic Jargon & Biological Suffix Inspection
    if check_jargon:
        for j_term in jargon_set:
            pattern = r"\b" + re.escape(j_term) + r"\b"
            if re.search(pattern, raw_text, re.IGNORECASE):
                issues.append(f"Forbidden scientific jargon term: '{j_term}' in {label}")

        suffix_matches = BIO_SUFFIX_REGEX.findall(raw_text)
        if suffix_matches:
            issues.append(f"Forbidden biological suffix term: {suffix_matches} in {label}")

    return issues


def main() -> None:
    """Main dynamic copy quality audit runner."""
    total_audited = 0
    total_issues = 0

    print("==================================================")
    print("  THE HEALTHSTREAM - Dynamic Copy Quality Audit   ")
    print("==================================================")

    # 1. Dynamically Load Lexicon Jargon Terms & Aliases
    jargon_set = load_vocab_jargon()
    print(f"Loaded {len(jargon_set)} dynamic science jargon terms from Lexicon.")
    print("--------------------------------------------------")

    # 2. Audit Vocabulary Entries
    vocab_path = "src/vocabulary.json"
    if os.path.exists(vocab_path):
        with open(vocab_path, "r", encoding="utf-8") as f:
            vocab = json.load(f)
        for term, data in vocab.items():
            analogy = data.get("vulgarized_analogy", "")
            if analogy:
                total_audited += 1
                entry_jargon = jargon_set - {term.lower().strip()}
                issues = audit_copy_component(
                    analogy,
                    f"Vocabulary Analogy '{term}'",
                    max_words=20,
                    jargon_set=entry_jargon,
                    check_jargon=True,
                )
                if issues:
                    total_issues += 1
                    print(f"[FAIL] Vocabulary Error in '{term}':")
                    for issue in issues:
                        print(f"   - {issue}")

    # 3. Audit Published Article Nodes
    node_files = glob.glob("src/nodes/en/*.json")
    for filepath in node_files:
        filename = os.path.basename(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Hook Question (<= 15 words)
        hook_q = data.get("hook_question", "")
        if hook_q:
            total_audited += 1
            issues = audit_copy_component(
                hook_q,
                f"Hook Question in {filename}",
                max_words=15,
                jargon_set=jargon_set,
                check_jargon=True,
            )
            if issues:
                total_issues += 1
                print(f"[FAIL] Node Hook Error in {filename}:")
                for issue in issues:
                    print(f"   - {issue}")

        # Systems Analogy Hook (<= 20 words)
        analogy = data.get("systems_analogy_hook", "")
        if analogy:
            total_audited += 1
            issues = audit_copy_component(
                analogy,
                f"Analogy Hook in {filename}",
                max_words=20,
                jargon_set=jargon_set,
                check_jargon=True,
            )
            if issues:
                total_issues += 1
                print(f"[FAIL] Node Analogy Error in {filename}:")
                for issue in issues:
                    print(f"   - {issue}")

        # Takeaway Pill (<= 25 words)
        pill = data.get("takeaway_pill", "")
        if pill:
            total_audited += 1
            issues = audit_copy_component(
                pill,
                f"Takeaway Pill in {filename}",
                max_words=25,
                jargon_set=jargon_set,
                check_jargon=False,
            )
            if issues:
                total_issues += 1
                print(f"[FAIL] Node Pill Error in {filename}:")
                for issue in issues:
                    print(f"   - {issue}")

    # 4. Audit Backlog Items
    backlog_path = "src/backlog.json"
    if os.path.exists(backlog_path):
        with open(backlog_path, "r", encoding="utf-8") as f:
            backlog = json.load(f)
        for item in backlog:
            item_id = item.get("id", "unknown")

            # Hook Question (<= 15 words)
            hook_q = item.get("hook_question", "")
            if hook_q:
                total_audited += 1
                issues = audit_copy_component(
                    hook_q,
                    f"Hook Question in backlog {item_id}",
                    max_words=15,
                    jargon_set=jargon_set,
                    check_jargon=True,
                )
                if issues:
                    total_issues += 1
                    print(f"[FAIL] Backlog Hook Error in {item_id}:")
                    for issue in issues:
                        print(f"   - {issue}")

            # Systems Analogy (<= 20 words)
            analogy = item.get("systems_analogy", "")
            if analogy:
                total_audited += 1
                issues = audit_copy_component(
                    analogy,
                    f"Systems Analogy in backlog {item_id}",
                    max_words=20,
                    jargon_set=jargon_set,
                    check_jargon=True,
                )
                if issues:
                    total_issues += 1
                    print(f"[FAIL] Backlog Analogy Error in {item_id}:")
                    for issue in issues:
                        print(f"   - {issue}")

            # Takeaway Pill (<= 25 words)
            pill = item.get("takeaway_pill", "")
            if pill:
                total_audited += 1
                issues = audit_copy_component(
                    pill,
                    f"Takeaway Pill in backlog {item_id}",
                    max_words=25,
                    jargon_set=jargon_set,
                    check_jargon=False,
                )
                if issues:
                    total_issues += 1
                    print(f"[FAIL] Backlog Pill Error in {item_id}:")
                    for issue in issues:
                        print(f"   - {issue}")

    print("--------------------------------------------------")
    print(f"Audited {total_audited} total copy elements.")
    if total_issues > 0:
        print(f"FAILED: Found {total_issues} copy quality issues.")
        sys.exit(1)
    else:
        print("SUCCESS: 100% of copy satisfies Dynamic Master Copy Standard!")
        sys.exit(0)


if __name__ == "__main__":
    main()
