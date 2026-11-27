#!/usr/bin/env python3
"""Collect the raw facts an AI visibility audit needs from a website.

It reads the sitemap, picks the pages that matter (homepage, about, contact,
service pages, pricing, reviews, the latest articles), and pulls out of each
one: title, headings, the opening text, structured data (JSON-LD), phone
numbers, addresses, dates, calls to action, pricing and review signals, and a
few distinctive sentences for the copied-content check.

It only collects evidence. Judging it is the auditor's job. Page-type labels
(service, article, ...) are guesses from URLs and must be confirmed.

Python 3.9+ standard library only. No installs.

Usage:
  python3 scan_site.py https://example.com
  python3 scan_site.py https://example.com --max-pages 30 --json site.json
  python3 scan_site.py https://example.com --urls https://example.com/a https://example.com/b
"""

import argparse
import gzip
import json
import re
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_ai_access import BROWSER_UA, curl_fetch, fetch, normalize  # noqa: E402


def fetch_page(url, timeout):
    """Fetch as a browser would. If the firewall refuses Python's client
    (401/403/429/503), retry once with curl, which firewalls often let through."""
    r = fetch(url, BROWSER_UA, timeout)
    if r.get("status") in (401, 403, 429, 503):
        second = curl_fetch(url, BROWSER_UA, timeout)
        if second and second.get("status") == 200:
            second["final_url"] = url
            second["fetched_with"] = f"curl (Python got HTTP {r['status']})"
            return second
    return r

PAGE_TYPES = [
    ("article", re.compile(r"/(blog|news|articles?|insights|resources?|resource-cent(er|re)|posts?|learn|library|"
                           r"knowledge(-base|-center)?|guides?|education|tips|stories)/.+|/20\d\d/\d\d/", re.I)),
    ("service", re.compile(r"/(services?|practice-areas?|areas-of-practice|treatments?|what-we-do|solutions|"
                           r"procedures?|specialt(y|ies)|our-work)(/|$)", re.I)),
    ("about", re.compile(r"/(about|about-us|team|our-team|staff|people|attorneys|lawyers|doctors|providers|"
                         r"meet-|who-we-are|bio)", re.I)),
    ("contact", re.compile(r"/(contact|book|schedule|appointment|request|get-started|quote|consult)", re.I)),
    ("pricing", re.compile(r"/(pricing|prices|fees|rates|cost|plans|packages|insurance|financing)", re.I)),
    ("reviews", re.compile(r"/(reviews?|testimonials?|case-stud(y|ies)|results|success)", re.I)),
    ("location", re.compile(r"/(locations?|areas?-we-serve|service-areas?|offices?|near-)", re.I)),
    ("faq", re.compile(r"/(faqs?|questions)", re.I)),
    ("legal", re.compile(r"/(privacy|terms|disclaimer|accessibility|cookie|sitemap)", re.I)),
]
SKIP_EXT = re.compile(r"\.(jpg|jpeg|png|gif|svg|webp|pdf|zip|mp4|mp3|css|js|ico|xml|txt)$", re.I)
CTA_WORDS = re.compile(r"\b(book|schedule|appointment|call us|call now|contact us|get a quote|free quote|"
                       r"request|consultation|get started|reserve|sign up|enquire|inquire)\b", re.I)
PRICE_PATTERNS = [
    (r"[$£€]\s?\d[\d,]*(\.\d\d)?", "money amount"),
    (r"\bfree (consultation|estimate|quote|assessment|inspection|initial)", "free first step"),
    (r"\b(flat|fixed)[- ]fee\b|\bflat rate\b", "flat or fixed fee"),
    (r"\bper (hour|session|visit|month|year)\b|\bhourly\b", "time-based rate"),
    (r"\b(pricing|prices|our fees|our rates|how much (does|do|will|is)|what (does|will) it cost)\b", "pricing words"),
    (r"\b(insurance|financing|payment plans?)\b", "insurance or financing"),
]
BOOKING_HOSTS = re.compile(
    r"(^|\.)(calendly\.com|acuityscheduling\.com|as\.me|square\.site|squareup\.com|vagaro\.com|fresha\.com|"
    r"mindbodyonline\.com|janeapp\.com|zocdoc\.com|booksy\.com|setmore\.com|schedulicity\.com|youcanbook\.me|"
    r"meetings\.hubspot\.com|tidycal\.com|savvycal\.com|cal\.com|simplybook\.me|housecallpro\.com|"
    r"getjobber\.com|clienthub\.getjobber\.com|opentable\.com|resy\.com|nexhealth\.com|localmed\.com|"
    r"glossgenius\.com|boulevard\.io|joinblvd\.com|appointy\.com|10to8\.com|typeform\.com|jotform\.com)$", re.I)
CTA_PATH = re.compile(r"/(book|booking|schedule|appointments?|consult|consultation|contact|quote|request|get-started)", re.I)
POSTLIKE_SITEMAP = re.compile(r"post|blog|article|news", re.I)
LIBRARY_MIN = 25  # a folder with this many URLs is treated as an article collection
REVIEW_PATTERNS = re.compile(r"\b(testimonials?|reviews?|rated|stars?|what (our )?(clients|patients|customers) say)\b", re.I)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]\d{4}(?!\d)")
US_ADDRESS_RE = re.compile(
    r"\d{1,6}\s+[A-Z0-9][\w.\s]{2,60}?\b(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct|"
    r"Place|Pl|Suite|Ste|Highway|Hwy|Parkway|Pkwy|Circle|Cir)\b\.?[^<\n]{0,80}?\b[A-Z]{2}\s+\d{5}(-\d{4})?")


class PageParser(HTMLParser):
    """Pull text, headings, links, JSON-LD and meta tags out of one HTML page."""
    SKIP = {"script", "style", "noscript", "svg", "template", "iframe", "title"}
    BLOCK = {"p", "div", "li", "br", "h1", "h2", "h3", "h4", "h5", "h6", "td", "th", "section", "article", "blockquote", "tr"}
    CHROME = {"nav", "header", "footer", "aside"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip_depth = 0
        self.chrome_depth = 0
        self.in_jsonld = False
        self.jsonld_raw = []
        self.heading = None
        self.headings = []
        self.links = []
        self.link_text = None
        self.meta = {}
        self.canonical = None
        self.times = []
        self.main_text = []
        self.all_text = []
        self.forms = 0
        self.microdata = set()
        self.lang = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.lang = a.get("lang")
        if tag == "script" and (a.get("type") or "").lower() == "application/ld+json":
            self.in_jsonld = True
            self.jsonld_raw.append("")
        if tag in self.SKIP:
            self.skip_depth += 1
        if tag in self.CHROME:
            self.chrome_depth += 1
        if tag in ("h1", "h2", "h3"):
            self.heading = [tag, ""]
        if tag == "a" and a.get("href"):
            self.link_text = [a["href"], ""]
        if tag == "meta":
            key = (a.get("name") or a.get("property") or "").lower()
            if key:
                self.meta[key] = a.get("content") or ""
        if tag == "link" and "canonical" in (a.get("rel") or "").lower():
            self.canonical = a.get("href")
        if tag == "time" and a.get("datetime"):
            self.times.append(a["datetime"])
        if tag == "form":
            self.forms += 1
        if a.get("itemtype"):
            self.microdata.add(a["itemtype"].rsplit("/", 1)[-1])

    def handle_endtag(self, tag):
        if tag in self.BLOCK:
            self.main_text.append("\u2029")  # paragraph break, keeps sentences apart
        if tag == "script" and self.in_jsonld:
            self.in_jsonld = False
        if tag in self.SKIP and self.skip_depth:
            self.skip_depth -= 1
        if tag in self.CHROME and self.chrome_depth:
            self.chrome_depth -= 1
        if self.heading and tag == self.heading[0]:
            text = _clean(self.heading[1])
            if text:
                self.headings.append((tag, text))
            self.heading = None
        if tag == "a" and self.link_text:
            self.links.append((self.link_text[0], _clean(self.link_text[1])))
            self.link_text = None

    def handle_data(self, data):
        if self.in_jsonld:
            self.jsonld_raw[-1] += data
            return
        if self.skip_depth:
            return
        if self.heading:
            self.heading[1] += data
        if self.link_text:
            self.link_text[1] += data
        self.all_text.append(data)
        if not self.chrome_depth:
            self.main_text.append(data)


def _clean(s):
    return re.sub(r"\s+", " ", s or "").strip()


def classify_url(url):
    path = urllib.parse.urlparse(url).path
    if path in ("", "/"):
        return "home"
    for name, rx in PAGE_TYPES:
        if rx.search(path):
            return name
    return "other"


def jsonld_items(raw_blocks):
    """Parse JSON-LD blocks. Returns (items, errors). Flattens @graph."""
    items, errors = [], []
    for i, raw in enumerate(raw_blocks):
        try:
            data = json.loads(raw.strip())
        except ValueError as e:
            errors.append(f"block {i + 1}: invalid JSON ({e})")
            continue
        stack = data if isinstance(data, list) else [data]
        while stack:
            d = stack.pop(0)
            if not isinstance(d, dict):
                continue
            if "@graph" in d and isinstance(d["@graph"], list):
                stack.extend(d["@graph"])
                if "@type" not in d:
                    continue
            items.append(d)
    return items, errors


def _types(item):
    t = item.get("@type", [])
    return t if isinstance(t, list) else [t]


def summarize_jsonld(items):
    """Keep the fields an audit compares with the visible page."""
    out = []
    keep = ("name", "legalName", "telephone", "email", "url", "address", "areaServed", "priceRange",
            "openingHours", "openingHoursSpecification", "aggregateRating", "sameAs", "datePublished",
            "dateModified", "author", "headline", "geo", "hasMap", "founder", "employee", "image", "logo")
    for it in items:
        row = {"@type": _types(it)}
        for k in keep:
            if k in it:
                v = it[k]
                s = json.dumps(v, ensure_ascii=False)
                row[k] = v if len(s) < 600 else s[:600] + "...(truncated)"
        out.append(row)
    return out


def distinctive_sentences(text, n=3):
    """Longer, specific sentences: good candidates for an exact-quote search."""
    sentences = re.split(r"\u2029|(?<=[.!?])\s+", text)
    good = []
    for s in sentences:
        s = _clean(s)
        words = s.split()
        if 14 <= len(words) <= 40 and not re.search(r"https?://|©|cookie|\bclick\b", s, re.I):
            good.append(s)
    good.sort(key=lambda s: -len(set(w.lower() for w in s.split())))
    return good[:n]


def normalize_phone(p):
    d = re.sub(r"\D", "", p)
    return d[1:] if len(d) == 11 and d.startswith("1") else d


def analyze_page(url, resp, page_type=None):
    row = {"url": url, "type": page_type or classify_url(resp.get("final_url") or url), "status": resp.get("status"),
           "final_url": resp.get("final_url"), "error": resp.get("error")}
    if resp.get("status") != 200:
        return row, None
    p = PageParser()
    try:
        p.feed(resp.get("text", ""))
    except Exception as e:  # malformed HTML: keep what was parsed
        row["parse_warning"] = str(e)
    main = _clean(" ".join(p.main_text))
    full = _clean(" ".join(p.all_text))
    items, errors = jsonld_items(p.jsonld_raw)
    phones = sorted({normalize_phone(m.group(0)) for m in PHONE_RE.finditer(full)}
                    | {normalize_phone(h[4:]) for h, _ in p.links if h.lower().startswith("tel:")})
    phones = [x for x in phones if len(x) == 10]
    ctas = sorted({t for h, t in p.links if t and CTA_WORDS.search(t)} |
                  {"tel: link" for h, _ in p.links if h.lower().startswith("tel:")})[:12]
    pricing = sorted({label for rx, label in PRICE_PATTERNS if re.search(rx, main, re.I)})
    dates = sorted(set(p.times + [p.meta[k] for k in ("article:published_time", "article:modified_time") if k in p.meta]
                       + [str(i[k]) for i in items for k in ("datePublished", "dateModified") if k in i]))
    words = main.split()
    row.update({
        "title": resp.get("title", ""),
        "meta_description": p.meta.get("description", ""),
        "canonical": p.canonical,
        "meta_robots": p.meta.get("robots", ""),
        "lang": p.lang,
        "h1": [t for tag, t in p.headings if tag == "h1"],
        "headings": [f"{tag}: {t}" for tag, t in p.headings][:40],
        "question_headings": sum(1 for _, t in p.headings if t.endswith("?")),
        "opening_text": " ".join(words[:120]),
        "word_count": len(words),
        "jsonld_types": sorted({t for i in items for t in _types(i)}),
        "jsonld": summarize_jsonld(items),
        "jsonld_errors": errors,
        "microdata_types": sorted(p.microdata),
        "phones": phones,
        # phone numbers are blanked first so a fax or phone number can't merge into a street number
        "addresses": sorted({_clean(m.group(0)) for m in US_ADDRESS_RE.finditer(PHONE_RE.sub(" | ", full))})[:5],
        "dates": dates[:10],
        "calls_to_action": ctas,
        "forms": p.forms,
        "pricing_signals": pricing,
        "review_signals": sorted({m.group(0).lower() for m in REVIEW_PATTERNS.finditer(main)})[:10],
        "og_site_name": p.meta.get("og:site_name", ""),
    })
    if any(t in ("Article", "BlogPosting", "NewsArticle") for t in row["jsonld_types"]) and row["type"] in ("other", "pricing"):
        row["type"] = "article"
    if row["type"] == "article":
        row["distinctive_sentences"] = distinctive_sentences(" ".join(p.main_text))
    return row, p


# ---------------------------------------------------------------- sitemap

def _sitemap_priority(url):
    """Read page/service/location sitemaps before post/tag/author ones."""
    low = url.lower()
    if re.search(r"page|service|location|area|product", low):
        return 0
    if re.search(r"post|blog|news|article", low):
        return 2
    if re.search(r"tag|categor|author|attachment|media|image", low):
        return 3
    return 1


def _read_one(sm, timeout):
    resp = fetch(sm, BROWSER_UA, timeout, keep_bytes=True)
    if resp.get("status") != 200:
        return None
    raw = resp.get("raw", b"")
    if raw[:2] == b"\x1f\x8b":
        try:
            raw = gzip.decompress(raw)
        except OSError:
            return None
    try:
        return ET.fromstring(raw.strip())
    except ET.ParseError:
        return None


def read_sitemaps(origin, robots_sitemaps, timeout, max_files=12, max_urls=5000):
    """Return ({url: lastmod}, notes, {url: sitemap_file}). Tries robots.txt sitemaps, then defaults."""
    found, notes, seen, source = {}, [], set(), {}
    starts = [robots_sitemaps] if robots_sitemaps else []
    starts += [[origin + "/sitemap.xml"], [origin + "/sitemap_index.xml"], [origin + "/wp-sitemap.xml"]]
    files = 0
    for queue in starts:
        queue = list(queue)
        while queue and files < max_files and len(found) < max_urls:
            sm = queue.pop(0)
            if sm in seen:
                continue
            seen.add(sm)
            files += 1
            root = _read_one(sm, timeout)
            if root is None:
                continue
            tag = root.tag.split("}")[-1]
            if tag == "sitemapindex":
                kids = [loc.text.strip() for loc in root.iter() if loc.tag.endswith("loc") and loc.text]
                queue.extend(sorted(kids, key=_sitemap_priority))
                notes.append(f"sitemap index: {sm} ({len(kids)} child sitemaps)")
            elif tag == "urlset":
                n = 0
                for u in root:
                    loc = lastmod = None
                    for c in u:
                        if c.tag.endswith("loc"):
                            loc = (c.text or "").strip()
                        elif c.tag.endswith("lastmod"):
                            lastmod = (c.text or "").strip()
                    if loc:
                        found[loc] = lastmod
                        source[loc] = sm
                        n += 1
                notes.append(f"sitemap: {sm} ({n} URLs)")
        if found:
            break
    if files >= max_files:
        notes.append(f"stopped after {max_files} sitemap files; URL counts may be incomplete")
    return found, notes, source


# ---------------------------------------------------------------- page types

def type_urls(candidates, source):
    """Guess a type for every URL. Beyond the URL patterns, two rules catch
    article collections the patterns miss: URLs listed in a post/blog sitemap
    file (WordPress often puts posts at the root), and any folder holding
    LIBRARY_MIN or more URLs that isn't a service or location folder
    (bought-in content libraries)."""
    types = {u: classify_url(u) for u in candidates}
    for u, t in types.items():
        sm = source.get(u, "")
        if t in ("other", "pricing") and POSTLIKE_SITEMAP.search(sm.rsplit("/", 1)[-1]):
            types[u] = "article"
    folders = {}
    for u in candidates:
        seg = urllib.parse.urlparse(u).path.strip("/").split("/")
        if len(seg) > 1:
            folders.setdefault(seg[0], []).append(u)
    for seg, urls in folders.items():
        if len(urls) >= LIBRARY_MIN:
            for u in urls:
                if types[u] in ("other", "pricing", "reviews"):
                    types[u] = "article"
    return types


# ---------------------------------------------------------------- page choice

PROMINENT_TEXT = re.compile(r"\b(learn more|read more|our services|services|what we do|see details|find out more)\b", re.I)


def prominent_pages(nav, home):
    """Homepage-linked pages that matter whatever their URL says: linked 3+ times,
    or linked with "Learn more"-style text. Returns {url: link_count}."""
    counts, prominent = {}, set()
    for u, text in nav:
        if u.rstrip("/") == home.rstrip("/"):
            continue
        counts[u] = counts.get(u, 0) + 1
        if text and PROMINENT_TEXT.search(text):
            prominent.add(u)
    return {u: c for u, c in counts.items() if c >= 3 or u in prominent}


def choose_pages(home, candidates, max_pages, types, prominent=None):
    """Pick a balanced set: core pages and prominent homepage links first,
    then services, then recent articles."""
    prominent = prominent or {}
    by_type = {}
    for url, lastmod in candidates.items():
        by_type.setdefault(types[url], []).append((url, lastmod or ""))
    quota = [("about", 3), ("contact", 2), ("service", 20), ("pricing", 2), ("reviews", 2),
             ("location", 3), ("faq", 1), ("article", 6), ("other", 4)]
    chosen = [home]
    for u, _ in sorted(prominent.items(), key=lambda x: -x[1])[:8]:
        if u in candidates and types.get(u) != "article" and u not in chosen:
            chosen.append(u)
    for t, n in quota:
        items = by_type.get(t, [])
        if t == "article":
            items = sorted(items, key=lambda x: x[1], reverse=True)
        else:
            items = sorted(items, key=lambda x: (-prominent.get(x[0], 0), x[0].count("/"), len(x[0])))
        for url, _ in items[:n]:
            if url not in chosen:
                chosen.append(url)
    return chosen[:max_pages], by_type


def same_site(url, host):
    u = urllib.parse.urlparse(url)
    return u.scheme in ("http", "https") and u.netloc.lower().removeprefix("www.") == host


# ---------------------------------------------------------------- booking links

def booking_links(page_links, host):
    """Links that a prospect uses to take the next step: booking tools, and
    contact/booking pages. page_links: [(page_url, [(href, text), ...]), ...]"""
    found = {}
    for page_url, links in page_links:
        for href, text in links:
            if href.lower().startswith(("tel:", "mailto:", "javascript:", "#", "sms:")):
                continue
            absu = urllib.parse.urljoin(page_url, href).split("#", 1)[0]
            u = urllib.parse.urlparse(absu)
            if u.scheme not in ("http", "https"):
                continue
            netloc = u.netloc.lower().removeprefix("www.")
            third_party_booking = bool(BOOKING_HOSTS.search(netloc))
            own_cta = netloc == host and (CTA_PATH.search(u.path) or (text and CTA_WORDS.search(text)))
            if third_party_booking or own_cta:
                entry = found.setdefault(absu, {"url": absu, "texts": set(), "found_on": set(),
                                                "third_party": third_party_booking})
                if text:
                    entry["texts"].add(text[:60])
                entry["found_on"].add(page_url)
    return list(found.values())


def check_links(entries, timeout, delay, limit=25):
    """Load each link once as a browser would. Third-party booking tools first."""
    entries = sorted(entries, key=lambda e: (not e["third_party"], -len(e["found_on"])))[:limit]
    out = []
    for e in entries:
        time.sleep(delay)
        r = fetch_page(e["url"], timeout)
        st = r.get("status")
        if st is None:
            result = "broken"
        elif st in (404, 410) or st >= 500:
            result = "broken"
        elif st in (401, 403, 429):
            result = "unclear"  # often bot protection; a person may see it fine
        elif st >= 400:
            result = "broken"
        else:
            result = "ok"
        out.append({"url": e["url"], "status": st, "error": r.get("error"), "final_url": r.get("final_url"),
                    "result": result, "link_texts": sorted(e["texts"]), "found_on": sorted(e["found_on"]),
                    "found_on_count": len(e["found_on"]), "third_party": e["third_party"]})
    return out


def run(url, max_pages=40, urls=None, timeout=20, delay=0.3):
    home = normalize(url)
    origin = "{0.scheme}://{0.netloc}".format(urllib.parse.urlparse(home))
    host = urllib.parse.urlparse(home).netloc.lower().removeprefix("www.")
    out = {"site": home, "notes": [], "label_warning":
           "Page types are guesses from URL patterns. Confirm before reporting."}

    home_resp = fetch_page(home, timeout)
    home_row, home_parser = analyze_page(home, home_resp)
    if home_resp.get("status") != 200:
        out["notes"].append(f"Homepage did not load normally: HTTP {home_resp.get('status')} {home_resp.get('error') or ''}")
    final_origin = home_resp.get("final_url") or home
    host = urllib.parse.urlparse(final_origin).netloc.lower().removeprefix("www.") or host

    nav = []
    if home_parser:
        for href, text in home_parser.links:
            absu = urllib.parse.urljoin(final_origin, href).split("#", 1)[0]
            if same_site(absu, host) and not SKIP_EXT.search(urllib.parse.urlparse(absu).path):
                nav.append((absu, text))
    out["homepage_links"] = [{"url": u, "text": t, "type": classify_url(u)} for u, t in dict(nav).items()][:150]

    rob = fetch(origin + "/robots.txt", BROWSER_UA, timeout)
    robots_sitemaps = re.findall(r"(?im)^\s*sitemap:\s*(\S+)", rob.get("text", "")) if rob.get("status") == 200 else []
    sitemap_urls, sm_notes, sm_source = read_sitemaps(origin, robots_sitemaps, timeout)
    out["sitemap"] = {"sources": sm_notes, "url_count": len(sitemap_urls)}
    if not sitemap_urls:
        out["notes"].append("No readable XML sitemap found; pages were chosen from homepage links only.")

    candidates = {u: lm for u, lm in sitemap_urls.items() if same_site(u, host) and not SKIP_EXT.search(u)}
    for u, _ in nav:
        candidates.setdefault(u, None)
    seen_paths = {}
    for u in list(candidates):  # drop /page vs /page/ duplicates
        key = u.rstrip("/")
        if key in seen_paths:
            candidates.pop(u)
        else:
            seen_paths[key] = u
    candidates.pop(home, None)
    candidates.pop(final_origin, None)

    types = type_urls(candidates, sm_source)
    if urls:
        chosen = [home] + [normalize(u) for u in urls]
        by_type = {}
        for u, lm in candidates.items():
            by_type.setdefault(types[u], []).append((u, lm or ""))
    else:
        chosen, by_type = choose_pages(home, candidates, max_pages, types, prominent_pages(nav, final_origin))
        skipped = {t: len(v) - sum(1 for u, _ in v if u in chosen) for t, v in by_type.items()}
        if skipped.get("service", 0) > 0:
            out["notes"].append(f"{skipped['service']} more service-type URLs were not scanned; "
                                f"rerun with --max-pages {max_pages + 20} or list them with --urls.")

    out["url_inventory"] = {t: {"count": len(v), "sample": [u for u, _ in sorted(v)[:60]]} for t, v in sorted(by_type.items())}
    arts = sorted((lm for _, lm in by_type.get("article", []) if lm), reverse=True)
    out["articles"] = {"count": len(by_type.get("article", [])),
                       "newest_lastmod": arts[0] if arts else None, "oldest_lastmod": arts[-1] if arts else None}

    pages = [home_row]
    page_links = [(home_resp.get("final_url") or home, home_parser.links if home_parser else [])]
    for u in chosen[1:]:
        time.sleep(delay)
        resp = fetch_page(u, timeout)
        row, parser = analyze_page(u, resp, types.get(u))
        if resp.get("fetched_with"):
            row["fetched_with"] = resp["fetched_with"]
        pages.append(row)
        if parser:
            page_links.append((resp.get("final_url") or u, parser.links))
    out["pages"] = pages
    out["booking_links"] = check_links(booking_links(page_links, host), timeout, delay)

    # site-level consistency
    phones, names, addresses = {}, {}, {}
    for p in pages:
        for ph in p.get("phones", []):
            phones.setdefault(ph, []).append(p["url"])
        for it in p.get("jsonld", []):
            if it.get("name") and any(t in ("Organization", "LocalBusiness") or t.endswith(("Business", "Service", "Office", "Clinic", "Practice", "Dentist", "Attorney", "LegalService", "Physician", "Contractor", "Plumber", "Electrician"))
                                      for t in it["@type"] if isinstance(t, str)):
                names.setdefault(str(it["name"]), []).append(p["url"])
            if it.get("address"):
                addresses.setdefault(json.dumps(it["address"], ensure_ascii=False, sort_keys=True)[:300], []).append(p["url"])
        for ad in p.get("addresses", []):
            addresses.setdefault(ad, []).append(p["url"])
    out["consistency"] = {
        "phones": {k: len(v) for k, v in phones.items()},
        "business_names_in_structured_data": {k: len(v) for k, v in names.items()},
        "og_site_names": sorted({p.get("og_site_name") for p in pages if p.get("og_site_name")}),
        "addresses": {k: len(v) for k, v in addresses.items()},
        "pages_with_business_schema": sum(1 for p in pages if any(
            t not in ("WebPage", "WebSite", "BreadcrumbList", "ImageObject", "SiteNavigationElement", "ReadAction",
                      "SearchAction", "ListItem", "Person", "Article", "BlogPosting")
            for t in p.get("jsonld_types", []))),
    }
    return out


def summarize(r):
    L = [f"Site scan for {r['site']}", r["label_warning"], ""]
    sm = r["sitemap"]
    L.append(f"Sitemap: {sm['url_count']} URLs from {len(sm['sources'])} source(s)")
    L.append("URL inventory by guessed type: " + ", ".join(f"{t} {v['count']}" for t, v in r["url_inventory"].items()))
    a = r["articles"]
    if a["count"]:
        L.append(f"Articles: {a['count']} (newest lastmod {a['newest_lastmod']}, oldest {a['oldest_lastmod']})")
    bl = r.get("booking_links", [])
    broken = [b for b in bl if b["result"] == "broken"]
    L.append(f"Booking / next-step links checked: {len(bl)}; broken: {len(broken)}")
    for b in broken:
        L.append(f"   BROKEN: {b['url']} -> {b['status'] or b['error']}  (link text {b['link_texts'][:2]}, on {b['found_on_count']} page(s))")
    for b in bl:
        if b["result"] == "unclear":
            L.append(f"   unclear: {b['url']} -> HTTP {b['status']} (may be bot protection; check in a browser)")
    c = r["consistency"]
    L.append(f"Phones seen (number: pages): {c['phones'] or 'none found'}")
    L.append(f"Business names in structured data: {c['business_names_in_structured_data'] or 'none'}")
    if c["og_site_names"]:
        L.append(f"og:site_name values: {c['og_site_names']}")
    L.append(f"Addresses seen: {len(c['addresses'])} distinct form(s)")
    L.append("")
    for p in r["pages"]:
        L.append(f"[{p['type']}] {p['url']}  HTTP {p['status']}" + (f"  error: {p['error']}" if p.get("error") else ""))
        if p.get("status") != 200:
            continue
        L.append(f"   title: {p['title']}")
        L.append(f"   h1: {p['h1']}   words: {p['word_count']}   question headings: {p['question_headings']}")
        L.append(f"   schema: {p['jsonld_types'] or 'none'}" + (f"  ERRORS: {p['jsonld_errors']}" if p["jsonld_errors"] else ""))
        if p["dates"]:
            L.append(f"   dates: {p['dates'][:3]}")
        L.append(f"   CTAs: {p['calls_to_action'][:5]}  forms: {p['forms']}  pricing: {p['pricing_signals']}")
        if p["type"] == "home":
            L.append(f"   opening text: {p['opening_text'][:500]}")
        for s in p.get("distinctive_sentences", []):
            L.append(f"   quote-check: \"{s}\"")
    for n in r["notes"]:
        L.append("Note: " + n)
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Collect audit evidence from a website.")
    ap.add_argument("url")
    ap.add_argument("--max-pages", type=int, default=40, help="pages to scan in detail (default 40)")
    ap.add_argument("--urls", nargs="*", help="scan exactly these pages (plus the homepage)")
    ap.add_argument("--json", help="write full results to this JSON file")
    ap.add_argument("--timeout", type=float, default=20)
    ap.add_argument("--delay", type=float, default=0.3)
    args = ap.parse_args(argv)
    r = run(args.url, args.max_pages, args.urls, args.timeout, args.delay)
    print(summarize(r))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(r, f, indent=2, ensure_ascii=False)
        print(f"\nFull results written to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
