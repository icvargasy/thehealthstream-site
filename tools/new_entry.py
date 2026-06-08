#!/usr/bin/env python3
"""CLI tool to programmatically bootstrap new article entries for The Healthstream.

This script prompts the author for metadata, content hook, and category options,
then outputs a formatted JSON document to the src/nodes/en/ directory.
"""

import json
import os
import re
import sys
from typing import Any, Dict


def slugify(text: str) -> str:
    """Converts a raw title string into a url-safe filename slug.

    Args:
        text: Raw text string (e.g. "AMPK Activation Pathway").

    Returns:
        A lowercase slug with non-alphanumeric characters replaced by hyphens.
    """
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "-", text)


def prompt_user(prompt_text: str, default: str = "") -> str:
    """Prompts the user for text input with optional default fallback.

    Args:
        prompt_text: The instructions displayed to the user.
        default: Fallback string value if input is empty.

    Returns:
        The validated input string.
    """
    display = f"{prompt_text} [{default}]: " if default else f"{prompt_text}: "
    user_input = input(display).strip()
    return user_input if user_input else default


def select_option(prompt_text: str, options: Dict[str, str]) -> str:
    """Forces user to select from a dictionary of options.

    Args:
        prompt_text: Instructive title of the prompt.
        options: Dictionary mapping character key to display text.

    Returns:
        The key selected by the user.
    """
    print(f"\n{prompt_text}")
    for key, value in options.items():
        print(f"  [{key}] {value}")

    while True:
        choice = input("Select option key: ").strip().lower()
        if choice in options:
            return choice
        print("Invalid key selection. Attempt again.")


def main() -> None:
    """Runs the interactive draft bootstrap CLI.

    Raises:
        OSError: If target save directory is unreachable.
    """
    print("==================================================")
    print("   THE HEALTHSTREAM - New Article Bootstrapper   ")
    print("==================================================\n")

    # 1. Type Selection
    type_options = {
        "b": "biology (Science/Pathway Decodings)",
        "l": "lifestyle (Behavioral/Habit Protocols)",
        "k": "book (Curated Longevity Literature)",
    }
    type_key = select_option("Select content node category:", type_options)
    type_map = {"b": "biology", "l": "lifestyle", "k": "book"}
    content_type = type_map[type_key]

    # 2. Title & Hook inputs
    title = prompt_user("Enter Article Title")
    if not title:
        print("Error: Article title is required.")
        sys.exit(1)

    default_slug = slugify(title)
    slug = prompt_user("Confirm Filename Slug", default_slug)

    hook = prompt_user("Enter Curiosity Hook / Engaging Question")
    pill = prompt_user("Enter 1-Min Takeaway Pill (Actionable conclusion)")

    # 3. Epistemic Consensus Scale
    status_options = {
        "c": "consensus (Established scientific consensus)",
        "d": "developing (Developing hypothesis / active research)",
        "h": "high-controversy (Early theories / conflicting data)",
    }
    status_key = select_option("Select Epistemic Status Level:", status_options)
    status_map = {
        "c": "consensus",
        "d": "developing",
        "h": "high-controversy",
    }
    epistemic_status = status_map[status_key]

    content = prompt_user("Enter Article Content Body (Markdown)", "Define the systems biology feedback loops here.")

    # 4. Generate JSON schema
    node_data: Dict[str, Any] = {
        "type": content_type,
        "title": title,
        "hook_question": hook,
        "takeaway_pill": pill,
        "epistemic_status": epistemic_status,
        "tags": [content_type],
        "content": content,
        "evidence_table": [],
        "bibliography": [],
    }

    # 5. File Management
    target_dir = os.path.join("src", "nodes", "en")
    target_file = os.path.join(target_dir, f"{slug}.json")

    try:
        os.makedirs(target_dir, exist_ok=True)
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(node_data, f, indent=2, ensure_ascii=False)
        print(f"\n[Success] Draft bootstrapped successfully at: {target_file}")
    except OSError as e:
        print(f"\n[Error] Failed writing target file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProcess interrupted by author. Exiting.")
        sys.exit(0)
