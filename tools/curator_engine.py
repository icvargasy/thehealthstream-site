"""Curator RAG & Research Engine.

Processes local sources in src/sources/ and integrates online biomedical databases.
"""

import os
import sys
import re
import json
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Tuple
from pypdf import PdfReader

# Path configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES_DIR = os.path.join(BASE_DIR, "src", "sources")


def list_sources() -> List[str]:
    """Lists all local source files available in src/sources/."""
    if not os.path.exists(SOURCES_DIR):
        return []
    return [
        f for f in os.listdir(SOURCES_DIR)
        if f.endswith((".pdf", ".txt", ".md")) and not f.startswith(".")
    ]


def parse_pdf(filename: str) -> str:
    """Extracts text from a local PDF document.

    Args:
        filename: Name of the file in src/sources/.

    Returns:
        The extracted plain text.
    """
    path = os.path.join(SOURCES_DIR, filename)
    if not os.path.exists(path):
        return ""
    try:
        reader = PdfReader(path)
        text = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text.append(t)
        return "\n".join(text)
    except Exception as e:
        print(f"Error parsing PDF '{filename}': {e}", file=sys.stderr)
        return ""


def parse_text_or_markdown(filename: str) -> str:
    """Reads a plain text or markdown source file.

    Args:
        filename: Name of the file in src/sources/.

    Returns:
        The file contents as a string.
    """
    path = os.path.join(SOURCES_DIR, filename)
    if not os.path.exists(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file '{filename}': {e}", file=sys.stderr)
        return ""


def get_file_content(filename: str) -> str:
    """Extracts full text context from a file based on extension.

    Args:
        filename: Name of the source file.

    Returns:
        String text content.
    """
    if filename.endswith(".pdf"):
        return parse_pdf(filename)
    elif filename.endswith((".txt", ".md")):
        return parse_text_or_markdown(filename)
    return ""


def search_text_for_definitions(text: str, term: str) -> List[Dict[str, Any]]:
    """Searches text for sentences containing the term.

    Identifies potential direct definition sentences.

    Args:
        text: Raw corpus string.
        term: The jargon word or acronym to match.

    Returns:
        A list of matching dictionaries with sentence text and definition flags.
    """
    if not text or not term:
        return []
        
    # Split text into sentences using simple punctuation check
    sentences = re.split(r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s", text)
    matches = []
    pattern = r"\b" + re.escape(term) + r"\b"
    
    # Definition indicators
    def_triggers = [
        r"\bis\b", 
        r"\brefers to\b", 
        r"\bis defined as\b", 
        r"\bconstitutes\b", 
        r"\bacts as\b",
        r"\bplays a key role in\b"
    ]
    trigger_pattern = "|".join(def_triggers)
    
    for idx, sentence in enumerate(sentences):
        clean_sentence = sentence.replace("\n", " ").strip()
        # Clean extra spacing
        clean_sentence = re.sub(r"\s+", " ", clean_sentence)
        
        if re.search(pattern, clean_sentence, re.IGNORECASE):
            is_defining = False
            if re.search(trigger_pattern, clean_sentence, re.IGNORECASE):
                is_defining = True
                
            matches.append({
                "sentence": clean_sentence,
                "is_defining": is_defining,
                "index": idx
            })
            
    # Sort defining sentences to the top
    matches.sort(key=lambda x: x["is_defining"], reverse=True)
    return matches


def query_pubmed(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Queries PubMed E-utilities API to retrieve verified citations.

    Args:
        query: Article title or query string.
        max_results: Cap on returned summaries.

    Returns:
        List of publication dictionaries with metadata.
    """
    try:
        # Step 1: Search for PMIDs
        encoded_query = urllib.parse.quote_plus(query)
        search_url = (
            f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?"
            f"db=pubmed&term={encoded_query}&retmode=json&retmax={max_results}"
        )
        req = urllib.request.Request(search_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as response:
            search_data = json.loads(response.read().decode("utf-8"))
            
        pmids = search_data.get("esearchresult", {}).get("idlist", [])
        if not pmids:
            return []
            
        # Step 2: Fetch metadata summaries
        ids_str = ",".join(pmids)
        summary_url = (
            f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?"
            f"db=pubmed&id={ids_str}&retmode=json"
        )
        req = urllib.request.Request(summary_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as response:
            summary_data = json.loads(response.read().decode("utf-8"))
            
        results = []
        uid_results = summary_data.get("result", {})
        for pmid in pmids:
            item = uid_results.get(pmid, {})
            if not item:
                continue
                
            title = item.get("title", "No Title")
            # Remove trailing periods if present in PubMed title
            if title.endswith("."):
                title = title[:-1]
                
            authors = [a.get("name", "") for a in item.get("authors", [])]
            author_str = f"{authors[0]} et al." if len(authors) > 1 else (authors[0] if authors else "Unknown")
            pub_date = item.get("pubdate", "Unknown")
            year = pub_date.split()[0] if pub_date else "Unknown"
            source = item.get("source", "PubMed")
            
            # Extract DOI
            doi = ""
            for article_id in item.get("articleids", []):
                if article_id.get("idtype") == "doi":
                    doi = article_id.get("value", "")
                    break
                    
            link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            
            # Vancouver Citation assembly: Author(s). Title. Journal. Year;volume(issue):pages.
            citation_text = f"{author_str}. {title}. {source}. {year}."
            if doi:
                doi_link = f"https://doi.org/{doi}"
            else:
                doi_link = link
                
            results.append({
                "pmid": pmid,
                "title": title,
                "author_summary": author_str,
                "year": year,
                "source": source,
                "doi": doi,
                "link": doi_link,
                "citation": citation_text
            })
        return results
    except Exception as e:
        # Fail silently in CLI, return empty results
        print(f"PubMed search error: {e}", file=sys.stderr)
        return []
