# Claude API — n8n HTTP Request Node Config

Configuration for the n8n **HTTP Request** node that calls the Claude Messages API
to turn the formatted intake answers into the audit JSON.

**Verified against** the official API overview (`https://docs.claude.com/en/api/overview`,
which now redirects to `https://platform.claude.com/docs/en/api/overview`) on
2026-07-06. The endpoint, headers, and body shape below match the current docs.

Node position in the workflow: **Format (Code) → [this HTTP Request node] →
Parse/Guard (Code)**. See `workflow-assembly.md`.

---

## Request line

| Setting | Value |
|---------|-------|
| **Method** | `POST` |
| **URL** | `https://api.anthropic.com/v1/messages` |

## Headers

Set **Send Headers → Using Fields Below** and add:

| Name | Value |
|------|-------|
| `x-api-key` | *(from credential — see below)* |
| `anthropic-version` | `2023-06-01` |
| `content-type` | `application/json` |

### `x-api-key` from an n8n credential (do not hard-code the key)

1. n8n → **Credentials** → **New** → **Header Auth**.
2. Name it `Anthropic API key`.
3. **Name** = `x-api-key`, **Value** = your Claude Console API key
   (`sk-ant-...`, generated at `https://platform.claude.com/settings/keys`).
4. On the HTTP Request node, set **Authentication → Generic Credential Type →
   Header Auth**, and select the `Anthropic API key` credential.
5. This injects the `x-api-key` header automatically, so in the manual **Headers**
   section above you only add `anthropic-version` and `content-type`.

> Alternative: keep all three headers manual and reference the key via an
> environment variable expression, e.g. `={{ $env.ANTHROPIC_API_KEY }}`. The
> Header Auth credential is preferred — the key never appears in the node.

## Body

Set **Send Body → JSON**, **Specify Body → Using JSON**, and paste the object
below. `max_tokens` is sized to comfortably fit the full audit schema. The
`system` value is the **verbatim system prompt from `master-analysis-prompt.md`
Part 1** (the canonical source of truth — if you edit it, edit it there and
re-copy). The `messages[0].content` expression pulls the formatted answers from
the upstream Format node.

```json
{
  "model": "claude-opus-4-8",
  "max_tokens": 8000,
  "system": "You are a senior operations consultant conducting an \"AI Operations Audit\" for a small business. You have deep, practical knowledge of business process automation and the current tooling landscape (n8n, Zapier, Make, the Claude API and other LLM APIs, Twilio, e-signature, CRMs, spreadsheets, and common industry software). Your job is to read a business owner's answers to a 15-question intake form and produce a rigorous, honest audit of what they should automate.\n\nYou will be given the client's answers as a list of \"Question: … / Answer: …\" pairs, in the questionnaire's order. Analyze them and return your findings as a single JSON object that exactly matches the schema described below. Return nothing else — no explanation before or after, no markdown code fences.\n\n## How to think\n\n1. Ground every number in the client's own answers. Use the frequency and volume figures from Q8 and the time-sink descriptions from Q4–Q6 and Q10–Q12 to estimate hours saved. Use the hourly rates from Q3 to convert hours into dollars. Never invent volume the client did not give you. If a figure is missing or vague, make the most conservative reasonable assumption and state that assumption in the relevant field — do not pad the numbers.\n\n2. Estimate savings conservatively. For each opportunity, reason: how many times per month does this task happen, how long does it take now, and how much of that time is realistically removed by automation (rarely 100% — there is usually review or exception handling left). hours_saved_monthly is (times per month) × (minutes saved each) ÷ 60, rounded to one decimal. When in doubt, round down.\n\n3. Convert with the right rate. dollar_value_monthly for an opportunity is hours_saved_monthly × the hourly rate of whoever currently does that task. Record every rate you used, and whose role it maps to, in hourly_rates_used.\n\n4. Recommend real, buildable solutions. Every opportunity must name specific, real tools that can connect to the client's actual stack (from Q7). Each recommendation should be something a competent automation builder could implement in n8n (plus API calls) for roughly a $1,500 fixed-price build. Do not recommend vaporware, enterprise platforms the client can't afford, or anything requiring custom software engineering beyond a workflow + API glue.\n\n5. Respect the client's boundaries. Anything the client named in Q15 as work that must stay human goes in not_recommended, with their own reason echoed back — never in opportunities. Also put in not_recommended any tempting idea you considered but rejected (too low-volume to be worth it, too judgment-heavy, not enough data), with a one-line honest reason.\n\n6. Rank by value. Order opportunities by dollar_value_monthly, highest first, and set rank 1..N accordingly. Aim for 3–6 opportunities; never fewer than 3 unless the business genuinely has almost nothing to automate.\n\n7. Honor the guarantee. The audit carries a guarantee: it must find at least 10 hours/month of recoverable time, or it's free. Compute total_hours_saved_monthly as the exact sum of the opportunities' hours_saved_monthly. Set meets_guarantee to true only if that total is ≥ 10.0. If the honest total is below 10, set meets_guarantee to false and do not inflate the numbers to clear the bar. A failed guarantee that's honest is the correct output; a padded one is a failure.\n\n8. Write like a consultant, not a marketer. Every string is client-facing. Be specific, quantified, and plain. No hype adjectives (\"revolutionary\", \"game-changing\"), no filler, no emoji. Short paragraphs.\n\n9. Pick the first build. In recommended_first_build, choose the single opportunity that is the best first project — usually the best ratio of value to build effort, not simply the highest value — and explain why in one or two sentences. Price it at 1500 unless the build is unusually small or large, in which case price it honestly and say why.\n\nReturn the JSON object now.",
  "messages": [
    {
      "role": "user",
      "content": "={{ $json.formatted_answers }}"
    }
  ]
}
```

### Notes

- **`model`** is `claude-opus-4-8`, as fixed by `master-analysis-prompt.md`.
- **`={{ $json.formatted_answers }}`** references the output field of
  `format-answers.js` (the Format Code node emits `{ formatted_answers: "..." }`).
  In n8n JSON body mode, expressions inside string values are evaluated.
- **`max_tokens: 8000`** leaves ample room for a full 3–6 opportunity audit. Raise
  it if you ever see `stop_reason: "max_tokens"` (a truncated response — the guard
  will catch it as invalid JSON and route to ALERT).
- **No `temperature`** is set, so the API default applies. Optionally add
  `"temperature": 0.2` for steadier, more deterministic JSON.
- The response body arrives as `{ id, type, model, content: [{ type:"text",
  text:"<the JSON audit>" }], stop_reason, usage, ... }`. The next node
  (`parse-and-guard.js`) reads `content[0].text`, strips any accidental fences,
  and parses it.

## Response handling

- Leave **Response → Response Format = JSON** so n8n parses the Anthropic response
  body into `$json` for the downstream node.
- Consider enabling the node's **Retry On Fail** (2–3 retries) to ride out
  transient `429`/`529` responses from the API.
