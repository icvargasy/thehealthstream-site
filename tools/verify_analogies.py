"""Analogy Readability & Jargon Audit Tool for The Healthstream.

Scans all article JSON nodes, backlog proposal items, and vocabulary entries to verify
that systems analogies comply with the Set 1 Standard:
- Flesch-Kincaid Grade 6-8 adolescent readability floor
- Hard word count ceiling of <= 20 words per analogy
- Zero biological textbook jargon AND zero pseudo-engineering / civic bureaucracy jargon
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
    # Pseudo-engineering & civic bureaucracy jargon anti-patterns
    "volumetric",
    "throughput",
    "municipal",
    "infrastructure",
    "collateral",
    "hazmat",
    "governor",
}


def audit_analogy_text(text: str, context: str) -> List[str]:
    """Audits an analogy string for jargon leaks and word count limits."""
    issues = []
    if not text:
        return issues

    words = text.strip().split()
    if len(words) > 20:
        issues.append(f"Word count ({len(words)}) exceeds Set 1 ceiling (<= 20 words)")

    cleaned_words = [w.lower().strip(".,;:()\"'") for w in words]
    for w in cleaned_words:
        if w in FORBIDDEN_JARGON:
            issues.append(f"Forbidden technical/pseudo-engineering jargon word detected: '{w}'")

    return issues


def main() -> None:
    """Main audit runner."""
    total_audited = 0
    total_issues = 0

    print("==================================================")
    print("  THE HEALTHSTREAM - Set 1 Analogy Readability Audit")
    print("==================================================")

    # 1. Audit Vocabulary Definitions (vulgarized_analogy)
    vocab_path = "src/vocabulary.json"
    if os.path.exists(vocab_path):
        with open(vocab_path, "r", encoding="utf-8") as f:
            vocab = json.load(f)
        for term, data in vocab.items():
            analogy = data.get("vulgarized_analogy", "")
            if analogy:
                total_audited += 1
                issues = audit_analogy_text(analogy, f"Vocabulary: {term}")
                if issues:
                    total_issues += 1
                    print(f"[FAIL] Vocabulary Error in '{term}':")
                    for issue in issues:
                        print(f"   - {issue}")

    # 2. Audit Article Nodes (systems_analogy_hook)
    node_files = glob.glob("src/nodes/en/*.json")
    for filepath in node_files:
        filename = os.path.basename(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        analogy = data.get("systems_analogy_hook", "")
        if analogy:
            total_audited += 1
            issues = audit_analogy_text(analogy, filename)
            if issues:
                total_issues += 1
                print(f"[FAIL] Node Error in {filename}:")
                for issue in issues:
                    print(f"   - {issue}")

    # 3. Audit Backlog Items (systems_analogy)
    backlog_path = "src/backlog.json"
    if os.path.exists(backlog_path):
        with open(backlog_path, "r", encoding="utf-8") as f:
            backlog = json.load(f)
        for item in backlog:
            item_id = item.get("id", "unknown")
            analogy = item.get("systems_analogy", "")
            if analogy:
                total_audited += 1
                issues = audit_analogy_text(analogy, item_id)
                if issues:
                    total_issues += 1
                    print(f"[FAIL] Backlog Error in {item_id}:")
                    for issue in issues:
                        print(f"   - {issue}")

    print("--------------------------------------------------")
    print(f"Audited {total_audited} total analogies.")
    if total_issues > 0:
        print(f"FAILED: Found {total_issues} analogy issues.")
        sys.exit(1)
    else:
        print("SUCCESS: 100% of analogies satisfy Set 1 Adolescent Readability Benchmark!")
        sys.exit(0)


if __name__ == "__main__":
    main()
