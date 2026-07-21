import re
import html
import markdown
from typing import Dict, Any
from .utils import slugify

# Global cache for compiled popover HTML definitions to prevent O(M x N x V) re-rendering
_POPOVER_CACHE: Dict[str, str] = {}


def clear_popover_cache():
    """Clears the internal popover HTML cache."""
    global _POPOVER_CACHE
    _POPOVER_CACHE.clear()


# Robust HTML tag split pattern supporting quotes in attributes and comments
HTML_TAG_SPLIT_REGEX = re.compile(r"(<!--.*?-->|<(?:[^>\"']|\"[^\"]*\"|'[^']*')*>)")

def inject_simple_links(html_content: str, vocabulary: Dict[str, Any], current_term: str) -> str:
    """Wraps jargon terms inside definition snippets in simple external anchor links.

    These links target _blank (new tab) and are styled with a clean ↗ icon.
    """
    if not vocabulary:
        return html_content

    current_term_lower = current_term.lower()
    current_aliases = set()
    if current_term in vocabulary:
        current_aliases = {alias.lower() for alias in vocabulary[current_term].get("aliases", [])}
    
    phrase_to_canonical = {}
    for term, details in vocabulary.items():
        term_lower = term.lower()
        if term_lower == current_term_lower or term_lower in current_aliases:
            continue
        phrase_to_canonical[term_lower] = term
        for alias in details.get("aliases", []):
            alias_lower = alias.lower()
            if alias_lower == current_term_lower or alias_lower in current_aliases:
                continue
            phrase_to_canonical[alias_lower] = term

    sorted_phrases = sorted(phrase_to_canonical.keys(), key=len, reverse=True)
    if not sorted_phrases:
        return html_content

    escaped_phrases = [re.escape(phrase) for phrase in sorted_phrases]
    pattern_str = r"(?<![\w-])(" + "|".join(escaped_phrases) + r")(?![\w-])"
    pattern = re.compile(pattern_str, re.IGNORECASE)

    tokens = HTML_TAG_SPLIT_REGEX.split(html_content)
    skip_depth = 0
    
    for i in range(len(tokens)):
        token = tokens[i]
        
        if token.startswith("<"):
            tag_lower = token.lower().strip()
            if re.match(r"^</a[\s>]", tag_lower):
                if skip_depth > 0:
                    skip_depth -= 1
            elif re.match(r"^<a[\s/>]", tag_lower):
                skip_depth += 1
            continue

        if skip_depth > 0:
            continue

        def replace_callback(match: re.Match) -> str:
            matched_text = match.group(1)
            matched_lower = matched_text.lower()
            canonical_key = phrase_to_canonical.get(matched_lower, matched_text)
            slug = slugify(canonical_key)
            
            return (
                f'<a href="{{{{base_path}}}}vocabulary/{slug}.html" '
                f'target="_blank" class="popover-nested-link">{matched_text}&nbsp;↗</a>'
            )

        tokens[i] = pattern.sub(replace_callback, token)

    return "".join(tokens)


def _get_compiled_definition(canonical_key: str, vocabulary: Dict[str, Any]) -> str:
    """Pre-compiles and caches popover HTML definitions for a canonical term."""
    if canonical_key in _POPOVER_CACHE:
        return _POPOVER_CACHE[canonical_key]

    vocab_item = vocabulary[canonical_key]
    raw_def = vocab_item.get("definition", "")
    definition_html = markdown.markdown(raw_def).strip()
    if definition_html.startswith("<p>") and definition_html.endswith("</p>"):
        definition_html = definition_html[3:-4]

    definition_html = inject_simple_links(definition_html, vocabulary, canonical_key)
    escaped_def = html.escape(definition_html, quote=True)
    _POPOVER_CACHE[canonical_key] = escaped_def
    return escaped_def


def inject_jargon_links(html_content: str, vocabulary: Dict[str, Any]) -> str:
    """Scans HTML content and wraps jargon terms in hover popover spans.

    Only targets raw text nodes, ignoring HTML attributes, tag names, or
    text already nested inside anchor tags, code blocks, scripts, or existing jargon terms.
    """
    if not vocabulary:
        return html_content

    phrase_to_canonical = {}
    for term, details in vocabulary.items():
        phrase_to_canonical[term.lower()] = term
        for alias in details.get("aliases", []):
            phrase_to_canonical[alias.lower()] = term

    sorted_phrases = sorted(phrase_to_canonical.keys(), key=len, reverse=True)
    if not sorted_phrases:
        return html_content
        
    escaped_phrases = [re.escape(phrase) for phrase in sorted_phrases]
    pattern_str = r"(?<![\w-])(" + "|".join(escaped_phrases) + r")(?![\w-])"
    pattern = re.compile(pattern_str, re.IGNORECASE)

    tokens = HTML_TAG_SPLIT_REGEX.split(html_content)
    skip_depth = 0
    
    for i in range(len(tokens)):
        token = tokens[i]
        
        if token.startswith("<"):
            tag_lower = token.lower().strip()
            
            if re.match(r"^</(a|span|code|pre|script|style)[\s>]", tag_lower):
                if skip_depth > 0:
                    skip_depth -= 1
                continue
                
            is_anchor = bool(re.match(r"^<a[\s/>]", tag_lower))
            is_jargon = "jargon-term" in tag_lower
            is_code = bool(re.match(r"^<(code|pre|script|style)[\s/>]", tag_lower))
            
            if is_anchor or is_jargon or is_code:
                skip_depth += 1
            continue

        if skip_depth > 0:
            continue

        def replace_callback(match: re.Match) -> str:
            matched_text = match.group(1)
            matched_lower = matched_text.lower()
            canonical_key = phrase_to_canonical.get(matched_lower, matched_text)
            definition = _get_compiled_definition(canonical_key, vocabulary)
            slug = slugify(canonical_key)
            
            return (
                f'<span class="jargon-term" '
                f'tabindex="0" role="button" aria-haspopup="dialog" '
                f'data-term="{canonical_key}" '
                f'data-definition="{definition}" '
                f'data-matched-text="{matched_text}" '
                f'data-slug="{slug}">{matched_text}</span>'
            )

        tokens[i] = pattern.sub(replace_callback, token)

    return "".join(tokens)


def inject_direct_links(html_content: str, vocabulary: Dict[str, Any], current_term: str, base_path: str = "./") -> str:
    """Wraps jargon terms inside Lexicon definitions in direct relative hyperlinks."""
    if not vocabulary:
        return html_content

    current_term_lower = current_term.lower()
    current_aliases = set()
    if current_term in vocabulary:
        current_aliases = {alias.lower() for alias in vocabulary[current_term].get("aliases", [])}
    
    phrase_to_canonical = {}
    for term, details in vocabulary.items():
        term_lower = term.lower()
        if term_lower == current_term_lower or term_lower in current_aliases:
            continue
        phrase_to_canonical[term_lower] = term
        for alias in details.get("aliases", []):
            alias_lower = alias.lower()
            if alias_lower == current_term_lower or alias_lower in current_aliases:
                continue
            phrase_to_canonical[alias_lower] = term

    sorted_phrases = sorted(phrase_to_canonical.keys(), key=len, reverse=True)
    if not sorted_phrases:
        return html_content

    escaped_phrases = [re.escape(phrase) for phrase in sorted_phrases]
    pattern_str = r"(?<![\w-])(" + "|".join(escaped_phrases) + r")(?![\w-])"
    pattern = re.compile(pattern_str, re.IGNORECASE)

    tokens = re.split(r"(<[^>]+>)", html_content)
    in_link = False
    
    for i in range(len(tokens)):
        token = tokens[i]
        
        if token.startswith("<"):
            tag_lower = token.lower()
            if re.match(r"^<a[\s/>]", tag_lower):
                in_link = True
            elif tag_lower == "</a>":
                in_link = False
            continue

        if in_link:
            continue

        def replace_callback(match: re.Match) -> str:
            matched_text = match.group(1)
            matched_lower = matched_text.lower()
            canonical_key = phrase_to_canonical.get(matched_lower, matched_text)
            slug = slugify(canonical_key)
            
            return (
                f'<a href="{base_path}vocabulary/{slug}.html" '
                f'class="vocab-nested-link">{matched_text}</a>'
            )

        tokens[i] = pattern.sub(replace_callback, token)

    return "".join(tokens)
