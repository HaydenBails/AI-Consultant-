/**
 * parse-and-guard.js
 * ------------------
 * n8n Code node script (also runnable/importable in plain Node for testing).
 *
 * Purpose: take the raw Claude API response text, turn it back into a validated
 * audit object, and decide where the workflow routes it:
 *   - route = "review"  -> looks good, build a REVIEW draft for the founder.
 *   - route = "alert"   -> guarantee failed OR validation failed; build an ALERT
 *                          draft so the founder does not silently ship a bad audit.
 *
 * What it does, in order:
 *   1. Pull the assistant text out of the Claude Messages response
 *      (content[0].text), or accept a raw string / already-parsed object.
 *   2. Strip any accidental ```json ... ``` markdown fences.
 *   3. JSON.parse it.
 *   4. Validate every field of the canonical schema exists with the right type.
 *   5. Independently sum opportunities[].hours_saved_monthly and compare to the
 *      model's total_hours_saved_monthly; flag if they differ by more than 5%.
 *   6. Route to "alert" if meets_guarantee is false OR any validation/mismatch
 *      failed; otherwise route to "review".
 *
 * The canonical schema is defined in master-analysis-prompt.md (Part 2).
 */

const HOURS_TOLERANCE = 0.05; // 5%

// ---- small type helpers ----------------------------------------------------
const isString = (v) => typeof v === 'string';
const isNonEmptyString = (v) => typeof v === 'string' && v.trim() !== '';
const isNumber = (v) => typeof v === 'number' && !Number.isNaN(v);
const isBool = (v) => typeof v === 'boolean';
const isArray = (v) => Array.isArray(v);
const isObject = (v) => v !== null && typeof v === 'object' && !Array.isArray(v);

/**
 * Strip accidental markdown code fences and surrounding whitespace.
 */
function stripFences(text) {
  if (typeof text !== 'string') return text;
  let t = text.trim();
  // Remove a leading fence line like ``` or ```json
  t = t.replace(/^```[a-zA-Z0-9]*\s*\n?/, '');
  // Remove a trailing fence
  t = t.replace(/\n?```\s*$/, '');
  return t.trim();
}

/**
 * Pull the model text out of whatever shape we were handed.
 */
function extractText(input) {
  if (input === null || input === undefined) return '';
  if (typeof input === 'string') return input;
  // Claude Messages API response: { content: [{ type:"text", text:"..." }], ... }
  if (isObject(input) && isArray(input.content)) {
    const textBlock = input.content.find((b) => b && b.type === 'text' && isString(b.text));
    if (textBlock) return textBlock.text;
    // fall back: concat any .text fields
    const joined = input.content.map((b) => (b && isString(b.text) ? b.text : '')).join('');
    if (joined) return joined;
  }
  // Already a parsed audit object (has client_name) — signal caller via marker.
  if (isObject(input) && 'client_name' in input) return { __alreadyParsed: input };
  return '';
}

/**
 * Validate the audit object against the canonical schema.
 * Returns an array of human-readable error strings (empty = valid).
 */
function validateSchema(a) {
  const errors = [];
  if (!isObject(a)) {
    return ['root is not an object'];
  }

  // top-level scalars
  if (!isNonEmptyString(a.client_name)) errors.push('client_name must be a non-empty string');
  if (!isNonEmptyString(a.business_summary)) errors.push('business_summary must be a non-empty string');
  if (!isBool(a.meets_guarantee)) errors.push('meets_guarantee must be a boolean');
  if (!isNumber(a.total_hours_saved_monthly)) errors.push('total_hours_saved_monthly must be a number');
  if (!isNumber(a.total_dollar_value_monthly)) errors.push('total_dollar_value_monthly must be a number');

  // hourly_rates_used[]
  if (!isArray(a.hourly_rates_used) || a.hourly_rates_used.length === 0) {
    errors.push('hourly_rates_used must be a non-empty array');
  } else {
    a.hourly_rates_used.forEach((r, i) => {
      if (!isObject(r)) { errors.push(`hourly_rates_used[${i}] must be an object`); return; }
      if (!isNonEmptyString(r.role)) errors.push(`hourly_rates_used[${i}].role must be a non-empty string`);
      if (!isNumber(r.rate)) errors.push(`hourly_rates_used[${i}].rate must be a number`);
    });
  }

  // opportunities[]
  if (!isArray(a.opportunities) || a.opportunities.length < 3) {
    errors.push('opportunities must be an array of at least 3 objects');
  } else {
    a.opportunities.forEach((o, i) => {
      const p = `opportunities[${i}]`;
      if (!isObject(o)) { errors.push(`${p} must be an object`); return; }
      if (!Number.isInteger(o.rank)) errors.push(`${p}.rank must be an integer`);
      if (!isNonEmptyString(o.name)) errors.push(`${p}.name must be a non-empty string`);
      if (!isNonEmptyString(o.current_process)) errors.push(`${p}.current_process must be a non-empty string`);
      if (!isNonEmptyString(o.recommended_solution)) errors.push(`${p}.recommended_solution must be a non-empty string`);
      if (!isArray(o.tools) || o.tools.length === 0 || !o.tools.every(isString)) errors.push(`${p}.tools must be a non-empty array of strings`);
      if (!isNumber(o.hours_saved_monthly)) errors.push(`${p}.hours_saved_monthly must be a number`);
      if (!isNumber(o.dollar_value_monthly)) errors.push(`${p}.dollar_value_monthly must be a number`);
      if (!['Low', 'Medium', 'High'].includes(o.complexity)) errors.push(`${p}.complexity must be one of Low|Medium|High`);
      if (!isNonEmptyString(o.basis)) errors.push(`${p}.basis must be a non-empty string`);
    });

    // sorted by dollar_value_monthly desc + rank consistency
    for (let i = 1; i < a.opportunities.length; i++) {
      const prev = a.opportunities[i - 1];
      const cur = a.opportunities[i];
      if (isNumber(prev.dollar_value_monthly) && isNumber(cur.dollar_value_monthly) &&
          cur.dollar_value_monthly > prev.dollar_value_monthly + 1e-9) {
        errors.push('opportunities must be sorted by dollar_value_monthly descending');
        break;
      }
    }
    a.opportunities.forEach((o, i) => {
      if (Number.isInteger(o.rank) && o.rank !== i + 1) {
        errors.push(`opportunities[${i}].rank (${o.rank}) inconsistent with sorted position (${i + 1})`);
      }
    });
  }

  // not_recommended[] (array required; may be empty)
  if (!isArray(a.not_recommended)) {
    errors.push('not_recommended must be an array');
  } else {
    a.not_recommended.forEach((nr, i) => {
      const p = `not_recommended[${i}]`;
      if (!isObject(nr)) { errors.push(`${p} must be an object`); return; }
      if (!isNonEmptyString(nr.name)) errors.push(`${p}.name must be a non-empty string`);
      if (!isNonEmptyString(nr.reason)) errors.push(`${p}.reason must be a non-empty string`);
    });
  }

  // roadmap{}
  if (!isObject(a.roadmap)) {
    errors.push('roadmap must be an object');
  } else {
    ['days_1_30', 'days_31_60', 'days_61_90'].forEach((k) => {
      if (!isNonEmptyString(a.roadmap[k])) errors.push(`roadmap.${k} must be a non-empty string`);
    });
  }

  // recommended_first_build{}
  if (!isObject(a.recommended_first_build)) {
    errors.push('recommended_first_build must be an object');
  } else {
    const rfb = a.recommended_first_build;
    if (!isNonEmptyString(rfb.opportunity)) errors.push('recommended_first_build.opportunity must be a non-empty string');
    if (!isNonEmptyString(rfb.why)) errors.push('recommended_first_build.why must be a non-empty string');
    if (!isNumber(rfb.price)) errors.push('recommended_first_build.price must be a number');
    if (!isNonEmptyString(rfb.estimated_timeline)) errors.push('recommended_first_build.estimated_timeline must be a non-empty string');
    // must match an opportunity name exactly
    if (isNonEmptyString(rfb.opportunity) && isArray(a.opportunities)) {
      const names = a.opportunities.map((o) => (o && o.name) || '');
      if (!names.includes(rfb.opportunity)) {
        errors.push('recommended_first_build.opportunity must exactly match one opportunities[].name');
      }
    }
  }

  return errors;
}

/**
 * Pure core: take raw model input, return a guard result object.
 */
function parseAndGuard(input) {
  const result = {
    route: 'alert',
    validation_errors: [],
    hours_check: null,
    dollars_check: null,
    guarantee_check: null,
    audit: null,
  };

  // 1. get text (or an already-parsed object)
  const extracted = extractText(input);
  let audit;

  if (extracted && typeof extracted === 'object' && extracted.__alreadyParsed) {
    audit = extracted.__alreadyParsed;
  } else {
    const cleaned = stripFences(extracted);
    if (!cleaned) {
      result.validation_errors.push('empty model response — nothing to parse');
      return result;
    }
    try {
      audit = JSON.parse(cleaned);
    } catch (e) {
      result.validation_errors.push(`JSON.parse failed: ${e.message}`);
      return result;
    }
  }

  result.audit = audit;

  // 2. schema validation
  const schemaErrors = validateSchema(audit);
  result.validation_errors.push(...schemaErrors);

  // 3. independent totals recomputation (only if opportunities are usable)
  if (isArray(audit && audit.opportunities)) {
    const hoursValues = audit.opportunities
      .map((o) => (o && isNumber(o.hours_saved_monthly) ? o.hours_saved_monthly : null))
      .filter((v) => v !== null);
    const dollarValues = audit.opportunities
      .map((o) => (o && isNumber(o.dollar_value_monthly) ? o.dollar_value_monthly : null))
      .filter((v) => v !== null);

    const computedHours = Math.round(hoursValues.reduce((s, v) => s + v, 0) * 100) / 100;
    const computedDollars = Math.round(dollarValues.reduce((s, v) => s + v, 0) * 100) / 100;

    if (isNumber(audit.total_hours_saved_monthly)) {
      const modelHours = audit.total_hours_saved_monthly;
      const denom = Math.abs(modelHours) > 1e-9 ? Math.abs(modelHours) : 1;
      const relDiff = Math.abs(computedHours - modelHours) / denom;
      const ok = relDiff <= HOURS_TOLERANCE;
      result.hours_check = { model: modelHours, computed: computedHours, rel_diff: Number(relDiff.toFixed(4)), within_tolerance: ok };
      if (!ok) {
        result.validation_errors.push(
          `total_hours_saved_monthly mismatch: model=${modelHours}, computed=${computedHours} (rel diff ${(relDiff * 100).toFixed(1)}% > 5%)`
        );
      }
    }

    if (isNumber(audit.total_dollar_value_monthly)) {
      const modelDollars = audit.total_dollar_value_monthly;
      const denom = Math.abs(modelDollars) > 1e-9 ? Math.abs(modelDollars) : 1;
      const relDiff = Math.abs(computedDollars - modelDollars) / denom;
      const ok = relDiff <= HOURS_TOLERANCE;
      result.dollars_check = { model: modelDollars, computed: computedDollars, rel_diff: Number(relDiff.toFixed(4)), within_tolerance: ok };
      if (!ok) {
        result.validation_errors.push(
          `total_dollar_value_monthly mismatch: model=${modelDollars}, computed=${computedDollars} (rel diff ${(relDiff * 100).toFixed(1)}% > 5%)`
        );
      }
    }
  }

  // 4. guarantee consistency: meets_guarantee must be true iff total >= 10.0
  if (isBool(audit && audit.meets_guarantee) && isNumber(audit && audit.total_hours_saved_monthly)) {
    const shouldMeet = audit.total_hours_saved_monthly >= 10.0;
    const consistent = audit.meets_guarantee === shouldMeet;
    result.guarantee_check = {
      meets_guarantee: audit.meets_guarantee,
      total_hours: audit.total_hours_saved_monthly,
      expected: shouldMeet,
      consistent,
    };
    if (!consistent) {
      result.validation_errors.push(
        `meets_guarantee (${audit.meets_guarantee}) inconsistent with total_hours_saved_monthly (${audit.total_hours_saved_monthly}); expected ${shouldMeet}`
      );
    }
  }

  // 5. routing
  const guaranteeFailed = !audit || audit.meets_guarantee !== true;
  const validationFailed = result.validation_errors.length > 0;
  result.route = (guaranteeFailed || validationFailed) ? 'alert' : 'review';

  return result;
}

// ---------------------------------------------------------------------------
// n8n Code node glue.
// Input item is the Claude HTTP Request node output (the parsed JSON body).
// We emit one item carrying the guard result; the downstream IF node branches
// on {{$json.route}} === "review".
// ---------------------------------------------------------------------------
if (typeof $input !== 'undefined') {
  const claudeResponse = $input.first().json;
  const guard = parseAndGuard(claudeResponse);
  return [{
    json: {
      route: guard.route,
      validation_errors: guard.validation_errors,
      hours_check: guard.hours_check,
      dollars_check: guard.dollars_check,
      guarantee_check: guard.guarantee_check,
      client_name: guard.audit && guard.audit.client_name ? guard.audit.client_name : 'UNKNOWN',
      audit: guard.audit,
      audit_pretty: guard.audit ? JSON.stringify(guard.audit, null, 2) : '',
    },
  }];
}

// Node / test import glue.
if (typeof module !== 'undefined') {
  module.exports = { parseAndGuard, validateSchema, stripFences, extractText };
}
