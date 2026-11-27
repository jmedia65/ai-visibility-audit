"""Tests for scripts/check_ai_access.py. Standard library only.

Run from the repo root:  python3 -m unittest discover tests
"""
import http.server
import sys
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import check_ai_access as cac  # noqa: E402

HOME = ("<html><head><title>Oakline Plumbing | Plumbers in Riverside</title></head><body>"
        + "<p>Emergency plumbing and drain cleaning in Riverside.</p>" * 200
        + '<a href="/services/drain-cleaning/">Drain cleaning</a><a href="tel:5550100">Call</a>'
        + "</body></html>")
CHALLENGE = "<html><head><title>Just a moment...</title></head><body>Checking your browser</body></html>"


class FakeSite(http.server.BaseHTTPRequestHandler):
    """Simulates a site whose robots.txt allows everyone but whose firewall does not."""

    def log_message(self, *args):
        pass

    def _send(self, status, body, ctype="text/html; charset=utf-8", headers=None):
        data = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        ua = self.headers.get("User-Agent", "")
        if self.path == "/robots.txt":
            return self._send(200, "User-agent: *\nAllow: /\n\nUser-agent: Google-Extended\nDisallow: /\n",
                              "text/plain")
        if self.path == "/llms.txt":
            return self._send(404, "not found")
        if "GPTBot" in ua:
            return self._send(403, "<html><title>403 Forbidden</title>Access denied</html>",
                              headers={"Server": "cloudflare"})
        if "ClaudeBot" in ua:
            return self._send(503, CHALLENGE, headers={"cf-mitigated": "challenge", "Server": "cloudflare"})
        if "PerplexityBot" in ua:
            return self._send(200, CHALLENGE)
        if "Claude-User" in ua:
            return self._send(200, "<html><title>Hi</title>short</html>")
        if "Applebot" in ua and self.headers.get("Accept-Encoding") == "identity":
            # Python's urllib sends this header and curl doesn't: stands in for a
            # firewall that recognises the test tool rather than the bot.
            return self._send(403, CHALLENGE, headers={"cf-mitigated": "challenge"})
        return self._send(200, HOME, headers={"Server": "cloudflare"})


class LiveCheckTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), FakeSite)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        cls.result = cac.run(cls.base + "/", timeout=5, delay=0)
        cls.bots = {b["token"]: b for b in cls.result["bots"]}

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_inner_page_picked_from_homepage_links(self):
        self.assertEqual(self.result["pages"][1]["url"], self.base + "/services/drain-cleaning/")

    def test_403_despite_allow_is_key_finding(self):
        gpt = self.bots["GPTBot"]
        self.assertTrue(gpt["robots"][0]["allowed"])
        self.assertEqual(gpt["live"][0]["result"], "blocked")
        self.assertTrue(gpt["key_finding"])

    def test_cloudflare_challenge_header_detected(self):
        self.assertEqual(self.bots["ClaudeBot"]["live"][0]["result"], "challenge")
        self.assertTrue(self.bots["ClaudeBot"]["key_finding"])

    def test_challenge_text_with_200_detected(self):
        self.assertEqual(self.bots["PerplexityBot"]["live"][0]["result"], "challenge")

    def test_much_smaller_page_flagged_different(self):
        self.assertEqual(self.bots["Claude-User"]["live"][0]["result"], "different")
        self.assertFalse(self.bots["Claude-User"]["key_finding"])

    @unittest.skipUnless(cac.CURL, "curl not installed")
    def test_block_that_curl_passes_is_client_flagged(self):
        apple = self.bots["Applebot"]["live"][0]
        self.assertEqual(apple["result"], "client_flagged")
        self.assertEqual(apple["curl_status"], 200)
        self.assertFalse(self.bots["Applebot"]["key_finding"])

    @unittest.skipUnless(cac.CURL, "curl not installed")
    def test_real_block_confirmed_with_curl(self):
        self.assertIn("confirmed with curl", self.bots["GPTBot"]["live"][0]["detail"])

    def test_pattern_is_ai_specific(self):
        self.assertEqual(self.result["pattern"]["code"], "ai_specific_block_likely")

    def test_llms_state_wording(self):
        self.assertEqual(self.result["llms_txt"]["state"], "not present (HTTP 404)")

    def test_normal_bot_ok(self):
        self.assertEqual(self.bots["OAI-SearchBot"]["live"][0]["result"], "ok")
        self.assertFalse(self.bots["OAI-SearchBot"]["key_finding"])

    def test_robots_only_token_not_requested_and_blocked(self):
        ge = self.bots["Google-Extended"]
        self.assertEqual(ge["live"], [])
        self.assertFalse(ge["robots"][0]["allowed"])

    def test_protection_hint_named(self):
        self.assertIn("Cloudflare", self.result["pages"][0]["protection_hints"])

    def test_llms_txt_absent(self):
        self.assertFalse(self.result["llms_txt"]["present"])

    def test_summary_renders(self):
        text = cac.summarize(self.result)
        self.assertIn("KEY FINDING", text)
        self.assertIn("GPTBot", text)


class PatternTest(unittest.TestCase):
    def row(self, token, vendor, result):
        return {"token": token, "vendor": vendor, "live": [{"result": result}]}

    def test_search_bots_blocked_too_means_fake_bot_filter(self):
        rows = [self.row("GPTBot", "OpenAI", "challenge"), self.row("Googlebot", "Google", "challenge"),
                self.row("bingbot", "Microsoft Bing", "blocked"), self.row("ClaudeBot", "Anthropic", "ok")]
        self.assertEqual(cac.site_pattern(rows)[0], "fake_bot_filter_likely")

    def test_only_client_flagged(self):
        rows = [self.row("GPTBot", "OpenAI", "client_flagged"), self.row("Googlebot", "Google", "ok"),
                self.row("bingbot", "Microsoft Bing", "ok")]
        self.assertEqual(cac.site_pattern(rows)[0], "client_flagged_only")

    def test_all_ok(self):
        rows = [self.row("GPTBot", "OpenAI", "ok"), self.row("Googlebot", "Google", "ok")]
        self.assertEqual(cac.site_pattern(rows)[0], "none")


class RobotsParserTest(unittest.TestCase):
    def decide(self, txt, token, path):
        return cac.robots_decision(cac.parse_robots(txt), token, path)[0]

    def test_specific_group_overrides_star(self):
        txt = "User-agent: *\nDisallow: /\n\nUser-agent: GPTBot\nAllow: /\n"
        self.assertTrue(self.decide(txt, "GPTBot", "/"))
        self.assertFalse(self.decide(txt, "ClaudeBot", "/"))

    def test_longest_match_wins(self):
        txt = "User-agent: *\nDisallow: /services/\nAllow: /services/drains/\n"
        self.assertTrue(self.decide(txt, "x", "/services/drains/clogs"))
        self.assertFalse(self.decide(txt, "x", "/services/heating"))

    def test_tie_goes_to_allow(self):
        txt = "User-agent: *\nDisallow: /page\nAllow: /page\n"
        self.assertTrue(self.decide(txt, "x", "/page"))

    def test_wildcards_and_end_anchor(self):
        txt = "User-agent: *\nDisallow: /*.pdf$\n"
        self.assertFalse(self.decide(txt, "x", "/files/menu.pdf"))
        self.assertTrue(self.decide(txt, "x", "/files/menu.pdf?x=1"))

    def test_shared_group_and_case_insensitive_agent(self):
        txt = "User-agent: gptbot\nUser-agent: CLAUDEBOT\nDisallow: /\n"
        self.assertFalse(self.decide(txt, "GPTBot", "/"))
        self.assertFalse(self.decide(txt, "ClaudeBot", "/"))
        self.assertTrue(self.decide(txt, "PerplexityBot", "/"))

    def test_empty_disallow_allows(self):
        self.assertTrue(self.decide("User-agent: *\nDisallow:\n", "x", "/"))

    def test_no_group_reports_none(self):
        allowed, group, rule = cac.robots_decision(cac.parse_robots(""), "GPTBot", "/")
        self.assertTrue(allowed)
        self.assertIsNone(group)

    def test_comments_ignored(self):
        txt = "# block training\nUser-agent: GPTBot # openai\nDisallow: / # all\n"
        self.assertFalse(self.decide(txt, "GPTBot", "/"))


if __name__ == "__main__":
    unittest.main()
