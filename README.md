# AI Operations Audit — Foundation

The canonical assets for **Northstar Automation Co.**'s AI Operations Audit: a
$400, 48-hour, money-back-guaranteed audit that maps a small business's workflows
and delivers a branded PDF showing what to automate, the hours/dollars saved, and
a 90-day roadmap. Each report's top recommendation carries a $1,500 fixed-price
implementation upsell.

This repo currently holds the **foundation** — the four assets everything else in
the launch plan (`agentexecutionplan.md`, Agents A–E) treats as canonical and
builds on. Build these correctly and the rest of the pipeline has solid ground.

## The pipeline (target state)

```
client fills 15-question intake (Tally)
        ->  n8n webhook
        ->  format answers into "Q: … / A: …" pairs        [Agent A]
        ->  Claude API (claude-opus-4-8) + master prompt    [this repo]
        ->  structured JSON (canonical schema)              [this repo]
        ->  parse + validate + guard  ->  ALERT | REVIEW    [Agent A]
        ->  founder reviews ~30 min
        ->  branded PDF generated + sent                    [Agent B, from this repo]
```

## Files

| File | What it is |
|------|-----------|
| `intake-questionnaire.md` | The 15 intake questions (source of truth for the Tally form and the pipeline). Q15 is the "do not automate" boundary. |
| `master-analysis-prompt.md` | The analysis **system prompt** + the exact **canonical JSON output schema**. The single source of truth for the data contract. |
| `build_report.py` | One-off generator for the approved sample PDF (hardcoded "Harbor Lane" data). Defines the visual design. Agent B refactors this into a data-driven `generate_report.py`. |
| `sample-audit-report.pdf` | The rendered, approved sample — a **fictional** Harbor Lane Property Management audit, clearly labeled as a demonstration. |

## How the assets fit together

The **JSON schema** in `master-analysis-prompt.md` is the hinge. The intake
questions feed it, the analysis prompt produces it, and `build_report.py` consumes
it. All three were written together so they line up field-for-field — the sample
PDF is literally the schema rendered.

## Design system

`navy #16243D` · `teal #12A594` · `light #F2F5F9` · Helvetica. Layout order:
cover → stat strip → guarantee banner → business summary → ranking table →
opportunity detail blocks → not-recommended → 90-day roadmap → navy CTA box →
methodology footnote.

## Regenerate the sample

```bash
pip install reportlab
python3 build_report.py     # writes sample-audit-report.pdf
```

The script self-checks that the totals equal the sum of the opportunities, that
`meets_guarantee` matches the 10-hour floor, and that `recommended_first_build`
names a real opportunity — the same invariants the pipeline guard enforces.

## Honesty rule

The founder has **zero clients**. The sample report is fictional and labeled as
such on its cover. No invented testimonials, results, or credentials anywhere. The
moment there is one real client result, replace the fictional sample everywhere.
