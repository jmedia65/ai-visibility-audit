---
name: ai-visibility-audit
description: Audit how visible a local or regional service business is to AI assistants (ChatGPT, Claude, Perplexity, Gemini, Google AI Overviews and AI Mode) and produce an evidence-backed report with the five next fixes ranked by impact and effort. Checks whether AI crawlers can actually reach the site (including firewalls that silently block them), whether the site clearly says who, where and what, service pages, reviews and pricing clarity, Business Profile consistency, copied content, and runs an AI answer test. Use this whenever someone asks to audit a website for AI visibility, AI search, AEO, GEO or LLM visibility, asks "why doesn't ChatGPT recommend us?" or "do we show up in AI answers?", or wants an AI-readiness check of a dentist, law firm, accountant, clinic, contractor, agency, consultant or any other local business site, even if they don't say "audit".
license: MIT
compatibility: Needs network access. The bundled scripts need Python 3.9+ (standard library only, no installs). Web search, if available, enables the AI answer approximation and the copied-content check.
metadata:
  author: Max Braglia
  homepage: https://maxbraglia.com
  version: "1.0.0"
---

# AI visibility audit

Audits how visible a local or regional service business is to AI assistants and hands the owner a prioritized, evidence-backed fix list.

**The fix list is the product.** The owner should come away with findings they didn't already know and five fixes specific enough to act on today. The score is secondary: a trend line for re-audits.

## Ground rules

These keep the report trustworthy. An audit that invents one finding loses the owner's trust in all the others.

- **Evidence or "not checked".** Every finding cites a URL with a quote, a status code, a script output line or a search result. If you couldn't see something (login needed, page didn't load, no web search), write "not checked" with the reason. Never guess, and never describe a page you didn't load.
- **Label approximations.** The web-search mode of the AI answer test is not what AI tools actually answer. Say "approximation" everywhere it appears.
- **Plain English.** Many readers are not developers. Explain a technical term in one line the first time you use it. No hype, no promises of rankings, citations or traffic.
- **Respect the owner's choices.** Blocking AI *training* bots while allowing *search* bots is a valid setup, not a mistake.
- **Stay in bounds.** No logging in, no scraping Google Maps or other sites that forbid it, no paid services unless the user has connected them and agrees. Nothing industry-specific, legal or professional advice.

## Workflow

The scripts live in `scripts/` next to this file. Use this skill's own directory to build their paths. Write their JSON output to a temporary folder (or `./ai-visibility-audit-data/` if there is none), not into the user's project.

### Step 1: Scan first, then ask once

The user must give a website URL. If they didn't, ask for it and stop.

Run the site scan straight away, so your questions come with sensible guesses:

```bash
python3 <skill-dir>/scripts/scan_site.py <url> --json <tmp>/site.json
```

From the homepage title, opening text, headings, structured data and service-looking URLs, work out: the business name as customers would search it, the main town or service area, and the 3-6 main services. Then ask **one short round** of questions (skip anything the user already told you):

> I scanned [domain]. Please confirm or correct:
> 1. Business name: **[guess]**
> 2. Main town / service area: **[guess]**
> 3. Main services: **[guess list]**
>
> Optional, improves the audit: 1-3 competitors you worry about, your public Google Business Profile link, and whether you have Search Console, GA4 or an SEO data tool connected here.

If the user can't answer (e.g., a non-interactive run), continue with your guesses and list them as assumptions at the top of the report.

If `python3` isn't available, do the checks with your own fetch and search tools: robots.txt and the pages can still be read, but mark the live crawler test (check 1d) "not checked: needs Python to send requests as each crawler".

### Step 2: Crawler access

```bash
python3 <skill-dir>/scripts/check_ai_access.py <url> --json <tmp>/access.json
```

It reads robots.txt for 13 AI and search crawlers, then requests the homepage and one inner page with each crawler's user agent and compares the answer with a normal browser request. Pass `--inner <url>` to test a specific service page instead of the auto-picked one. Read `references/crawlers.md` for what each bot does and for the limit of this test (requests come from the user's computer, not the vendors' addresses), and `references/checklist.md` section 1 for how to report it.

### Step 3: Audit areas 2-6

Read `references/checklist.md` and work through areas 2-6 in order, using `site.json` first and loading pages or searching the web only where the scan didn't capture what you need. The checklist says what to look at, what counts as evidence, and which patterns are the high-value findings. Most of those patterns are things generic checklists miss:

- robots.txt says "allow" while the CDN or firewall blocks AI bots.
- A key service exists only as a bullet point, so a competitor with a dedicated page gets the recommendation.
- No explanation of how pricing works, so AI tools add "confirm pricing first" caveats.
- Bought-in articles copied word for word across many other sites, often off-topic.
- Business Profile errors: wrong category, hours, map pin, or two different names.
- Name searches (referrals checking the business out) hitting a broken booking link or outdated profile.
- A handful of reviews against competitors with dozens. Usually nobody asked.
- Specific gets found, generic gets skipped.

If the user has Search Console, GA4 or an SEO data tool connected, use it to support findings (e.g., the share of searches that are the business's own name, which pages get found). Never require it, and ask before any call that spends credits.

### Step 4: AI answer test

Read `references/prompt-templates.md`. Build 5-8 prompts the way a prospect would ask. Then:

- **Mode B (automatic):** if you have web search, run the prompts and record who appears and which sources recur. Label it as an approximation.
- **Mode A (the real test):** put the prompts and a blank scorecard in the report for the owner to run in ChatGPT, Perplexity, Gemini and Google AI Mode.

Report "known by name" and "recommended" separately. A business can be described perfectly when asked about by name and still never be suggested to someone who doesn't know it. Make that gap visible.

### Step 5: Score and rank fixes

Read `references/scoring.md`. Rate each area 0-5 against the anchors, compute the overall score from the rated areas only (never count "not checked" as zero), then choose the top 5 fixes: blockers first, then impact, then least effort. Each fix says what to do, where, who usually does it, and which findings it comes from.

### Step 6: Write the report

Read `references/report-template.md` and follow its structure exactly. Save the report as `AI-VISIBILITY-AUDIT-<domain>-<YYYY-MM-DD>.md` in the working directory. If an earlier report for the same domain is there, add the comparison section. Then give the short chat summary the template describes.

Before saving, reread the report once and check:

- every finding has evidence,
- every Mode B mention is labeled,
- each top fix is specific enough to do today,
- nothing is claimed about pages, profiles or AI answers you didn't actually see.

An example of a finished report, for a fictional business, is in `examples/sample-report.md`.

## What this skill doesn't do

It doesn't track rankings, crawl a whole site for technical SEO, write the content for the owner, measure how often AI tools actually cite the business, or give legal or professional advice. It says so in the report's "What wasn't checked" section.
