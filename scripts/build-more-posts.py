#!/usr/bin/env python3
"""Fill the "More posts to read" block on every blog post.

Reads content/catalog.json and writes three cards into each
blog/<slug>/index.html. The block sits after .article-body, inside
.wrap. The current post is excluded. Cards prefer related posts and
fill any open slots with the most recent others.

Run from the repo root after adding or editing a catalog entry:

    python3 scripts/build-more-posts.py
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOG = ROOT / "blog"
CATALOG = ROOT / "content" / "catalog.json"

STOP = {
    "a", "an", "the", "and", "or", "of", "to", "for", "in", "on", "at", "by",
    "with", "from", "into", "about", "as", "is", "are", "was", "were", "be",
    "been", "being", "it", "its", "it's", "this", "that", "these", "those",
    "you", "your", "we", "our", "they", "their", "what", "who", "how", "why",
    "when", "where", "which", "before", "after", "than", "then", "too", "very",
    "just", "not", "but", "can", "must", "will", "has", "have", "had", "over",
    "under", "across", "through", "most", "more", "other", "also", "new",
    "khalid", "parekh", "amsys",
}

SECTION_RE = re.compile(
    r"\n\s*<!-- more-posts:catalog -->\s*"
    r"<section class=\"more-posts\"[\s\S]*?</section>"
    r"|\n\s*<section class=\"more-posts\"[\s\S]*?</section>"
)


def tokens(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [word for word in words if word not in STOP and len(word) > 2]


def shares(left: list[str], right: list[str]) -> int:
    used: set[int] = set()
    hits = 0
    for word in left:
        for index, other in enumerate(right):
            if index in used:
                continue
            same = word == other
            # "strategy" / "strategies" share a stem but neither starts with the other.
            stem = len(word) >= 6 and len(other) >= 6 and word[:6] == other[:6]
            if same or stem:
                used.add(index)
                hits += 1
                break
    return hits


def pick_posts(current: dict, posts: list[dict]) -> list[dict]:
    title = tokens(current.get("title") or "")
    excerpt = tokens(current.get("excerpt") or "")
    ranked = []
    for post in posts:
        if post["slug"] == current["slug"]:
            continue
        post_title = tokens(post.get("title") or "")
        post_excerpt = tokens(post.get("excerpt") or "")
        score = (
            shares(title, post_title) * 4
            + shares(title, post_excerpt)
            + shares(excerpt, post_title)
        )
        ranked.append((score, post["date"], post["slug"], post))
    ranked.sort(key=lambda row: (row[0], row[1], row[2]), reverse=True)

    chosen: list[dict] = []
    seen: set[str] = set()
    for score, _date, slug, post in ranked:
        # A single shared word is too weak to beat a newer post.
        if score < 2:
            break
        chosen.append(post)
        seen.add(slug)
        if len(chosen) == 3:
            return chosen

    recent = sorted(
        (
            post
            for post in posts
            if post["slug"] != current["slug"] and post["slug"] not in seen
        ),
        key=lambda post: (post["date"], post["slug"]),
        reverse=True,
    )
    for post in recent:
        chosen.append(post)
        if len(chosen) == 3:
            break
    return chosen


def display_date(iso: str) -> str:
    parsed = datetime.strptime(iso, "%Y-%m-%d")
    return f"{parsed.strftime('%b')} {parsed.day}, {parsed.year}"


def display_excerpt(text: str, limit: int = 148) -> str:
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    cleaned = re.sub(r"\s*(\[\s*…\s*\]|\[\s*\.\.\.\s*\])\s*$", "", cleaned).strip()
    if len(cleaned) > limit:
        cleaned = cleaned[:limit].rsplit(" ", 1)[0].rstrip(" ,;:—-")
        return cleaned + "…"
    if cleaned and cleaned[-1] not in ".!?…\"'”":
        parts = cleaned.split(" ")
        if len(parts) > 1 and len(parts[-1]) <= 2:
            cleaned = " ".join(parts[:-1]).rstrip(" ,;:—-")
        return cleaned + "…"
    return cleaned


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_section(posts: list[dict]) -> str:
    cards = []
    for post in posts:
        cards.append(
            "\n".join(
                [
                    f'          <a class="mag-item" href="../{esc(post["slug"])}/">',
                    f'            <div class="meta">{esc(display_date(post["date"]))}</div>',
                    f'            <h3>{esc(post["title"])}</h3>',
                    f'            <p>{esc(display_excerpt(post.get("excerpt") or ""))}</p>',
                    '            <span class="more">Read →</span>',
                    "          </a>",
                ]
            )
        )
    body = "\n".join(cards)
    return (
        "    <!-- more-posts:catalog -->\n"
        '    <section class="more-posts" aria-labelledby="more-posts-heading">\n'
        '      <div class="wrap">\n'
        '        <h2 id="more-posts-heading">More posts to read</h2>\n'
        '        <div class="mag-cols">\n'
        f"{body}\n"
        "        </div>\n"
        "      </div>\n"
        "    </section>"
    )


def inject(html: str, section: str) -> str:
    if 'class="article-body"' not in html:
        raise SystemExit("Refusing to edit a page without .article-body")
    if SECTION_RE.search(html):
        return SECTION_RE.sub("\n" + section, html, count=1)
    start = html.find('class="article-body"')
    end = html.find("</article>", start)
    if end < 0:
        raise SystemExit("Refusing to edit a page without a closing </article>")
    end += len("</article>")
    return html[:end] + "\n" + section + html[end:]


def article_pages() -> list[tuple[Path, str, str]]:
    pages = []
    for path in sorted(BLOG.glob("*/index.html")):
        text = path.read_text(encoding="utf-8")
        if 'class="article-body"' not in text:
            continue
        pages.append((path, path.parent.name, text))
    return pages


def load_catalog(page_slugs: set[str]) -> list[dict]:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    posts = []
    for entry in catalog:
        slug = entry.get("slug")
        if not slug or not entry.get("title") or not entry.get("date"):
            raise SystemExit(f"Catalog entry missing slug, title, or date: {entry!r}")
        if slug not in page_slugs:
            print(f"skip {slug}: no blog/{slug}/index.html", file=sys.stderr)
            continue
        posts.append(entry)
    return posts


def main() -> int:
    check_only = "--check" in sys.argv
    pages = article_pages()
    page_slugs = {slug for _path, slug, _text in pages}
    posts = load_catalog(page_slugs)
    by_slug = {post["slug"]: post for post in posts}
    missing = sorted(page_slugs - set(by_slug))
    for slug in missing:
        print(
            f"warn {slug}: page exists but is not in content/catalog.json, "
            "so other posts will not link to it",
            file=sys.stderr,
        )

    failures = []
    for path, slug, html in pages:
        current = by_slug.get(slug) or {
            "slug": slug,
            "title": slug.replace("-", " "),
            "date": "1970-01-01",
            "excerpt": "",
        }
        chosen = pick_posts(current, posts)
        section = render_section(chosen)
        updated = inject(html, section)
        if check_only:
            if updated != html:
                failures.append(f"{path.relative_to(ROOT)} is stale; re-run the script")
        elif updated != html:
            path.write_text(updated, encoding="utf-8")
            print(f"updated {path.relative_to(ROOT)}")
        else:
            print(f"ok {path.relative_to(ROOT)}")

        hrefs = re.findall(r'class="mag-item" href="([^"]+)"', section)
        titles = re.findall(r"<h3>(.*?)</h3>", section)
        if len(hrefs) != 3 or len(titles) != 3:
            failures.append(f"{slug}: expected 3 cards, found {len(hrefs)}")
        if f"../{slug}/" in hrefs:
            failures.append(f"{slug}: section includes the current post")
        if any(not title.strip() for title in titles):
            failures.append(f"{slug}: card is missing descriptive anchor text")

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    print(f"{len(pages)} posts, 3 cards each")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
