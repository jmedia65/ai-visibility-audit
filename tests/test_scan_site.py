"""Tests for scripts/scan_site.py against a fictional local site.

Run from the repo root:  python3 -m unittest discover tests
"""
import gzip
import http.server
import json
import sys
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import scan_site  # noqa: E402

BIZ = {"@context": "https://schema.org", "@type": "Plumber", "name": "Oakline Plumbing",
       "telephone": "(555) 010-0100",
       "address": {"@type": "PostalAddress", "streetAddress": "12 Mill Street", "addressLocality": "Riverside",
                   "addressRegion": "CA", "postalCode": "90000"}}


def page(title, body, jsonld=None, extra_head=""):
    ld = f'<script type="application/ld+json">{jsonld}</script>' if jsonld else ""
    return (f"<html lang='en'><head><title>{title}</title>{ld}{extra_head}</head><body>"
            f"<nav><a href='/'>Home</a><a href='/services/drain-cleaning/'>Drain cleaning</a>"
            f"<a href='/about/'>About</a><a href='/contact/'>Contact us</a></nav>"
            f"<main>{body}</main><footer>Call (555) 010-0100. 12 Mill Street, Riverside, CA 90000</footer></body></html>")


PAGES = {
    "/": page("Oakline Plumbing | Riverside plumbers",
              "<h1>Plumbers in Riverside</h1><p>Oakline Plumbing fixes leaks, drains and water heaters for homes "
              "in Riverside.</p><a href='tel:+15550100100'>Call now</a><a href='/book/'>Book a visit</a>",
              json.dumps(BIZ)),
    "/services/drain-cleaning/": page("Drain cleaning", "<h1>Drain cleaning</h1><h2>How much does drain cleaning cost?</h2>"
                                      "<p>Most visits are a flat fee of $149 with a free estimate first.</p>"),
    "/about/": page("About", "<h1>Meet the team</h1><p>Founded by Dana Reyes, licensed master plumber.</p>",
                    '{"@type": "Organization", "name": "Oakline Plumbing Co"'),  # broken JSON on purpose
    "/contact/": page("Contact", "<h1>Contact</h1><form></form><p>Call (555) 010-0199 after hours.</p>"
                      "<p>Fax 555-010-0177 4 Elm Road, Riverside, CA 90000</p>"),
    "/spring-drain-tips/": page("Spring drain tips", "<h1>Spring drain tips</h1><p>Roots from street trees push into old "
                                "clay sewer lines every spring, and the first sign is usually a gurgling ground-floor "
                                "toilet after heavy rain.</p>"),
    "/blog/winter-pipes/": page(
        "Winter pipes", "<h1>Keeping pipes safe in winter</h1><p>When the overnight temperature in Riverside drops "
        "below freezing, uninsulated pipes along exterior walls are the first to split and flood a crawlspace. "
        "Short.</p>", json.dumps({"@type": "BlogPosting", "headline": "Winter pipes",
                                  "datePublished": "2026-01-15"})),
}


def urlset(paths):
    return ("<?xml version='1.0'?><urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"
            + "".join(f"<url><loc>{{base}}{p}</loc><lastmod>2026-01-15</lastmod></url>" for p in paths)
            + "</urlset>")


POST_SET = urlset(["/blog/winter-pipes/", "/spring-drain-tips/"])  # WordPress-style post at the root
PAGE_SET = urlset([p for p in PAGES if p not in ("/", "/blog/winter-pipes/", "/spring-drain-tips/")])


class FakeSite(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, status, data, ctype):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        base = f"http://127.0.0.1:{self.server.server_address[1]}"
        if self.path == "/robots.txt":
            return self._send(200, f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap_index.xml\n".encode(), "text/plain")
        if self.path == "/sitemap_index.xml":
            body = (f"<?xml version='1.0'?><sitemapindex xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"
                    f"<sitemap><loc>{base}/post-sitemap.xml.gz</loc></sitemap>"
                    f"<sitemap><loc>{base}/page-sitemap.xml.gz</loc></sitemap></sitemapindex>")
            return self._send(200, body.encode(), "application/xml")
        if self.path in ("/page-sitemap.xml.gz", "/post-sitemap.xml.gz"):
            body = POST_SET if self.path.startswith("/post") else PAGE_SET
            return self._send(200, gzip.compress(body.replace("{base}", base).encode()), "application/gzip")
        if self.path in PAGES:
            return self._send(200, PAGES[self.path].encode(), "text/html; charset=utf-8")
        return self._send(404, b"<html><title>Not found</title></html>", "text/html")


class ScanSiteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), FakeSite)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        cls.r = scan_site.run(cls.base + "/", timeout=5, delay=0)
        cls.pages = {p["url"].replace(cls.base, ""): p for p in cls.r["pages"]}

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_gzipped_sitemap_index_read(self):
        self.assertEqual(self.r["sitemap"]["url_count"], 5)

    def test_root_post_from_post_sitemap_is_article(self):
        self.assertEqual(self.pages["/spring-drain-tips/"]["type"], "article")
        self.assertEqual(self.r["articles"]["count"], 2)

    def test_broken_booking_link_found(self):
        broken = [b for b in self.r["booking_links"] if b["result"] == "broken"]
        self.assertTrue(any(b["url"].endswith("/book/") and b["status"] == 404 for b in broken))

    def test_fax_number_not_merged_into_address(self):
        addrs = self.pages["/contact/"]["addresses"]
        self.assertTrue(any(a.startswith("4 Elm Road") for a in addrs), addrs)

    def test_page_types_guessed(self):
        self.assertEqual(self.pages["/services/drain-cleaning/"]["type"], "service")
        self.assertEqual(self.pages["/blog/winter-pipes/"]["type"], "article")
        self.assertEqual(self.pages["/"]["type"], "home")

    def test_business_schema_parsed(self):
        home = self.pages["/"]
        self.assertIn("Plumber", home["jsonld_types"])
        self.assertEqual(self.r["consistency"]["business_names_in_structured_data"], {"Oakline Plumbing": 1})

    def test_broken_jsonld_reported(self):
        self.assertTrue(self.pages["/about/"]["jsonld_errors"])

    def test_phone_inconsistency_visible(self):
        phones = self.r["consistency"]["phones"]
        self.assertIn("5550100100", phones)
        self.assertIn("5550100199", phones)

    def test_address_found(self):
        self.assertTrue(any("Mill Street" in a for a in self.r["consistency"]["addresses"]))

    def test_pricing_and_question_headings(self):
        svc = self.pages["/services/drain-cleaning/"]
        self.assertIn("money amount", svc["pricing_signals"])
        self.assertIn("flat or fixed fee", svc["pricing_signals"])
        self.assertEqual(svc["question_headings"], 1)

    def test_ctas_found(self):
        self.assertIn("tel: link", self.pages["/"]["calls_to_action"])
        self.assertIn("Book a visit", self.pages["/"]["calls_to_action"])

    def test_article_dates_and_quote_candidates(self):
        art = self.pages["/blog/winter-pipes/"]
        self.assertIn("2026-01-15", art["dates"])
        self.assertEqual(len(art["distinctive_sentences"]), 1)
        self.assertTrue(art["distinctive_sentences"][0].startswith("When the overnight"))

    def test_nav_text_excluded_from_opening_text(self):
        self.assertTrue(self.pages["/"]["opening_text"].startswith("Plumbers in Riverside"))

    def test_summary_renders(self):
        text = scan_site.summarize(self.r)
        self.assertIn("quote-check", text)
        self.assertIn("[service]", text)


class TypeRulesTest(unittest.TestCase):
    def test_large_folder_treated_as_article_library(self):
        urls = {f"https://x.example/resource-hub/topic-{i}/": None for i in range(30)}
        urls["https://x.example/services/drains/"] = None
        types = scan_site.type_urls(urls, {})
        self.assertEqual(types["https://x.example/resource-hub/topic-3/"], "article")
        self.assertEqual(types["https://x.example/services/drains/"], "service")

    def test_prominent_homepage_link_is_scanned_first(self):
        home = "https://x.example/"
        cands = {f"https://x.example/page-{i}/": None for i in range(12)}
        cands["https://x.example/a/b/gold-plan/"] = None  # odd URL, deep path
        nav = [("https://x.example/a/b/gold-plan/", "Learn more")] * 3 + [("https://x.example/page-1/", "Team")]
        prominent = scan_site.prominent_pages(nav, home)
        self.assertEqual(prominent, {"https://x.example/a/b/gold-plan/": 3})
        types = scan_site.type_urls(cands, {})
        chosen, _ = scan_site.choose_pages(home, cands, 5, types, prominent)
        self.assertEqual(chosen[1], "https://x.example/a/b/gold-plan/")

    def test_resource_center_is_article_not_pricing(self):
        self.assertEqual(scan_site.classify_url("https://x.example/resource-center/insurance/home-cover/"), "article")


if __name__ == "__main__":
    unittest.main()
