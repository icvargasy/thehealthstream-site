"""Robust Jargon Lexicon Linking and Popover Injection Engine.

Provides dual regex matching (case-sensitive for acronyms and case-insensitive
for general terms and morphological variants) and safe HTML text tokenization.
"""

import html
import itertools
import re
from typing import Any, Dict, List, Optional, Set, Tuple
import markdown
from .utils import SYNAPSE_LOGO_SVG, slugify

# Global cache for compiled popover HTML definitions to prevent O(M x N x V) re-rendering
_POPOVER_CACHE: Dict[str, str] = {}


def clear_popover_cache() -> None:
    """Clears the internal popover HTML cache."""
    global _POPOVER_CACHE
    _POPOVER_CACHE.clear()


# Robust HTML tag split pattern supporting quotes in attributes and comments
HTML_TAG_SPLIT_REGEX = re.compile(r"(<!--.*?-->|<(?:[^>\"']|\"[^\"]*\"|'[^']*')*>)")

IRREGULAR_PLURALS: Dict[str, str] = {
    "dysbiosis": "dysbioses",
    "microglia": "microglial",
    "matrix": "matrices",
    "hypothesis": "hypotheses",
    "bacterium": "bacteria",
    "criterion": "criteria",
    "mitochondrion": "mitochondria",
    "cytoskeleton": "cytoskeletal",
    "xenohormesis": "xenohormetic",
    "pathology": "pathologies",
    "axis": "axes",
    "synapse": "synapses",
    "neuron": "neurons",
    "astrocyte": "astrocytes",
    "biochemistry": "biochemical",
    "physiology": "physiological",
}
REVERSE_IRREGULAR: Dict[str, str] = {v: k for k, v in IRREGULAR_PLURALS.items()}


def is_acronym(term: str) -> bool:
    """Checks if a term is a short uppercase acronym (e.g., DNA, GRADE, ATP, FMT, RCT).

    Args:
        term: Term string to inspect.

    Returns:
        True if the term is a short acronym that should strictly match case-sensitively.
    """
    t = term.strip().rstrip("sS")
    if len(term.split()) == 1:
        if term.isupper() and len(t) <= 5:
            return True
        if re.fullmatch(r"[A-Z0-9\+]{2,5}", t):
            return True
    known_acronyms = {
        "DNA", "GRADE", "ATP", "FMT", "RCT", "CGM", "LPS", "MRI", "RNA",
        "TLR4", "ROS", "BDNF", "GABA", "SCFA", "SCFAs", "DHA", "EGCG", "NAD+", "COR388"
    }
    return term in known_acronyms


def get_morphological_variants(term: str) -> Set[str]:
    """Generates singular, plural, hyphenated, and irregular variations of a lexical term.

    Args:
        term: Canonical term or alias string.

    Returns:
        Set of derived surface forms.
    """
    variants: Set[str] = {term}

    # 1. Skip morphological stemming for short uppercase acronyms (e.g., DNA, RNA, ATP, GRADE)
    if is_acronym(term):
        return variants

    # 2. Generate hyphen / whitespace permutation variants for compound terms
    parts = re.split(r"[\s-]+", term)
    if 1 < len(parts) <= 4:
        for seps in itertools.product([" ", "-"], repeat=len(parts) - 1):
            combined = "".join(p + s for p, s in zip(parts[:-1], seps)) + parts[-1]
            variants.add(combined)
    else:
        if "-" in term:
            variants.add(term.replace("-", " "))
        if " " in term:
            variants.add(term.replace(" ", "-"))

    # 3. Irregular & standard inflections on the terminal head word for all base variants
    base_variants = list(variants)
    for v_term in base_variants:
        words = v_term.split()
        if not words:
            continue
        last_word = words[-1]
        last_word_lower = last_word.lower()
        prefix = " ".join(words[:-1]) + (" " if len(words) > 1 else "")

        if last_word_lower in IRREGULAR_PLURALS:
            variants.add(f"{prefix}{IRREGULAR_PLURALS[last_word_lower]}")
        if last_word_lower in REVERSE_IRREGULAR:
            variants.add(f"{prefix}{REVERSE_IRREGULAR[last_word_lower]}")

        # Biological -sis <-> -ses
        if last_word_lower.endswith("sis") and len(last_word_lower) > 4:
            variants.add(f"{prefix}{last_word[:-3]}ses")
        elif (last_word_lower.endswith("oses") or last_word_lower.endswith("ises") or last_word_lower.endswith("yses")) and len(last_word_lower) > 4:
            variants.add(f"{prefix}{last_word[:-3]}sis")

        # Standard English plurals / singulars
        if last_word_lower.endswith("ies") and len(last_word_lower) > 4:
            variants.add(f"{prefix}{last_word[:-3]}y")
        elif last_word_lower.endswith("y") and not last_word_lower.endswith(("ay", "ey", "oy", "uy")) and len(last_word_lower) > 3:
            variants.add(f"{prefix}{last_word[:-1]}ies")
        elif any(last_word_lower.endswith(sfx) for sfx in ("xes", "shes", "ches", "sses")) and len(last_word_lower) > 4:
            variants.add(f"{prefix}{last_word[:-2]}")
        elif any(last_word_lower.endswith(sfx) for sfx in ("x", "sh", "ch", "ss")):
            variants.add(f"{prefix}{last_word}es")
        elif last_word_lower.endswith("s") and not any(last_word_lower.endswith(sfx) for sfx in ("ss", "is", "us", "as", "os")) and len(last_word_lower) > 3:
            variants.add(f"{prefix}{last_word[:-1]}")
        elif not last_word_lower.endswith("s") and not last_word_lower.endswith("a"):
            variants.add(f"{prefix}{last_word}s")

    # Apply hyphen/space variations to all newly generated forms
    final_variants = set(variants)
    for v in variants:
        if "-" in v:
            final_variants.add(v.replace("-", " "))
        if " " in v:
            final_variants.add(v.replace(" ", "-"))

    return {v for v in final_variants if v}


class LexiconMatcher:
    """Compiled dual regex matcher for precise jargon term identification."""

    def __init__(
        self,
        cs_pat: Optional[re.Pattern],
        ci_pat: Optional[re.Pattern],
        combined_pat: Optional[re.Pattern],
        cs_map: Dict[str, str],
        ci_map: Dict[str, str],
    ):
        self.cs_pat = cs_pat
        self.ci_pat = ci_pat
        self.pattern = combined_pat
        self.cs_map = cs_map
        self.ci_map = ci_map
        self.phrase_to_canonical = {**ci_map, **cs_map}

    def __iter__(self):
        return iter((self.cs_pat, self.cs_map, self.ci_pat, self.ci_map))

    def __getitem__(self, key: Any) -> Any:
        if isinstance(key, int):
            return (self.cs_pat, self.cs_map, self.ci_pat, self.ci_map)[key]
        return getattr(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def get_canonical(self, matched_text: str) -> Optional[str]:
        """Resolves matched text to its canonical vocabulary term."""
        if matched_text in self.cs_map:
            return self.cs_map[matched_text]
        return self.ci_map.get(matched_text.lower())

    def search_in_text(self, text: str) -> Set[str]:
        """Returns the set of canonical terms found in text."""
        if not text:
            return set()
        found: Set[str] = set()
        if self.pattern:
            for match in self.pattern.finditer(text):
                matched_text = match.group(1)
                canonical = self.get_canonical(matched_text)
                if canonical:
                    found.add(canonical)
        else:
            if self.cs_pat:
                for match in self.cs_pat.finditer(text):
                    canonical = self.cs_map.get(match.group(1))
                    if canonical:
                        found.add(canonical)
            if self.ci_pat:
                for match in self.ci_pat.finditer(text):
                    canonical = self.ci_map.get(match.group(1).lower())
                    if canonical:
                        found.add(canonical)
        return found


def build_lexicon_matcher(
    vocabulary: Dict[str, Any],
    exclude_term: Optional[str] = None,
) -> LexiconMatcher:
    """Compiles dual regex matchers for vocabulary terms and morphological variants.

    Compiles case-sensitive regex for short uppercase acronyms and case-insensitive
    regex for regular vocabulary terms, aliases, and morphological variations.

    Args:
        vocabulary: Dictionary of vocabulary terms and definitions.
        exclude_term: Optional canonical term string to exclude from matching (e.g. self-linking).

    Returns:
        A compiled LexiconMatcher instance.
    """
    cs_map: Dict[str, str] = {}
    ci_map: Dict[str, str] = {}
    exclude_aliases: Set[str] = set()
    if exclude_term and exclude_term in vocabulary:
        exclude_aliases = {a.lower() for a in vocabulary[exclude_term].get("aliases", [])}
    exclude_term_lower = exclude_term.lower() if exclude_term else None

    for term, details in vocabulary.items():
        if exclude_term and (term == exclude_term or term.lower() == exclude_term_lower):
            continue
        phrases = [term] + details.get("aliases", [])
        for p in phrases:
            if not p:
                continue
            if exclude_term and (p.lower() == exclude_term_lower or p.lower() in exclude_aliases):
                continue
            variants = get_morphological_variants(p)
            for v in variants:
                if is_acronym(v):
                    cs_map[v] = term
                else:
                    ci_map[v.lower()] = term

    sorted_cs = sorted(cs_map.keys(), key=len, reverse=True)
    sorted_ci = sorted(ci_map.keys(), key=len, reverse=True)

    cs_escaped = [re.escape(k) for k in sorted_cs if k]
    ci_escaped = [re.escape(k) for k in sorted_ci if k]

    cs_pat = re.compile(r"(?<![\w-])(" + "|".join(cs_escaped) + r")(?![\w-])") if cs_escaped else None
    ci_pat = re.compile(r"(?<![\w-])(" + "|".join(ci_escaped) + r")(?![\w-])", re.IGNORECASE) if ci_escaped else None

    if cs_escaped and ci_escaped:
        combined_str = r"(?<![\w-])((?-i:" + "|".join(cs_escaped) + r")|(?i:" + "|".join(ci_escaped) + r"))(?![\w-])"
        combined_pat = re.compile(combined_str)
    elif cs_escaped:
        combined_pat = cs_pat
    elif ci_escaped:
        combined_pat = ci_pat
    else:
        combined_pat = None

    return LexiconMatcher(cs_pat, ci_pat, combined_pat, cs_map, ci_map)


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

    matcher = build_lexicon_matcher(vocabulary, exclude_term=current_term)
    if not matcher.pattern:
        return html_content

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

        def replace_callback(match: re.Match, _bp: str = base_path, _m: LexiconMatcher = matcher) -> str:
            matched_text = match.group(1)
            canonical_key = _m.get_canonical(matched_text) or matched_text
            slug = slugify(canonical_key)
            return (
                f'<a href="{_bp}vocabulary/{slug}.html" '
                f'target="_blank" class="popover-nested-link">{matched_text}&nbsp;↗</a>'
            )

        tokens[i] = matcher.pattern.sub(replace_callback, token)

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

    matcher = build_lexicon_matcher(vocabulary)
    if not matcher.pattern:
        return html_content

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

        def replace_callback(
            match: re.Match,
            _vocab: Dict[str, Any] = vocabulary,
            _m: LexiconMatcher = matcher,
            _bp: str = base_path,
        ) -> str:
            matched_text = match.group(1)
            canonical_key = _m.get_canonical(matched_text) or matched_text
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

        tokens[i] = matcher.pattern.sub(replace_callback, token)

    return "".join(tokens)


def inject_direct_links(
    html_content: str,
    vocabulary: Dict[str, Any],
    current_term: str,
    base_path: str = "./",
) -> str:
    """Wraps jargon terms inside Lexicon definitions in direct relative hyperlinks."""
    if not vocabulary:
        return html_content

    matcher = build_lexicon_matcher(vocabulary, exclude_term=current_term)
    if not matcher.pattern:
        return html_content

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

        def replace_callback(match: re.Match, _m: LexiconMatcher = matcher) -> str:
            matched_text = match.group(1)
            canonical_key = _m.get_canonical(matched_text) or matched_text
            slug = slugify(canonical_key)

            return (
                f'<a href="{base_path}vocabulary/{slug}.html" '
                f'class="vocab-nested-link">{matched_text}</a>'
            )

        tokens[i] = matcher.pattern.sub(replace_callback, token)

    return "".join(tokens)
