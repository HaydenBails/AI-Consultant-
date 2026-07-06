# AI Operations Audit — Intake Questionnaire

**Canonical asset.** These are the 15 questions a client answers before the audit
runs. The wording, order, and numbering here are the source of truth. The intake
form (Tally) and the analysis pipeline both mirror this file — do not renumber or
reorder questions without updating `master-analysis-prompt.md` and the pipeline.

Everything below is written to be answered by a busy owner in about 15 minutes.
Helper text under each question tells the client how to answer well. The audit is
only as good as these answers, so the form encourages specifics (numbers, tool
names, real examples) over vague statements.

---

## Section A — Your business

### Q1. What is your business name, and what does it do?
One or two sentences. Include your industry and who your customers are.
*Example: "Harbor Lane Property Management. We manage 140 residential rental units
for private landlords across two cities."*

### Q2. How many people work in the business, and what are their main roles?
List each role and how many people hold it (including you). If someone wears
several hats, say so.
*Example: "Owner/broker (1), leasing coordinator (1), part-time bookkeeper (1)."*

### Q3. What is the rough fully-loaded hourly cost of each role?
Your best estimate of what an hour of each person's time costs the business
(salary + overhead, or what you'd pay to replace that hour). A range is fine.
This is what we use to convert saved hours into dollars — if you're unsure,
give your honest guess and we'll note the assumption.
*Example: "Owner ~$60/hr, leasing coordinator ~$28/hr, bookkeeper ~$35/hr."*

---

## Section B — Where the time goes

### Q4. Walk us through a typical week. Where does the most time get spent on work that feels repetitive, manual, or low-value?
Name the 3–5 biggest time sinks. Don't filter for "automatable" — just tell us
what eats the day. Be concrete about the task, not just the category.
*Example: "Re-typing maintenance requests from voicemails and emails into our PM
software; chasing tenants for late rent; copying applicant details into
spreadsheets."*

### Q5. What tasks get done over and over in almost exactly the same way?
The more a task follows the same steps every time, the better a candidate it is.
List anything that feels like it follows a script.
*Example: "Sending the same move-in packet to every new tenant; posting each
vacancy to the same 4 listing sites."*

### Q6. Where do you or your team copy and paste information between systems, or re-enter the same data twice?
Double entry is a top automation target. Tell us the source and destination.
*Example: "Applicant info from our application form gets manually keyed into
Buildium and again into a screening portal."*

---

## Section C — Your tools and volume

### Q7. What software, tools, and apps do you use to run the business?
List everything meaningful: CRM, email, spreadsheets, accounting, industry
software, scheduling, messaging, e-signature, etc. Tool names matter — they
determine what we can connect.
*Example: "Buildium, Gmail, Google Sheets, QuickBooks, DocuSign, RingCentral,
Zillow Rental Manager."*

### Q8. For your busiest recurring tasks, roughly how often do they happen and in what volume?
Give numbers where you can. Frequency and volume are how we size the savings —
this is the single most valuable question in the form, so estimate even if you're
unsure.
*Example: "~40 maintenance requests/month; ~15 rental applications/month; rent
reminders to ~140 tenants monthly; ~8 new tenant onboardings/month."*

### Q9. How do customers, clients, or leads first reach you, and how do you respond?
Describe the intake channels (phone, web form, email, referral) and what happens
after someone reaches out — who does what, and how fast.
*Example: "Prospects call or submit a Zillow inquiry; the coordinator replies
within a day to schedule a showing and emails an application link."*

---

## Section D — Coordination, follow-up, and reporting

### Q10. What follow-ups, reminders, or nudges does someone have to remember to send?
Anything that depends on a person remembering to chase something is a strong
automation candidate.
*Example: "Reminding tenants about rent 3 days before it's due; following up with
applicants who started but didn't finish; nudging vendors for invoices."*

### Q11. What scheduling or coordination back-and-forth eats time?
Booking, rescheduling, dispatching, matching people to slots — anything that
involves several messages to lock in a time.
*Example: "Coordinating maintenance vendor visits around tenant availability
usually takes 4–5 messages per request."*

### Q12. What reports, summaries, or updates do you prepare regularly, and for whom?
Recurring documents assembled by hand — owner statements, status updates,
performance summaries — are often automatable.
*Example: "Monthly owner statements pulled together from QuickBooks and Buildium;
a weekly vacancy report I build in a spreadsheet."*

---

## Section E — Constraints and boundaries

### Q13. What's currently holding the business back from growing, or what would you do with the time if you got it back?
Tells us where saved hours are most valuable and what "success" looks like to you.
*Example: "I can't take on more units without hiring, because admin already
maxes out the team. I'd rather spend the time on landlord relationships."*

### Q14. Have you tried to automate or streamline anything before? What happened?
Past attempts — what worked, what broke, what you abandoned — help us recommend
things that will actually stick.
*Example: "Set up Zapier once to post listings, but it kept duplicating them so
we turned it off."*

### Q15. What should we NOT try to automate — the work that must stay human?
Just as important as what to automate. Tell us the judgment calls, relationships,
and sensitive touchpoints that should stay with a person no matter what. We will
explicitly leave these alone and explain why in the report.
*Example: "Handling an upset tenant or an eviction conversation — that always
needs a real person. And final approval on who we rent to."*

---

## Notes for the pipeline (not shown to the client)

- **Q1–Q3** establish `client_name`, `business_summary`, and the `hourly_rates_used`
  the analysis must convert hours into dollars with.
- **Q4, Q5, Q6, Q10, Q11, Q12** surface candidate `opportunities`.
- **Q8** supplies the frequency/volume figures the analysis needs to size
  `hours_saved_monthly`. If Q8 is blank or vague, the analysis must say so and stay
  conservative rather than inventing volume — a missing Q8 is the most common
  reason a draft should route to ALERT.
- **Q7** constrains recommended tools to things that can connect to the client's
  actual stack.
- **Q15** is a hard boundary: anything named here must appear in `not_recommended`
  with the client's own reason echoed back, never in `opportunities`.
