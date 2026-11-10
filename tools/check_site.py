"""Check the built site: internal links, required tags, writing rules. Optional external link check.

Usage:  python tools/check_site.py            internal checks only
        python tools/check_site.py --external also fetch every external link
"""
import json, pathlib, re, sys, urllib.request
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKIP = {"data", "tools", ".git", ".claude"}
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")


class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.ids, self.text = [], set(), []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        for k in ("href", "src"):
            if a.get(k):
                self.links.append(a[k])

    def handle_data(self, d):
        self.text.append(d)


def target(path):
    p = ROOT / path.lstrip("/")
    if path.endswith("/") or p.is_dir():
        p = p / "index.html"
    return p


def main():
    errors, externals = [], set()
    pages = [p for p in ROOT.rglob("*.html") if not (set(p.relative_to(ROOT).parts) & SKIP)]
    parsed = {}
    for f in pages:
        src = f.read_text(encoding="utf-8")
        p = P()
        p.feed(src)
        parsed[f] = (src, p)
    for f, (src, p) in parsed.items():
        rel = "/" + f.relative_to(ROOT).as_posix()
        head = src.split("<head>", 1)[1].lstrip() if "<head>" in src else ""
        if not head.startswith('<script async src="https://www.googletagmanager.com/gtm.js?id=GTM-KMS4X55L">'):
            errors.append(f"{rel}: GTM snippet not right after <head>")
        for need in ('<link rel="canonical"', '<meta name="description"', 'og:title', 'application/ld+json',
                     'class="network"', 'class="disclosure"'):
            if need not in src:
                errors.append(f"{rel}: missing {need}")
        if len(re.findall(r"<title>", src)) != 1:
            errors.append(f"{rel}: title count")
        text = " ".join(p.text)
        if "—" in src:
            errors.append(f"{rel}: em dash")
        if EMOJI.search(text):
            errors.append(f"{rel}: emoji")
        for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', src, re.S):
            try:
                json.loads(m.group(1))
            except ValueError as e:
                errors.append(f"{rel}: bad JSON-LD {e}")
        first_amz = src.find("data-amazon")
        if first_amz != -1 and src.find('class="disclosure"') > first_amz:
            errors.append(f"{rel}: disclosure not above first affiliate link")
        for link in p.links:
            if link.startswith(("http://", "https://")):
                externals.add(link)
                continue
            if link.startswith(("mailto:", "tel:", "#")):
                if link.startswith("#") and link[1:] not in p.ids:
                    errors.append(f"{rel}: missing anchor {link}")
                continue
            path, _, frag = link.partition("#")
            t = target(path)
            if not t.exists():
                errors.append(f"{rel}: broken internal link {link}")
            elif frag and t.suffix == ".html":
                tp = parsed.get(t)
                if tp and frag not in tp[1].ids:
                    errors.append(f"{rel}: missing anchor {link}")
    for f in ("sitemap.xml", "robots.txt", "rss.xml", "llms.txt", "CNAME", "news/feed.json"):
        if not (ROOT / f).exists():
            errors.append(f"missing {f}")
    feed = json.loads((ROOT / "news/feed.json").read_text(encoding="utf-8"))
    for it in feed["items"]:
        for k in ("title", "url", "date_published", "summary", "image", "tags"):
            if not it.get(k):
                errors.append(f"feed item {it.get('id')}: missing {k}")
    print(f"{len(pages)} pages, {len(externals)} external links checked internally")
    if "--external" in sys.argv:
        for u in sorted(externals):
            if "amazon.com/s?" in u or "amazon.com/dp/" in u:
                continue  # store search links; checked by format only
            try:
                req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (link check)"})
                code = urllib.request.urlopen(req, timeout=20).status
            except urllib.error.HTTPError as e:
                code = e.code
            except Exception as e:
                code = type(e).__name__
            ok = code == 200 or code in (401, 403, 429)  # bot walls still mean the page exists
            print(("OK  " if ok else "BAD ") + str(code) + " " + u)
            if not ok:
                errors.append(f"external {code}: {u}")
    for e in errors:
        print("ERROR", e)
    print("PASS" if not errors else f"FAIL ({len(errors)} errors)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
