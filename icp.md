# Ideal Client Profile — Recruiting & Staffing Agencies

The first niche for the AI Operations Audit. This file defines exactly who to
target and gives a repeatable, manual process for building a 100-prospect list
without paid data tools.

---

## 1. Who we're selling to

**Business type:** Independent recruiting, staffing, executive-search, or talent
agencies. Includes contingency recruiters, retained search, temp/contract
staffing, and RPO boutiques.

**Size:** 2–15 people. This is the sweet spot:
- Big enough to have real, repeated administrative volume (multiple recruiters,
  multiple open roles, weekly client reporting).
- Small enough that the owner still touches operations and can say "yes" to a
  $400 audit without a committee or procurement.
- Too small to have an internal ops/RevOps hire who already owns automation.

**Decision-maker:** Founder / Owner / Managing Director / Principal. In an agency
this size they are usually still billing desks themselves, so their own time is
the most expensive thing being wasted — which is exactly what the audit quantifies.

**Geography (first pass):** {{CITY}} and surrounding metro, then English-speaking
North America. Local-first makes the "book a 20-min call" ask easier and the
personalization more credible.

### Why recruiting agencies are a strong first niche
- Their day is *made of* repeatable administrative motion: sourcing, data entry
  between job boards and their ATS, formatting candidate submittals, scheduling
  interviews, chasing candidates and clients for updates, weekly pipeline reports,
  and (for staffing) timesheets and invoicing.
- They already believe in leverage — they sell it. "Automate the admin so
  recruiters recruit" is a message they nod along to.
- The work maps cleanly to the intake questionnaire's time-sink questions
  (Q4–Q6, Q10–Q12) and to the kind of n8n + API builds the $1,500 upsell delivers.

### Disqualifiers (skip these)
- Solo recruiter with no repeated volume (audit may not clear the 10-hour floor).
- 50+ people or a named ops/automation hire (already solved or needs enterprise).
- In-house talent-acquisition teams (they're a cost center, not a buyer of this).
- Agencies mid-rebuild of their tech stack (they'll defer everything).

---

## 2. Signals that an agency has administrative drag

These are what make a prospect *worth* the audit. Look for them while building
the list and record them — they become the personalization slot in outreach.
The more signals, the higher the priority.

**Strong signals**
- **Many open roles posted at once** across multiple job boards (LinkedIn Jobs,
  Indeed, ZipRecruiter, niche boards) — implies repeated manual multi-posting and
  candidate re-keying.
- **Actively hiring a "Recruiting Coordinator," "Recruitment Admin," "Ops
  Assistant," or "Sourcer"** — they are about to spend salary on exactly the
  administrative load the audit targets. This is the single best signal.
- **Owner still visibly doing the work** — posting jobs, replying to candidates,
  and running the LinkedIn account personally.
- **Job posts that mention "fast-growing," "scaling," or "high volume."**

**Moderate signals**
- Uses a mid-market ATS you can see referenced (Bullhorn, Loxo, JobAdder, Recruit
  CRM, Manatal, Crelate, Vincere) — data lives in a system that n8n can connect to.
- A careers/jobs page that is clearly manually updated.
- Recent LinkedIn posts about being busy, time-to-fill, or "not enough hours."
- Staffing/temp model (adds timesheet + invoicing drag on top of recruiting).
- Reviews or posts mentioning slow follow-up (a symptom of manual process).

**Where to see the signals:** the agency's LinkedIn "Jobs" tab and recent posts,
their website careers page, the owner's personal LinkedIn activity, and their
job-board footprint (search the agency name on Indeed).

---

## 3. How to build a 100-prospect list by hand

Goal: 100 qualified agencies with a named decision-maker and at least one drag
signal each. Budget ~4–6 focused hours. No paid tools required (Sales Navigator
optional and helpful, not mandatory).

### Source A — LinkedIn (aim for ~60 of the 100)

Use LinkedIn search, filter **People**, then set filters or bake them into the
query. Copy these strings into the LinkedIn search bar. Combine a title term with
an industry/keyword term; set **Locations** to {{CITY}} / your target metro and
**Company headcount** (in Sales Navigator) to 2–10 and 11–50.

Title × keyword search strings (run each, page through results):

```
("Founder" OR "Owner" OR "Managing Director" OR "Principal") AND ("recruiting agency" OR "staffing agency")
("Founder" OR "Managing Partner") AND ("executive search" OR "talent acquisition firm")
("Owner" OR "Director") AND ("recruitment" OR "staffing" OR "search firm")
"Recruitment Agency" AND ("Founder" OR "CEO")
"Staffing" AND ("President" OR "Owner") AND {{CITY}}
```

Also search **Companies** directly, then open each and read the "People" and
"Jobs" tabs:

```
"recruiting agency" {{CITY}}
"staffing agency" {{CITY}}
"executive search" {{CITY}}
"talent solutions" {{CITY}}
```

For each company that fits 2–15 people, find the owner via the company's "People"
tab and capture them as a row.

Sales Navigator (if available) filters to replicate the above:
- Geography = {{CITY}} + metro
- Company headcount = 2–10, 11–50
- Industry = Staffing & Recruiting
- Title = Owner, Founder, Managing Director, Principal, President
- Keyword = recruiting / staffing / search
- Bonus: "Posted on LinkedIn in past 30 days" and "Hiring on LinkedIn" spotlights
  surface the strongest drag signals.

### Source B — Directories (aim for ~30 of the 100)

- **Google Maps / Google Search:** `staffing agency {{CITY}}`,
  `recruiting agency {{CITY}}`, `[vertical] recruiters {{CITY}}` (e.g. "IT
  recruiters," "healthcare staffing"). Map results skew to real local SMBs.
- **Clutch.co** and **DesignRush** — filter by "Staffing & Recruiting" and city;
  they list boutique agencies with size bands and websites.
- **American Staffing Association (ASA) member directory** and **NAPS** (National
  Association of Personnel Services) member lists.
- **"Best recruiting agencies in {{CITY}}" listicle articles** — journalists and
  bloggers have already compiled local shortlists; harvest the names.
- **Local chamber of commerce** member directory (filter by category).
- **Yelp / Yellow Pages** under "Employment Agencies" for owner-operator shops.

For each directory hit, visit the website, confirm size (About/Team page), then
find the owner on LinkedIn to complete the row.

### Source C — Job boards as a discovery + signal tool (aim for ~10, and enrich all)

- Search **Indeed** and **LinkedIn Jobs** for roles in {{CITY}} and note which
  ones are posted "via [Agency Name]." Each agency name posting multiple roles is
  a qualified, high-signal prospect.
- Search **LinkedIn Jobs** for `recruiting coordinator {{CITY}}` and
  `recruitment admin {{CITY}}` — the agencies *posting* these roles are your
  hottest signal (they're about to pay salary for the drag you can automate).

### Finding the email (keep it simple, no paid enrichment required)
1. Check the website (About / Contact / footer) for a direct or
   `firstname@domain` pattern.
2. Infer from the domain's visible pattern (if one address is
   `jane@acme.com`, the owner is likely `john@acme.com`).
3. LinkedIn "Contact info" on the profile.
4. If email is uncertain, mark it **Low** confidence and default that prospect to
   the **LinkedIn** channel instead (see `linkedin-dm.md`).

Never guess-and-blast to made-up addresses; low-confidence email → use LinkedIn.

---

## 4. Tracking spreadsheet — column layout

One row per prospect. Suggested tab name: `Prospects`. Columns:

| # | Column | What goes in it |
|---|--------|-----------------|
| A | Company | Agency name |
| B | Website | URL |
| C | LinkedIn (company) | Company page URL |
| D | Contact name | Decision-maker (owner/MD) |
| E | Title | Their role |
| F | Contact LinkedIn | Personal profile URL |
| G | Email | Best email found |
| H | Email confidence | High / Med / Low (Low ⇒ LinkedIn channel) |
| I | City | Location |
| J | Headcount | Approx people (2–15 target) |
| K | Vertical | Niche: IT, healthcare, finance, exec search, temp, general |
| L | ATS / tools spotted | Bullhorn / Loxo / JobAdder / unknown |
| M | Drag signal(s) | e.g. "hiring a coordinator; 12 open roles" |
| N | Personalization note | The one specific line you'll use in touch 1 |
| O | Channel | Email / LinkedIn |
| P | Touch 1 date | Day 0 sent |
| Q | Touch 2 date | Day 3 sent |
| R | Touch 3 date | Day 7 sent |
| S | Status | Not started / In sequence / Replied / Call booked / Won / Dead |
| T | Reply? | Y / N + sentiment (pos/neutral/neg) |
| U | Next action | The very next step + date |
| V | Notes | Anything else (referrals, timing, objections) |

**Fill order while prospecting:** A–F and I–M first (fast, from LinkedIn/website),
then G–H, then write N (the personalization note) while the tab is still open —
capturing it now saves the "under 2 minutes" personalization step later.

**Priority sort:** sort by number/strength of drag signals in column M so the
hottest prospects enter the sequence first.
