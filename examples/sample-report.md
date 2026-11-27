> **Fictional example.** Oakline Plumbing, its competitors, its website and every number below are invented to show what the report looks like. The `.example` domain is reserved and does not exist.

# AI visibility audit: Oakline Plumbing

**Site:** https://oaklineplumbing.example · **Location:** Riverside and surrounding county · **Services checked:** emergency plumbing, drain cleaning, water heater installation, leak detection · **Date:** 2026-03-02

## 1. Summary

The biggest problem is invisible to you: your website's security service is turning away the search bots that ChatGPT, Claude and Perplexity use, even though your robots.txt file invites them in.
Your homepage is clear about who you are and where, and your drain-cleaning page is one of the best in the area.
Unblocking those bots, fixing the booking link on your Google profile and getting a steady flow of reviews would remove the main reasons AI tools have to skip you.

**Score: 49 / 100** (scored on 7 of 7 areas; area 7 is an approximation). This is a trend line for comparing future audits, not a grade.

## 2. Top 5 fixes

| # | Fix | Impact | Effort | Who | Findings |
|---|-----|--------|--------|-----|----------|
| 1 | Let AI search bots through the firewall | High | Minutes | Web person | 1.1 |
| 2 | Fix the booking link and Saturday hours on your Google profile | High | Minutes | Owner | 5.1, 5.2 |
| 3 | Use one business name everywhere | High | Minutes | Owner + web person | 2.2, 5.3 |
| 4 | Ask every happy customer for a review | High | Minutes a week | Owner | 4.1 |
| 5 | Give water heaters and emergency call-outs their own pages | High | Hours | Web person | 3.1, 3.2 |

**1. Let AI search bots through the firewall.**
Your site runs behind Cloudflare (a service that speeds up and protects websites). When we requested your pages as `OAI-SearchBot` (ChatGPT search), `Claude-SearchBot` and `PerplexityBot`, Cloudflare answered with a "Just a moment..." check page instead of your site. Google's and Bing's bots got through. In Cloudflare, open the bot settings and turn off the option that blocks AI bots, or add an exception that allows `OAI-SearchBot`, `ChatGPT-User`, `Claude-SearchBot`, `Claude-User`, `PerplexityBot` and `Perplexity-User`. If you don't want AI companies training on your content, you can keep blocking `GPTBot` and `ClaudeBot`: that won't affect whether you're found.

**2. Fix the booking link and Saturday hours on your Google profile.**
The "Book online" link on your profile goes to `https://oaklineplumbing.example/book-online`, which returns "page not found" (HTTP 404). Change it to `https://oaklineplumbing.example/book/`. Your profile also says you're closed Saturdays; your website says "Saturday 8am-2pm". People who search your name to check you out (often referrals) hit these first.

**3. Use one business name everywhere.**
Your website header says "Oakline Plumbing", the hidden business details on your site (structured data) say "Oakline Plumbing & Drain LLC", and two directories list "Oakline Plumbing and Heating". Pick one, normally the name on your sign and Google profile, and change the others. Ask your web person to update the structured data and footer; update the directory listings yourself.

**4. Ask every happy customer for a review.**
Your profile shows 7 reviews, the newest from 2024. The three plumbers that appeared most in our search approximation show 96 to 212 reviews, most from the last year. After each finished job this month, text the customer a direct link to your review page with one line: "Would you mind sharing how today went? It really helps a small business." Aim for 20 detailed reviews in 60 days. Never offer anything in return for a review.

**5. Give water heaters and emergency call-outs their own pages.**
Water heater installation, which you told us is your most profitable job, appears only as a bullet point on `/services/`. Emergency plumbing has no page of its own either. Create `/services/water-heater-installation/` and `/services/emergency-plumber/`. Open each with one sentence that answers the question directly, for example: "Oakline Plumbing installs and replaces gas and electric water heaters across Riverside county, usually within two days." Then cover who it's for, what's involved, how pricing works, the area you cover and how to book.

## 3. Scorecard

| Area | Rating | Verdict |
|------|--------|---------|
| 1. AI crawler access | 2 Needs work | robots.txt allows AI bots, but the firewall blocks their search bots |
| 2. Clarity | 3 Needs work | Clear opening; two business names and no named people |
| 3. Service coverage | 3 Needs work | Strong drain page; two main services are only bullets |
| 4. Trust and proof | 2 Needs work | 7 reviews, newest from 2024; no pricing explanation |
| 5. Local presence | 3 Needs work | Profile found; broken booking link and wrong hours |
| 6. Content quality | 1 Missing | 140 articles, most copied word for word on other sites |
| 7. AI answer test | 3 (approximation) Needs work | Known by name, not found for recommendation searches |

## 4. Findings by area

### 1. AI crawler access

**Verdict:** your robots.txt says yes, your firewall says no, for most AI search bots.

| Crawler | Vendor | Job | robots.txt | Live test |
|---------|--------|-----|------------|-----------|
| OAI-SearchBot | OpenAI | Search | allowed | challenge (HTTP 403) |
| ChatGPT-User | OpenAI | User-triggered | allowed | challenge (HTTP 403) |
| Claude-SearchBot | Anthropic | Search | allowed | challenge (HTTP 403) |
| Claude-User | Anthropic | User-triggered | allowed | challenge (HTTP 403) |
| PerplexityBot | Perplexity | Search | allowed | challenge (HTTP 403) |
| Perplexity-User | Perplexity | User-triggered | allowed | challenge (HTTP 403) |
| GPTBot, ClaudeBot | OpenAI, Anthropic | Training | allowed | challenge (HTTP 403) |
| Googlebot, bingbot, Applebot | Google, Bing, Apple | Search | allowed | OK (HTTP 200) |
| Google-Extended, Applebot-Extended | Google, Apple | Training | allowed | robots.txt rule only |

- **1.1 AI search bots get a challenge page despite robots.txt allowing them.** Requests to `https://oaklineplumbing.example/` and `/services/drain-cleaning/` with the user agents of six AI search and user-triggered bots returned HTTP 403 with the header `cf-mitigated: challenge` and the page title "Just a moment...". A normal browser got HTTP 200 and the real page. Google, Bing and Apple's bots got the real page, so this looks like an AI-specific block rather than a general bot filter. These requests came from our computer, not from the AI companies' own addresses, so this is strong evidence, not proof; your Cloudflare security log will confirm it. Why it matters: AI tools that can't read your pages can't recommend or cite them.
- **1.2 robots.txt is fine.** `https://oaklineplumbing.example/robots.txt` (robots.txt: a file that tells crawlers which pages they may visit) loads (HTTP 200) and allows all crawlers with `User-agent: *` / `Allow: /`.
- **1.3 No page-level blocks.** No `noindex` or `nosnippet` tags on the pages checked.
- **1.4 No llms.txt.** `/llms.txt` returns 404. This is informational only: major AI search tools haven't committed to using it, and Google says no special AI file is needed.

### 2. Clarity

**Verdict:** a machine can tell what you do and where, but not exactly what you're called or who works there.

- **2.1 The opening is clear.** Homepage opening: "Oakline Plumbing is a family-run plumber in Riverside, fixing leaks, drains and water heaters for homeowners across the county." Name, place, services and audience are all in the first sentence.
- **2.2 Two business names on the site.** Header and page titles: "Oakline Plumbing". Structured data (the hidden block that describes the business to machines) on the homepage: `"name": "Oakline Plumbing & Drain LLC"`. AI tools may treat these as two different businesses.
- **2.3 Phone and address match.** `(555) 010-0100` and "12 Mill Street, Riverside" appear identically on all 18 pages checked.
- **2.4 No named people.** `/about/` says "our experienced team of licensed plumbers" but names nobody and shows no licence numbers or photos.
- **2.5 Structured data is valid** (`Plumber` type, no errors) but is missing `openingHours` and `areaServed`.

### 3. Service coverage

**Verdict:** one excellent service page; your most profitable service has none.

- **3.1 Water heater installation is only a bullet.** On `/services/`: "• Water heater installation and repair". No other page mentions it. No page found in the sitemap (84 URLs) or the menu.
- **3.2 Emergency plumbing has no page.** The homepage says "24/7 emergency call-outs" once, in the footer.
- **3.3 Drain cleaning page is strong.** `/services/drain-cleaning/`: 1,240 words, names Riverside in the title and opening, five question headings (e.g., "How long does drain cleaning take?" answered in the first sentence), and a "Book a visit" button.
- **3.4 Leak detection page is thin.** `/services/leak-detection/`: 160 words, no location, no next step.

### 4. Trust and proof

**Verdict:** good work, little visible proof, and no word on cost.

- **4.1 Few, old reviews.** Your Google profile (details you pasted) shows 7 reviews, the newest from June 2024. Review counts visible in search results for the competitors that appeared most: Northgate Plumbing 212, Mill Valley Plumbing 141, Riverside Rooter Co 96.
- **4.2 Two testimonials on the site,** both on the homepage, both first name only: "Fast, tidy and fair. — Jen".
- **4.3 No explanation of pricing.** No prices, ranges, call-out fee or "free estimate" wording on any of the 18 pages checked. AI tools tend to fill this gap with "contact them for pricing" caveats.

### 5. Local presence

**Verdict:** you have a profile, but two of its details send customers to the wrong place.

(Checked from the profile details you pasted.)

- **5.1 Broken booking link.** Profile "Book online" link: `https://oaklineplumbing.example/book-online` → HTTP 404. The working booking page is `/book/` (HTTP 200).
- **5.2 Saturday hours disagree.** Profile: "Saturday: Closed". Website footer: "Sat 8am-2pm".
- **5.3 Name variation in directories.** Two directory listings found by web search use "Oakline Plumbing and Heating": `https://riversidedirectory.example/oakline-plumbing-heating` and `https://countytrades.example/listing/4471`.
- **5.4 Category fits.** Primary category "Plumber".

### 6. Content quality

**Verdict:** the blog is mostly rented content.

- **6.1 Articles copied word for word on other sites.** We searched three sentences from three different articles as exact quotes. Each appeared on 23 to 41 other plumbing websites. Example: "A running toilet can waste up to 200 gallons of water a day, which adds up quickly on your monthly bill." (`/blog/running-toilet-costs/`).
- **6.2 Many articles are off-topic.** Of 140 articles, titles include "10 spring cleaning tips for your garage" and "How to choose patio furniture".
- **6.3 Last article: 2025-08-14.**
- **6.4 No next step in articles.** None of the 5 articles checked links to a service page or booking.

## 5. AI answer test

Being known by name is not the same as being recommended. Searches for your name find you and describe you correctly; searches a new customer would make don't find you at all.

### Mode B: web search approximation (not real AI answers)

This shows which pages web search surfaces for these questions: the sources AI tools with search are likely to draw from. It does not show what ChatGPT, Gemini or any other AI tool actually answers. Search tool: agent web search, 2026-03-02.

| # | Prompt | You appeared? | Where | Competitors appearing | Recurring sources |
|---|--------|---------------|-------|-----------------------|-------------------|
| 1 | Who's a good plumber in Riverside? | No | | Northgate, Riverside Rooter, Mill Valley | review sites, "best plumbers" list articles |
| 2 | Best emergency plumber near Riverside | No | | Northgate, Riverside Rooter | review sites, Northgate's emergency page |
| 3 | Who can install a new water heater in Riverside? | No | | Mill Valley (dedicated page) | Mill Valley's water heater page |
| 4 | Who can clear a blocked drain in Riverside? | Yes | your drain-cleaning page, result 4 | Riverside Rooter | your page, review sites |
| 5 | My water heater is leaking in Riverside, who should I call? | No | | Mill Valley, Northgate | list articles |
| 6 | Oakline Plumbing reviews | Yes | your Google profile, your site | | review sites |
| 7 | Is Oakline Plumbing in Riverside any good? | Yes | your site, one directory | | directories |

- **Known by name (approximation):** results describe you accurately, but show only 7 reviews.
- **Recommended (approximation):** you appeared in 1 of 5 recommendation searches, and only for the one service with its own strong page.

AI tools can describe you when someone already knows your name, but are unlikely to suggest you to someone who doesn't.

### Mode A: run these yourself (the real test)

Open each AI tool in a private or logged-out browser window if you can. Paste each prompt exactly, and fill one row per prompt per tool. It takes about 20 minutes. Run it again at the re-audit to compare.

Tools: ChatGPT, Perplexity, Gemini, Google AI Mode (google.com, "AI Mode" tab).

1. Who's a good plumber in Riverside?
2. Best emergency plumber near Riverside
3. Who can install a new water heater in Riverside?
4. Who can clear a blocked drain in Riverside?
5. My water heater is leaking in Riverside, who should I call?
6. Oakline Plumbing reviews
7. Is Oakline Plumbing in Riverside any good?

```
Tool: ____________   Date: ____________

| # | Were you named? (yes / no / only when asked by name) | Competitors named | Sources cited | Anything wrong or cautionary said about you? |
|---|------|------|------|------|
| 1 |      |      |      |      |
| 2 |      |      |      |      |
| 3 |      |      |      |      |
| 4 |      |      |      |      |
| 5 |      |      |      |      |
| 6 |      |      |      |      |
| 7 |      |      |      |      |
```

## 6. What wasn't checked, and why

- **Map pin location:** needs a look at the profile map; not visible in what you pasted.
- **Reviews on sites other than Google:** counts weren't visible in search results without logging in.
- **Pages beyond the 18 scanned:** the scan covered the homepage, about, contact, all service pages and the 5 newest articles.
- This audit doesn't measure rankings, traffic or how often AI tools actually cite you. Those need Search Console, analytics or a tracking tool.

## 7. Re-audit

Run this audit again in 30-60 days, after the top fixes are done, and compare the scorecard and the Mode A results. Ask: "Re-audit https://oaklineplumbing.example and compare with AI-VISIBILITY-AUDIT-oaklineplumbing.example-2026-03-02.md".
