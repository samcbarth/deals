#!/usr/bin/env python3
"""Static build for deals.samcbarth.com (Deal Notes).

Sources (edit these, never the generated HTML):
  data/site.json            site name, nav, network bar
  data/guides/<slug>.json   one buying guide each, with its product picks
  data/pages/<slug>.json    deal-event guides, explainers, legal pages
  data/news/<slug>.json     one news story each
  assets/config.js          AMAZON_TAG / ADSENSE_CLIENT / HubSpot ids

Run:  python build.py      (writes HTML, feeds, sitemap etc. into the repo root)
"""
import html, json, pathlib, re, shutil, sys
from datetime import datetime, timezone
from urllib.parse import quote_plus

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT / "data"
SITE = json.loads((DATA / "site.json").read_text(encoding="utf-8"))
BASE = SITE["base"].rstrip("/")
NAME = SITE["name"]
NEWS_BRAND = SITE["news_brand"]
BUILD_DATE = "2026-11-09"

GTM = '''<script async src="https://www.googletagmanager.com/gtm.js?id=GTM-KMS4X55L"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
</script>'''

DISCLOSURE = ('<p class="disclosure">Disclosure: As an Amazon Associate, Deal Notes earns from qualifying purchases. '
              'Some links on this page may earn us a commission at no extra cost to you. '
              '<a href="/affiliate-disclosure/">How this works</a>.</p>')

GENERATED_DIRS = ["guides", "deal-events", "news", "how-to-spot-a-real-deal", "price-history",
                  "about", "contact", "privacy", "terms", "affiliate-disclosure"]


def esc(s):
    return html.escape(str(s), quote=True)


def read_config():
    txt = (ROOT / "assets" / "config.js").read_text(encoding="utf-8")
    out = {}
    for key in ("AMAZON_TAG", "ADSENSE_CLIENT"):
        m = re.search(key + r"\s*:\s*'([^']*)'", txt)
        out[key] = m.group(1).strip() if m else ""
    return out


CFG = read_config()


def load_dir(name):
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted((DATA / name).glob("*.json"))]


GUIDE_ORDER = ["kitchen", "home-office", "tech-accessories", "tools", "outdoor", "gifts"]
GUIDES = sorted(load_dir("guides"), key=lambda g: GUIDE_ORDER.index(g["slug"]) if g["slug"] in GUIDE_ORDER else 99)
GUIDE_BY_SLUG = {g["slug"]: g for g in GUIDES}
PAGES = load_dir("pages")
PAGE_BY_SLUG = {p["slug"]: p for p in PAGES}
NEWS = sorted(load_dir("news"), key=lambda s: s["date_published"], reverse=True)
EVENT_ORDER = ["black-friday", "cyber-monday", "prime-day", "back-to-school"]
EVENTS = [PAGE_BY_SLUG[s] for s in EVENT_ORDER if s in PAGE_BY_SLUG]


def resolve_gifts():
    for g in GUIDES:
        if not g.get("gift_mode"):
            continue
        picks = []
        for ref in g["gift_refs"]:
            gslug, pid = ref.split("/")
            src = GUIDE_BY_SLUG[gslug]
            pick = next(p for p in src["picks"] if p["id"] == pid)
            picks.append(dict(pick, from_guide=gslug))
        g["picks"] = picks


resolve_gifts()


# ---------- images ----------
IMAGES = {
    "home": ("Deal Notes", "Buying guides and deal-event help", "#0f6b5c"),
    "guides": ("Buying guides", "Picks backed by published testing", "#0f6b5c"),
    "events": ("Deal events", "Dates straight from Amazon", "#8a3b12"),
    "news": (NEWS_BRAND, "Sales events, recalls, launches", "#243b6b"),
    "guide-kitchen": ("Kitchen", "Gear worth buying", "#7a3e1d"),
    "guide-home-office": ("Home office", "Webcam, keyboard, mouse", "#2f4a6d"),
    "guide-tech": ("Tech accessories", "Chargers, cables, power banks", "#3b3f8f"),
    "guide-tools": ("Tools", "A first toolkit", "#6b5a12"),
    "guide-outdoor": ("Outdoor", "Camp and day-trip gear", "#2d6a3e"),
    "guide-gifts": ("Gifts", "By recipient and budget", "#8f2d4d"),
    "event-black-friday": ("Black Friday 2026", "November 27", "#1f1f1f"),
    "event-cyber-monday": ("Cyber Monday 2026", "November 30", "#1d3d5c"),
    "event-prime-day": ("Prime Day", "Dates and rules", "#155e75"),
    "event-back-to-school": ("Back to school", "When to shop", "#7c4a03"),
    "explainer-real-deal": ("Spot a real deal", "7 checks before you buy", "#0f6b5c"),
    "explainer-price-history": ("Price history", "How to read the chart", "#0f6b5c"),
    "news-retail": ("Retail events", NEWS_BRAND, "#243b6b"),
    "news-recall": ("Recall", NEWS_BRAND, "#9b1c1c"),
    "news-tech": ("Tech launch", NEWS_BRAND, "#3b3f8f"),
}


def make_images():
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Pillow missing: skipping image generation (pip install pillow)")
        return
    out = ROOT / "assets" / "img"
    (out / "og").mkdir(parents=True, exist_ok=True)
    fonts = pathlib.Path("C:/Windows/Fonts")

    def font(bold, size):
        for f in (["segoeuib.ttf", "arialbd.ttf"] if bold else ["segoeui.ttf", "arial.ttf"]):
            if (fonts / f).exists():
                return ImageFont.truetype(str(fonts / f), size)
        return ImageFont.load_default()

    for key, (title, sub, color) in IMAGES.items():
        webp, png = out / f"{key}.webp", out / "og" / f"{key}.png"
        if webp.exists() and png.exists():
            continue
        # samcbarth.com brand: black field, purple glow, 2px black-to-purple rule, uppercase type.
        im = Image.new("RGB", (1200, 630), (0, 0, 0))
        glow = Image.new("RGB", (1200, 630), (0, 0, 0))
        gd = ImageDraw.Draw(glow)
        for i in range(60):
            r = 620 - i * 9
            c = (int(154 * i / 60 * .55), 0, int(255 * i / 60 * .55))
            gd.ellipse([1180 - r, 80 - r, 1180 + r, 80 + r], fill=c)
        im.paste(glow)
        d = ImageDraw.Draw(im)
        for x in range(1200):
            d.line([(x, 540), (x, 541)], fill=(int(154 * x / 1199), 0, int(255 * x / 1199)))
        d.ellipse([72, 142, 88, 158], fill=(154, 0, 255))
        d.text((104, 128), "DEAL NOTES", font=font(True, 30), fill=(142, 124, 195))
        d.text((70, 200), title.upper(), font=font(True, 96), fill="white")
        d.text((74, 340), sub.upper(), font=font(False, 44), fill=(205, 205, 205))
        d.text((72, 566), "DEALS.SAMCBARTH.COM", font=font(True, 28), fill=(200, 200, 200))
        im.save(webp, "WEBP", quality=80)
        im.save(png, "PNG", optimize=True)


# ---------- helpers ----------
def amazon_url(pick):
    a = pick["amazon"]
    tag = CFG["AMAZON_TAG"]
    if a.get("asin"):
        url = f"https://www.amazon.com/dp/{a['asin']}"
        return url + (f"?tag={quote_plus(tag)}" if tag else "")
    url = f"https://www.amazon.com/s?k={quote_plus(a['search'])}"
    return url + (f"&tag={quote_plus(tag)}" if tag else "")


def amazon_button(pick):
    return (f'<a class="btn-amz" data-amazon href="{esc(amazon_url(pick))}" target="_blank" '
            f'rel="sponsored nofollow noopener">Check price on Amazon</a>')


def live_price(pick):
    """Only renders when a Product Advertising API price has been written into the JSON."""
    p = pick.get("price") or {}
    if not (p.get("live") and p.get("fetched_at")):
        return ""
    return (f'<p class="meta">Price at Amazon: {esc(p.get("currency", "$"))}{esc(p["live"])} '
            f'(as of {esc(p["fetched_at"])}; prices change, the price on Amazon at purchase applies).</p>')


def nice_date(iso):
    d = datetime.fromisoformat(iso[:10])
    return d.strftime("%B %-d, %Y") if sys.platform != "win32" else d.strftime("%B %#d, %Y")


def ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False) + "</script>"


def crumbs_ld(trail):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": BASE + p} for i, (n, p) in enumerate(trail)]}


def crumbs_html(trail):
    if len(trail) < 2:
        return ""
    parts = [f'<a href="{p}">{esc(n)}</a>' for n, p in trail[:-1]] + [esc(trail[-1][0])]
    return '<nav class="crumbs" aria-label="Breadcrumb">' + " / ".join(parts) + "</nav>"


WEBSITE_LD = {"@context": "https://schema.org", "@type": "WebSite", "name": NAME, "url": BASE + "/",
              "description": SITE["tagline"], "publisher": {"@type": "Person", "name": SITE["owner"]}}


def article_ld(kind, title, desc, path, image, published, modified):
    return {"@context": "https://schema.org", "@type": kind, "headline": title[:110], "description": desc,
            "mainEntityOfPage": BASE + path, "url": BASE + path, "image": [f"{BASE}/assets/img/og/{image}.png"],
            "datePublished": published, "dateModified": modified,
            "author": {"@type": "Person", "name": SITE["owner"], "url": BASE + "/about/"},
            "publisher": {"@type": "Organization", "name": NAME, "url": BASE + "/"}}


def faq_html(faq):
    if not faq:
        return ""
    items = "".join(f"<details><summary>{esc(f['q'])}</summary><p>{esc(f['a'])}</p></details>" for f in faq)
    return f'<h2 id="faq">Frequently asked questions</h2>{items}'


def related_html(paths):
    titles = {}
    for g in GUIDES:
        titles[f"/guides/{g['slug']}/"] = g["h1"]
    for p in PAGES:
        titles[p["path"]] = p["h1"]
    for s in NEWS:
        titles[f"/news/{s['slug']}/"] = s["title"]
    titles["/news/"] = NEWS_BRAND
    titles["/guides/"] = "All buying guides"
    titles["/deal-events/"] = "All deal events"
    links = [f'<li><a href="{p}">{esc(titles.get(p, p))}</a></li>' for p in paths]
    return f'<h2>Related</h2><ul>{"".join(links)}</ul>' if links else ""


def card(href, title, text, img=None, tag=None):
    pic = (f'<img src="/assets/img/{img}.webp" alt="" width="1200" height="630" loading="lazy" decoding="async">'
           if img else "")
    t = f'<span class="tag">{esc(tag)}</span>' if tag else ""
    return f'<article class="card">{pic}{t}<h3><a href="{href}">{esc(title)}</a></h3><p>{esc(text)}</p></article>'


AD = '<div class="ad-slot" aria-hidden="true"></div>'


# ---------- page shell ----------
def page(path, title, desc, body, trail, image="home", ld_extra=(), og_type="website", noindex=False):
    canonical = BASE + path
    nav = "".join(f'<a href="{href}"{" aria-current=\"page\"" if path.startswith(href) else ""}>{esc(label)}</a>'
                  for label, href in SITE["nav"])
    net = "".join(f'<a href="{u}"{" aria-current=\"true\"" if n == SITE["current_network"] else ""}>{esc(n)}</a>'
                  for n, u in SITE["network"])
    lds = "\n".join(ld(o) for o in [WEBSITE_LD, crumbs_ld(trail), *ld_extra])
    robots = '<meta name="robots" content="noindex">' if noindex else ""
    full_title = title if NAME in title else f"{title} | {NAME}"
    return f'''<!doctype html>
<html lang="en">
<head>
{GTM}
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">
{robots}
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{esc(NAME)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{BASE}/assets/img/og/{image}.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#000000">
<meta name="color-scheme" content="dark">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="alternate" type="application/rss+xml" title="{esc(NAME)}" href="/rss.xml">
<link rel="alternate" type="application/feed+json" title="{esc(NEWS_BRAND)}" href="/news/feed.json">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700&family=Barlow:wght@900&family=Inter:wght@400;500;700&display=swap">
<link rel="stylesheet" href="/assets/site.css">
<script src="/assets/config.js"></script>
<script src="/assets/site.js" defer></script>
{lds}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-head"><div class="wrap">
<a class="logo" href="/"><span class="dot" aria-hidden="true"></span>Deal<span class="sub">Notes</span></a>
<nav class="nav" aria-label="Main">{nav}</nav>
</div></header>
<div class="grad-rule" aria-hidden="true"></div>
<main id="main"><div class="wrap">
{crumbs_html(trail)}
{DISCLOSURE}
{body}
</div></main>
<div class="grad-rule" aria-hidden="true"></div>
<footer class="site-foot"><div class="wrap">
<div class="foot-links">
<a href="/about/">About</a><a href="/contact/">Contact</a><a href="/privacy/">Privacy</a>
<a href="/terms/">Terms</a><a href="/affiliate-disclosure/">Affiliate disclosure</a>
<a href="/news/">{esc(NEWS_BRAND)}</a><a href="/rss.xml">RSS</a><a href="/news/feed.json">JSON Feed</a>
</div>
<nav class="network" aria-label="samcbarth.com network"><strong>Network</strong>{net}</nav>
<p class="foot-disclosure">As an Amazon Associate, Deal Notes earns from qualifying purchases. Prices and availability are set by Amazon and can change at any time.</p>
<p class="foot-disclosure">&copy; 2026 {esc(SITE["owner"])}</p>
</div></footer>
</body>
</html>
'''


def write(path, content):
    out = ROOT / path.lstrip("/")
    if path.endswith("/"):
        out = out / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8", newline="\n")


# ---------- renderers ----------
def render_pick(p, show_guide=False):
    srcs = ", ".join(f'<a href="{esc(s["url"])}" rel="noopener">{esc(s["label"])}</a>' for s in p["sources"])
    chips = "".join(f'<span class="chip">{esc(r)}</span>' for r in p.get("recipients", []))
    from_guide = ""
    if show_guide:
        g = GUIDE_BY_SLUG[p["from_guide"]]
        from_guide = f' More in our <a href="/guides/{g["slug"]}/">{esc(g["short"].lower())} guide</a>.'
    return f'''<section class="pick" id="{esc(p["id"])}">
<span class="role">{esc(p["role"])}</span>
<h3>{esc(p["name"])}</h3>
{f'<div class="chips">{chips}</div>' if show_guide and chips else ''}
<p>{esc(p["why"])}</p>
<p><strong>Good to know:</strong> {esc(p["good_to_know"])}</p>
<p class="src">Source: {srcs}.{from_guide}</p>
{live_price(p)}
{amazon_button(p)}
</section>'''


def build_guide(g):
    path = f"/guides/{g['slug']}/"
    trail = [(NAME, "/"), ("Guides", "/guides/"), (g["short"], path)]
    toc = "".join(f'<li><a href="#{p["id"]}">{esc(p["name"])}</a>: {esc(p["role"])}</li>' for p in g["picks"])
    if g.get("gift_mode"):
        blocks = []
        for b in g["bands"]:
            ps = [p for p in g["picks"] if p["band"] == b["id"]]
            if ps:
                blocks.append(f'<h2 id="band-{b["id"]}">{esc(b["label"])}</h2><p class="meta">{esc(b["note"])}</p>'
                              + "".join(render_pick(p, True) for p in ps))
        recips = {}
        for p in g["picks"]:
            for r in p.get("recipients", []):
                recips.setdefault(r, []).append(p)
        rows = "".join(f'<tr><td>{esc(r)}</td><td>{", ".join(f"<a href=\"#{p["id"]}\">{esc(p["name"])}</a>" for p in ps)}</td></tr>'
                       for r, ps in sorted(recips.items()))
        picks_html = (f'<h2>Gift ideas by recipient</h2><div class="table-wrap"><table><thead><tr><th>Shopping for</th>'
                      f'<th>Ideas</th></tr></thead><tbody>{rows}</tbody></table></div>{AD}' + "".join(blocks))
    else:
        picks_html = f'<h2>Our picks</h2><ol>{toc}</ol>{AD}' + "".join(render_pick(p) for p in g["picks"])
    body = f'''<article class="read">
<h1>{esc(g["h1"])}</h1>
<p class="meta">Updated {nice_date(g["updated"])} &middot; By {esc(SITE["owner"])}</p>
<img class="hero-img" src="/assets/img/{g["image"]}.webp" alt="" width="1200" height="630" decoding="async">
<div class="answer"><p>{esc(g["intro"])}</p></div>
<h2>How we chose these picks</h2>
<p>{esc(g["how_chosen"])}</p>
{picks_html}
{faq_html(g["faq"])}
{AD}
{related_html(g["related"])}
</article>'''
    items = {"@context": "https://schema.org", "@type": "ItemList", "name": g["h1"], "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": p["name"], "url": f"{BASE}{path}#{p['id']}"}
        for i, p in enumerate(g["picks"])]}
    art = article_ld("Article", g["title"], g["description"], path, g["image"], g["updated"], g["updated"])
    write(path, page(path, g["title"], g["description"], body, trail, g["image"], [art, items], "article"))


def build_content_page(p):
    path = p["path"]
    if p["kind"] == "event":
        trail = [(NAME, "/"), ("Deal events", "/deal-events/"), (p["short"], path)]
    else:
        trail = [(NAME, "/"), (p["short"], path)]
    facts = ""
    if p.get("facts"):
        rows = "".join(f'<tr><th scope="row">{esc(f["label"])}</th><td>{esc(f["value"])}</td>'
                       f'<td><a href="{esc(f["source"]["url"])}" rel="noopener">{esc(f["source"]["label"])}</a></td></tr>'
                       for f in p["facts"])
        facts = (f'<h2>Key dates and facts</h2><div class="table-wrap"><table><thead><tr><th>What</th><th>Detail</th>'
                 f'<th>Source</th></tr></thead><tbody>{rows}</tbody></table></div>')
    secs = []
    for i, s in enumerate(p["sections"]):
        bodyp = "".join(f"<p>{b}</p>" for b in s["body"])  # body strings may carry trusted inline links
        secs.append(f'<h2>{esc(s["h"])}</h2><div class="answer"><p>{esc(s["answer"])}</p></div>{bodyp}')
        if i == 1 and p["kind"] != "legal":
            secs.append(AD)
    contact = ""
    if p.get("contact_form"):
        contact = ('<h2>Send a message</h2><div id="contact-target" class="note"><p>The contact form is being set up. '
                   'Until then, corrections can be sent through the samcbarth.com network sites.</p></div>')
    img = p.get("image", "home")
    hero = (f'<img class="hero-img" src="/assets/img/{img}.webp" alt="" width="1200" height="630" decoding="async">'
            if p.get("image") else "")
    body = f'''<article class="read">
<h1>{esc(p["h1"])}</h1>
<p class="meta">Updated {nice_date(p["updated"])}{" &middot; By " + esc(SITE["owner"]) if p["kind"] != "legal" else ""}</p>
{hero}
<p class="lede">{esc(p["intro"])}</p>
{facts}
{contact}
{"".join(secs)}
{faq_html(p.get("faq"))}
{AD if p["kind"] != "legal" else ""}
{related_html(p.get("related", []))}
</article>'''
    extra = []
    if p["kind"] != "legal":
        extra.append(article_ld("Article", p["title"], p["description"], path, img, p["updated"], p["updated"]))
    write(path, page(path, p["title"], p["description"], body, trail, img, extra,
                     "article" if p["kind"] != "legal" else "website"))


def build_news_story(s):
    path = f"/news/{s['slug']}/"
    trail = [(NAME, "/"), (NEWS_BRAND, "/news/"), (s["title"][:40] + ("..." if len(s["title"]) > 40 else ""), path)]
    paras = "".join(f"<p>{esc(b)}</p>" for b in s["body"])
    tags = "".join(f'<span class="chip">{esc(t)}</span>' for t in s["tags"])
    body = f'''<article class="read">
<p class="tag">{esc(NEWS_BRAND)}</p>
<h1>{esc(s["title"])}</h1>
<p class="meta"><time datetime="{s["date_published"]}">{nice_date(s["date_published"])}</time> &middot; By {esc(SITE["owner"])}</p>
<div class="chips">{tags}</div>
<div class="answer"><p>{esc(s["summary"])}</p></div>
{paras}
<div class="source-box"><strong>Primary source:</strong> <a href="{esc(s["source"]["url"])}" rel="noopener">{esc(s["source"]["label"])}</a></div>
{AD}
{related_html(s["related"])}
</article>'''
    art = article_ld("NewsArticle", s["title"], s["summary"], path, s["image"], s["date_published"], s["date_published"])
    write(path, page(path, s["title"], s["summary"], body, trail, s["image"], [art], "article"))


def build_indexes():
    # home
    guide_cards = "".join(card(f"/guides/{g['slug']}/", g["h1"], g["description"], g["image"], "Guide") for g in GUIDES)
    event_cards = "".join(card(p["path"], p["h1"], p["description"], p["image"], "Deal event") for p in EVENTS)
    news_items = "".join(f'<li><a href="/news/{s["slug"]}/">{esc(s["title"])}</a><p>{nice_date(s["date_published"])} &middot; {esc(s["summary"])}</p></li>'
                         for s in NEWS[:5])
    home = f'''<h1>Amazon buying guides and deal-event help, without the hype</h1>
<div class="answer read"><p>Deal Notes helps you decide what to buy on Amazon and when. Our picks come from published, test-based reviews (we say which), event dates come straight from Amazon, and we never show made-up prices, ratings or countdown timers.</p></div>
<h2>Next big sale: Black Friday is November 27, 2026</h2>
<p class="read">Amazon has confirmed Black Friday on November 27 and Cyber Monday on November 30, with early deals live now. <a href="/deal-events/black-friday/">What Amazon has confirmed so far</a>.</p>
<h2>Buying guides</h2>
<div class="grid">{guide_cards}</div>
{AD}
<h2>Deal events</h2>
<div class="grid">{event_cards}</div>
<h2>Shop smarter</h2>
<div class="grid">{card("/how-to-spot-a-real-deal/", PAGE_BY_SLUG["how-to-spot-a-real-deal"]["h1"], PAGE_BY_SLUG["how-to-spot-a-real-deal"]["description"], "explainer-real-deal")}{card("/price-history/", PAGE_BY_SLUG["price-history"]["h1"], PAGE_BY_SLUG["price-history"]["description"], "explainer-price-history")}</div>
<h2>Latest from {esc(NEWS_BRAND)}</h2>
<ul class="news-list read">{news_items}</ul>
<p><a href="/news/">All news</a></p>'''
    write("/", page("/", f"{NAME}: Amazon Buying Guides and Deal Event Help",
                    "Amazon buying guides backed by published testing, plus Black Friday, Cyber Monday and Prime Day dates from Amazon itself. No scraped prices or fake ratings.",
                    home, [(NAME, "/")], "home"))
    # guides index
    gbody = f'''<h1>Amazon buying guides</h1>
<div class="answer read"><p>Each guide lists a few products worth buying in one category, why each was chosen, and the published review it comes from. We link to Amazon for the current price instead of quoting one.</p></div>
<div class="grid">{guide_cards}</div>'''
    coll = {"@context": "https://schema.org", "@type": "CollectionPage", "name": "Amazon buying guides", "url": BASE + "/guides/"}
    write("/guides/", page("/guides/", "Amazon Buying Guides by Category",
                           "Kitchen, home office, tech accessories, tools, outdoor and gift guides with picks from published, test-based reviews.",
                           gbody, [(NAME, "/"), ("Guides", "/guides/")], "guides", [coll]))
    # events index
    ebody = f'''<h1>Amazon deal events: dates and how to shop them</h1>
<div class="answer read"><p>Amazon's big 2026 sales: Prime Day ran June 23 to 26, Prime Big Deal Days ran October 6 to 7, and Black Friday (November 27) and Cyber Monday (November 30) are next. We only list dates Amazon itself has announced.</p></div>
<div class="grid">{event_cards}</div>
<h2>Before any sale</h2>
<p class="read">Read <a href="/how-to-spot-a-real-deal/">how to spot a real deal</a> and <a href="/price-history/">how price history works</a> so you can tell a real discount from an inflated list price.</p>'''
    coll = {"@context": "https://schema.org", "@type": "CollectionPage", "name": "Amazon deal events", "url": BASE + "/deal-events/"}
    write("/deal-events/", page("/deal-events/", "Amazon Deal Events 2026: Black Friday, Cyber Monday, Prime Day",
                                "Official 2026 dates for Amazon Black Friday, Cyber Monday, Prime Day and Prime Big Deal Days, sourced from Amazon, plus back-to-school timing.",
                                ebody, [(NAME, "/"), ("Deal events", "/deal-events/")], "events", [coll]))
    # news index
    items = "".join(f'<li><span class="tag">{esc(s["tags"][0])}</span><br><a href="/news/{s["slug"]}/">{esc(s["title"])}</a>'
                    f'<p><time datetime="{s["date_published"]}">{nice_date(s["date_published"])}</time> &middot; {esc(s["summary"])}</p></li>'
                    for s in NEWS)
    nbody = f'''<h1>{esc(NEWS_BRAND)}</h1>
<div class="answer read"><p>{esc(SITE["news_tagline"])} for Amazon shoppers. Short, original write-ups with a link to the primary source on every story.</p></div>
<ul class="news-list read">{items}</ul>
<p class="meta">Follow along: <a href="/news/feed.json">JSON Feed</a> &middot; <a href="/rss.xml">RSS</a></p>'''
    coll = {"@context": "https://schema.org", "@type": "CollectionPage", "name": NEWS_BRAND, "url": BASE + "/news/"}
    write("/news/", page("/news/", f"{NEWS_BRAND}: Sales Events, Recalls and Tech Launches",
                         "Short, sourced news for Amazon shoppers: retail sales events, product recalls from the CPSC, and consumer tech launches.",
                         nbody, [(NAME, "/"), (NEWS_BRAND, "/news/")], "news", [coll]))
    # 404
    (ROOT / "404.html").write_text(page("/404.html", "Page not found", "This page does not exist.",
                                        '<h1>Page not found</h1><p>Try the <a href="/guides/">buying guides</a>, <a href="/deal-events/">deal events</a> or <a href="/news/">news</a>.</p>',
                                        [(NAME, "/")], noindex=True), encoding="utf-8", newline="\n")


def all_urls():
    urls = [("/", BUILD_DATE), ("/guides/", BUILD_DATE), ("/deal-events/", BUILD_DATE), ("/news/", NEWS[0]["date_published"][:10])]
    urls += [(f"/guides/{g['slug']}/", g["updated"]) for g in GUIDES]
    urls += [(p["path"], p["updated"]) for p in PAGES]
    urls += [(f"/news/{s['slug']}/", s["date_published"][:10]) for s in NEWS]
    return urls


def build_feeds():
    feed = {"version": "https://jsonfeed.org/version/1.1", "title": f"{NEWS_BRAND} ({NAME})",
            "home_page_url": BASE + "/news/", "feed_url": BASE + "/news/feed.json",
            "description": SITE["news_tagline"], "language": "en-US",
            "icon": BASE + "/assets/img/og/news.png", "authors": [{"name": SITE["owner"]}],
            "items": [{"id": f"{BASE}/news/{s['slug']}/", "url": f"{BASE}/news/{s['slug']}/", "title": s["title"],
                       "summary": s["summary"], "content_text": "\n\n".join(s["body"]),
                       "date_published": s["date_published"], "image": f"{BASE}/assets/img/og/{s['image']}.png",
                       "tags": s["tags"], "external_url": s["source"]["url"]} for s in NEWS]}
    (ROOT / "news" / "feed.json").write_text(json.dumps(feed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    def rfc822(iso):
        d = datetime.fromisoformat(iso if "T" in iso else iso + "T12:00:00+00:00")
        return d.astimezone(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    entries = [(s["title"], f"/news/{s['slug']}/", s["summary"], s["date_published"]) for s in NEWS]
    entries += [(g["h1"], f"/guides/{g['slug']}/", g["description"], g["updated"]) for g in GUIDES]
    entries += [(p["h1"], p["path"], p["description"], p["updated"]) for p in PAGES if p["kind"] != "legal"]
    items = "".join(f"<item><title>{esc(t)}</title><link>{BASE}{u}</link><guid>{BASE}{u}</guid>"
                    f"<description>{esc(d)}</description><pubDate>{rfc822(dt)}</pubDate></item>"
                    for t, u, d, dt in entries)
    rss = (f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>'
           f"<title>{esc(NAME)}</title><link>{BASE}/</link><description>{esc(SITE['tagline'])}</description>"
           f'<language>en-us</language><atom:link href="{BASE}/rss.xml" rel="self" type="application/rss+xml"/>{items}</channel></rss>\n')
    (ROOT / "rss.xml").write_text(rss, encoding="utf-8", newline="\n")

    sm = "".join(f"<url><loc>{BASE}{u}</loc><lastmod>{d}</lastmod></url>" for u, d in all_urls())
    (ROOT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>\n',
                                      encoding="utf-8", newline="\n")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n", encoding="utf-8", newline="\n")

    lines = [f"# {NAME}", "", f"> {SITE['tagline']}. Picks come from published, test-based reviews (each linked); "
             "deal-event dates come from Amazon's own announcements. No scraped prices or ratings.", "",
             "## Buying guides"]
    lines += [f"- [{g['h1']}]({BASE}/guides/{g['slug']}/): {g['description']}" for g in GUIDES]
    lines += ["", "## Deal events"] + [f"- [{p['h1']}]({BASE}{p['path']}): {p['description']}" for p in EVENTS]
    lines += ["", "## Explainers"] + [f"- [{PAGE_BY_SLUG[s]['h1']}]({BASE}{PAGE_BY_SLUG[s]['path']}): {PAGE_BY_SLUG[s]['description']}"
                                      for s in ("how-to-spot-a-real-deal", "price-history")]
    lines += ["", "## News"] + [f"- [{s['title']}]({BASE}/news/{s['slug']}/) ({s['date_published'][:10]})" for s in NEWS]
    lines += ["", "## Feeds", f"- JSON Feed: {BASE}/news/feed.json", f"- RSS: {BASE}/rss.xml", ""]
    (ROOT / "llms.txt").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    (ROOT / "CNAME").write_text("deals.samcbarth.com\n", encoding="utf-8", newline="\n")
    (ROOT / ".nojekyll").write_text("", encoding="utf-8")


def main():
    for d in GENERATED_DIRS:
        shutil.rmtree(ROOT / d, ignore_errors=True)
    make_images()
    for g in GUIDES:
        build_guide(g)
    for p in PAGES:
        build_content_page(p)
    for s in NEWS:
        build_news_story(s)
    build_indexes()
    build_feeds()
    print(f"Built {len(all_urls())} pages | AMAZON_TAG={'set' if CFG['AMAZON_TAG'] else 'empty'} | "
          f"guides={len(GUIDES)} pages={len(PAGES)} news={len(NEWS)}")


if __name__ == "__main__":
    main()
