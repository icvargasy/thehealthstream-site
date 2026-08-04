import re
import html
import markdown
from typing import Dict, Any
from .utils import slugify, SYNAPSE_LOGO_SVG

# Global cache for compiled popover HTML definitions to prevent O(M x N x V) re-rendering
_POPOVER_CACHE: Dict[str, str] = {}


def clear_popover_cache():
    """Clears the internal popover HTML cache."""
    global _POPOVER_CACHE
    _POPOVER_CACHE.clear()


# Robust HTML tag split pattern supporting quotes in attributes and comments
HTML_TAG_SPLIT_REGEX = re.compile(r"(<!--.*?-->|<(?:[^>\"']|\"[^\"]*\"|'[^']*')*>)")
def inject_simple_links(
    html_content: str,
    vocabulary: Dict[str, Any],
    current_term: str,
    base_path: str = "./",
) -> str:
    """Wraps jargon terms inside definition snippets in simple anchor links.

    Links resolve at compile time using the provided base_path, so no
    placeholder substitution is needed at runtime.

    Args:
        html_content: HTML string to process.
        vocabulary: Glossary dictionary.
        current_term: The term whose definition is being rendered (excluded from linking).
        base_path: Relative path prefix to the site root (e.g. './' or '../').
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

        # Capture base_path in closure via default argument to avoid late-binding.
        def replace_callback(match: re.Match, _bp: str = base_path) -> str:
            matched_text = match.group(1)
            matched_lower = matched_text.lower()
            canonical_key = phrase_to_canonical.get(matched_lower, matched_text)
            slug = slugify(canonical_key)
            return (
                f'<a href="{_bp}vocabulary/{slug}.html" '
                f'target="_blank" class="popover-nested-link">{matched_text}&nbsp;↗</a>'
            )

        tokens[i] = pattern.sub(replace_callback, token)

    return "".join(tokens)


def _get_compiled_definition(
    canonical_key: str,
    vocabulary: Dict[str, Any],
    base_path: str = "./",
) -> str:
    """Pre-compiles and caches popover content for a canonical term.

    The cache key includes base_path so root-level and vocabulary sub-pages
    each get correctly resolved link URLs without sharing stale entries.

    Args:
        canonical_key: The canonical term string from the vocabulary.
        vocabulary: The full glossary dictionary.
        base_path: Relative path prefix to the site root (e.g. './' for root
            pages, '../' for pages inside a sub-directory like vocabulary/).
    """
    cache_key = f"{base_path}|{canonical_key}"
    if cache_key in _POPOVER_CACHE:
        return _POPOVER_CACHE[cache_key]

    vocab_item = vocabulary[canonical_key]
    analogy = vocab_item.get("vulgarized_analogy", "")
    is_analogy = bool(analogy)
    raw_content = analogy or vocab_item.get("definition", "")
    content_html = markdown.markdown(raw_content).strip()
    if content_html.startswith("<p>") and content_html.endswith("</p>"):
        content_html = content_html[3:-4]

    if is_analogy:
        content_html = (
            f'<span class="popover-analogy-badge" style="display: inline-flex; align-items: center; gap: 4px; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; background-color: transparent; color: var(--accent-synapse); border: 1px solid var(--accent-synapse); padding: 2px 6px; border-radius: var(--radius-pill); margin-right: 6px; vertical-align: middle;">{SYNAPSE_LOGO_SVG} Systems Analogy</span>'
            f'<span style="font-style: italic; display: inline;">{content_html}</span>'
        )

    content_html = inject_simple_links(content_html, vocabulary, canonical_key, base_path)
    escaped_content = html.escape(content_html, quote=True)
    _POPOVER_CACHE[cache_key] = escaped_content
    return escaped_content


def inject_jargon_links(
    html_content: str,
    vocabulary: Dict[str, Any],
    base_path: str = "./",
) -> str:
    """Scans HTML content and wraps jargon terms in hover popover spans.

    Only targets raw text nodes, ignoring HTML attributes, tag names, or
    text already nested inside anchor tags, code blocks, scripts, or existing jargon terms.

    Args:
        html_content: HTML string to process.
        vocabulary: Glossary dictionary.
        base_path: Relative path prefix to the site root. Forwarded to
            _get_compiled_definition so popover nested links resolve correctly.
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

        # Capture mutable closure vars via default args to avoid late-binding.
        def replace_callback(
            match: re.Match,
            _vocab: Dict[str, Any] = vocabulary,
            _p2c: Dict[str, str] = phrase_to_canonical,
            _bp: str = base_path,
        ) -> str:
            matched_text = match.group(1)
            matched_lower = matched_text.lower()
            canonical_key = _p2c.get(matched_lower, matched_text)
            definition = _get_compiled_definition(canonical_key, _vocab, _bp)
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

    # Use the same robust HTML tokenizer as inject_jargon_links to handle
    # attributes containing '>' (e.g. SVG viewBox, inline style).
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
                f'<a href="{base_path}vocabulary/{slug}.html" '
                f'class="vocab-nested-link">{matched_text}</a>'
            )

        tokens[i] = pattern.sub(replace_callback, token)

    return "".join(tokens)
