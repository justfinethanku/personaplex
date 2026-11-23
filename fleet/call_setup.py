"""Build one PersonaPlex call link from the fleet databases.

The web client does not read a prompt from the address on its own.
This script writes the prompt, checks that five facts are actually in it,
and writes producer.html with one link that opens the queue already filled in.

Claude is Sonnet 5.5 through OpenRouter (fleet secret OPENROUTER_API_KEY).
A short role prompt does not need a larger model. The key stays in the
fleet vault; this script never writes it down.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

NEWS_URL = "https://limitededitionjonathan.com/news-factory"
SUBSTACK_FEED = "https://limitededitionjonathan.substack.com/feed"
ORIGIN = "https://spark-3368.tail6e7cfb.ts.net:8998/"
# Sonnet 5.5 spends a short budget on reasoning and returns content=null.
# This squeeze is a word cap over facts we already filtered, so 4.6 is enough.
MODEL = "anthropic/claude-sonnet-4.6"
# Phase 0 sets the useful length. 120 is the stand-in until that table exists.
DEFAULT_WORDS = 120
VOICE = "NATF2.pt"
FLEET_SQL = Path.home() / ".claude/skills/fleet-context/scripts/fleet-sql"

# Private day-to-day notes stay out of a voice prompt.
FACT_CATEGORIES = ("project", "employment", "work")


def fleet_sql(query: str) -> str:
    return subprocess.check_output(
        ["bash", str(FLEET_SQL), query, "-tA"],
        text=True,
    )


def fleet_get(name: str) -> str:
    value = subprocess.check_output(["fleet", "get", name], text=True).strip()
    if not value:
        raise RuntimeError(f"fleet get {name} returned nothing")
    return value.splitlines()[-1].strip()


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "fleet-personaplex"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", "replace")


def news_factory_latest() -> dict:
    page = fetch(NEWS_URL)
    pattern = re.compile(
        r'href="(/news-factory/[a-z0-9-]+)"[^>]*>([^<]+)</a>'
    )
    seen = set()
    for match in pattern.finditer(page):
        path, title = match.group(1), html.unescape(match.group(2)).strip()
        if path in seen or title.lower().startswith("explore"):
            continue
        seen.add(path)
        return {
            "title": title,
            "url": "https://limitededitionjonathan.com" + path,
            "source": NEWS_URL,
        }
    raise RuntimeError("no News Factory story found on the index")


def substack_latest() -> dict:
    feed = fetch(SUBSTACK_FEED)
    root = ET.fromstring(feed)
    item = root.find(".//item")
    if item is None:
        raise RuntimeError("substack feed had no items")
    return {
        "title": (item.findtext("title") or "").strip(),
        "url": (item.findtext("link") or "").strip(),
        "source": SUBSTACK_FEED,
    }


def person_lines() -> list[str]:
    rows = fleet_sql(
        "SELECT category || '|' || attribute || '|' || left(value, 180) "
        "FROM person_facts WHERE person_id = 23 "
        "AND coalesce(status,'') NOT IN ('rejected','superseded') "
        "AND category IN ('project','employment') "
        "ORDER BY created_at DESC LIMIT 6"
    )
    lines = []
    for line in rows.splitlines():
        if not line.strip():
            continue
        category, attribute, value = line.split("|", 2)
        if any(word in value.lower() for word in ("password", "passcode", "keychain", "token")):
            continue
        lines.append(f"{category}/{attribute}: {value}")
    return lines


def recent_context() -> list[str]:
    rows = fleet_sql(
        "SELECT kind || '|' || left(title, 140) FROM project_context "
        "WHERE project IN ('lej','lej-website','lej-news-factory') "
        "AND kind IN ('decision','spec') "
        "AND title NOT ILIKE 'session prompts%' "
        "AND title NOT ILIKE 'gemini%' "
        "ORDER BY created_at DESC LIMIT 5"
    )
    return [line for line in rows.splitlines() if line.strip()]


def graph_projects() -> list[str]:
    script = (
        'MATCH (p:Person {name:"Jonathan Edwards"})-[r:WORKS_FOR|PART_OF]->(n) '
        "RETURN type(r), head(labels(n)), n.name LIMIT 12"
    )
    try:
        out = subprocess.check_output(
            ["python3", str(Path.home() / ".claude/data/mem"), "graph", script],
            text=True,
            timeout=30,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        return [f"neo4j unavailable: {exc}"]
    return [line.strip() for line in out.splitlines() if line.strip()]


def distinctive(title: str) -> str:
    cleaned = re.sub(r"[’']s\b", "", title)
    words = re.findall(r"[A-Za-z][A-Za-z0-9+-]{2,}", cleaned)
    stop = {"the", "and", "for", "with", "from", "that", "this", "its", "his", "her"}
    for word in words:
        if word[0].isupper() and word.lower() not in stop:
            return word
    return " ".join(title.split()[:4])


def sources() -> dict:
    news = news_factory_latest()
    post = substack_latest()
    return {
        "news": news,
        "substack": post,
        "person_facts": person_lines(),
        "project_context": recent_context(),
        "neo4j": graph_projects(),
        "facts": {
            "name": "Ruby",
            "employer": "Limited Edition Jonathan",
            "desk": "News Factory",
            "story": distinctive(news["title"]),
            "company": "AI Cred",
        },
    }


def squeeze(bundle: dict, words: int) -> str:
    facts = bundle["facts"]
    phrases = list(facts.values())
    system = (
        "You write the text role prompt for a full-duplex voice model. "
        "The speaker is a podcast producer in the room with Jon, prepping the next episode. "
        f"Use at most {words} words. Output only the prompt, no quotes and no label. "
        "Use short spoken sentences. Do not invent facts. "
        "The first two sentences state her name, her employer, and the desk as facts she already knows."
    )
    user = (
        "Include each of these phrases exactly, once, as facts. Do not write 'if asked': "
        + "; ".join(phrases)
        + ".\n"
        "She is prepping an episode about this News Factory story: "
        f"{bundle['news']['title']} ({bundle['news']['url']}).\n"
        "His latest Substack post is: "
        f"{bundle['substack']['title']} ({bundle['substack']['url']}).\n"
        "Person facts, already filtered:\n- "
        + "\n- ".join(bundle["person_facts"] or ["none"])
        + "\nRecent fleet notes:\n- "
        + "\n- ".join(bundle["project_context"] or ["none"])
        + "\nGraph lines:\n- "
        + "\n- ".join(bundle["neo4j"] or ["none"])
        + "\nThe episode topic is the News Factory story. "
        "Mention the Substack title only if it still fits the word cap."
    )
    key = fleet_get("OPENROUTER_API_KEY")
    body = json.dumps(
        {
            "model": MODEL,
            "temperature": 0.2,
            "max_tokens": 800,
            "reasoning": {"enabled": False},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
    ).encode()
    request = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        payload = json.loads(response.read().decode())
    if "error" in payload:
        raise RuntimeError(json.dumps(payload["error"])[:1500])
    message = payload["choices"][0]["message"]
    text = message.get("content") or ""
    if not text.strip():
        raise RuntimeError("empty completion: " + json.dumps(message)[:1500])
    text = re.sub(r"^```[a-z]*\n?|```$", "", text).strip().strip('"')
    return text


def call_url(prompt: str) -> str:
    query = urllib.parse.urlencode(
        {
            "text_prompt": prompt,
            "voice_prompt": VOICE,
            "autostart": "1",
        }
    )
    return ORIGIN + "?" + query


def write_page(path: Path, url: str, facts: dict, words: int, drift_note: str) -> None:
    items = "".join(f"<li>{html.escape(label)}: {html.escape(value)}</li>" for label, value in facts.items())
    page = f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Producer: next episode</title>
<style>
  body {{ font: 18px/1.4 system-ui, sans-serif; margin: 2rem auto; max-width: 38rem; color: #1a1a1a; }}
  a.tap {{ display: inline-block; background: #111; color: #fff; text-decoration: none;
           padding: 0.8rem 1.1rem; border-radius: 999px; }}
  p, li {{ font-size: 0.95rem; }}
  .note {{ color: #444; }}
</style>
<h1>Producer: next episode</h1>
<p><a class="tap" href="{html.escape(url, quote=True)}">Producer: next episode</a></p>
<p class="note">Opens the PersonaPlex queue with a {words}-word prompt already filled in, voice NATF2.
The browser will ask for the microphone. The prompt was built from the News Factory, the Substack feed,
person facts, project_context, and the graph.</p>
<p class="note">{html.escape(drift_note)}</p>
<ul>{items}</ul>
</html>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(page)


def direct_prompt(facts: dict) -> str:
    """Say each fact as its own sentence. A narrative squeeze kept the phrases
    but the voice model did not answer with them."""
    return (
        f"Your name is {facts['name']}. "
        f"You work for {facts['employer']}. "
        f"The story is on the {facts['desk']} page. "
        f"Today's story is about {facts['story']}. "
        f"Jon co-founded {facts['company']} with Nate Jones. "
        "You are a podcast producer prepping the next episode with him. "
        "Ask short questions. Do not invent facts."
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--words", type=int, default=DEFAULT_WORDS)
    parser.add_argument("--topic", default="", help="Unused override kept for the spec's call-type interface.")
    parser.add_argument("--type", default="producer")
    parser.add_argument("--sources-only", action="store_true")
    parser.add_argument(
        "--direct",
        action="store_true",
        help="State each fact as its own sentence instead of asking Claude to paraphrase.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("/home/lej/clients/LEJ/personaplex/var/fleet-335/call"),
    )
    args = parser.parse_args()
    if args.type != "producer":
        raise SystemExit("only the producer call is built in this job")
    bundle = sources()
    if args.topic:
        bundle["topic_override"] = args.topic
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "sources.json").write_text(json.dumps(bundle, indent=2))
    print("sources", args.out / "sources.json")
    print("facts", json.dumps(bundle["facts"]))
    if args.sources_only:
        return
    prompt = direct_prompt(bundle["facts"]) if args.direct else squeeze(bundle, args.words)
    missing = [v for v in bundle["facts"].values() if v not in prompt]
    if missing and not args.direct:
        prompt = squeeze(bundle, args.words)
        missing = [v for v in bundle["facts"].values() if v not in prompt]
    if missing or "if asked" in prompt.lower():
        raise SystemExit(f"prompt is missing facts or hides them: {missing}\n---\n{prompt}")
    opening = " ".join(prompt.split()[:40]).lower()
    for phrase in ("ruby", "limited edition jonathan", "news factory"):
        if phrase not in opening:
            raise SystemExit(f"opening does not state {phrase!r}\n---\n{prompt}")
    count = len(prompt.split())
    if count > args.words + 15:
        raise SystemExit(f"prompt is {count} words, cap is {args.words}")
    url = call_url(prompt)
    if len(url) > 7000:
        raise SystemExit(f"call url is {len(url)} chars; the server line limit is 8190")
    summary = Path(__file__).resolve().parent / "phase0" / "drift_summary.json"
    if summary.exists():
        drift = json.loads(summary.read_text())
        note = drift.get("reconnect_note", "")
    else:
        note = "Reconnect note is filled in after the Phase 0 drift table."
    record = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "model": "direct" if args.direct else MODEL,
        "words": count,
        "word_cap": args.words,
        "voice": VOICE,
        "prompt": prompt,
        "facts": bundle["facts"],
        "url": url,
        "news": bundle["news"],
        "substack": bundle["substack"],
    }
    (args.out / "call.json").write_text(json.dumps(record, indent=2))
    write_page(args.out / "producer.html", url, bundle["facts"], count, note)
    print(f"words={count} url_chars={len(url)}")
    print("page", args.out / "producer.html")


if __name__ == "__main__":
    main()
