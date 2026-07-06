# Tally Setup — AI Operations Audit Intake Form

This builds the client intake form in [Tally](https://tally.so) from the canonical
`intake-questionnaire.md`. The form is the first node of the delivery pipeline:
its webhook fires the n8n workflow.

**Rule:** the form must mirror `intake-questionnaire.md` exactly — same 15
questions, same wording, same order, same numbering. The pipeline's
`format-answers.js` matches each answer back to a canonical question by the
`Q<n>.` tag at the start of the field title, so **every question title must begin
with its `Q<n>.` tag** (e.g. `Q7. What software...`). Do not renumber or reorder.

---

## 1. Create the form

1. Log in to Tally → **Create form** → **Start from scratch**.
2. Name it **AI Operations Audit — Intake**.
3. Add a short intro/cover block (optional) with one line: *"About 15 minutes.
   The more specific you are — real numbers, tool names, examples — the better
   your audit."* This mirrors the intent of the questionnaire's preamble.
4. Optionally group questions with Tally **Section / Page break** blocks matching
   the five sections (A–E). Sections are cosmetic and do not affect the webhook
   payload.

## 2. Add the 15 questions

For each question below: add the block type shown, paste the **exact title**
(including the `Q<n>.` prefix), paste the helper text into the block's
**description**, and set **Required** as noted.

| # | Question title (must start with `Q<n>.`) | Tally block type | Required |
|---|------------------------------------------|------------------|----------|
| Q1 | What is your business name, and what does it do? | **Long answer** (Textarea) | Yes |
| Q2 | How many people work in the business, and what are their main roles? | **Long answer** | Yes |
| Q3 | What is the rough fully-loaded hourly cost of each role? | **Long answer** | Yes |
| Q4 | Walk us through a typical week. Where does the most time get spent on work that feels repetitive, manual, or low-value? | **Long answer** | Yes |
| Q5 | What tasks get done over and over in almost exactly the same way? | **Long answer** | Yes |
| Q6 | Where do you or your team copy and paste information between systems, or re-enter the same data twice? | **Long answer** | Yes |
| Q7 | What software, tools, and apps do you use to run the business? | **Long answer** | Yes |
| Q8 | For your busiest recurring tasks, roughly how often do they happen and in what volume? | **Long answer** | Yes |
| Q9 | How do customers, clients, or leads first reach you, and how do you respond? | **Long answer** | Yes |
| Q10 | What follow-ups, reminders, or nudges does someone have to remember to send? | **Long answer** | Yes |
| Q11 | What scheduling or coordination back-and-forth eats time? | **Long answer** | Yes |
| Q12 | What reports, summaries, or updates do you prepare regularly, and for whom? | **Long answer** | Yes |
| Q13 | What's currently holding the business back from growing, or what would you do with the time if you got it back? | **Long answer** | Yes |
| Q14 | Have you tried to automate or streamline anything before? What happened? | **Long answer** | Yes |
| Q15 | What should we NOT try to automate — the work that must stay human? | **Long answer** | Yes |

**Field type rationale:** every intake answer is open-ended prose the analysis
prompt reads directly, so all 15 are **Long answer / Textarea** blocks. Do **not**
use dropdowns, multiple choice, or rating blocks — they would constrain answers
the master prompt expects as free text. (`format-answers.js` still handles
multi-value blocks gracefully if you ever add one, but the canonical form is all
textareas.)

**Helper text:** copy the italic helper paragraph under each question in
`intake-questionnaire.md` into that block's **description** field so clients see
the same guidance and examples.

**Recommended add (optional, not one of the 15):** a **Short answer / Email**
block at the top titled `Your email (so we can send your audit)`, marked Required.
Keep its title free of a `Q<n>.` tag so `format-answers.js` ignores it. This gives
the founder the client's address for delivery without polluting the analysis.

## 3. Enable the webhook (Integrations → Webhooks)

Tally webhooks are a **Tally Pro** feature. To wire the form to n8n:

1. In n8n, create/open the workflow and add a **Webhook** trigger node (see
   `workflow-assembly.md`). Copy its **Production URL**
   (looks like `https://<your-instance>.app.n8n.cloud/webhook/<path>`).
2. In Tally, open the form → **Integrations** tab → **Webhooks** → **Connect**
   (or **Add webhook**).
3. Paste the n8n **Production** webhook URL into **Endpoint URL**.
4. Leave the **Signing secret** blank for the first test, or set one and verify it
   in n8n later (optional hardening — not required for the pipeline to work).
5. **Save.** Tally sends a `POST` with `Content-Type: application/json` and a body
   shaped like `test-payload.json` (`eventType: "FORM_RESPONSE"`, answers under
   `data.fields[]`, each field carrying `label`, `type`, and `value`).

## 4. Verify the connection

1. In n8n, click **Listen for test event** on the Webhook node (or activate the
   workflow so the Production URL is live).
2. In Tally, use **Preview** and submit a test response, or use the webhook's
   **Send test** button if shown.
3. Confirm n8n receives an item whose JSON matches the shape of
   `test-payload.json` — specifically `data.fields[]` with `label` values that
   start with `Q1.` … `Q15.`.
4. If labels arrive **without** the `Q<n>.` prefix, edit each Tally question title
   to add it. The `Q<n>.` tag is what keeps answers aligned to canonical order
   even if Tally reorders fields.

Once n8n receives a well-formed submission, continue with `workflow-assembly.md`.
