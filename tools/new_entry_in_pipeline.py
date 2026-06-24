#!/usr/bin/env python3
"""CLI tool to manage The Healthstream's content backlog pipeline.

Handles manual entry creation and imports submissions/votes directly from Google Sheets.
"""

import argparse
import csv
import os
import re
import sys
import urllib.request
from typing import Any, Dict, List

# Ensure tools/ is in the python path for importing compiler modules
sys.path.insert(0, os.path.dirname(__file__))
from compiler.utils import slugify, load_json_file, save_json_file


def import_from_google_sheets(translations_path: str, backlog_path: str, inbox_path: str) -> None:
    """Downloads proposals and votes CSV sheets and merges them.

    Votes update the backlog directly, while new proposals are staged in the inbox.

    Args:
        translations_path: Path to translations.json to get CSV URLs.
        backlog_path: Path to backlog.json to merge vote counts.
        inbox_path: Path to inbox.json to store raw proposals.
    """
    translations = load_json_file(translations_path)
    labels = translations.get("en", {})

    proposals_url = labels.get("google_sheet_proposals_csv_url", "")
    votes_url = labels.get("google_sheet_votes_csv_url", "")

    if "PLACEHOLDER" in proposals_url or "PLACEHOLDER" in votes_url:
        print("[Warning] Google Sheet URLs are still placeholders in translations.json. Ingestion skipped.")
        return

    # 1. Load existing backlog and inbox
    backlog = load_json_file(backlog_path, default_empty=[])
    backlog_by_id = {item["id"]: item for item in backlog}
    backlog_by_title = {item["title"].lower().strip(): item for item in backlog}

    inbox = load_json_file(inbox_path, default_empty=[])
    inbox_by_id = {item["id"]: item for item in inbox}
    inbox_by_title = {item["title"].lower().strip(): item for item in inbox}

    # 2. Ingest and tally votes
    votes_tally: Dict[str, int] = {}
    if votes_url:
        print("Downloading votes from Google Sheets...")
        try:
            req = urllib.request.Request(votes_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req) as response:
                csv_data = response.read().decode("utf-8").splitlines()
                reader = csv.DictReader(csv_data)
                for row in reader:
                    topic = row.get("Which topic are you voting for?", "").strip()
                    if topic:
                        votes_tally[topic.lower()] = votes_tally.get(topic.lower(), 0) + 1
            print("Processed votes tally successfully.")
        except Exception as e:
            print(f"[Error] Failed to fetch or parse votes: {e}")

    # 3. Ingest new proposals to inbox staging area
    new_inbox_count = 0
    if proposals_url:
        print("Downloading proposals from Google Sheets...")
        try:
            req = urllib.request.Request(proposals_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req) as response:
                csv_data = response.read().decode("utf-8").splitlines()
                reader = csv.DictReader(csv_data)
                for row in reader:
                    question = row.get("What is the core question or problem you want to explore?", "").strip()
                    if not question:
                        continue

                    category_raw = row.get("What category best describes this idea?", "").strip()
                    if "Biology" in category_raw:
                        category = "biology"
                    elif "lifestyle" in category_raw.lower():
                        category = "lifestyle"
                    elif "synthesis" in category_raw.lower() or "book" in category_raw.lower():
                        category = "book"
                    else:
                        category = "biology"

                    clean_question = re.sub(r"[^\w\s-]", "", question).strip()
                    words = clean_question.split()
                    title = " ".join(words[:5]) + "..." if len(words) > 5 else " ".join(words)
                    title = title.capitalize()

                    slug = slugify(title)

                    # Check if already exists in backlog or inbox
                    if (slug in backlog_by_id or title.lower().strip() in backlog_by_title or
                        slug in inbox_by_id or title.lower().strip() in inbox_by_title):
                        continue

                    # Append new inbox item
                    new_item = {
                        "id": slug,
                        "title": title,
                        "description": question,
                        "category": category,
                        "votes": 1,
                        "tags": [category],
                    }
                    inbox.append(new_item)
                    inbox_by_id[slug] = new_item
                    inbox_by_title[title.lower().strip()] = new_item
                    new_inbox_count += 1
            print(f"Processed new proposals successfully. Added {new_inbox_count} items to inbox.")
        except Exception as e:
            print(f"[Error] Failed to fetch or parse proposals: {e}")

    # 4. Update vote counts based on tally
    for topic_lower, count in votes_tally.items():
        if topic_lower in backlog_by_id:
            backlog_by_id[topic_lower]["votes"] += count
        elif topic_lower in backlog_by_title:
            backlog_by_title[topic_lower]["votes"] += count
        elif topic_lower in inbox_by_id:
            inbox_by_id[topic_lower]["votes"] += count
        elif topic_lower in inbox_by_title:
            inbox_by_title[topic_lower]["votes"] += count

    # Save files
    save_json_file(backlog_path, backlog)
    save_json_file(inbox_path, inbox)
    print(f"Pipeline updated. Backlog items: {len(backlog)}, Inbox items: {len(inbox)}")


def add_custom_entry(backlog_path: str) -> None:
    """Prompts the author to manually add a custom proposal to the backlog.

    Args:
        backlog_path: Path to backlog.json.
    """
    print("==================================================")
    print("   THE HEALTHSTREAM - Create Pipeline Proposal    ")
    print("==================================================\n")

    title = input("Enter Proposal Title: ").strip()
    if not title:
        print("Error: Title is required.")
        sys.exit(1)

    slug = slugify(title)
    backlog = load_json_file(backlog_path, default_empty=[])
    existing_item = next((item for item in backlog if item["id"] == slug), None)
    if existing_item:
        print(f"\nA proposal with ID '{slug}' already exists. Let's update its tags.")
        tags_input = input(f"Current tags: {existing_item.get('tags', [])}. Enter new tags (comma-separated): ").strip()
        if tags_input:
            new_tags = [t.strip().lower() for t in tags_input.split(",") if t.strip()]
            
            # Validate tags taxonomy
            tags_registry_path = os.path.join("src", "tags.json")
            if os.path.exists(tags_registry_path):
                valid_tags = set(load_json_file(tags_registry_path).keys())
                invalid_tags = [t for t in new_tags if t not in valid_tags]
                if invalid_tags:
                    print(f"Error: Non-standard tags: {invalid_tags}. Allowed tags: {sorted(list(valid_tags))}")
                    sys.exit(1)
            existing_item["tags"] = new_tags

        save_json_file(backlog_path, backlog)
        print(f"\n[Success] Updated tags for proposal: {slug}")
        sys.exit(0)

    print("\nSelect Category:")
    print("  [1] Biology & Science")
    print("  [2] Lifestyle Practices")
    print("  [3] Synthesis & Reviews")
    cat_choice = input("Select category [1-3]: ").strip()
    category = "biology"
    if cat_choice == "2":
        category = "lifestyle"
    elif cat_choice == "3":
        category = "book"

    description = input("\nEnter Description / Curiosity Question:\n> ").strip()
    if not description:
        description = "Explore feedback loops and connectivity for this concept."

    tags_input = input("\nEnter Tags (comma-separated, e.g., 'biology, metabolism'): ").strip()
    if tags_input:
        tags = [t.strip().lower() for t in tags_input.split(",") if t.strip()]
        # Validate tags taxonomy
        tags_registry_path = os.path.join("src", "tags.json")
        if os.path.exists(tags_registry_path):
            valid_tags = set(load_json_file(tags_registry_path).keys())
            invalid_tags = [t for t in tags if t not in valid_tags]
            if invalid_tags:
                print(f"Error: Non-standard tags: {invalid_tags}. Allowed tags: {sorted(list(valid_tags))}")
                sys.exit(1)
    else:
        tags = [category]

    try:
        starting_votes = int(input("\nEnter starting votes [0]: ").strip() or "0")
    except ValueError:
        starting_votes = 0

    new_item = {
        "id": slug,
        "title": title,
        "description": description,
        "category": category,
        "votes": starting_votes,
        "tags": tags,
    }

    backlog.append(new_item)
    save_json_file(backlog_path, backlog)
    print(f"\n[Success] Appended proposal successfully to pipeline: {slug}")


def main() -> None:
    """Parses command line arguments and routes pipeline actions."""
    parser = argparse.ArgumentParser(description="Manage The Healthstream backlog pipeline.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--add", action="store_true", help="Manually add a custom proposal to the backlog.")
    group.add_argument("--import", action="store_true", dest="import_sheets", help="Import proposals and votes from Google Sheets.")

    args = parser.parse_args()

    src_dir = "src"
    backlog_path = os.path.join(src_dir, "backlog.json")
    inbox_path = os.path.join(src_dir, "inbox.json")
    translations_path = os.path.join(src_dir, "translations.json")

    if args.add:
        add_custom_entry(backlog_path)
    elif args.import_sheets:
        import_from_google_sheets(translations_path, backlog_path, inbox_path)


if __name__ == "__main__":
    main()
