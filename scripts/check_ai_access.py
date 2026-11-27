#!/usr/bin/env python3
"""Check whether AI crawlers can reach a website.

Two checks, because they often disagree:
  1. What robots.txt says each AI crawler may do (the site's stated rules).
  2. What the server actually returns when a request arrives with each
     crawler's user agent, compared with a normal browser request.

A site whose robots.txt says "allow" while its firewall or CDN answers bots
with 403 or a challenge page is invisible to those AI tools, and the owner
usually has no idea.

Python 3.9+ standard library only. No installs.

Usage:
  python3 check_ai_access.py https://example.com
  python3 check_ai_access.py https://example.com --inner https://example.com/services/
  python3 check_ai_access.py https://example.com --json access.json

Limit: requests come from your computer, not from the vendors' own IP
addresses. Some firewalls block anything that claims to be a bot but comes
from the wrong address, so a block seen here is strong evidence, not proof.
The report wording should say "likely blocked" and suggest how to confirm.
"""

import argparse
import html
import json
import re
import socket
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

VERIFIED_ON = "2026-11-27"  # date the bot list below was checked against vendor docs

BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# purpose: "training" = collects content for model training
#          "search"   = indexes pages so the AI tool can show/cite them
#          "user"     = fetches a page when a person asks the AI tool about it
# live: False means the token is a robots.txt rule only and never crawls itself.
BOTS = [
    {"token": "GPTBot", "vendor": "OpenAI", "purpose": "training", "live": True,
     "ua": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; GPTBot/1.4; +https://openai.com/gptbot",
     "source": "https://developers.openai.com/api/docs/bots"},
    {"token": "OAI-SearchBot", "vendor": "OpenAI", "purpose": "search", "live": True,
     "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36; compatible; OAI-SearchBot/1.4; +https://openai.com/searchbot",
     "source": "https://developers.openai.com/api/docs/bots"},
    {"token": "ChatGPT-User", "vendor": "OpenAI", "purpose": "user", "live": True,
     "ua": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ChatGPT-User/1.0; +https://openai.com/bot",
     "source": "https://developers.openai.com/api/docs/bots"},
    {"token": "ClaudeBot", "vendor": "Anthropic", "purpose": "training", "live": True,
     "ua": "Mozilla/5.0 (compatible; ClaudeBot/1.0)",
     "source": "https://support.claude.com/en/articles/8896518"},
    {"token": "Claude-SearchBot", "vendor": "Anthropic", "purpose": "search", "live": True,
     "ua": "Mozilla/5.0 (compatible; Claude-SearchBot/1.0)",
     "source": "https://support.claude.com/en/articles/8896518"},
    {"token": "Claude-User", "vendor": "Anthropic", "purpose": "user", "live": True,
     "ua": "Mozilla/5.0 (compatible; Claude-User/1.0)",
     "source": "https://support.claude.com/en/articles/8896518"},
    {"token": "PerplexityBot", "vendor": "Perplexity", "purpose": "search", "live": True,
     "ua": "Mozilla/5.0 (compatible; PerplexityBot/1.0; +https://perplexity.ai/perplexitybot)",
     "source": "https://docs.perplexity.ai/guides/bots"},
    {"token": "Perplexity-User", "vendor": "Perplexity", "purpose": "user", "live": True,
     "ua": "Mozilla/5.0 (compatible; Perplexity-User/1.0; +https://perplexity.ai/perplexity-user)",
     "source": "https://docs.perplexity.ai/guides/bots"},
    {"token": "Googlebot", "vendor": "Google", "purpose": "search", "live": True,
     "ua": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Googlebot/2.1; +http://www.google.com/bot.html) Chrome/131.0.0.0 Safari/537.36",
     "source": "https://developers.google.com/search/docs/crawling-indexing/google-common-crawlers"},
    {"token": "Google-Extended", "vendor": "Google", "purpose": "training", "live": False,
     "ua": None,
     "source": "https://developers.google.com/search/docs/crawling-indexing/google-common-crawlers"},
    {"token": "bingbot", "vendor": "Microsoft Bing", "purpose": "search", "live": True,
     "ua": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm) Chrome/131.0.0.0 Safari/537.36",
     "source": "https://www.bing.com/webmasters/help/which-crawlers-does-bing-use-8c184ec0"},
    {"token": "Applebot", "vendor": "Apple", "purpose": "search", "live": True,
     "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15 (Applebot/0.1; +http://www.apple.com/go/applebot)",
     "source": "https://support.apple.com/en-us/119829"},
    {"token": "Applebot-Extended", "vendor": "Apple", "purpose": "training", "live": False,
     "ua": None,
     "source": "https://support.apple.com/en-us/119829"},
]

# Text that bot-protection pages show. Only counted when the browser request
# did NOT show the same text, so a normal contact-form captcha is not flagged.
CHALLENGE_MARKERS = [
    "just a moment...", "cf-chl", "challenge-platform", "attention required! | cloudflare",
    "checking your browser", "verify you are human", "_incapsula_resource", "px-captcha",
    "captcha-delivery.com", "sucuri website firewall", "access denied", "request unsuccessful",
    "bot protection", "ddos protection",
]
BLOCK_STATUSES = {401, 403, 406, 429, 451, 503}
MAX_BYTES = 2_000_000


# ---------------------------------------------------------------- robots.txt

def parse_robots(text):
    """Parse robots.txt into {agent_lowercase: [(allow_bool, path), ...]}.

    Follows RFC 9309: consecutive user-agent lines share a group, groups for
    the same agent are merged, unknown lines are ignored.
    """
    groups = {}
    current = []
    last_was_agent = False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key, value = key.strip().lower(), value.strip()
        if key == "user-agent":
            if not last_was_agent:
                current = []
            agent = value.lower()
            current.append(agent)
            groups.setdefault(agent, [])
            last_was_agent = True
        elif key in ("allow", "disallow"):
            last_was_agent = False
            if not current:
                continue
            if key == "disallow" and value == "":
                continue  # "Disallow:" with no path allows everything
            for agent in current:
                groups[agent].append((key == "allow", value))
        else:
            # sitemap, crawl-delay and others do not end a user-agent group
            # for our purposes, but they do mark the group as started.
            if key != "sitemap":
                last_was_agent = False
    return groups


def _rule_matches(rule_path, path):
    regex = ""
    for ch in rule_path:
        if ch == "*":
            regex += ".*"
        elif ch == "$":
            regex += "$"
        else:
            regex += re.escape(ch)
    return re.match(regex, path) is not None


def robots_decision(groups, token, path):
    """Return (allowed, matched_group, matched_rule).

    matched_group is the user-agent line that applied ("*" or the token),
    or None when robots.txt has no group for this crawler at all.
    Longest matching rule wins; on a tie, allow wins (RFC 9309).
    """
    token_l = token.lower()
    if token_l in groups:
        group_name = token_l
    elif "*" in groups:
        group_name = "*"
    else:
        return True, None, None
    best = None
    for allow, rule_path in groups[group_name]:
        if not _rule_matches(rule_path, path):
            continue
        length = len(rule_path)
        if best is None or length > best[0] or (length == best[0] and allow and not best[1]):
            best = (length, allow, rule_path)
    if best is None:
        return True, group_name, None
    return best[1], group_name, ("Allow: " if best[1] else "Disallow: ") + best[2]


# ---------------------------------------------------------------- fetching

def fetch(url, ua, timeout, keep_bytes=False):
    """GET a URL. Never raises; returns a dict describing what came back."""
    req = urllib.request.Request(url, headers={
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    ctx = ssl.create_default_context()
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            body = resp.read(MAX_BYTES)
            status, headers, final = resp.status, resp.headers, resp.geturl()
    except urllib.error.HTTPError as e:
        try:
            body = e.read(MAX_BYTES)
        except Exception:
            body = b""
        status, headers, final = e.code, e.headers, e.geturl()
    except (urllib.error.URLError, socket.timeout, ssl.SSLError, ConnectionError, OSError) as e:
        reason = getattr(e, "reason", e)
        return {"url": url, "status": None, "error": str(reason), "ms": int((time.time() - started) * 1000)}
    text = body.decode(_charset(headers), "replace")
    extra = {"raw": body} if keep_bytes else {}
    return {**extra, 
        "url": url,
        "final_url": final,
        "status": status,
        "bytes": len(body),
        "title": _title(text),
        "headers": {k.lower(): v for k, v in (headers.items() if headers else [])},
        "text": text,
        "ms": int((time.time() - started) * 1000),
    }


def _charset(headers):
    if headers:
        m = re.search(r"charset=([\w-]+)", headers.get("Content-Type", "") or "", re.I)
        if m:
            return m.group(1)
    return "utf-8"


def _title(text):
    m = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
    return html.unescape(re.sub(r"\s+", " ", m.group(1))).strip()[:150] if m else ""


def _markers(text):
    low = text.lower()
    return {m for m in CHALLENGE_MARKERS if m in low}


def protection_hints(headers):
    """Name the CDN or firewall if response headers reveal it."""
    h = headers or {}
    hints = []
    server = h.get("server", "").lower()
    if "cloudflare" in server or "cf-ray" in h:
        hints.append("Cloudflare")
    if "x-sucuri-id" in h or "sucuri" in server:
        hints.append("Sucuri")
    if "akamai" in server or "x-akamai-transformed" in h:
        hints.append("Akamai")
    if "x-iinfo" in h or "incapsula" in str(h).lower():
        hints.append("Imperva")
    if "x-datadome" in h or "datadome" in server:
        hints.append("DataDome")
    if "x-served-by" in h and "cache" in h.get("x-served-by", "").lower():
        hints.append("Fastly")
    if "wpe-backend" in h or "x-wpe" in str(h).lower():
        hints.append("WP Engine")
    if "x-vercel-id" in h:
        hints.append("Vercel")
    if "x-amz-cf-id" in h:
        hints.append("Amazon CloudFront")
    return hints


def classify(bot_resp, baseline):
    """Compare a bot response with the browser baseline.

    Returns (result, detail). result is one of:
      ok, blocked, challenge, different, error, baseline_failed
    """
    if baseline.get("status") is None or baseline["status"] >= 400:
        return "baseline_failed", "the normal browser request also failed, so this comparison is not meaningful"
    if bot_resp.get("status") is None:
        return "error", "no response: " + bot_resp.get("error", "unknown error")
    st = bot_resp["status"]
    if bot_resp.get("headers", {}).get("cf-mitigated", "").lower() == "challenge":
        return "challenge", f"HTTP {st} with header cf-mitigated: challenge (Cloudflare challenge page)"
    new_markers = _markers(bot_resp.get("text", "")) - _markers(baseline.get("text", ""))
    if st in BLOCK_STATUSES or st >= 400:
        extra = f"; page text includes {sorted(new_markers)}" if new_markers else ""
        return "blocked", f"HTTP {st} (browser got HTTP {baseline['status']}){extra}"
    if new_markers:
        return "challenge", f"HTTP {st} but the page shows bot-check text {sorted(new_markers)}"
    b_bytes, r_bytes = baseline.get("bytes", 0), bot_resp.get("bytes", 0)
    if b_bytes > 5000 and r_bytes < b_bytes * 0.4:
        return "different", f"HTTP {st} but only {r_bytes} bytes vs {b_bytes} for a browser (title: '{bot_resp.get('title','')}')"
    return "ok", f"HTTP {st}, {r_bytes} bytes (browser: {b_bytes} bytes)"


# ---------------------------------------------------------------- inner page

class _LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)


SKIP_EXT = re.compile(r"\.(jpg|jpeg|png|gif|svg|webp|pdf|zip|mp4|mp3|css|js|ico|xml)$", re.I)
PREFER = re.compile(r"service|practice|what-we-do|treatment|about|team|contact", re.I)


def pick_inner_page(home_url, html):
    p = _LinkParser()
    try:
        p.feed(html)
    except Exception:
        return None
    home = urllib.parse.urlparse(home_url)
    host = home.netloc.lower().removeprefix("www.")
    candidates = []
    for href in p.links:
        if href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        absolute = urllib.parse.urljoin(home_url, href).split("#", 1)[0]
        u = urllib.parse.urlparse(absolute)
        if u.scheme not in ("http", "https") or u.netloc.lower().removeprefix("www.") != host:
            continue
        if u.path in ("", "/") or SKIP_EXT.search(u.path):
            continue
        if absolute not in candidates:
            candidates.append(absolute)
    preferred = [c for c in candidates if PREFER.search(c)]
    return (preferred or candidates or [None])[0]


# ---------------------------------------------------------------- main audit

def normalize(url):
    if not re.match(r"https?://", url, re.I):
        url = "https://" + url
    u = urllib.parse.urlparse(url)
    return urllib.parse.urlunparse((u.scheme, u.netloc, u.path or "/", "", u.query, ""))


def meta_robots(resp):
    """noindex / nosnippet signals that limit AI features (Google, Apple)."""
    found = []
    xrt = resp.get("headers", {}).get("x-robots-tag")
    if xrt:
        found.append(f"X-Robots-Tag header: {xrt}")
    for m in re.finditer(r"<meta[^>]+name=[\"']?(robots|googlebot|applebot|bingbot)[\"']?[^>]*>", resp.get("text", ""), re.I):
        c = re.search(r"content=[\"']([^\"']*)", m.group(0), re.I)
        if c:
            found.append(f"<meta name=\"{m.group(1)}\" content=\"{c.group(1)}\">")
    return found


def run(url, inner=None, timeout=20, delay=0.4):
    home_url = normalize(url)
    origin = "{0.scheme}://{0.netloc}".format(urllib.parse.urlparse(home_url))
    out = {"checked_url": home_url, "bot_list_verified_on": VERIFIED_ON, "notes": []}

    # 1. robots.txt
    rob = fetch(origin + "/robots.txt", BROWSER_UA, timeout)
    robots_info = {"url": origin + "/robots.txt", "status": rob.get("status"), "error": rob.get("error")}
    groups = {}
    if rob.get("status") == 200 and "<html" not in rob.get("text", "")[:500].lower():
        groups = parse_robots(rob["text"])
        robots_info["state"] = "found"
        robots_info["sitemaps"] = re.findall(r"(?im)^\s*sitemap:\s*(\S+)", rob["text"])
        robots_info["raw"] = rob["text"][:5000]
    elif rob.get("status") == 200:
        robots_info["state"] = "returned an HTML page instead of a robots.txt file (treated as no rules)"
    elif rob.get("status") and 400 <= rob["status"] < 500:
        robots_info["state"] = f"not found (HTTP {rob['status']}): crawlers treat this as 'everything allowed'"
    else:
        robots_info["state"] = ("unreachable or server error: under the robots.txt standard (RFC 9309) "
                                "crawlers may treat this as 'everything blocked'")
        groups = {"*": [(False, "/")]}
    out["robots_txt"] = robots_info

    # 2. pages to test
    baseline_home = fetch(home_url, BROWSER_UA, timeout)
    if inner is None and baseline_home.get("status") == 200:
        inner = pick_inner_page(baseline_home.get("final_url", home_url), baseline_home.get("text", ""))
    pages = [("homepage", home_url, baseline_home)]
    if inner:
        inner = normalize(inner)
        pages.append(("inner page", inner, fetch(inner, BROWSER_UA, timeout)))
    else:
        out["notes"].append("No inner page found on the homepage; only the homepage was tested.")

    out["pages"] = [{
        "label": label, "url": u, "browser_status": b.get("status"), "browser_final_url": b.get("final_url"),
        "browser_bytes": b.get("bytes"), "browser_title": b.get("title"), "browser_error": b.get("error"),
        "protection_hints": protection_hints(b.get("headers")),
        "meta_robots": meta_robots(b) if b.get("status") == 200 else [],
    } for label, u, b in pages]

    # 3. each bot
    results = []
    for bot in BOTS:
        row = {k: bot[k] for k in ("token", "vendor", "purpose", "source")}
        row["robots"] = []
        for label, u, _ in pages:
            path = urllib.parse.urlparse(u).path or "/"
            q = urllib.parse.urlparse(u).query
            allowed, grp, rule = robots_decision(groups, bot["token"], path + ("?" + q if q else ""))
            row["robots"].append({"page": label, "allowed": allowed, "group": grp, "rule": rule})
        row["live"] = []
        if bot["live"]:
            for label, u, base in pages:
                time.sleep(delay)
                resp = fetch(u, bot["ua"], timeout)
                result, detail = classify(resp, base)
                row["live"].append({"page": label, "status": resp.get("status"), "result": result,
                                    "detail": detail, "protection_hints": protection_hints(resp.get("headers"))})
        row["key_finding"] = any(r["allowed"] for r in row["robots"]) and any(
            l["result"] in ("blocked", "challenge") for l in row["live"])
        results.append(row)
    out["bots"] = results

    # 4. llms.txt (informational only)
    ll = fetch(origin + "/llms.txt", BROWSER_UA, timeout)
    is_text = ll.get("status") == 200 and "<html" not in ll.get("text", "")[:500].lower()
    out["llms_txt"] = {"url": origin + "/llms.txt", "status": ll.get("status"), "present": is_text,
                       "first_line": ll.get("text", "").strip().splitlines()[0][:150] if is_text and ll.get("text", "").strip() else None,
                       "note": "Informational only. Major AI search tools have not committed to using llms.txt."}
    return out


def summarize(r):
    lines = [f"AI crawler access check for {r['checked_url']}",
             f"(bot list verified against vendor docs on {r['bot_list_verified_on']})", ""]
    rt = r["robots_txt"]
    lines.append(f"robots.txt: {rt['state']}  [{rt['url']}]")
    for p in r["pages"]:
        st = p["browser_status"] if p["browser_status"] is not None else "no response: " + str(p["browser_error"])
        lines.append(f"{p['label']}: {p['url']} -> browser HTTP {st}"
                     + (f", behind {', '.join(p['protection_hints'])}" if p["protection_hints"] else ""))
        for m in p["meta_robots"]:
            lines.append(f"    robots meta/header: {m}")
    lines.append("")
    lines.append(f"{'crawler':<18}{'vendor':<16}{'purpose':<10}{'robots.txt':<34}live request")
    for b in r["bots"]:
        rob = "; ".join(("allowed" if x["allowed"] else "BLOCKED") + (f" ({x['rule']})" if x["rule"] else
                        " (no rule)" if x["group"] is None else "") for x in b["robots"][:1])
        if len({x["allowed"] for x in b["robots"]}) > 1:
            rob += " / inner page differs"
        live = ", ".join(f"{l['page']}: {l['result']}" + (f" HTTP {l['status']}" if l["status"] else "") for l in b["live"]) \
            or "robots.txt rule only (this token never crawls by itself)"
        flag = "  <-- KEY FINDING: robots.txt allows, server blocks" if b["key_finding"] else ""
        lines.append(f"{b['token']:<18}{b['vendor']:<16}{b['purpose']:<10}{rob[:33]:<34}{live}{flag}")
    lines.append("")
    for b in r["bots"]:
        for l in b["live"]:
            if l["result"] not in ("ok",):
                lines.append(f"  {b['token']} / {l['page']}: {l['result']}: {l['detail']}")
    ll = r["llms_txt"]
    lines.append("")
    lines.append(f"llms.txt: {'present' if ll['present'] else 'not present'} (HTTP {ll['status']}). {ll['note']}")
    for n in r["notes"]:
        lines.append("Note: " + n)
    lines.append("Limit: requests came from this computer, not the vendors' IP addresses. "
                 "A block here is strong evidence, not proof.")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check whether AI crawlers can reach a website.")
    ap.add_argument("url", help="homepage URL, e.g. https://example.com")
    ap.add_argument("--inner", help="an inner page to test as well (default: picked from homepage links)")
    ap.add_argument("--json", help="also write full results to this JSON file")
    ap.add_argument("--timeout", type=float, default=20, help="seconds to wait per request (default 20)")
    ap.add_argument("--delay", type=float, default=0.4, help="pause between requests in seconds (default 0.4)")
    args = ap.parse_args(argv)
    result = run(args.url, args.inner, args.timeout, args.delay)
    print(summarize(result))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"\nFull results written to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
