"""Jargon linking and regex injection module for The Healthstream.

This module scans article content body and automatically links jargon terms
defined in the glossary to interactive popovers, avoiding tag collisions.
"""

import re
import markdown
from typing import Dict, Any
from .utils import slugify


def inject_jargon_links(html_content: str, vocabulary: Dict[str, Any], visited: set = None) -> str:
    """Scans HTML content and wraps jargon terms in hover popover spans.

    Only targets raw text nodes, ignoring HTML attributes, tag names, or
    text already nested inside anchor tags (<a>...</a>).

    Args:
        html_content: The compiled HTML body string of the article.
        vocabulary: The dictionary of jargon definitions.
        visited: Set of already processed term keys to prevent recursion loops.

    Returns:
        The modified HTML string with injected jargon markers.
    """
    if not vocabulary:
        return html_content
    if visited is None:
        visited = set()

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
            
            if canonical_key in visited:
                return f"<strong>{matched_text}</strong>"
                    
            vocab_item = vocabulary[canonical_key]
            raw_def = vocab_item.get("definition", "")
            definition_html = markdown.markdown(raw_def).strip()
            if definition_html.startswith("<p>") and definition_html.endswith("</p>"):
                definition_html = definition_html[3:-4]
            
            # Recurse with loop protection
            next_visited = visited | {canonical_key}
            definition_html = inject_jargon_links(definition_html, vocabulary, next_visited)
            definition = definition_html.replace('"', "&quot;")
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
