# Report template

Save as `AI-VISIBILITY-AUDIT-<domain>-<YYYY-MM-DD>.md` in the working directory (domain without `www.`, e.g. `AI-VISIBILITY-AUDIT-oaklineplumbing.com-2026-03-02.md`), so re-audits don't overwrite earlier reports.

Writing rules:

- Plain English for a busy owner. Short sentences. No hype, no promises of rankings, citations or traffic.
- Explain any technical term the first time, in one line (e.g., "robots.txt (a file that tells crawlers which pages they may visit)").
- Every finding has evidence: URL plus quote, status code, or search result. If you didn't see it, it goes in "What wasn't checked".
- Mode B is labeled "approximation" every time it appears.
- Don't pad. If an area is fine, say so in one line and move on.

Use this structure exactly. Replace everything in [brackets].

````markdown
# AI visibility audit: [Business name]

**Site:** [URL] · **Location:** [town / service area] · **Services checked:** [list] · **Date:** [YYYY-MM-DD]

> **Assumptions** [only if something wasn't confirmed by the owner; otherwise leave this block out]
> - [e.g., "Main services are my reading of the homepage: X, Y, Z. Correct me if others bring most of the work."]
> - [e.g., "You said Millbrook; every address on the site says Riverside, so the checks use Riverside."]

## 1. Summary

[Sentence 1: the single most important thing found.]
[Sentence 2: what is working.]
[Sentence 3: what fixing the top issues would change, stated without promises.]

**Score: [NN] / 100** (scored on [N] of 7 areas[; X not checked][; capped: not recommended in any of N recommendation searches; NN before the cap]). This is a trend line for comparing future audits, not a grade.

## 2. Top 5 fixes

| # | Fix | Impact | Effort | Who | Findings |
|---|-----|--------|--------|-----|----------|
| 1 | [short name] | High | Minutes | [Owner / Web person] | [1.2] |
| ... |

**1. [Fix name]**
[What to do, exactly, and where (URL or setting). 2-5 sentences. Include draft wording or the exact lines to change when that helps.]

[Repeat for 2-5.]

## 3. Scorecard

| Area | Rating | Verdict |
|------|--------|---------|
| 1. AI crawler access | [0-5] [Strong / Needs work / Missing] | [one line] |
| 2. Clarity | | |
| 3. Service coverage | | |
| 4. Trust and proof | | |
| 5. Local presence | [or "Not checked: needs your input", or "N (partly checked)"] | |
| 6. Content quality | | |
| 7. AI answer test | [N (spot checks + approximation) / N (approximation) / N (your Mode A results)] | |

## 4. Findings by area

### 1. AI crawler access

**Verdict:** [one line]

| Crawler | Vendor | Job | robots.txt | Live test |
|---------|--------|-----|------------|-----------|
| [from check_ai_access.py output; list all 13, or group "all others: allowed, OK"] |

- **1.1 [Finding title].** [What was seen.] Evidence: [URL, status code, quote]. [Why it matters, one line.]

[Repeat for every area 2-6, same pattern: verdict line, then numbered findings with evidence. Include good findings too, briefly ("2.3 Name, address and phone match on all 14 pages checked").]

### 5. Local presence

[If the profile wasn't seen: "Not checked: needs your input." then the 5-minute self-check from checklist.md, then any 5d name-variation findings.]

## 5. AI answer test

Being known by name is not the same as being recommended. [One or two sentences on what this audit found about the gap.]

### Spot checks: real Google AI Overviews (seen once, [date], not signed in)

[Only if you ran them. Table from prompt-templates.md section 4. One line after it: "These are real AI answers, seen once; they vary by person, place and time."]

### Mode B: web search approximation (not real AI answers)

[If the sanity check failed, start with: "The search tool used here didn't return your website even for its own domain, so these results may understate how visible you are."]

This shows which pages web search surfaces for these questions: the sources AI tools with search are likely to draw from. It does not show what ChatGPT, Gemini or any other AI tool actually answers. Search tool: [name/unknown], [date].

| # | Prompt | You appeared? | Where | Competitors appearing | Recurring sources |
|---|--------|---------------|-------|-----------------------|-------------------|

- **Known by name (approximation):** [...]
- **Recommended (approximation):** [...]

### Mode A: run these yourself (the real test)

[Instructions block and prompts from prompt-templates.md, numbered.]

[Blank scorecard table for ChatGPT, Perplexity, Gemini, Google AI Mode.]

## 6. What wasn't checked, and why

- [Check]: [reason: needs login / needs your input / no web search / page didn't load / outside this audit's scope]

Always include: "This audit doesn't measure rankings, traffic or how often AI tools actually cite you. Those need Search Console, analytics or a tracking tool."

## 7. Re-audit

Run this audit again in 30-60 days, after the top fixes are done, and compare the scorecard and the Mode A results. Ask: "Re-audit [URL] and compare with [this report's filename]".
````

## Chat summary (after saving the file)

Show in chat, in this order, nothing more:

1. The score line, with the number of areas scored.
2. The top 5 fixes as a numbered list: one line each, with impact and effort.
3. One line on the AI answer test (labeled approximation if Mode B).
4. The file path of the saved report.
5. One line on what needs the owner's input (e.g., the Business Profile, Mode A).

## Re-audit comparison

If an earlier `AI-VISIBILITY-AUDIT-<same domain>-*.md` exists in the working directory, read its scorecard and add a section after the Scorecard:

```markdown
### Change since [previous date]

| Area | Before | Now | What changed |
```

Compare only areas scored both times. Note that a "not checked" area changing to scored is not an improvement.
