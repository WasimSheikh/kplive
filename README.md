# Khalid Parekh — Personal Brand Website

## Preview

```bash
cd /Applications/Projects/Office/kp
python3 -m http.server 8080
```

## Menu → Routes

| Menu | Public route |
|------|--------------|
| Home | `/` |
| About | `/about/` |
| Press & News | `/press/` |
| Leadership & Vision | `/leadership/` |
| Blog | `/blog/` + `/blog/&lt;slug&gt;/` |
| Store | `/product/` |
| Contact | `/contact/` |

## Blog posts

Publish an essay at `blog/<slug>/index.html`. Copy `content/post-template.html`, then add a matching entry to `content/catalog.json` (slug, title, date, excerpt, link, kind, image) and list the URL on `blog/index.html` and in `sitemap.xml`.

The “More posts to read” block sits after `.article-body`, inside `.wrap`, on every post. Rebuild it from the catalog after each add or edit:

```bash
python3 scripts/build-more-posts.py
```

The script writes three cards — the same date, title, excerpt, and “Read →” treatment as the blog index — and leaves out the current post. It prefers related posts and fills any open slots with the most recent others. Run it again when the catalog changes so older posts link to the new one.

## Typography

- Headings: **Cormorant Garamond**
- Body: **Source Sans 3**
- Brand accent: crest crimson `#C8102E`
