/**
 * format-answers.js
 * -----------------
 * n8n Code node script (also runnable/importable in plain Node for testing).
 *
 * Purpose: take a Tally FORM_RESPONSE webhook payload and produce a single
 * string of "Question: ...\nAnswer: ..." pairs, in the canonical questionnaire
 * order (Q1..Q15), ready to send as the user message to the Claude API.
 *
 * Design:
 *   - The 15 canonical questions live in QUESTIONS below and mirror
 *     intake-questionnaire.md exactly (do not renumber/reorder).
 *   - Tally sends each answer as a field object { key, label, type, value }.
 *     We match each canonical question to a Tally field by the "Q<n>" tag at
 *     the start of the field label; if labels carry no tag we fall back to
 *     positional order. This keeps output in canonical order no matter how
 *     Tally happens to order or key its fields.
 *   - Missing / optional / blank answers degrade gracefully to a clear
 *     placeholder so the model (and the ALERT guard downstream) can see the gap
 *     rather than receiving a malformed prompt.
 */

// Canonical 15 questions — mirrors intake-questionnaire.md (source of truth).
const QUESTIONS = [
  { n: 1,  text: 'What is your business name, and what does it do?' },
  { n: 2,  text: 'How many people work in the business, and what are their main roles?' },
  { n: 3,  text: 'What is the rough fully-loaded hourly cost of each role?' },
  { n: 4,  text: 'Walk us through a typical week. Where does the most time get spent on work that feels repetitive, manual, or low-value?' },
  { n: 5,  text: 'What tasks get done over and over in almost exactly the same way?' },
  { n: 6,  text: 'Where do you or your team copy and paste information between systems, or re-enter the same data twice?' },
  { n: 7,  text: 'What software, tools, and apps do you use to run the business?' },
  { n: 8,  text: 'For your busiest recurring tasks, roughly how often do they happen and in what volume?' },
  { n: 9,  text: 'How do customers, clients, or leads first reach you, and how do you respond?' },
  { n: 10, text: 'What follow-ups, reminders, or nudges does someone have to remember to send?' },
  { n: 11, text: 'What scheduling or coordination back-and-forth eats time?' },
  { n: 12, text: 'What reports, summaries, or updates do you prepare regularly, and for whom?' },
  { n: 13, text: "What's currently holding the business back from growing, or what would you do with the time if you got it back?" },
  { n: 14, text: 'Have you tried to automate or streamline anything before? What happened?' },
  { n: 15, text: 'What should we NOT try to automate — the work that must stay human?' },
];

const MISSING_PLACEHOLDER = '(no answer provided)';

/**
 * Normalize a raw Tally field value into a plain answer string.
 * Handles strings, numbers, booleans, arrays (checkboxes / multi-select),
 * option-id objects, null/undefined and blanks.
 */
function normalizeValue(value, field) {
  if (value === null || value === undefined) return '';

  // Arrays: multi-select / checkboxes. Tally may send option IDs; if the field
  // carries an options list, map IDs -> human text where possible.
  if (Array.isArray(value)) {
    const options = (field && Array.isArray(field.options)) ? field.options : null;
    const parts = value.map((v) => {
      if (options) {
        const match = options.find((o) => o && (o.id === v || o.value === v));
        if (match && (match.text || match.label)) return match.text || match.label;
      }
      return typeof v === 'object' ? JSON.stringify(v) : String(v);
    });
    return parts.filter((p) => p !== '' && p !== null && p !== undefined).join(', ');
  }

  if (typeof value === 'object') {
    // Single option object or nested structure — prefer a readable field.
    if (value.text) return String(value.text);
    if (value.label) return String(value.label);
    if (value.value !== undefined) return String(value.value);
    return JSON.stringify(value);
  }

  return String(value);
}

/**
 * Extract the question number tag ("Q7", "q7.", "Q7:") from a Tally label.
 * Returns the integer, or null if the label carries no recognizable tag.
 */
function questionNumberFromLabel(label) {
  if (!label || typeof label !== 'string') return null;
  const m = label.match(/\bQ\s*(\d{1,2})\b/i);
  return m ? parseInt(m[1], 10) : null;
}

/**
 * Pure core: given a Tally webhook payload object, return the formatted string.
 */
function formatAnswers(payload) {
  const data = (payload && payload.data) ? payload.data : payload || {};
  const fields = Array.isArray(data.fields) ? data.fields : [];

  // Index Tally fields by detected question number.
  const byNumber = {};
  fields.forEach((f) => {
    const num = questionNumberFromLabel(f && f.label);
    if (num !== null && byNumber[num] === undefined) byNumber[num] = f;
  });

  const labelsHaveTags = Object.keys(byNumber).length > 0;

  const lines = QUESTIONS.map((q, idx) => {
    // Primary: match by Q<n> tag. Fallback: positional order (idx-th field).
    let field = labelsHaveTags ? byNumber[q.n] : fields[idx];
    if (field === undefined) field = fields[idx]; // secondary fallback

    const raw = field ? field.value : undefined;
    let answer = normalizeValue(raw, field);
    if (answer.trim() === '') answer = MISSING_PLACEHOLDER;

    return `Question: Q${q.n}. ${q.text}\nAnswer: ${answer}`;
  });

  return lines.join('\n\n');
}

// ---------------------------------------------------------------------------
// n8n Code node glue.
// In n8n, one item flows in from the Webhook node. Its JSON is the Tally body.
// We emit a single item carrying the formatted string as `formatted_answers`.
// ---------------------------------------------------------------------------
if (typeof $input !== 'undefined') {
  const payload = $input.first().json;
  const formatted = formatAnswers(payload);
  return [{ json: { formatted_answers: formatted } }];
}

// Node / test import glue.
if (typeof module !== 'undefined') {
  module.exports = { formatAnswers, normalizeValue, questionNumberFromLabel, QUESTIONS };
}
