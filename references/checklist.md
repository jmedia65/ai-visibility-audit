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
- **Field insight:** robots.txt says "allow" while the CDN or firewall answers bots with 403 or a challenge page. The script flags this as `KEY FINDING`. It is often the most valuable finding of the whole audit, because the owner believes they are open. Report it as "likely blocked" and include the confirm steps from `crawlers.md`. Look at the pattern: AI bots blocked while `Googlebot` and `bingbot` pass points strongly to an AI-specific block.
- `different` means the bot got a much smaller page. It can be a bot-check page the script did not recognise, or a stripped page. Mention it as "worth checking", not as a block.
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

**How to read it**

- **Field insight:** a service the business is proud of exists only as a bullet point in a list. When a prospect asks an AI tool about that exact service, the tool tends to recommend the competitor that has a clear page for it. This is usually a top-5 fix. Name the services and the page where the bullet lives.
- **Field insight:** specific gets found, generic gets skipped. A narrow page ("Emergency drain cleaning in Riverside") often outperforms the generic homepage for the exact question a prospect asks.
- A 150-word service page is better than none but thin. Note what a prospect would want answered that is missing.
- Don't demand a page per tiny sub-service. Focus on the 3-6 services that bring the most work (ask the user if unsure).
- If the sitemap is missing and the navigation is built with JavaScript, the scan may miss pages. Say so, and treat "no page found" as "not found by the scan", then check with a web search such as `site:example.com drain cleaning` if search is available.

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
- **Field insight:** one or very few reviews, against competitors with dozens or hundreds. Usually nobody ever asked customers. The fix is a simple ask-for-review routine, not a tool.
- **Field insight:** when a site does not say how pricing works, AI tools fill the blank with caveats such as "contact them to confirm pricing before engaging". The fix is not necessarily publishing prices; explaining *how* pricing works (ranges, what affects the cost, what the first step costs) is enough.
- Review platforms' rules differ. Never suggest buying reviews, gating reviews or offering rewards for positive ones.

**Fix templates**

- Reviews: "Ask every satisfied customer this month, by text or email, with a direct link to your review page. Aim for [N] new detailed reviews in 60 days." Effort: minutes per week.
- Pricing: draft a short "How pricing works" paragraph based only on what the site already implies, marked as a draft.

---

## 5. Local presence

**Sources:** the public Business Profile link if the user gave one, what is visible in web search results, and anything the user pastes. **Do not scrape Google Maps or any login-only page.**

| Check | How | Evidence |
|---|---|---|
| 5a. Business Profile exists and matches the site | If the user gave a public link or pasted details: compare name, primary category, hours, phone, website link and address with the site. If you have web search, search `"[business name]" [town]` and note what the results show. | each field: profile value vs site value |
| 5b. Primary category fits the main service | from 5a | |
| 5c. Hours and booking link work | from 5a; check the website link on the profile loads (HTTP status) | status code |
| 5d. **Name variations across the web** | Web search the business name and close variants (with and without "LLC", "& Co", the founder's name, an old name). Note directories and listings showing a different name, phone or address. | each variant + URL |

**How to read it**

- **Field insight:** profile errors are common and cheap to fix: wrong primary category, wrong hours, map pin in the wrong place, two different names. Fixing them takes minutes.
- **Field insight:** for many small businesses, most search traffic is people typing the business's own name: referrals checking them out. A broken booking link, wrong hours or an outdated profile loses those people silently.
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

**How to read it**

- **Key concept for the report: being known by name is not the same as being recommended.** A business can be described perfectly when asked about by name and still never appear when a prospect asks for a recommendation. Report 7a and 7b separately.
- Every Mode B statement in the report is labeled as an approximation.
- If the user ran Mode A and pasted results, those are real AI answers and take priority over Mode B. Quote them as given.
