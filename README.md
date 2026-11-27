# AI Visibility Audit

An Agent Skill that checks how visible a local or regional service business is to AI assistants (ChatGPT, Claude, Perplexity, Gemini, Google AI Overviews and AI Mode) and gives the owner the five next fixes, ranked by impact and effort, with evidence for every finding.

Built for owners and marketers of dentists, law firms, accountants, clinics, contractors, agencies, consultants, home services and similar businesses, and for the freelancers who audit them. Works with Claude Code, Claude Cowork, Codex, Cursor and other tools that support [Agent Skills](https://agentskills.io).

## What you get

A report saved as `AI-VISIBILITY-AUDIT-<domain>-<date>.md`, plus a short summary in chat. An excerpt from the [full sample report](examples/sample-report.md) for a fictional plumber:

> **Score: 49 / 100** (scored on 7 of 7 areas). This is a trend line for comparing future audits, not a grade.
>
> | # | Fix | Impact | Effort | Who |
> |---|-----|--------|--------|-----|
> | 1 | Let AI search bots through the firewall | High | Minutes | Web person |
> | 2 | Fix the booking link and Saturday hours on your Google profile | High | Minutes | Owner |
> | 3 | Use one business name everywhere | High | Minutes | Owner + web person |
> | 4 | Ask every happy customer for a review | High | Minutes a week | Owner |
> | 5 | Give water heaters and emergency call-outs their own pages | High | Hours | Web person |
>
> **1. Let AI search bots through the firewall.** Your site runs behind Cloudflare. When we requested your pages as `OAI-SearchBot` (ChatGPT search), `Claude-SearchBot` and `PerplexityBot`, Cloudflare answered with a "Just a moment..." check page instead of your site...

Every report has: a 3-sentence summary, the top 5 fixes, a scorecard, findings by area with evidence (URLs, quotes, status codes), the AI answer test, what wasn't checked and why, and a re-audit suggestion.

## Install

**Claude Code (plugin).** In a terminal:

```bash
claude plugin marketplace add jmedia65/ai-visibility-audit
```

```bash
claude plugin install ai-visibility-audit@ai-visibility-audit
```

Or run the same two commands inside Claude Code as `/plugin marketplace add jmedia65/ai-visibility-audit` and `/plugin install ai-visibility-audit@ai-visibility-audit`.

**Any supported agent (`npx skills`).** Needs Node.js 22.20 or later. From your project folder:

```bash
npx skills add jmedia65/ai-visibility-audit
```

Add `-g` to install it for all projects, or `-a claude-code`, `-a codex`, `-a cursor` to pick the agent.

**Manual copy.** Download or clone this repository from GitHub and copy the whole folder, named `ai-visibility-audit`, into your agent's skills folder. For Claude Code that's `~/.claude/skills/ai-visibility-audit/` (all projects) or `.claude/skills/ai-visibility-audit/` (one project). For other agents, see the [skills CLI agent table](https://github.com/vercel-labs/skills/blob/main/docs/agents.md). In Claude apps that let you upload skills, zip the folder and upload it.

## Use

Ask in plain words:

```
Audit https://example.com for a plumbing business in Riverside
```

```
Why doesn't ChatGPT recommend us? Our site is https://example.com, we're a family dental practice in Oak Park
```

```
Re-audit https://example.com and compare with last month's report
```

The skill scans the site first, then asks one short round of questions (business name, town, main services) with its own guesses filled in. Optionally, name 1-3 competitors and paste your public Google Business Profile link.

## What it checks

| Area | What it looks at |
|---|---|
| 1. AI crawler access | robots.txt rules for 13 AI and search crawlers, then live requests with each crawler's user agent, to catch firewalls that silently block AI bots |
| 2. Clarity | Does the top of the homepage say who, where, what and for whom? Consistent name, address and phone, named people, valid structured data |
| 3. Service coverage | Does each main service have its own page, with direct answers and the location? |
| 4. Trust and proof | Review count, recency and detail vs competitors; testimonials; whether the site explains how pricing works |
| 5. Local presence | Business Profile details vs the website, and name variations across the web |
| 6. Content quality | Whether articles are original or copied word for word on other sites, on-topic, fresh, and lead to a next step |
| 7. AI answer test | 5-8 prospect-style prompts: an automatic web search approximation, plus a scorecard for you to run them in ChatGPT, Perplexity, Gemini and Google AI Mode |

Each area gets a 0-5 rating. The overall score out of 100 counts only the areas that could be checked. It's meant as a trend line between audits, not a grade. Details: [references/scoring.md](references/scoring.md).

## Honest limits

- **The automatic AI answer test is an approximation.** It shows which pages web search surfaces, the sources AI tools are likely to draw from, not what ChatGPT actually answers. The report labels it everywhere and gives you the prompts to run the real test yourself.
- **The crawler test runs from your computer,** not from the AI companies' own servers. A block it finds is strong evidence, not proof, and the report tells you how to confirm it in your firewall settings.
- **No logins and no scraping of Google Maps.** If the audit can't see your Business Profile, it marks that area "needs your input" and gives you a 5-minute self-check.
- **Nothing is guessed.** Anything the audit couldn't see is listed under "What wasn't checked".
- It is not a rank tracker, a technical SEO crawler or a content writer. It doesn't promise rankings, citations or traffic, and it isn't legal or professional advice.

## Optional connections

None are required. If your agent has these connected, the audit uses them:

- **Web search:** enables the automatic AI answer approximation, review lookups and the copied-content check. Without it, those checks are marked "not checked".
- **Google Search Console, GA4 or an SEO data tool:** supports findings with real data, such as how many searches are for your business name. The skill asks before using anything that costs credits.

## Requirements

Network access, and Python 3.9 or later for the two bundled scripts (standard library only, nothing to install). Without Python, the audit still runs but skips the live crawler test.

## For contributors

```bash
python3 -m unittest discover tests
```

```bash
python3 scripts/check_ai_access.py https://example.com
```

The crawler list in [references/crawlers.md](references/crawlers.md) and `scripts/check_ai_access.py` was checked against each vendor's documentation on the date shown there. Please include a link to the vendor's official page when proposing changes.

## License and author

MIT License. Made by [Max Braglia](https://maxbraglia.com).
