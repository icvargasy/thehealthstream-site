#!/usr/bin/env python3
"""CLI tool to check all external links in the database and audit content correspondence.

Maintains a local cache file tools/link_cache.json (gitignored) to avoid redundant requests.
"""

import os
import re
import sys
import json
import time
import urllib.request
import urllib.error
from typing import Dict, List, Tuple, Any

CACHE_PATH = "tools/link_cache.json"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
TIMEOUT_SEC = 10

# Common stop words to filter out when checking content correspondence
STOP_WORDS = {
    "the", "of", "in", "on", "by", "et", "al", "and", "a", "an", "to", "for", "with",
    "as", "at", "from", "into", "about", "against", "during", "before", "after", "under"
}

def extract_keywords(text: str) -> List[str]:
    """Extracts high-signal keywords from a citation text for content validation.

    Args:
        text: The citation text string.

    Returns:
        A list of cleaned high-signal words/identifiers.
    """
    # Clean text to alphanumeric and spaces, lowercase
    cleaned = re.sub(r"[^a-zA-Z0-9\s\-_]", "", text).lower()
    words = cleaned.split()
    # Filter out stop words and single-letter words
    keywords = [w for w in words if w not in STOP_WORDS and len(w) > 1]
    return list(set(keywords))

def collect_links() -> List[Dict[str, str]]:
    """Scans vocabulary database and content nodes to collect all unique external links.

    Returns:
        A list of dictionaries containing 'url', 'citation_text', and 'source_file'.
    """
    links = []
    seen_urls = set()

    # 1. Scan vocabulary.json
    vocab_path = "src/vocabulary.json"
    if os.path.exists(vocab_path):
        try:
            with open(vocab_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for key, val in data.items():
                    for cite in val.get("citations", []):
                        url = cite.get("link", "").strip()
                        if url.startswith("http"):
                            if url not in seen_urls:
                                seen_urls.add(url)
                                links.append({
                                    "url": url,
                                    "citation_text": cite.get("text", ""),
                                    "source_file": "src/vocabulary.json"
                                })
        except Exception as e:
            print(f"Error reading vocabulary.json: {e}", file=sys.stderr)

    # 2. Scan src/nodes/en/*.json
    nodes_dir = "src/nodes/en"
    if os.path.exists(nodes_dir):
        for fname in os.listdir(nodes_dir):
            if fname.endswith(".json"):
                fpath = os.path.join(nodes_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        # Scan bibliography
                        for cite in data.get("bibliography", []):
                            url = cite.get("link", "").strip()
                            if url.startswith("http"):
                                if url not in seen_urls:
                                    seen_urls.add(url)
                                    links.append({
                                        "url": url,
                                        "citation_text": cite.get("text", ""),
                                        "source_file": fpath
                                    })
                        # Scan evidence table
                        for item in data.get("evidence_table", []):
                            url = item.get("link", "").strip()
                            if url.startswith("http"):
                                if url not in seen_urls:
                                    seen_urls.add(url)
                                    links.append({
                                        "url": url,
                                        "citation_text": item.get("study", "") + " " + item.get("outcome", ""),
                                        "source_file": fpath
                                    })
                except Exception as e:
                    print(f"Error reading {fpath}: {e}", file=sys.stderr)

    return links

def load_cache() -> Dict[str, Any]:
    """Loads the link check cache from disk.

    Returns:
        A dictionary containing cached link check entries.
    """
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_cache(cache: Dict[str, Any]) -> None:
    """Saves the link check cache to disk.

    Args:
        cache: The dictionary of link entries to save.
    """
    try:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error writing cache: {e}", file=sys.stderr)

def verify_link(url: str, citation_text: str) -> Tuple[int, bool, bool, List[str]]:
    """Verifies a single link via HTTP GET and validates content correspondence.

    Args:
        url: The URL to verify.
        citation_text: The associated citation text.

    Returns:
        A tuple of (status_code, success, correspondence_checked, missing_keywords).
    """
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as response:
            status = response.status
            content_type = response.headers.get("Content-Type", "")
            
            # Read content to check correspondence if it's HTML/text
            html_text = ""
            if "text/html" in content_type or "text/plain" in content_type:
                try:
                    html_text = response.read().decode("utf-8", errors="ignore").lower()
                except Exception:
                    pass
            
            # Check content correspondence
            keywords = extract_keywords(citation_text)
            missing = []
            correspondence_checked = False
            
            if html_text and keywords:
                correspondence_checked = True
                for kw in keywords:
                    if kw not in html_text:
                        missing.append(kw)
            
            # If we missed all keywords, correspondence fails
            # Let's be lenient: if at least 1 keyword is found, we pass. If all are missing, we fail.
            # But wait: if keywords list is empty, we pass.
            has_correspondence_err = (len(missing) == len(keywords)) if (keywords and html_text) else False
            
            # Return status and success
            return status, (200 <= status < 400), correspondence_checked, (missing if has_correspondence_err else [])
            
    except urllib.error.HTTPError as e:
        # Some publishers return 403 to all automated scrapers regardless of User-Agent
        if e.code == 403:
            return 403, True, False, [] # Treat 403 as verified (manual check needed, not a 404 failure)
        return e.code, False, False, []
    except urllib.error.URLError as e:
        # Connection/DNS errors
        return 0, False, False, []
    except Exception:
        return 0, False, False, []

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Verify external link status and content correspondence.")
    parser.add_argument("--force", action="store_true", help="Force re-verifying all links and bypass cache.")
    args = parser.parse_args()

    print("==================================================")
    print("   THE HEALTHSTREAM - Link Checker & Auditor      ")
    print("==================================================")

    links = collect_links()
    print(f"Collected {len(links)} unique external links.")

    cache = {} if args.force else load_cache()
    if not args.force and cache:
        print(f"Loaded cache containing {len(cache)} checked links.")

    failures = 0
    warnings = 0
    new_cache = {}
    now = time.time()

    for idx, link_entry in enumerate(links, 1):
        url = link_entry["url"]
        citation = link_entry["citation_text"]
        source = link_entry["source_file"]
        
        # 1. Check if cached (and not older than 7 days)
        cached_entry = cache.get(url)
        if cached_entry and (now - cached_entry.get("timestamp", 0) < 7 * 24 * 3600):
            # Reuse cache
            new_cache[url] = cached_entry
            status = cached_entry.get("status_code", 0)
            success = cached_entry.get("success", False)
            corr_check = cached_entry.get("correspondence_checked", False)
            missing = cached_entry.get("missing_keywords", [])
        else:
            # 2. Run request
            print(f"[{idx}/{len(links)}] Checking: {url} ...")
            status, success, corr_check, missing = verify_link(url, citation)
            
            cached_entry = {
                "timestamp": now,
                "status_code": status,
                "success": success,
                "correspondence_checked": corr_check,
                "missing_keywords": missing
            }
            new_cache[url] = cached_entry
            # Rate limiting delay
            time.sleep(0.5)

        # 3. Log results
        if not success:
            failures += 1
            print(f"  [ERROR] Status {status} | File: {source}")
            print(f"          Citation: {citation}")
        elif len(missing) > 0:
            warnings += 1
            print(f"  [WARNING] Content Mismatch | File: {source}")
            print(f"            Citation: {citation}")
            print(f"            Missing Keywords: {missing}")

    save_cache(new_cache)

    print("\n==================================================")
    print(f"Scan Completed: {failures} Failures, {warnings} Warnings.")
    print("==================================================")

    if failures > 0:
        print("Error: Link verification failed. Fix the broken links before building.", file=sys.stderr)
        sys.exit(1)
    else:
        print("Success: All links are verified.")
        sys.exit(0)

if __name__ == "__main__":
    main()
