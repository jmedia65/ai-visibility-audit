# Audit checklist

Every check, how to verify it, and what counts as evidence. Read the section for an area before you audit it.

**Evidence rule.** A finding needs at least one of: a URL plus a short quote of what is (or is not) on it, an HTTP status code, a script output line, or a search result URL. If you could not get evidence, the check is "not checked" with the reason. Never fill a gap with a guess, and never describe a page you did not load.

**Finding IDs.** Number findings by area (`1.1`, `1.2`, `3.4` ...) so the top fixes can point to them.

Contents:
1. AI crawler access
2. Clarity: can a machine tell who you are?
3. Service coverage
4. Trust and proof
5. Local presence
6. Content quality
7. AI answer test (see `prompt-templates.md` for the prompts)

---

## 1. AI crawler access

**Source:** `scripts/check_ai_access.py` output. Background and limits: `crawlers.md`.

| Check | How | Evidence |
|---|---|---|
| 1a. robots.txt loads | `robots_txt.state` | URL + status |
| 1b. Search and user-triggered bots allowed by robots.txt | `bots[].robots` for `OAI-SearchBot`, `ChatGPT-User`, `Claude-SearchBot`, `Claude-User`, `PerplexityBot`, `Perplexity-User`, `Googlebot`, `bingbot`, `Applebot` | the matching rule line (e.g. `Disallow: /`) and which group (`*` or the bot name) it came from |
| 1c. Training bots | same, for `GPTBot`, `ClaudeBot`, `Google-Extended`, `Applebot-Extended` | rule line |
| 1d. **Server lets bots in** | `bots[].live`: `blocked`, `challenge` or `different` | status code and detail line, plus `protection_hints` (CDN name) |
| 1e. Page-level blocks | `pages[].meta_robots`: `noindex`, `nosnippet`, `none`, `max-snippet:0` | the tag or header text |
| 1f. llms.txt | `llms_txt.present` | informational only, never affects the score |

**How to read it**

- Blocked **training** bots with allowed **search** bots is a deliberate, valid setup. Report it neutrally ("training bots are blocked; search bots are allowed, so AI tools can still cite you"). Do not recommend unblocking training unless the owner says they want it.
- Blocked **search or user-triggered** bots is a high-impact finding. Quote the rule.
- **Read the `Pattern` line first.** It sums up the live test and decides how you report it:
  - `ai_specific_block_likely`: **field insight:** robots.txt says "allow" while the CDN or firewall answers AI bots with 403 or a challenge page, and Googlebot and bingbot get through. The script flags each such bot as `KEY FINDING`. It is often the most valuable finding of the whole audit, because the owner believes they are open. Report it as "likely blocked" (confirmed with a second request tool) and include the confirm steps from `crawlers.md`.
  - `fake_bot_filter_likely`: Googlebot and bingbot were blocked too. The firewall is probably rejecting anything that claims to be a well-known bot from the wrong address. Normal protection, not evidence against AI bots. One line in the findings, plus the confirm steps as an optional check. Not a top-5 fix on its own.
  - `client_flagged_only`: the firewall reacted to the test tool (Python), and `curl` got the real page. **Not a finding.** At most one line saying the live test passed on the second try.
  - `none`: all good.
- `different` means the bot got a much smaller page. It can be a bot-check page the script did not recognise, or a stripped page. Mention it as "worth checking", not as a block.
- If the output says `curl` was not found, every block is unconfirmed: say so and lower your confidence.
- A site-wide `noindex` or `nosnippet` on the homepage is critical: it hides the page from search and AI features.
- If the browser request itself failed (`baseline_failed`), the site may be blocking all automated requests, or be down. Say so and mark 1d "not checked".

**Fix templates**

- AI-specific firewall block: "In [CDN name, if known], find the setting that blocks AI bots and allow at least `OAI-SearchBot`, `ChatGPT-User`, `Claude-SearchBot`, `Claude-User`, `PerplexityBot` and `Perplexity-User`. You can keep blocking training bots (`GPTBot`, `ClaudeBot`) if you prefer." Effort: minutes, if the owner or web person has access.
- robots.txt block: give the exact lines to change and the replacement.

---

## 2. Clarity: can a machine tell who you are?

**Sources:** `scan_site.py` output (`pages[]` for home, about, contact), then the pages themselves if you need more text.

| Check | How | Evidence |
|---|---|---|
| 2a. **The opening says who, where, what, for whom** | Read the homepage `opening_text`, `title`, `h1` and `meta_description`. Within roughly the first 100 words, are all four present in plain words: business name, town or area, main service(s), who it is for? | quote the opening text; list which of the four are missing |
| 2b. Generic copy | Look for sentences that could belong to any competitor: "We serve individuals, families and businesses", "quality service you can trust", "your satisfaction is our priority". Test: swap in a competitor's name; if the sentence still works, it is generic. | quote 1-3 examples |
| 2c. Name, address, phone consistent | `consistency.phones`, `consistency.addresses`, `business_names_in_structured_data`, `og_site_names`, plus the footer of each page | list every variant and the pages it appears on |
| 2d. About page with real people | `about` pages: names, roles, credentials, photos, years of experience | URL + names found, or "no named people found on [URLs]" |
| 2e. Structured data present | `jsonld_types` on the homepage and contact page. Look for a business type (`LocalBusiness` or a subtype such as `Dentist`, `Plumber`, `LegalService`, `ProfessionalService`, `MedicalClinic`) or at least `Organization`. | types found, page URL |
| 2f. Structured data valid | `jsonld_errors` | the error text |
| 2g. Structured data matches the page | Compare `jsonld` name, telephone, address, opening hours with the visible page and with each other | each mismatch with both values |

**How to read it**

- Structured data (JSON-LD, the hidden block that describes the business to machines) helps machines parse the page. Never present it as a ranking guarantee or as the main fix. Missing structured data on a site that is otherwise clear is a medium finding at most.
- Two different business names (e.g., "Oakline Plumbing" on the site, "Oakline Plumbing & Heating LLC" in structured data, a third in the page title) is a real failure mode: AI tools may treat them as two businesses. Report every variant.
- A different phone number on one page can be legitimate (after-hours line, second office). Report it as "check this is intended".
- **Opening hours in structured data:** `"opens": "00:00", "closes": "00:00"` means **closed all day**, not open 24 hours. Open 24 hours is `"opens": "00:00", "closes": "23:59"` ([Google's LocalBusiness documentation](https://developers.google.com/search/docs/appearance/structured-data/local-business)). Sites that mean "by appointment" often set 00:00 to 00:00 for every day, which tells machines the business is never open: a real finding.
- **The town the user named isn't on the site.** If the user said one town and every address on the site (and the profile, if seen) says another, report it: the owner may think of themselves as serving one place while every machine-readable signal says another. Use the site's address for the checks unless the user confirms otherwise, and suggest stating the service area in plain words if they serve both.
- If the scan could not load the homepage (status not 200), mark the area "not checked".

**Fix templates**

- Rewrite the opening: give a concrete draft sentence built from what the site already says, e.g. "Oakline Plumbing is a family-run plumbing company in Riverside, fixing leaks, drains and water heaters for homeowners across the county." Mark it as a draft for the owner to correct.
- Structured data: name the type to use and the fields to fill (name, address, telephone, url, openingHours, areaServed). Do not paste a full block with values you have not verified.

---

## 3. Service coverage

**Sources:** `scan_site.py` `url_inventory`, `homepage_links`, service-type pages; the services the user confirmed at the start.

| Check | How | Evidence |
|---|---|---|
| 3a. **Each main service has its own page** | For every confirmed service, find a page whose URL, title or H1 is about that service. Search `url_inventory` samples and `homepage_links` by keyword, not only the `service` type guess. | per service: the URL, or "only mentioned as a list item on [URL]: '[quote]'", or "not found on the site" |
| 3b. Service page depth | `word_count`, headings, whether it explains what, who for, process, cost, area | URL + word count + what is missing |
| 3c. Question-style headings with direct answers | `question_headings`, `headings` | quote a heading and the first sentence under it |
| 3d. Location on service pages | Is the town or area named in the title, H1 or opening text? | quote |
| 3e. Next step on service pages | `calls_to_action`, `forms`, `tel: link` | list found, or "none" |
| 3f. **Booking links work** | `booking_links` in `site.json`: every booking tool and contact/booking page linked from the scanned pages, loaded once. `broken` = 404, 410, server error or no response. `unclear` = 401/403/429, often bot protection: open it in a browser if you have one, otherwise list it as "worth clicking yourself". | the link, its status, the button text, how many pages use it |

**How to read it**

- **Field insight:** a service the business is proud of exists only as a bullet point in a list. When a prospect asks an AI tool about that exact service, the tool tends to recommend the competitor that has a clear page for it. This is usually a top-5 fix. Name the services and the page where the bullet lives.
- **Field insight:** specific gets found, generic gets skipped. A narrow page ("Emergency drain cleaning in Riverside") often outperforms the generic homepage for the exact question a prospect asks.
- A 150-word service page is better than none but thin. Note what a prospect would want answered that is missing.
- **A broken booking link is a high-impact, minutes-to-fix finding.** Referrals and people who search the business by name land on the homepage and click "Book": if that fails, they leave silently. Name the button text and every page it appears on.
- Don't demand a page per tiny sub-service. Focus on the 3-6 services that bring the most work (ask the user if unsure).
- If the sitemap is missing and the navigation is built with JavaScript, the scan may miss pages. Say so, and treat "no page found" as "not found by the scan", then check with a web search such as `site:example.com drain cleaning` if search is available. A `site:` search that finds nothing proves nothing: search tools often return no results for it even when the pages exist and are indexed. Never report "not indexed" from a `site:` search; for indexing questions, point the owner to Google Search Console and Bing Webmaster Tools.

**Fix template:** "Create a page for [service] at [suggested URL]. Open with one sentence that answers 'who does [service] in [town]?', then: who it's for, what's involved, how pricing works, the area covered, and how to book." Effort: hours per page.

---

## 4. Trust and proof

**Sources:** site pages (`reviews` type, `review_signals`, `aggregateRating` in `jsonld`), web search for reviews, and anything the user pastes.

| Check | How | Evidence |
|---|---|---|
| 4a. **Review count, recency and detail** | Web search `"[business name]" reviews` and `"[business name]" [town]`. Record the review sources and counts visible in results (Google, Yelp, industry directories, Facebook). Do not log in and do not scrape map listings. If counts are not visible, ask the user or mark "needs your input". | source URL + count + newest review date if visible |
| 4b. Reviews compared with competitors | Same search for each competitor given | counts side by side, with sources |
| 4c. Testimonials or case examples on the site | `reviews` pages, `review_signals` | URL + one short quote |
| 4d. Real people and credentials | from 2d | |
| 4e. **Pricing or fee clarity** | `pricing_signals` on service, pricing and FAQ pages; read the pages. Does the site say how pricing works: ranges, packages, "free first consultation", hourly vs fixed, insurance accepted, financing? | URL + quote, or "no pricing information found on [URLs]" |

**How to read it**

- Recency and detail beat raw count: 80 recent, specific reviews beat 200 old generic ones. Say which you could see.
- **No reviews visible anywhere is a finding, not a gap in the audit.** If the profile (seen in a browser or pasted by the user) and web search show no reviews, AI tools see none either. Report it as "no reviews visible to search or AI tools", and say where you looked.
- Some professions have their own rules about testimonials and advertising. When recommending reviews or testimonials, add one generic line: "check your profession's rules before publishing testimonials on your site." Don't go further than that.
- **Field insight:** one or very few reviews, against competitors with dozens or hundreds. Usually nobody ever asked customers. The fix is a simple ask-for-review routine, not a tool.
- **Field insight:** when a site does not say how pricing works, AI tools fill the blank with caveats such as "contact them to confirm pricing before engaging". The fix is not necessarily publishing prices; explaining *how* pricing works (ranges, what affects the cost, what the first step costs) is enough.
- Review platforms' rules differ. Never suggest buying reviews, gating reviews or offering rewards for positive ones.

**Fix templates**

- Reviews: "Ask every satisfied customer this month, by text or email, with a direct link to your review page. Aim for [N] new detailed reviews in 60 days." Effort: minutes per week.
- Pricing: draft a short "How pricing works" paragraph based only on what the site already implies, marked as a draft.

---

## 5. Local presence

**Sources:** the public Business Profile link if the user gave one, what is visible in web search results, and anything the user pastes. **No automated scraping of Google Maps** (no Maps data URLs such as `tbm=map` or `/maps/preview`, no bulk or repeated requests) and no login-only pages.

**How to see the profile, in order of preference:**

1. **The user pasted the details:** use them, and say so.
2. **The user gave a link and you have a real browser** (a browser pane, a browser extension or similar): open the link **once** and read what the page shows. A `share.google/...` link opens a Google search page with the business panel beside the results (the easiest to read); a `maps.app.goo.gl/...` link opens the place in Google Maps, with the details in the side panel. Read: business name, primary category, rating and review count, hours, phone, address, website and booking links, and any linked social profiles. Don't click through the review list, photos or questions, and don't pan the map. If the page asks you to sign in or shows a CAPTCHA, stop and mark it "needs your input". Don't note the location the browser reports about itself. If the page loads but shows no text (Google Maps draws its panel only when the browser view is visible and has a size), make the view visible or give it a size, or read it from a screenshot. That isn't a second visit. If it still shows nothing, say so and ask for the details or a `share.google` link.
3. **Only a fetch tool:** profile share links (`share.google`, `maps.app.goo.gl`) usually lead to pages that refuse automated visits. That's expected. Don't try workarounds. Resolving the link's redirect can reveal the listing name: that is fine to use.
4. Otherwise: "needs your input", with the self-check below.

Check the profile's website and booking links yourself (load them once, record the status): these are what name searches and referrals click.

| Check | How | Evidence |
|---|---|---|
| 5a. Business Profile exists and matches the site | Compare name, primary category, hours, phone, website link and address with the site. If you have web search, search `"[business name]" [town]` and note what the results show. | each field: profile value vs site value, and how you saw it (browser view, pasted, search result) |
| 5b. Primary category fits the main service | from 5a | |
| 5c. Hours and booking link work | from 5a; check the website link on the profile loads (HTTP status) | status code |
| 5d. **Name variations across the web** | Web search the business name and close variants (with and without "LLC", "& Co", the founder's name, an old name). Note directories and listings showing a different name, phone or address. | each variant + URL |

**How to read it**

- **Field insight:** profile errors are common and cheap to fix: wrong primary category, wrong hours, map pin in the wrong place, two different names. Fixing them takes minutes.
- **Field insight:** for many small businesses, most search traffic is people typing the business's own name: referrals checking them out. A broken booking link, wrong hours or an outdated profile loses those people silently.
- If you saw only some fields (e.g., the name from the link's redirect), report what you saw, mark the area **"partly checked"**, and list the fields still needed.
- When you cannot see the profile, do not guess. Mark 5a-5c **"needs your input"** and include this 5-minute self-check in the report:

> **5-minute Business Profile self-check.** Search your business name on Google and on Apple Maps. Check: (1) the name is exactly the one on your website, (2) the primary category is the service that brings the most work, (3) hours are correct, including holidays, (4) the map pin is on your door, not the street or a neighbour, (5) the website and booking links open the right page, (6) the phone number rings you, (7) there is only one listing for your business at this address. Fix anything wrong from the profile's edit screen.

---

## 6. Content quality

**Sources:** `scan_site.py` `articles`, `url_inventory.article`, article pages and their `distinctive_sentences`; web search for exact quotes.

| Check | How | Evidence |
|---|---|---|
| 6a. **Original or syndicated** | Take 2-3 `distinctive_sentences` from different articles. Web search each in quotes (`"exact sentence"`). Count other domains showing the same text. | the sentence, the search, and the other URLs found |
| 6b. Relevance | Compare article topics (titles in `url_inventory.article.sample`) with the business's services. Estimate the share that is unrelated. | 3-5 example titles that are off-topic |
| 6c. Freshness | `articles.newest_lastmod`, page `dates` | newest date and URL |
| 6d. Next step | `calls_to_action` and `forms` on article pages | per article: found or none |
| 6e. Volume vs. value | `articles.count` | count |

**How to read it**

- **Field insight:** bought-in "content library" articles: hundreds of posts, copied word for word onto many other sites, often on topics unrelated to the business. AI tools have little reason to cite a page that exists in identical form on 50 other sites. If the same sentence appears on 3 or more other domains, report the articles as likely syndicated. Two other domains could be quoting; say "possibly".
- **When exact-quote search doesn't work.** Some search tools ignore quotation marks and return loosely related pages. Test it once: if a quoted sentence returns results that don't contain the sentence, the tool can't do this check. Then:
  - try the article's exact title in quotes, and a shorter, unusual 8-12 word fragment of a sentence;
  - look for library footprints: a large folder of articles (`site.json` treats 25+ URLs in one folder as an article collection), generic topics unrelated to the services, a "content provided by" or vendor credit line, or the same titles on other businesses' sites;
  - if footprints are present, report "possibly syndicated" with those signals as evidence. If you can't tell, mark 6a "inconclusive" and say why. Never call content copied without seeing the copy.
- A site with no blog is not a failure. Mark 6a-6e "not applicable" and score the area on service-page content only (see `scoring.md`).
- Without web search, mark 6a "not checked (needs web search)".
- Old articles are fine if they are still accurate. Flag age only when the newest post is more than 12 months old *and* the business relies on articles.

**Fix templates:** "Stop renewing the content library (or ask the provider to noindex syndicated posts). Replace with one original article a month answering a real question customers ask, linked to the matching service page."

---

## 7. AI answer test

Prompts, the Mode A scorecard and Mode B procedure are in `prompt-templates.md`.

| Check | How | Evidence |
|---|---|---|
| 7a. Named for recommendation prompts | Mode B: is the business, or a page of its site, among the results for "who's a good [service] in [town]"-style prompts? | results list with URLs |
| 7b. Known by name | Mode B: for "[business name] reviews" style prompts, are the results about this business, and what do they say? | URLs + short quotes |
| 7c. Competitors that appear | Mode B: which businesses appear instead | names + URLs |
| 7d. Sources AI tools draw from | Mode B: which sites appear repeatedly (directories, review sites, the business's own pages) | domains |
| 7e. Wrong or cautionary information | Anything inaccurate or negative found in results | quote + URL |
| 7f. Real AI Overviews (spot checks) | If you have a real browser: up to 3 Google searches, not signed in, reading the AI Overview when one appears (procedure in `prompt-templates.md`) | the query, whether an AI Overview appeared, who it named, the sources it cited, a short quote; labeled "seen once" |

**How to read it**

- **Key concept for the report: being known by name is not the same as being recommended.** A business can be described perfectly when asked about by name and still never appear when a prospect asks for a recommendation. Report 7a and 7b separately.
- Every Mode B statement in the report is labeled as an approximation.
- Evidence order: Mode A results the user pasted, then your spot checks (real AI answers, seen once), then Mode B (an approximation). When they disagree, say so and lead with the stronger one.
