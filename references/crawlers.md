# AI crawlers: who they are and what blocking them does

Last checked against each vendor's own documentation: **2026-11-27**. Vendors rename and add bots. If this date is more than about six months old, re-check the source links before relying on the table.

A **crawler** (or bot) is a program that visits web pages automatically. A **user agent** is the name a crawler gives when it requests a page. **robots.txt** is a plain text file at `yoursite.com/robots.txt` that tells crawlers which pages they may visit.

## The three jobs a crawler can do

| Job | What it means for the business | Typical owner wish |
|---|---|---|
| **Training** | Page content may be used to train future AI models. Blocking it does not remove the site from AI answers today. | Often blocked. That is a fair choice. |
| **Search** | Indexes pages so the AI tool can find, show and cite them in answers. Blocking it removes the site from that tool's answers. | Should be allowed. |
| **User-triggered** | Fetches a page at the moment a person asks the AI tool about it (e.g., pastes the URL, or the tool looks up the business). | Should be allowed. |

Many owners want "block training, allow search". The audit should check that the site actually does what the owner intends, and never assume blocking training is a mistake.

## The table

| Token (robots.txt name) | Vendor | Job | Notes | Source |
|---|---|---|---|---|
| `GPTBot` | OpenAI | Training | | https://developers.openai.com/api/docs/bots |
| `OAI-SearchBot` | OpenAI | Search | Controls appearing in ChatGPT search answers. | same |
| `ChatGPT-User` | OpenAI | User-triggered | OpenAI says robots.txt rules "may not apply" to it. | same |
| `ClaudeBot` | Anthropic | Training | | https://support.claude.com/en/articles/8896518 |
| `Claude-SearchBot` | Anthropic | Search | | same |
| `Claude-User` | Anthropic | User-triggered | | same |
| `PerplexityBot` | Perplexity | Search | Perplexity says it is not used for training. | https://docs.perplexity.ai/guides/bots |
| `Perplexity-User` | Perplexity | User-triggered | Perplexity says it "generally ignores robots.txt rules". | same |
| `Googlebot` | Google | Search | Also controls Google AI Overviews and AI Mode, which are part of Search. | https://developers.google.com/search/docs/crawling-indexing/google-common-crawlers |
| `Google-Extended` | Google | Training (and Gemini grounding) | **robots.txt rule only**, never visits pages itself. Google says it "does not impact a site's inclusion in Google Search". | same |
| `bingbot` | Microsoft Bing | Search | Bing documents no separate AI crawler. | https://www.bing.com/webmasters/help/which-crawlers-does-bing-use-8c184ec0 |
| `Applebot` | Apple | Search | Powers Spotlight, Siri and Safari suggestions. Apple says its data may also be used for AI features. | https://support.apple.com/en-us/119829 |
| `Applebot-Extended` | Apple | Training | **robots.txt rule only**, never visits pages itself. Blocking it does not remove the site from Apple search. | same |

## Facts that change the advice

- **Blocking `Google-Extended` does not hide a site from AI Overviews or AI Mode.** Only `Googlebot` rules and page-level controls (`noindex`, `nosnippet`, `max-snippet`, `data-nosnippet`) affect those. Source: https://developers.google.com/search/docs/appearance/ai-features
- **Google says no special AI file or markup is needed** to appear in AI Overviews or AI Mode. Source: same page. This is why `llms.txt` is reported as informational only.
- **`nosnippet` limits AI use.** A `nosnippet` meta tag stops Google from using the page text in snippets and AI features, and Apple says it stops Applebot content being used as AI context. A site-wide `nosnippet` is a serious finding.
- **robots.txt that fails to load is not harmless.** Under the robots.txt standard (RFC 9309), a robots.txt that returns a server error (5xx) or cannot be reached may be treated by crawlers as "block everything". A 404 (not found) is treated as "allow everything".

## How the live test works and its limit

`scripts/check_ai_access.py` requests the homepage and one inner page as a normal browser, then again with each crawler's user agent, and compares the answers.

- OpenAI, Perplexity, Google, Bing and Apple publish full user-agent strings. The script uses them.
- Anthropic publishes only the token names, so the script uses a short string containing the token (e.g., `Mozilla/5.0 (compatible; ClaudeBot/1.0)`). Firewalls usually match on the token, but this is an approximation.
- The requests come from the auditor's computer, not from the vendors' published IP addresses, and firewalls know it. Two kinds of false alarm are common, and the script handles both:
  - **The firewall reacts to the test tool.** Cloudflare, for example, recognises the "fingerprint" of Python's web client and challenges it when it claims to be a known bot, while the same request from another tool gets through. The script re-tests every block with `curl` (installed by default on macOS, Windows 10+ and most Linux). If `curl` gets the real page, the result is `client_flagged`: **not a finding**, don't report it as a block.
  - **The firewall rejects fake search bots in general.** If `Googlebot` and `bingbot` are blocked too, the firewall is probably rejecting anything that claims to be a well-known bot from the wrong address. The script's pattern is then `fake_bot_filter_likely`. That is normal protection and says little about real AI bots. Mention it in one line, with the confirm steps below, but don't present it as an AI block.
- The script only flags `KEY FINDING` when its pattern is `ai_specific_block_likely`: AI bots blocked (confirmed with `curl`) while `Googlebot` and `bingbot` get through. Even then it is strong evidence, not proof. Report it as "likely blocked" and give the owner a way to confirm (see below).
- Without `curl`, blocks can't be re-tested. The script says so; treat any block as unconfirmed.

### How the owner can confirm

- **Cloudflare, or another CDN or firewall (Sucuri, Wordfence, Imperva, host-level):** open the bot or security settings and look for anything that blocks "AI bots", "AI crawlers", "scrapers" or "bad bots". Then check the security events or firewall log for the bot names above. Menu names change, so search the provider's help pages for "block AI bots" if the setting is hard to find.
- **Server logs:** search for the bot names and check the status codes returned.
- Vendors publish IP lists to verify real bot traffic: OpenAI (`https://openai.com/gptbot.json`, `searchbot.json`, `chatgpt-user.json`), Anthropic (`https://claude.com/crawling/bots.json`), Perplexity (`https://www.perplexity.ai/perplexitybot.json`, `perplexity-user.json`).
