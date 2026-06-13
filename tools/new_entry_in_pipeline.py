#!/usr/bin/env python3
"""CLI tool to manage The Healthstream's content backlog pipeline.

Handles manual entry creation and imports submissions/votes directly from Google Sheets.
"""

import argparse
import csv
import json
import os
import re
import sys
import urllib.request
from typing import Any, Dict, List


def slugify(text: str) -> str:
    """Converts a raw title string into a url-safe slug.

    Args:
        text: Raw text string.

    Returns:
        A lowercase slug with non-alphanumeric characters replaced by hyphens.
    """
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "-", text)


def load_json_file(file_path: str) -> Any:
    """Loads a JSON file safely.

    Args:
        file_path: Path to the JSON file.

    Returns:
        Parsed JSON content.
    """
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []


def save_json_file(file_path: str, data: Any) -> None:
    """Saves data to a JSON file.

    Args:
        file_path: Path to write the JSON file.
        data: Data to serialize.
    """
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving to {file_path}: {e}")


def import_from_google_sheets(translations_path: str, backlog_path: str) -> None:
    """Downloads proposals and votes CSV sheets and merges them into the backlog.

    Args:
        translations_path: Path to translations.json to get CSV URLs.
        backlog_path: Path to backlog.json to merge data.
    """
    translations = load_json_file(translations_path)
    labels = translations.get("en", {})

    proposals_url = labels.get("google_sheet_proposals_csv_url", "")
    votes_url = labels.get("google_sheet_votes_csv_url", "")

    if "PLACEHOLDER" in proposals_url or "PLACEHOLDER" in votes_url:
        print("[Warning] Google Sheet URLs are still placeholders in translations.json. Ingestion skipped.")
        return

    # 1. Load existing backlog
    backlog = load_json_file(backlog_path)
    backlog_by_id = {item["id"]: item for item in backlog}
    backlog_by_title = {item["title"].lower().strip(): item for item in backlog}

    # 2. Ingest and tally votes
    votes_tally: Dict[str, int] = {}
    if votes_url:
        print(f"Downloading votes from Google Sheets...")
        try:
            req = urllib.request.Request(votes_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req) as response:
                csv_data = response.read().decode("utf-8").splitlines()
                reader = csv.DictReader(csv_data)
                for row in reader:
                    # Form field: "Which topic are you voting for?"
                    topic = row.get("Which topic are you voting for?", "").strip()
                    if topic:
                        votes_tally[topic.lower()] = votes_tally.get(topic.lower(), 0) + 1
            print(f"Processed votes tally successfully.")
        except Exception as e:
            print(f"[Error] Failed to fetch or parse votes: {e}")

    # 3. Ingest new proposals
    if proposals_url:
        print(f"Downloading proposals from Google Sheets...")
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

                    # Generate title from first few words of the question
                    clean_question = re.sub(r"[^\w\s-]", "", question).strip()
                    words = clean_question.split()
                    title = " ".join(words[:5]) + "..." if len(words) > 5 else " ".join(words)
                    title = title.capitalize()

                    slug = slugify(title)

                    # Check if already exists in backlog
                    if slug in backlog_by_id or title.lower().strip() in backlog_by_title:
                        continue

                    # Append new backlog item
                    new_item = {
                        "id": slug,
                        "title": title,
                        "description": question,
                        "category": category,
                        "votes": 1,
                        "tags": [category],
                    }
                    backlog.append(new_item)
                    backlog_by_id[slug] = new_item
                    backlog_by_title[title.lower().strip()] = new_item
            print(f"Processed new proposals successfully.")
        except Exception as e:
            print(f"[Error] Failed to fetch or parse proposals: {e}")

    # 4. Update vote counts in backlog based on tally
    for topic_lower, count in votes_tally.items():
        # Match by ID or by title
        if topic_lower in backlog_by_id:
            backlog_by_id[topic_lower]["votes"] += count
        elif topic_lower in backlog_by_title:
            backlog_by_title[topic_lower]["votes"] += count

    # Save backlog
    save_json_file(backlog_path, backlog)
    print(f"Backlog updated successfully. Total backlog items: {len(backlog)}")


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
    backlog = load_json_file(backlog_path)
    existing_item = next((item for item in backlog if item["id"] == slug), None)
    if existing_item:
        print(f"\nA proposal with ID '{slug}' already exists. Let's update its tags.")
        tags_input = input(f"Current tags: {existing_item.get('tags', [])}. Enter new tags (comma-separated): ").strip()
        if tags_input:
            existing_item["tags"] = [t.strip().lower() for t in tags_input.split(",") if t.strip()]
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
    translations_path = os.path.join(src_dir, "translations.json")

    if args.add:
        add_custom_entry(backlog_path)
    elif args.import_sheets:
        import_from_google_sheets(translations_path, backlog_path)


if __name__ == "__main__":
    main()
