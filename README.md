# Distill

**Give your AI agents clean, readable web content.**

Raw HTML is noisy — navigation bars, cookie banners, footers, ads, and a thousand lines of boilerplate for every paragraph of actual content. Feeding that to an LLM wastes tokens and buries the signal.

This tool converts any URL into clean, structured Markdown that agents can actually read. It bypasses Cloudflare and bot detection, strips boilerplate, and extracts the content that matters. Obsidian integration is included — save clips directly to your vault — but the core capability works with or without Obsidian.

## What it does

1. **Fetches** the URL using [Scrapling](https://github.com/D4Vinci/Scrapling) — a stealth headless browser that bypasses Cloudflare and other bot-detection systems that block standard HTTP requests
2. **Extracts** the main content using [readability-lxml](https://github.com/buriy/python-readability), the same engine behind Obsidian's own web clipper and Firefox Reader Mode
3. **Converts** to clean Markdown using [markdownify](https://github.com/matthewwithanm/python-markdownify), with [trafilatura](https://trafilatura.readthedocs.io/) as fallback for complex pages
4. **Saves** to your Obsidian vault with YAML frontmatter (title, source URL, date, topic) — or use the JSON output directly in your pipeline

## Who it's for

**AI agent builders.** If you're building agents that research the web, you don't want your model wading through raw HTML. Run this as a preprocessing step and feed agents clean markdown instead. Works with Claude Code, LangChain, CrewAI, custom agents — anything that can call a subprocess.

**Obsidian power users.** Run it on a server or cron job. Clip pages to your vault from anywhere, without a browser open.

**Python developers.** Use it as a library or subprocess for any pipeline that needs reliable web content extraction.

## Installation

```bash
git clone https://github.com/jcenters/distill
cd distill
pip install -r requirements.txt
playwright install chromium
```

## Usage

### Command line

```bash
# Save to $OBSIDIAN_CLIPPINGS/research/
python clip.py https://example.com/article

# Save to $OBSIDIAN_CLIPPINGS/tech/
python clip.py https://example.com/article tech
```

### From an AI agent

```python
import subprocess, json

result = json.loads(
    subprocess.check_output(["python", "clip.py", url, topic])
)
# result = {"file": "clippings/tech/2026-03-26-title.md", "title": "...", "path": "..."}
```

The agent can then read the saved Markdown file, or you can capture the extracted content inline and pass it directly to the model.

### Output format

JSON to stdout:

```json
{
  "file": "clippings/research/2026-03-26-article-title.md",
  "title": "Article Title",
  "topic": "research",
  "url": "https://example.com/article",
  "path": "/absolute/path/to/file.md"
}
```

Saved file:

```markdown
---
title: "Article Title"
source: https://example.com/article
clipped: 2026-03-26
topic: research
---

[Clean article content as Markdown — no nav, no ads, no boilerplate]
```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `OBSIDIAN_VAULT` | `~/Documents/Obsidian` | Path to your Obsidian vault |
| `OBSIDIAN_CLIPPINGS` | `$OBSIDIAN_VAULT/clippings` | Path to clippings folder |

```bash
export OBSIDIAN_VAULT=~/my-vault
python clip.py https://example.com/article research
```

## What it handles that other tools don't

**Cloudflare and bot detection.** Standard `requests` or `urllib` get blocked by most modern sites. Scrapling runs a real headless browser with stealth headers, solving this at the fetch layer.

**Boilerplate removal.** Readability extracts the main content and discards everything else — the same algorithm Firefox uses for Reader Mode. The Markdown you get is what a human would copy-paste, not the full page dump.

**Nested lists and structure.** Unlike simpler extractors, the readability + markdownify pipeline preserves nested lists, blockquotes, code blocks, and heading hierarchy.

**Fallback resilience.** If readability can't identify a main content block, trafilatura takes over — a battle-tested extraction library used by HuggingFace, IBM, and Microsoft Research.

## Credits

Built on top of excellent open-source work:

- **[Scrapling](https://github.com/D4Vinci/Scrapling)** by D4Vinci — stealth headless fetching. BSD 3-Clause License.
- **[readability-lxml](https://github.com/buriy/python-readability)** by Yuri Baburov — Python port of Mozilla Readability. Apache License 2.0.
- **[markdownify](https://github.com/matthewwithanm/python-markdownify)** by Matthew Withanm — HTML to Markdown conversion. MIT License.
- **[trafilatura](https://github.com/adbar/trafilatura)** by Adrien Barbaresi — web scraping and text extraction. Apache License 2.0.

## License

MIT
