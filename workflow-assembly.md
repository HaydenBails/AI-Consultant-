# n8n Workflow Assembly — AI Operations Audit Delivery Pipeline

Node-by-node build of the full pipeline:

```
Tally Webhook → Format (Code) → Claude (HTTP Request) → Parse/Guard (Code)
   → IF (route === "review")
        ├─ TRUE  → Gmail: create draft  "REVIEW: audit draft ready for {client_name}"
        └─ FALSE → Gmail: create draft  "ALERT: guarantee/validation failure"
```

The pipeline only ever **creates Gmail drafts** — nothing is sent automatically.
The founder reviews every draft before it goes anywhere.

---

## Founder checkpoints — do this in n8n

These are the steps only you (the founder) can perform in your live n8n cloud
instance. Do them in order; do not skip the sabotage check.

1. **Build the Tally form** per `tally-setup.md` and copy the n8n Webhook node's
   **Production URL** into Tally's webhook integration.
2. **Import the Claude API config** from `claude-node-config.md` into the HTTP
   Request node: method `POST`, URL `https://api.anthropic.com/v1/messages`, the
   three headers, the `Anthropic API key` Header Auth credential, and the JSON
   body (model `claude-opus-4-8`, `max_tokens`, the verbatim `system` prompt, and
   `content: ={{ $json.formatted_answers }}`).
3. **Paste the two Code node scripts:** `format-answers.js` into the Format node
   and `parse-and-guard.js` into the Parse/Guard node (paste the whole file — the
   n8n glue at the bottom activates automatically inside a Code node).
4. **Run the happy path:** import `test-payload.json` as a pinned/test item on the
   Webhook node and execute the workflow end-to-end. **Confirm** it produces the
   `REVIEW: audit draft ready for Cedar & Vine Property Management` Gmail draft
   containing the pretty-printed audit JSON, and that the IF node took the TRUE
   (`review`) branch.
5. **Confirm the sabotage case ALERTs:** take `test-payload.json`, delete the
   **Q8** field from `data.fields[]` (the frequency/volume answer), run it again.
   With volume missing, an honest audit cannot clear the 10-hour guarantee, so
   `meets_guarantee` comes back `false` and the guard sets `route = "alert"`.
   **Confirm** the workflow takes the FALSE branch and creates the
   `ALERT: guarantee/validation failure` draft instead. (This exact routing is
   proven by the bundled node test — see the project summary.)
6. **Only after both checks pass**, connect the live Tally webhook and activate
   the workflow.

Do not send any client email from n8n. The pipeline stops at "draft created."

---

## Node 1 — Webhook (trigger)

- Add node: **Webhook**.
- **HTTP Method:** `POST`.
- **Path:** e.g. `audit-intake` (this forms the Production URL you paste into Tally).
- **Respond:** `Immediately` (or `When Last Node Finishes`; Tally does not need the
  audit back, so `Immediately` with a `200` is fine).
- Output: one item whose `json` is the Tally body (shape = `test-payload.json`,
  with answers under `data.fields[]`).
- For testing without Tally: click **Listen for test event**, or pin
  `test-payload.json` as the node's output.

## Node 2 — Format (Code)

- Add node: **Code** → **Run Once for All Items** → language **JavaScript**.
- Paste the entire contents of `format-answers.js`.
- It reads the Tally payload via `$input.first().json`, maps each answer to its
  canonical question by the `Q<n>.` label tag (falling back to positional order if
  labels lack tags), handles missing/optional answers as `(no answer provided)`,
  and returns `[{ json: { formatted_answers: "Question: …\nAnswer: …\n\n…" } }]`.
- Output field consumed downstream: `formatted_answers`.

## Node 3 — Claude (HTTP Request)

- Add node: **HTTP Request**. Configure exactly per `claude-node-config.md`:
  - Method `POST`, URL `https://api.anthropic.com/v1/messages`.
  - Headers `anthropic-version: 2023-06-01`, `content-type: application/json`, and
    `x-api-key` via the **Header Auth** credential named `Anthropic API key`.
  - Body (JSON): `model: claude-opus-4-8`, `max_tokens: 8000`, `system` = verbatim
    master prompt, `messages: [{ role:"user", content: ={{ $json.formatted_answers }} }]`.
  - **Response Format: JSON**; optionally **Retry On Fail**.
- Output: the Anthropic response object, with the audit text at `content[0].text`.

## Node 4 — Parse/Guard (Code)

- Add node: **Code** → **Run Once for All Items** → JavaScript.
- Paste the entire contents of `parse-and-guard.js`.
- It reads the Claude response via `$input.first().json`, extracts `content[0].text`,
  strips accidental markdown fences, `JSON.parse`s it, validates every canonical
  schema field and type, independently re-sums `opportunities[].hours_saved_monthly`
  (and dollars) and flags a >5% mismatch, checks `meets_guarantee` consistency, and
  emits one item:
  ```
  { route, validation_errors, hours_check, dollars_check, guarantee_check,
    client_name, audit, audit_pretty }
  ```
- `route` is `"review"` only if `meets_guarantee === true` **and** there are zero
  validation errors; otherwise `"alert"`.

## Node 5 — IF (router)

- Add node: **IF**.
- **Condition (String / Equals):** left `={{ $json.route }}`, right `review`.
- **TRUE** output → Node 6 (REVIEW draft). **FALSE** output → Node 7 (ALERT draft).

## Node 6 — Gmail: create draft (REVIEW branch)

- Add node: **Gmail** → **Resource: Draft** → **Operation: Create**.
- Use your Gmail OAuth2 credential.
- **Subject:**
  `={{ "REVIEW: audit draft ready for " + $json.client_name }}`
- **Message (Text):** include the pretty-printed audit JSON so you can review it,
  e.g.:
  ```
  ={{ "Audit draft for " + $json.client_name + " passed all guard checks.\n\n"
      + "Hours check: " + JSON.stringify($json.hours_check) + "\n"
      + "Dollars check: " + JSON.stringify($json.dollars_check) + "\n\n"
      + "----- AUDIT JSON -----\n" + $json.audit_pretty }}
  ```
- **Do not set a recipient / do not send.** This is a draft for the founder only.
  (Next step, outside this workflow: 30-min review, then run `build_report.py` on
  the approved JSON to generate the branded PDF.)

## Node 7 — Gmail: create draft (ALERT branch)

- Add node: **Gmail** → **Resource: Draft** → **Operation: Create**.
- **Subject:** `ALERT: guarantee/validation failure`
  (optionally append the client:
  `={{ "ALERT: guarantee/validation failure — " + $json.client_name }}`)
- **Message (Text):** surface exactly why it failed so you can act:
  ```
  ={{ "This submission did NOT pass the guard and needs manual attention.\n\n"
      + "Client: " + $json.client_name + "\n"
      + "Route: " + $json.route + "\n\n"
      + "Validation errors:\n" + ($json.validation_errors.length
           ? "- " + $json.validation_errors.join("\n- ")
           : "(none — failed on the guarantee)") + "\n\n"
      + "Guarantee check: " + JSON.stringify($json.guarantee_check) + "\n"
      + "Hours check: " + JSON.stringify($json.hours_check) + "\n\n"
      + "----- RAW AUDIT (may be null if JSON was unparseable) -----\n"
      + ($json.audit_pretty || "(no parseable audit)") }}
  ```
- Again: **create draft only, never send.** An ALERT usually means the guarantee
  honestly failed (offer a refund / decline) or the model output was malformed
  (re-run, or hand-fix and re-review).

## Notes & hardening (optional)

- **Idempotency:** Tally can retry a webhook. If you activate live, consider a
  dedupe on `data.submissionId` before Node 3 so you don't double-bill Claude
  calls on retries.
- **Signing secret:** if you set a Tally webhook signing secret, verify the
  `tally-signature` header in an early Code/IF node before Node 2.
- **Cost guard:** `max_tokens: 8000` bounds the response; a truncated response
  (`stop_reason: "max_tokens"`) fails JSON parsing and routes to ALERT — which is
  the safe outcome.
