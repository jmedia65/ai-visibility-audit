# AI answer test

Tests what AI tools actually say, not only what the page contains. Two modes, always kept apart and labeled.

## 1. Build the prompts (5-8)

Write them the way a prospect would type or speak them: short, casual, often with "near me" or a town. Use the services the user confirmed and the town or area. Fill these patterns, keep the ones that fit, and stop at 8:

| # | Pattern | Example (fictional) |
|---|---|---|
| 1 | Who's a good [service] in [town]? | Who's a good plumber in Riverside? |
| 2 | Best [service] near [town] | Best emergency plumber near Riverside |
| 3 | Who can help with [specific service] in [town]? (one per main service, up to 3) | Who can fix a burst pipe in Riverside tonight? |
| 4 | [Specific problem a customer has] in [town], who should I call? | My water heater is leaking in Riverside, who should I call? |
| 5 | [Business name] reviews | Oakline Plumbing reviews |
| 6 | Is [business name] any good? | Is Oakline Plumbing in Riverside any good? |
| 7 | [Business name] vs [competitor] (only if competitors were given) | Oakline Plumbing vs Northgate Plumbing |

Prompts 1-4 test **being recommended**. Prompts 5-7 test **being known by name**. Keep both kinds; the gap between them is the key insight.

Tips:

- Use the words customers use, not the business's internal terms ("tooth pulled" rather than "exodontia").
- Use the main town, not a list of every area served. If the service area is large, add one prompt for the second-largest town.
- Don't include the business name in prompts 1-4.

## 2. Mode A: run these yourself (the real test)

This is the real test, because it shows what AI tools actually answer. The agent cannot do it reliably: answers depend on the tool, the account, the location and the day. Give the owner the prompts and this scorecard.

Instructions to include in the report:

> Open each AI tool in a private or logged-out browser window if you can (it reduces personalisation). Paste each prompt exactly. Fill one row per prompt per tool. It takes about 20 minutes. Run it again at the re-audit to compare.
>
> Tools: ChatGPT, Perplexity, Gemini, Google AI Mode (google.com, "AI Mode" tab). Optional: Claude, Copilot, Google AI Overviews (the summary at the top of normal Google results, when it appears).

Scorecard (one table per tool):

```
Tool: ____________   Date: ____________

| # | Prompt | Were you named? (yes / no / only when asked by name) | Competitors named | Sources cited (sites or links) | Anything wrong or cautionary said about you? |
|---|--------|------|------|------|------|
| 1 | ...    |      |      |      |      |
```

If the owner pastes Mode A results back, rate area 7 from them and quote them as given.

## 3. Mode B: web search approximation (automatic)

Only if the agent has a web search tool. Otherwise mark Mode B "not run (no web search available)" and keep Mode A.

**What it shows:** which pages and businesses web search surfaces for these questions, which are the sources AI tools with search are likely to draw from. **What it does not show:** what ChatGPT, Gemini or any other tool actually answers. Label every Mode B result as an approximation, in the table header and in any sentence that uses it.

Procedure:

1. Run each prompt through web search exactly as written. For prompts 1-4, also run one keyword version (`[service] [town]`), because search tools treat questions and keywords differently.
2. For each search, record the top results (up to 10): title, URL, and whether it is:
   - the business's own site,
   - a third-party page that mentions the business (directory, review site, news, list article),
   - a competitor,
   - other.
3. Note which **domains** recur across searches. Those are the sources AI tools are likely to cite (often directories, review sites and "best [service] in [town]" list articles). Being listed on them matters.
4. For by-name prompts (5-7): note what the results say. Quote anything wrong, outdated or cautionary, with the URL.
5. Note the search tool used (name, if known) and the date.

Do not count a result as "the business appears" unless the business name or domain is actually in the result. A directory page listing 40 plumbers counts only if the business is on it; say "listed on [URL]" and only claim that if you saw the name.

Report table (`report-template.md` has the full section):

```
### Mode B: web search approximation (not real AI answers)

| # | Prompt | You appeared? | Where | Competitors appearing | Recurring sources |
|---|--------|---------------|-------|-----------------------|-------------------|
```

Then two lines:

- **Known by name:** [what by-name searches show]
- **Recommended:** [how often the business appears for recommendation prompts, e.g. "0 of 5 recommendation searches"]

If known by name but not recommended, say plainly: "AI tools can describe you when someone already knows your name, but are unlikely to suggest you to someone who doesn't."
