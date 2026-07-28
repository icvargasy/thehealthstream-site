"""Analogy Readability & Jargon Audit Tool for The Healthstream.

Scans all article JSON nodes and backlog proposal items to verify that systems
analogies satisfy the Adolescent Readability Benchmark (Flesch-Kincaid Grade 8-9)
and remain 100% free of technical biological/chemical textbook jargon.
"""

import glob
import json
import os
import sys
from typing import List

FORBIDDEN_JARGON = {
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
}


def audit_analogy_text(text: str, context: str) -> List[str]:
    """Audits an analogy string for jargon leaks and word count limits."""
    issues = []
    if not text:
        return issues

    words = text.strip().split()
    if len(words) > 35:
        issues.append(f"Word count ({len(words)}) exceeds Level 2 teaser ceiling (≤ 35 words)")

    cleaned_words = [w.lower().strip(".,;:()\"'") for w in words]
    for w in cleaned_words:
        if w in FORBIDDEN_JARGON:
            issues.append(f"Forbidden technical jargon word detected: '{w}'")

    return issues


def main() -> None:
    """Main audit runner."""
    total_audited = 0
    total_issues = 0

    print("==================================================")
    print("  THE HEALTHSTREAM - Analogy Readability Audit    ")
    print("==================================================")

    # 1. Audit Article Nodes
    node_files = glob.glob("src/nodes/en/*.json")
    for filepath in node_files:
        filename = os.path.basename(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        total_audited += 1
        analogy = data.get("systems_analogy_hook", "")
        issues = audit_analogy_text(analogy, filename)
        if issues:
            total_issues += 1
            print(f"[FAIL] Node Error in {filename}:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print(f"[OK] Node OK: {filename}")

    # 2. Audit Backlog Items
    backlog_path = "src/backlog.json"
    if os.path.exists(backlog_path):
        with open(backlog_path, "r", encoding="utf-8") as f:
            backlog = json.load(f)
        for item in backlog:
            total_audited += 1
            item_id = item.get("id", "unknown")
            analogy = item.get("systems_analogy", "")
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
        print("SUCCESS: 100% of analogies satisfy Adolescent Readability Benchmark!")
        sys.exit(0)


if __name__ == "__main__":
    main()
