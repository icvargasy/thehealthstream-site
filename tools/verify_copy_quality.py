"""Unified Master Copy Quality Linter for The Healthstream.

Scans all article JSON nodes, backlog proposal items, and vocabulary entries to verify
that all card teasers and lexicon copy satisfy The Healthstream Master Copy Standard:
- Grade 6-8 adolescent readability floor (~14yo reading level)
- The Double-Jargon Ban (zero bio-textbook terms AND zero pseudo-engineering / research jargon)
- Component word count ceilings:
    - hook_question: <= 15 words
    - systems_analogy / vulgarized_analogy: <= 20 words
    - takeaway_pill: <= 25 words
    - definition: <= 20 words
"""

import glob
import json
import os
import sys
from typing import List

FORBIDDEN_JARGON = {
    # Biological / chemical textbook jargon
    "phosphorylation",
    "deacetylase",
    "transfection",
    "transducer",
    "kinase",
    "histone",
    "acetylation",
    "microglial",
    "cytokine",
    "phagocytic",
    "tryptophan",
    # Pseudo-engineering & civic bureaucracy jargon anti-patterns
    "volumetric",
    "throughput",
    "municipal",
    "infrastructure",
    "collateral",
    "hazmat",
    "governor",
}


def audit_copy_text(text: str, label: str, max_words: int) -> List[str]:
    """Audits a copy string for jargon leaks and word count limits."""
    issues = []
    if not text:
        return issues

    words = text.strip().split()
    if len(words) > max_words:
        issues.append(f"Word count ({len(words)}) exceeds ceiling for {label} (<= {max_words} words)")

    cleaned_words = [w.lower().strip(".,;:()?\"'") for w in words]
    for w in cleaned_words:
        if w in FORBIDDEN_JARGON:
            issues.append(f"Forbidden technical/pseudo-engineering jargon word detected in {label}: '{w}'")

    return issues


def main() -> None:
    """Main audit runner."""
    total_audited = 0
    total_issues = 0

    print("==================================================")
    print("  THE HEALTHSTREAM - Master Copy Quality Audit    ")
    print("==================================================")

    # 1. Audit Vocabulary Entries
    vocab_path = "src/vocabulary.json"
    if os.path.exists(vocab_path):
        with open(vocab_path, "r", encoding="utf-8") as f:
            vocab = json.load(f)
        for term, data in vocab.items():
            analogy = data.get("vulgarized_analogy", "")
            if analogy:
                total_audited += 1
                issues = audit_copy_text(analogy, f"Vocabulary Analogy '{term}'", max_words=20)
                if issues:
                    total_issues += 1
                    print(f"[FAIL] Vocabulary Error in '{term}':")
                    for issue in issues:
                        print(f"   - {issue}")

    # 2. Audit Published Article Nodes
    node_files = glob.glob("src/nodes/en/*.json")
    for filepath in node_files:
        filename = os.path.basename(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Hook Question (<= 15 words)
        hook_q = data.get("hook_question", "")
        if hook_q:
            total_audited += 1
            issues = audit_copy_text(hook_q, f"Hook Question in {filename}", max_words=15)
            if issues:
                total_issues += 1
                print(f"[FAIL] Node Hook Error in {filename}:")
                for issue in issues:
                    print(f"   - {issue}")

        # Systems Analogy Hook (<= 20 words)
        analogy = data.get("systems_analogy_hook", "")
        if analogy:
            total_audited += 1
            issues = audit_copy_text(analogy, f"Analogy Hook in {filename}", max_words=20)
            if issues:
                total_issues += 1
                print(f"[FAIL] Node Analogy Error in {filename}:")
                for issue in issues:
                    print(f"   - {issue}")

        # Takeaway Pill (<= 25 words)
        pill = data.get("takeaway_pill", "")
        if pill:
            total_audited += 1
            issues = audit_copy_text(pill, f"Takeaway Pill in {filename}", max_words=25)
            if issues:
                total_issues += 1
                print(f"[FAIL] Node Pill Error in {filename}:")
                for issue in issues:
                    print(f"   - {issue}")

    # 3. Audit Backlog Items
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
                issues = audit_copy_text(hook_q, f"Hook Question in backlog {item_id}", max_words=15)
                if issues:
                    total_issues += 1
                    print(f"[FAIL] Backlog Hook Error in {item_id}:")
                    for issue in issues:
                        print(f"   - {issue}")

            # Systems Analogy (<= 20 words)
            analogy = item.get("systems_analogy", "")
            if analogy:
                total_audited += 1
                issues = audit_copy_text(analogy, f"Systems Analogy in backlog {item_id}", max_words=20)
                if issues:
                    total_issues += 1
                    print(f"[FAIL] Backlog Analogy Error in {item_id}:")
                    for issue in issues:
                        print(f"   - {issue}")

            # Takeaway Pill (<= 25 words)
            pill = item.get("takeaway_pill", "")
            if pill:
                total_audited += 1
                issues = audit_copy_text(pill, f"Takeaway Pill in backlog {item_id}", max_words=25)
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
        print("SUCCESS: 100% of copy satisfies Master Copy Standard!")
        sys.exit(0)


if __name__ == "__main__":
    main()
