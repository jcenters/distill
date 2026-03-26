#!/usr/bin/env python3
"""
clip.py — Headless web clipper for Obsidian

Fetches a URL using Scrapling (bypasses Cloudflare and bot detection),
extracts the main article content using readability-lxml, converts to
clean Markdown using markdownify, and saves to your Obsidian vault.

Designed for use with AI agents (Claude, etc.) running on a server.
No browser extension required.

Usage:
    python clip.py <url> [topic]

    topic: subfolder under $OBSIDIAN_CLIPPINGS/ (e.g. "tech", "research")
           Defaults to "research".

Environment variables:
    OBSIDIAN_VAULT       Path to your Obsidian vault (default: ~/Documents/Obsidian)
    OBSIDIAN_CLIPPINGS   Path to clippings folder (default: $OBSIDIAN_VAULT/clippings)

Output (stdout, JSON):
    {"file": "relative/path.md", "title": "Page Title", "topic": "research"}

Exit codes:
    0 = success
    1 = fetch failed
    2 = extraction failed
"""

import sys
import os
import re
import json
import datetime
import logging

# Suppress library noise
logging.getLogger().setLevel(logging.ERROR)

from scrapling import Fetcher
from readability import Document
from markdownify import markdownify as md
import trafilatura

# ── Configuration ──────────────────────────────────────────────────────────────

DEFAULT_VAULT = os.path.expanduser(
    os.environ.get("OBSIDIAN_VAULT", "~/Documents/Obsidian")
)
VAULT = DEFAULT_VAULT
CLIPPINGS_BASE = os.environ.get(
    "OBSIDIAN_CLIPPINGS", os.path.join(VAULT, "clippings")
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def slugify(text, max_len=60):
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = text.strip("-")
    return text[:max_len]


def clean_markdown(text):
    """Post-process: collapse blank lines, clean up markdownify artifacts."""
    # fix definition list artifact: "  :   - item" → "  - item"
    text = re.sub(r"^\s*:\s{3}", "  ", text, flags=re.MULTILINE)
    # collapse 3+ consecutive blank lines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # strip trailing whitespace
    text = "\n".join(line.rstrip() for line in text.splitlines())
    return text.strip()


# ── Fetch ──────────────────────────────────────────────────────────────────────

def fetch_html(url):
    """Fetch URL via Scrapling (headless browser, bypasses bot detection)."""
    fetcher = Fetcher(auto_match=False)
    try:
        page = fetcher.get(url, stealthy_headers=True)
        if page.status != 200:
            return None, f"HTTP {page.status}"
        return page.html_content, None
    except Exception as e:
        return None, str(e)


# ── Extract ────────────────────────────────────────────────────────────────────

def extract_markdown(html, url):
    """
    Primary: readability-lxml + markdownify (preserves list structure).
    Fallback: trafilatura (better noise removal for some page types).
    """
    try:
        doc = Document(html)
        content_html = doc.summary()
        if content_html and len(content_html) > 200:
            result = md(
                content_html,
                heading_style="ATX",
                bullets="-",
                strip=["img", "script", "style"],
            )
            result = clean_markdown(result)
            if result and len(result) > 100:
                return result
    except Exception:
        pass

    # Fallback: trafilatura
    result = trafilatura.extract(
        html,
        url=url,
        include_links=True,
        include_images=False,
        output_format="markdown",
        favor_recall=True,
    )
    if result:
        result = clean_markdown(result)
    return result


def extract_title(html, url):
    """Extract page title from metadata or <title> tag."""
    try:
        meta = trafilatura.extract_metadata(html, default_url=url)
        if meta and meta.title:
            return meta.title
    except Exception:
        pass
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip()
    return url


# ── Save ───────────────────────────────────────────────────────────────────────

def save_clip(url, topic="research"):
    html, err = fetch_html(url)
    if err:
        return {"error": f"Fetch failed: {err}", "url": url}

    content = extract_markdown(html, url)
    if not content:
        return {"error": "Content extraction failed", "url": url}

    title = extract_title(html, url)
    today = datetime.date.today().isoformat()
    slug = slugify(title)
    filename = f"{today}-{slug}.md"

    topic_dir = os.path.join(CLIPPINGS_BASE, topic)
    os.makedirs(topic_dir, exist_ok=True)
    filepath = os.path.join(topic_dir, filename)

    # avoid clobbering existing files
    counter = 1
    while os.path.exists(filepath):
        filepath = os.path.join(topic_dir, f"{today}-{slug}-{counter}.md")
        filename = os.path.basename(filepath)
        counter += 1

    relative_path = os.path.relpath(filepath, VAULT)

    frontmatter = (
        f'---\ntitle: "{title.replace(chr(34), chr(39))}"\n'
        f"source: {url}\n"
        f"clipped: {today}\n"
        f"topic: {topic}\n"
        f"---\n\n"
    )

    with open(filepath, "w") as f:
        f.write(frontmatter + content)

    return {
        "file": relative_path,
        "title": title,
        "topic": topic,
        "url": url,
        "path": filepath,
    }


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: clip.py <url> [topic]"}))
        sys.exit(1)

    url = sys.argv[1]
    topic = sys.argv[2] if len(sys.argv) > 2 else "research"

    result = save_clip(url, topic)
    print(json.dumps(result))

    if "error" in result:
        sys.exit(2 if "extraction" in result.get("error", "") else 1)
