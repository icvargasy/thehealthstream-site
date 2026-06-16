"""Jargon linking and regex injection module for The Healthstream.

This module scans article content body and automatically links jargon terms
defined in the glossary to interactive popovers, avoiding tag collisions.
"""

import re
from typing import Dict, Any


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


def inject_jargon_links(html_content: str, vocabulary: Dict[str, Any]) -> str:
    """Scans HTML content and wraps jargon terms in hover popover spans.

    Only targets raw text nodes, ignoring HTML attributes, tag names, or
    text already nested inside anchor tags (<a>...</a>).

    Args:
        html_content: The compiled HTML body string of the article.
        vocabulary: The dictionary of jargon definitions.

    Returns:
        The modified HTML string with injected jargon markers.
    """
    if not vocabulary:
        return html_content

    # Build mapping from phrase to canonical term
    phrase_to_canonical = {}
    for term, details in vocabulary.items():
        phrase_to_canonical[term.lower()] = term
        for alias in details.get("aliases", []):
            phrase_to_canonical[alias.lower()] = term

    # Sort all phrases by length descending to match longer terms first
    sorted_phrases = sorted(phrase_to_canonical.keys(), key=len, reverse=True)
    
    # Create combined regex pattern with word boundaries
    escaped_phrases = [re.escape(phrase) for phrase in sorted_phrases]
    pattern_str = r"(?<![\w-])(" + "|".join(escaped_phrases) + r")(?![\w-])"
    pattern = re.compile(pattern_str, re.IGNORECASE)

    # Tokenize the HTML by tags to isolate text nodes
    # Tokens with odd indices are tags, even indices are raw text
    tokens = re.split(r"(<[^>]+>)", html_content)
    
    in_link = False
    
    for i in range(len(tokens)):
        token = tokens[i]
        
        # Check if the token is a tag
        if token.startswith("<"):
            tag_lower = token.lower()
            if tag_lower.startswith("<a ") or tag_lower == "<a>":
                in_link = True
            elif tag_lower == "</a>":
                in_link = False
            continue

        # If inside an existing link, skip replacing terms
        if in_link:
            continue

        # Replacement callback function
        def replace_callback(match: re.Match) -> str:
            matched_text = match.group(1)
            matched_lower = matched_text.lower()
            canonical_key = phrase_to_canonical.get(matched_lower, matched_text)
                    
            vocab_item = vocabulary[canonical_key]
            definition = vocab_item.get("definition", "").replace('"', "&quot;")
            slug = slugify(canonical_key)
            
            return (
                f'<span class="jargon-term" '
                f'data-term="{canonical_key}" '
                f'data-definition="{definition}" '
                f'data-slug="{slug}">{matched_text}</span>'
            )

        # Apply replacements to the raw text token
        tokens[i] = pattern.sub(replace_callback, token)

    return "".join(tokens)
