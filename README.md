# obsidian-server-clipper

A headless web clipper for [Obsidian](https://obsidian.md/) that runs on a server — no browser extension required.

Designed for use with AI agents (Claude Code, custom agents, cron jobs) that need to save web pages to an Obsidian vault from a remote machine.

## What it does

1. **Fetches** the URL using [Scrapling](https://github.com/D4Vinci/Scrapling) — a headless browser that bypasses Cloudflare and other bot detection
2. **Extracts** the main article content using [readability-lxml](https://github.com/buriy/python-readability) (the same extraction engine used by Obsidian's own web clipper)
3. **Converts** to clean Markdown using [markdownify](https://github.com/matthewwithanm/python-markdownify), with [trafilatura](https://trafilatura.readthedocs.io/) as fallback
4. **Saves** to your Obsidian vault with YAML frontmatter (title, source URL, date, topic)

## Why server-side?

Most Obsidian clippers are browser extensions. This one runs headlessly on a server or local machine via Python — useful when:

- You want an AI agent to clip pages during research
- You're running automations on a remote server
- You need to bypass bot detection (Cloudflare, etc.) that blocks standard `requests`

## Installation

```bash
git clone https://github.com/jcenters/obsidian-server-clipper
cd obsidian-server-clipper
pip install -r requirements.txt
```

Scrapling requires Playwright browsers on first run:

```bash
playwright install chromium
```

## Usage

```bash
# Basic usage — saves to $OBSIDIAN_CLIPPINGS/research/
python clip.py https://example.com/article

# With topic — saves to $OBSIDIAN_CLIPPINGS/tech/
python clip.py https://example.com/article tech
```

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `OBSIDIAN_VAULT` | `~/Documents/Obsidian` | Path to your Obsidian vault |
| `OBSIDIAN_CLIPPINGS` | `$OBSIDIAN_VAULT/clippings` | Path to clippings folder |

```bash
export OBSIDIAN_VAULT=~/workspace
python clip.py https://example.com/article research
```

### Output

Returns JSON to stdout:

```json
{
  "file": "clippings/research/2026-03-26-article-title.md",
  "title": "Article Title",
  "topic": "research",
  "url": "https://example.com/article",
  "path": "/absolute/path/to/file.md"
}
```

### Saved file format

```markdown
---
title: "Article Title"
source: https://example.com/article
clipped: 2026-03-26
topic: research
---

[Article content as clean Markdown...]
```

## Use with AI agents

```python
import subprocess, json

result = json.loads(
    subprocess.check_output(["python", "clip.py", url, topic])
)
print(f"Clipped: {result['title']}")
print(f"Saved to: {result['file']}")
```

## Credits

This tool is built on top of excellent open-source work:

- **[Scrapling](https://github.com/D4Vinci/Scrapling)** by D4Vinci — headless browser fetching with bot-detection bypass. BSD 3-Clause License.
- **[readability-lxml](https://github.com/buriy/python-readability)** by Yuri Baburov (buriy) — Python port of Mozilla's Readability.js for main content extraction. Apache License 2.0.
- **[markdownify](https://github.com/matthewwithanm/python-markdownify)** by Matthew Withanm — HTML to Markdown conversion. MIT License.
- **[trafilatura](https://github.com/adbar/trafilatura)** by Adrien Barbaresi — web scraping and text extraction library, used as fallback extractor. Apache License 2.0.

## License

MIT
