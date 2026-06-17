#!/usr/bin/env python3
"""CLI tool to programmatically bootstrap new article entries from the backlog pipeline.

Reads metadata from the backlog ledger, generates a schema-compliant draft,
and removes the activated item from the pipeline.
"""

import json
import os
import sys
from typing import Any, Dict, List


def load_json_file(file_path: str) -> Any:
    """Loads a JSON file safely.

    Args:
        file_path: Path to the JSON file.

    Returns:
        Parsed JSON content.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file contains invalid JSON.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Backlog file missing at: {file_path}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON content in: {file_path}") from e


def save_json_file(file_path: str, data: Any) -> None:
    """Saves data to a JSON file.

    Args:
        file_path: Path to write the JSON file.
        data: Data to serialize.

    Raises:
        IOError: If the file cannot be written.
    """
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        raise IOError(f"Failed writing to: {file_path}") from e


def main() -> None:
    """Runs the interactive draft bootstrap CLI."""
    print("==================================================")
    print("   THE HEALTHSTREAM - Active Draft Bootstrapper  ")
    print("==================================================\n")

    src_dir = "src"
    backlog_path = os.path.join(src_dir, "backlog.json")
    drafts_dir = os.path.join(src_dir, "nodes", "en", "drafts")

    # 1. Load active backlog items
    try:
        backlog = load_json_file(backlog_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)

    if not backlog:
        print("Pipeline is empty. Add items to the backlog first using: new_entry_in_pipeline.py --add")
        sys.exit(0)

    print("Active Backlog Pipeline Items:")
    for idx, item in enumerate(backlog):
        print(f"  [{idx + 1}] {item['title']} ({item['category']}) - Votes: {item['votes']}")

    # 2. Select entry
    while True:
        choice = input("\nSelect entry number to activate and write: ").strip()
        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(backlog):
                selected_item = backlog[choice_idx]
                break
        except ValueError:
            pass
        print("Invalid choice. Please input a number from the list.")

    slug = selected_item["id"]
    title = selected_item["title"]
    category = selected_item["category"]
    description = selected_item["description"]

    # 3. Formulate compliant schema output
    node_data: Dict[str, Any] = {
        "type": category,
        "title": title,
        "hook_question": description,
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
        "tags": selected_item.get("tags", [category]),
        "reading_modes": {
            "overview_3min": "A 3-min narrative overview mapping the biological feedback loops. Use bold `**` tags for glossary terms.",
            "deep_dive": [
                {
                    "heading": "Molecular Feedback Loops",
                    "body": "Detailed biochemical steps (use bold `**` for vocabulary terms)."
                }
            ]
        },
        "edges": [
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

    # 4. Save file to drafts folder
    os.makedirs(drafts_dir, exist_ok=True)
    target_file = os.path.join(drafts_dir, f"{slug}.json")

    save_json_file(target_file, node_data)
    print(f"\n[Success] Draft generated successfully at: {target_file}")

    # 5. Remove activated item from backlog
    backlog.pop(choice_idx)
    save_json_file(backlog_path, backlog)
    print(f"[Success] Removed '{slug}' from active backlog pipeline.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProcess interrupted. Exiting.")
        sys.exit(0)
