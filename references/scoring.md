# Scoring

The score is a **trend line for re-audits**, not a grade. It exists so the owner can run the audit again in 30-60 days and see whether things moved. The fix list is the product. Say this in the report.

## Area ratings (0-5)

Rate each area with the anchors below. Pick the closest anchor; use the numbers in between when the site sits between two. Labels: **4-5 Strong**, **2-3 Needs work**, **0-1 Missing**.

### 1. AI crawler access (weight 20)

| Rating | Anchor |
|---|---|
| 5 | All search and user-triggered bots allowed by robots.txt and get the real page in the live test. No `noindex` or `nosnippet` on key pages. |
| 4 | As 5, but a minor issue: robots.txt missing or messy, or one user-triggered bot gets a `different` result. |
| 3 | One AI vendor's search bot blocked (robots.txt or live), the rest fine. |
| 2 | Several AI search bots blocked or challenged, while Googlebot and bingbot pass. |
| 1 | Most AI search and user-triggered bots blocked or challenged. |
| 0 | Everything blocked: robots.txt disallows all, site-wide `noindex`, or every bot gets a block or challenge. |

Training bots (`GPTBot`, `ClaudeBot`, `Google-Extended`, `Applebot-Extended`) **do not lower the rating** when blocked. That is the owner's choice.

### 2. Clarity (weight 15)

| Rating | Anchor |
|---|---|
| 5 | Opening states who, where, what and for whom in plain words. One consistent name, address and phone. About page with named people and credentials. Valid business structured data matching the page. |
| 4 | One of those missing or weak (often: no structured data, or generic opening). |
| 3 | Two missing, or the opening is generic but the facts are on the page somewhere. |
| 2 | Hard to tell where the business is or what it mainly does without digging. Or name/phone inconsistencies across pages. |
| 1 | Most of the above missing. |
| 0 | A machine could not tell what this business is or where. |

### 3. Service coverage (weight 20)

| Rating | Anchor |
|---|---|
| 5 | Every main service has its own substantial page, naming the location, with question-style headings and a clear next step. |
| 4 | Every main service has a page; some are thin or don't name the location. |
| 3 | Most main services have pages; one important one is only a list item. |
| 2 | About half the main services have pages. |
| 1 | One general services page with a list. |
| 0 | Services are only mentioned on the homepage, or not at all. |

### 4. Trust and proof (weight 15)

| Rating | Anchor |
|---|---|
| 5 | Plenty of recent, detailed reviews (on par with or better than competitors). Testimonials or case examples on the site. Real people shown. Clear explanation of how pricing works. |
| 4 | One gap (often pricing clarity). |
| 3 | Reviews exist but are few, old or behind competitors; or two gaps. |
| 2 | Very few reviews and no on-site proof, or no pricing information and no proof. |
| 1 | Almost no proof of any kind. |
| 0 | Nothing a stranger could use to trust the business. |

If review counts could not be seen and the user did not provide them, rate 4c-4e only and mark the area **"partly checked"** in the scorecard.

### 5. Local presence (weight 10)

| Rating | Anchor |
|---|---|
| 5 | Profile found, all fields match the site, category fits, one name everywhere. |
| 4 | One small mismatch (hours, category could be more specific). |
| 3 | Two mismatches, or name variations in a few directories. |
| 2 | Wrong primary category, wrong phone or hours, or a duplicate listing. |
| 1 | Several serious errors. |
| 0 | No profile found where one clearly should exist. |

If the profile could not be seen, the area is **"not checked"** (needs your input), even if 5d was searched. Report 5d findings anyway.

### 6. Content quality (weight 10)

| Rating | Anchor |
|---|---|
| 5 | Original articles, relevant to the services, recent, each leading to a next step. Or no blog, with strong service pages. |
| 4 | Original and relevant, but stale or missing next steps. |
| 3 | Mixed: some original, some off-topic or thin. |
| 2 | Mostly off-topic or thin. |
| 1 | Large volume of likely syndicated articles. |
| 0 | Almost all content is confirmed copied from elsewhere. |

If the site has no articles, rate from service-page content quality (depth, specificity, originality of wording) and say so.

### 7. AI answer test (weight 10)

| Rating | Anchor |
|---|---|
| 5 | Appears for most recommendation prompts and is described accurately by name. |
| 4 | Appears for some recommendation prompts; accurate by name. |
| 3 | Rarely or never appears for recommendation prompts, but accurate when asked by name. |
| 2 | Not recommended, and by-name results are thin or mix the business up with another. |
| 1 | Not recommended; by-name results show wrong or negative information. |
| 0 | Not findable even by name. |

When only Mode B was run, write the rating as e.g. **"3 (approximation)"**. When Mode A results were pasted by the user, rate from those and say so. With neither, the area is "not checked".

## Overall score (out of 100)

1. For each rated area: `points = rating / 5 x weight`.
2. Add the points of the rated areas. Add the weights of the rated areas.
3. `overall = round(points_total / weights_total x 100)`.
4. Areas marked "not checked" are left out of both totals. They are never counted as zero and never guessed.

Show it as e.g. **"62 / 100 (scored on 6 of 7 areas; Local presence not checked)"**. If fewer than 4 areas were scored, don't give an overall score; say there is not enough data.

Bands for the summary sentence (wording, not a verdict):

- 80-100: AI tools can find and understand the business; the fixes are refinements.
- 60-79: Solid base with clear gaps that cost recommendations.
- 40-59: Real gaps; AI tools likely recommend competitors for some services.
- 0-39: Major gaps; AI tools may struggle to find or recommend the business.

## Top 5 fixes

The most important part of the report. Choose from all findings:

1. **Blockers first.** Anything that stops AI tools seeing the site (search bots blocked, `noindex`, site unreachable for bots) goes at the top regardless of effort.
2. Then sort by **impact** (high > medium > low), then by **effort** (minutes > hours > days: quicker first).
3. If two fixes tie, prefer the one with stronger evidence.
4. Merge findings that share one fix (e.g., three missing service pages = one fix: "create pages for X, Y and Z").

**Impact**

- **High:** changes whether AI tools can see, trust or recommend the business for its main services. Examples: AI search bots blocked; top service has no page; business appears under two names; a handful of reviews against competitors with dozens.
- **Medium:** weakens clarity or trust. Examples: generic opening, no pricing explanation, thin service pages, profile category too broad, syndicated articles.
- **Low:** polish. Examples: missing structured data on an otherwise clear site, a few articles without a next step, missing llms.txt (always low).

**Effort**

- **Minutes:** settings and small edits: firewall toggle, robots.txt line, profile fields, asking for reviews.
- **Hours:** writing or rewriting a page, adding structured data.
- **Days:** several new pages, replacing a content library, site rebuild.

Each fix must say: **what to do, where (URL or setting), who usually does it (owner or web person), and which finding IDs it comes from.** "Improve your content" is not a fix. "Create a page for emergency drain cleaning at /services/emergency-drain-cleaning/, opening with who you help in Riverside and how fast you arrive (finding 3.2)" is.
