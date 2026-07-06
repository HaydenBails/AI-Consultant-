#!/usr/bin/env python3
"""
build_report.py — one-off generator for the approved sample audit PDF.

This renders the "Harbor Lane Property Management" sample audit and is the source
of truth for the AI Operations Audit visual design. Agent B refactors this into a
data-driven `generate_report.py`; the layout, colors, and section order below are
what that refactor must preserve pixel-close.

Design system (canonical):
  navy   #16243D   headings, bands, tables, CTA
  teal   #12A594   accent numbers, rank chips, price
  light  #F2F5F9   soft section fills
  font   Helvetica (built-in)

Sections, in order:
  cover -> stat strip -> summary + guarantee -> ranking table ->
  opportunity detail pages -> not-recommended -> 90-day roadmap -> CTA box ->
  methodology footnote

Usage:
  python3 build_report.py            # writes sample-audit-report.pdf

The Harbor Lane data below is FICTIONAL and clearly labeled as such on the cover.
The founder has no clients; this exists only to demonstrate the deliverable.
"""

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
    KeepTogether, PageBreak, Flowable, NextPageTemplate,
)

# ---------------------------------------------------------------------------
# Brand
# ---------------------------------------------------------------------------
BRAND = "Northstar Automation Co."
NAVY = colors.HexColor("#16243D")
TEAL = colors.HexColor("#12A594")
LIGHT = colors.HexColor("#F2F5F9")
MID = colors.HexColor("#5B6B82")   # muted slate for secondary text
WHITE = colors.white

PAGE_W, PAGE_H = LETTER
MARGIN = 0.85 * inch
CONTENT_W = PAGE_W - 2 * MARGIN

# ---------------------------------------------------------------------------
# Sample audit data (FICTIONAL) — conforms to the canonical schema in
# master-analysis-prompt.md.
# ---------------------------------------------------------------------------
AUDIT = {
    "client_name": "Harbor Lane Property Management",
    "business_summary": (
        "Harbor Lane manages 140 residential rental units for private landlords "
        "with a three-person team. Its biggest operational drag is manual intake: "
        "maintenance requests, rental applications, and monthly owner statements "
        "are re-keyed by hand across Buildium, QuickBooks, and spreadsheets. That "
        "administrative load is the main reason the team can't take on more units "
        "without hiring."
    ),
    "meets_guarantee": True,
    "total_hours_saved_monthly": 36.3,
    "total_dollar_value_monthly": 1176.4,
    "hourly_rates_used": [
        {"role": "Owner / broker", "rate": 60},
        {"role": "Leasing coordinator", "rate": 28},
    ],
    "opportunities": [
        {
            "rank": 1,
            "name": "Maintenance request intake & triage",
            "current_process": (
                "About 40 maintenance requests arrive each month by voicemail, "
                "email, and text. The coordinator listens or reads, re-types each "
                "into Buildium as a work order, and decides urgency — roughly 20 "
                "minutes per request once follow-up questions are included."
            ),
            "recommended_solution": (
                "An n8n workflow captures requests from a dedicated phone line "
                "(Twilio) and the shared inbox, uses the Claude API to extract "
                "unit, issue, and urgency into a structured work order, and creates "
                "it in Buildium. The coordinator reviews a pre-filled queue and "
                "handles only flagged exceptions instead of typing every ticket."
            ),
            "tools": ["n8n", "Twilio", "Claude API", "Buildium"],
            "hours_saved_monthly": 13.3,
            "dollar_value_monthly": 372.4,
            "complexity": "Medium",
            "basis": "40 requests/mo x ~20 min re-keyed & triaged each = 13.3 hrs.",
        },
        {
            "rank": 2,
            "name": "Monthly owner-statement assembly",
            "current_process": (
                "Each month the owner compiles ~25 landlord statements by pulling "
                "figures from QuickBooks and Buildium and formatting them by hand — "
                "about 15 minutes apiece."
            ),
            "recommended_solution": (
                "A scheduled n8n flow pulls each owner's transactions, assembles the "
                "statement from a template, and drafts a short plain-language summary "
                "with the Claude API. The owner reviews and sends, rather than "
                "building each statement from scratch."
            ),
            "tools": ["n8n", "QuickBooks", "Buildium", "Claude API"],
            "hours_saved_monthly": 5.0,
            "dollar_value_monthly": 300.0,
            "complexity": "High",
            "basis": "25 statements/mo x ~12 min saved each = 5.0 hrs.",
        },
        {
            "rank": 3,
            "name": "Rent reminders & late-payment follow-up",
            "current_process": (
                "The coordinator manually sends rent reminders to 140 tenants and "
                "chases roughly 18 late payers each month, tracking who has paid in "
                "a spreadsheet."
            ),
            "recommended_solution": (
                "An n8n schedule sends templated reminders three days before rent is "
                "due and escalates a friendly follow-up to anyone unpaid by the grace "
                "date, reading payment status from Buildium so no one is chased in "
                "error."
            ),
            "tools": ["n8n", "Buildium", "Gmail"],
            "hours_saved_monthly": 9.0,
            "dollar_value_monthly": 252.0,
            "complexity": "Low",
            "basis": "Reminder + late-chase workload ≈ 9.0 hrs/mo removed.",
        },
        {
            "rank": 4,
            "name": "Applicant intake & screening data entry",
            "current_process": (
                "About 15 applications a month are entered twice — once into "
                "Buildium and again into the screening portal — at roughly 25 "
                "minutes per applicant."
            ),
            "recommended_solution": (
                "An n8n workflow takes the submitted application, creates the "
                "applicant record in Buildium, and pushes the same details to the "
                "screening portal, leaving the coordinator to review results rather "
                "than key data twice."
            ),
            "tools": ["n8n", "Buildium", "Google Sheets"],
            "hours_saved_monthly": 5.0,
            "dollar_value_monthly": 140.0,
            "complexity": "Low",
            "basis": "15 applications/mo x ~20 min double-entry saved = 5.0 hrs.",
        },
        {
            "rank": 5,
            "name": "Move-in packet & onboarding",
            "current_process": (
                "For each of ~8 new tenants a month, the coordinator assembles the "
                "same move-in packet and setup tasks by hand — about 40 minutes each."
            ),
            "recommended_solution": (
                "An n8n flow triggers on a signed lease, generates the personalized "
                "move-in packet, sends it for e-signature, and creates the standard "
                "onboarding tasks automatically."
            ),
            "tools": ["n8n", "DocuSign", "Buildium"],
            "hours_saved_monthly": 4.0,
            "dollar_value_monthly": 112.0,
            "complexity": "Low",
            "basis": "8 onboardings/mo x ~30 min saved each = 4.0 hrs.",
        },
    ],
    "not_recommended": [
        {
            "name": "Final approval of who to rent to",
            "reason": "Client asked (Q15) that the rent/deny decision stay a human judgment call.",
        },
        {
            "name": "Handling upset tenants and eviction conversations",
            "reason": "Client asked (Q15) that sensitive tenant conversations always stay with a real person.",
        },
        {
            "name": "Vacancy listing syndication to the 4 listing sites",
            "reason": "Low volume (~6 vacancies/mo) and a past Zapier attempt duplicated listings (Q14); revisit only after the core builds are proven.",
        },
    ],
    "roadmap": {
        "days_1_30": (
            "Build and prove the maintenance request intake & triage flow end to "
            "end — capturing phone, email, and text into structured Buildium work "
            "orders — and measure the real hours saved against the 13.3/month "
            "estimate."
        ),
        "days_31_60": (
            "Add rent reminders & late-payment follow-up and applicant intake "
            "double-entry — both low-complexity quick wins — once the first flow "
            "is trusted."
        ),
        "days_61_90": (
            "Automate monthly owner-statement assembly (the highest-effort build) "
            "and the move-in packet flow, then review measured savings and decide "
            "whether vacancy syndication is worth revisiting."
        ),
    },
    "recommended_first_build": {
        "opportunity": "Maintenance request intake & triage",
        "why": (
            "It targets the team's single biggest time sink and carries the highest "
            "monthly value of any opportunity. At Medium complexity it's comfortably "
            "a two-week build, and proving it frees the coordinator immediately."
        ),
        "price": 1500,
        "estimated_timeline": "2 weeks",
    },
    # Sample-only: rendered on the cover to keep the demonstration honest.
    "is_sample": True,
}

REPORT_DATE = "July 2026"

# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------
def money(n):
    return "${:,.0f}".format(n) if float(n).is_integer() else "${:,.1f}".format(n)


def hours(n):
    return "{:,.1f}".format(n)


# ---------------------------------------------------------------------------
# Paragraph styles
# ---------------------------------------------------------------------------
def _styles():
    s = {}
    s["cover_brand"] = ParagraphStyle(
        "cover_brand", fontName="Helvetica-Bold", fontSize=13, textColor=TEAL,
        leading=16, tracking=2,
    )
    s["cover_title"] = ParagraphStyle(
        "cover_title", fontName="Helvetica-Bold", fontSize=40, textColor=WHITE,
        leading=44,
    )
    s["cover_client"] = ParagraphStyle(
        "cover_client", fontName="Helvetica", fontSize=20, textColor=WHITE,
        leading=26,
    )
    s["cover_meta"] = ParagraphStyle(
        "cover_meta", fontName="Helvetica", fontSize=11, textColor=colors.HexColor("#AEB9C9"),
        leading=16,
    )
    s["cover_disclaimer"] = ParagraphStyle(
        "cover_disclaimer", fontName="Helvetica-Oblique", fontSize=9,
        textColor=colors.HexColor("#8595AB"), leading=13,
    )
    s["h2"] = ParagraphStyle(
        "h2", fontName="Helvetica-Bold", fontSize=17, textColor=NAVY, leading=21,
        spaceBefore=6, spaceAfter=8,
    )
    s["eyebrow"] = ParagraphStyle(
        "eyebrow", fontName="Helvetica-Bold", fontSize=9.5, textColor=TEAL,
        leading=12, spaceAfter=2, tracking=1.5,
    )
    s["body"] = ParagraphStyle(
        "body", fontName="Helvetica", fontSize=10.5, textColor=colors.HexColor("#25324A"),
        leading=15.5, alignment=TA_LEFT,
    )
    s["label"] = ParagraphStyle(
        "label", fontName="Helvetica-Bold", fontSize=9, textColor=MID, leading=12,
        tracking=1, spaceAfter=1,
    )
    s["opp_title"] = ParagraphStyle(
        "opp_title", fontName="Helvetica-Bold", fontSize=14, textColor=NAVY,
        leading=18,
    )
    s["stat_num"] = ParagraphStyle(
        "stat_num", fontName="Helvetica-Bold", fontSize=25, textColor=WHITE,
        leading=27, alignment=TA_CENTER,
    )
    s["stat_label"] = ParagraphStyle(
        "stat_label", fontName="Helvetica", fontSize=8.5, textColor=colors.HexColor("#AEB9C9"),
        leading=11, alignment=TA_CENTER,
    )
    s["cell"] = ParagraphStyle(
        "cell", fontName="Helvetica", fontSize=10, textColor=colors.HexColor("#25324A"),
        leading=13,
    )
    s["cell_b"] = ParagraphStyle(
        "cell_b", fontName="Helvetica-Bold", fontSize=10, textColor=NAVY, leading=13,
    )
    s["th"] = ParagraphStyle(
        "th", fontName="Helvetica-Bold", fontSize=9, textColor=WHITE, leading=12,
    )
    s["cta_h"] = ParagraphStyle(
        "cta_h", fontName="Helvetica-Bold", fontSize=16, textColor=WHITE, leading=20,
    )
    s["cta_body"] = ParagraphStyle(
        "cta_body", fontName="Helvetica", fontSize=10.5, textColor=colors.HexColor("#D6DEEA"),
        leading=15,
    )
    s["cta_price"] = ParagraphStyle(
        "cta_price", fontName="Helvetica-Bold", fontSize=30, textColor=TEAL, leading=32,
    )
    s["foot"] = ParagraphStyle(
        "foot", fontName="Helvetica", fontSize=8, textColor=MID, leading=11.5,
    )
    s["tag"] = ParagraphStyle(
        "tag", fontName="Helvetica-Bold", fontSize=8.5, textColor=NAVY, leading=11,
        alignment=TA_CENTER,
    )
    return s


ST = _styles()


# ---------------------------------------------------------------------------
# Small custom flowables
# ---------------------------------------------------------------------------
class HRule(Flowable):
    """A thin horizontal rule."""
    def __init__(self, width, color=colors.HexColor("#D7DEE8"), thickness=0.8, pad=0):
        super().__init__()
        self.width = width
        self.color = color
        self.thickness = thickness
        self.pad = pad
        self.height = thickness + pad

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, self.pad, self.width, self.pad)


def rank_chip(rank):
    """A small teal square holding the rank number."""
    t = Table([[str(rank)]], colWidths=[0.34 * inch], rowHeights=[0.34 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), TEAL),
        ("TEXTCOLOR", (0, 0), (-1, -1), WHITE),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 14),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def tool_pills(tools):
    """Render tool names as a light-fill inline string of pills (via a table row)."""
    cells = [Paragraph(t, ST["tag"]) for t in tools]
    # Size each pill to its text so labels never wrap (14pt total horizontal padding).
    widths = [stringWidth(t, "Helvetica-Bold", 8.5) + 16 for t in tools]
    tbl = Table([cells], colWidths=widths, hAlign="LEFT")
    style = [
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("BOX", (0, 0), (-1, -1), 0, WHITE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
    ]
    # thin white gaps between pills
    for i in range(len(tools) - 1):
        style.append(("LINEAFTER", (i, 0), (i, 0), 3, WHITE))
    tbl.setStyle(TableStyle(style))
    return tbl


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------
def cover_flowables(data):
    out = [Spacer(1, 1.7 * inch)]
    out.append(Paragraph(BRAND.upper(), ST["cover_brand"]))
    out.append(Spacer(1, 0.5 * inch))
    out.append(Paragraph("AI Operations<br/>Audit", ST["cover_title"]))
    out.append(Spacer(1, 0.35 * inch))
    out.append(HRule(2.2 * inch, color=TEAL, thickness=2))
    out.append(Spacer(1, 0.3 * inch))
    out.append(Paragraph("Prepared for", ST["cover_meta"]))
    out.append(Spacer(1, 0.06 * inch))
    out.append(Paragraph(data["client_name"], ST["cover_client"]))
    out.append(Spacer(1, 0.25 * inch))
    out.append(Paragraph(REPORT_DATE, ST["cover_meta"]))
    out.append(Spacer(1, 2.5 * inch))
    if data.get("is_sample"):
        out.append(Paragraph(
            "SAMPLE REPORT — Harbor Lane Property Management is a fictional business "
            "used to demonstrate the deliverable. All figures are illustrative.",
            ST["cover_disclaimer"]))
    out.append(PageBreak())
    return out


def stat_strip(data):
    annual = data["total_dollar_value_monthly"] * 12
    cards = [
        (hours(data["total_hours_saved_monthly"]), "HOURS SAVED / MONTH"),
        (money(data["total_dollar_value_monthly"]), "VALUE / MONTH"),
        (money(annual), "VALUE / YEAR"),
        (str(len(data["opportunities"])), "OPPORTUNITIES FOUND"),
    ]
    cells = []
    for num, lab in cards:
        inner = [
            [Paragraph(num, ST["stat_num"])],
            [Spacer(1, 2)],
            [Paragraph(lab, ST["stat_label"])],
        ]
        it = Table(inner, colWidths=[CONTENT_W / 4 - 8])
        it.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        cells.append(it)
    strip = Table([cells], colWidths=[CONTENT_W / 4] * 4)
    strip.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 16),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
        ("LINEAFTER", (0, 0), (-2, -1), 0.7, colors.HexColor("#2C3C57")),
    ]))
    return strip


def guarantee_banner(data):
    met = data["meets_guarantee"]
    if met:
        txt = ("<b>Guarantee met.</b>  This audit identifies "
               f"{hours(data['total_hours_saved_monthly'])} recoverable hours per "
               "month — above the 10-hour floor. If we hadn't found them, the audit "
               "would have been free.")
        fill = colors.HexColor("#E7F5F1")
        bar = TEAL
    else:
        txt = ("<b>Guarantee not met.</b>  This audit found fewer than 10 recoverable "
               "hours per month, so under our guarantee it is free. We won't inflate "
               "findings to clear the bar.")
        fill = colors.HexColor("#FBEEE8")
        bar = colors.HexColor("#C4622D")
    p = Paragraph(txt, ST["body"])
    t = Table([[p]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), fill),
        ("LINEBEFORE", (0, 0), (0, -1), 3, bar),
        ("TOPPADDING", (0, 0), (-1, -1), 11),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 11),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
    ]))
    return t


def ranking_table(data):
    header = [
        Paragraph("#", ST["th"]),
        Paragraph("OPPORTUNITY", ST["th"]),
        Paragraph("HRS/MO", ST["th"]),
        Paragraph("VALUE/MO", ST["th"]),
        Paragraph("EFFORT", ST["th"]),
    ]
    rows = [header]
    for o in data["opportunities"]:
        rows.append([
            Paragraph(str(o["rank"]), ST["cell_b"]),
            Paragraph(o["name"], ST["cell_b"]),
            Paragraph(hours(o["hours_saved_monthly"]), ST["cell"]),
            Paragraph(money(o["dollar_value_monthly"]), ST["cell"]),
            Paragraph(o["complexity"], ST["cell"]),
        ])
    # totals row
    rows.append([
        Paragraph("", ST["cell"]),
        Paragraph("Total", ST["cell_b"]),
        Paragraph(hours(data["total_hours_saved_monthly"]), ST["cell_b"]),
        Paragraph(money(data["total_dollar_value_monthly"]), ST["cell_b"]),
        Paragraph("", ST["cell"]),
    ])
    rank_w, hrs_w, val_w, eff_w = 0.4 * inch, 0.8 * inch, 1.05 * inch, 1.0 * inch
    col_w = [rank_w, CONTENT_W - rank_w - hrs_w - val_w - eff_w, hrs_w, val_w, eff_w]
    t = Table(rows, colWidths=col_w, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("ALIGN", (2, 0), (-1, -1), "LEFT"),
        ("LINEBELOW", (0, 0), (-1, -2), 0.6, colors.HexColor("#DCE3EC")),
        ("LINEABOVE", (0, -1), (-1, -1), 1.1, NAVY),
    ]
    # zebra + rank chip color
    for i in range(1, len(data["opportunities"]) + 1):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), LIGHT))
        style.append(("TEXTCOLOR", (0, i), (0, i), TEAL))
    style.append(("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#EAF6F2")))
    t.setStyle(TableStyle(style))
    return t


def opportunity_block(o):
    head = Table(
        [[rank_chip(o["rank"]), Paragraph(o["name"], ST["opp_title"])]],
        colWidths=[0.5 * inch, CONTENT_W - 0.5 * inch],
    )
    head.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("LEFTPADDING", (1, 0), (1, 0), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    # metric mini-strip for this opportunity
    metrics = Table(
        [[
            Paragraph(f"<font color='#12A594'><b>{hours(o['hours_saved_monthly'])}</b></font>"
                      " hrs/mo", ST["cell"]),
            Paragraph(f"<font color='#12A594'><b>{money(o['dollar_value_monthly'])}</b></font>"
                      " /mo", ST["cell"]),
            Paragraph(f"Effort: <b>{o['complexity']}</b>", ST["cell"]),
        ]],
        colWidths=[CONTENT_W / 3] * 3,
    )
    metrics.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    parts = [
        head,
        Spacer(1, 8),
        metrics,
        Spacer(1, 10),
        Paragraph("HOW IT WORKS TODAY", ST["label"]),
        Paragraph(o["current_process"], ST["body"]),
        Spacer(1, 8),
        Paragraph("WHAT TO BUILD", ST["label"]),
        Paragraph(o["recommended_solution"], ST["body"]),
        Spacer(1, 9),
        Paragraph("TOOLS", ST["label"]),
        Spacer(1, 2),
        tool_pills(o["tools"]),
        Spacer(1, 8),
        Paragraph(f"<i>Basis:</i> {o['basis']}", ST["foot"]),
        Spacer(1, 6),
        HRule(CONTENT_W, pad=0),
        Spacer(1, 16),
    ]
    return KeepTogether(parts)


def not_recommended_block(data):
    rows = []
    for nr in data["not_recommended"]:
        rows.append([
            Paragraph(nr["name"], ST["cell_b"]),
            Paragraph(nr["reason"], ST["cell"]),
        ])
    t = Table(rows, colWidths=[2.3 * inch, CONTENT_W - 2.3 * inch])
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("LINEBELOW", (0, 0), (-1, -2), 0.6, colors.HexColor("#DCE3EC")),
        ("LINEBEFORE", (0, 0), (0, -1), 3, colors.HexColor("#C7D0DC")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FAFBFD")),
    ]
    t.setStyle(TableStyle(style))
    return t


def roadmap_block(data):
    r = data["roadmap"]
    phases = [
        ("DAYS 1–30", r["days_1_30"]),
        ("DAYS 31–60", r["days_31_60"]),
        ("DAYS 61–90", r["days_61_90"]),
    ]
    rows = []
    for label, text in phases:
        chip = Table([[Paragraph(label, ST["th"])]], colWidths=[1.35 * inch])
        chip.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), NAVY),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ]))
        rows.append([chip, Paragraph(text, ST["body"])])
    t = Table(rows, colWidths=[1.55 * inch, CONTENT_W - 1.55 * inch])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
        ("LEFTPADDING", (1, 0), (1, -1), 14),
        ("LINEBELOW", (0, 0), (-1, -2), 0.6, colors.HexColor("#DCE3EC")),
    ]))
    return t


def cta_block(data):
    fb = data["recommended_first_build"]
    left = [
        Paragraph("RECOMMENDED FIRST BUILD", ST["eyebrow"]),
        Spacer(1, 4),
        Paragraph(fb["opportunity"], ST["cta_h"]),
        Spacer(1, 8),
        Paragraph(fb["why"], ST["cta_body"]),
        Spacer(1, 10),
        Paragraph(f"Fixed-price implementation &nbsp;·&nbsp; {fb['estimated_timeline']}",
                  ST["cta_body"]),
    ]
    left_tbl = Table([[x] for x in left], colWidths=[CONTENT_W - 2.0 * inch])
    left_tbl.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    right = [
        Paragraph(money(fb["price"]), ST["cta_price"]),
        Spacer(1, 2),
        Paragraph("fixed price", ST["cta_body"]),
    ]
    right_tbl = Table([[x] for x in right], colWidths=[2.0 * inch])
    right_tbl.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    box = Table([[left_tbl, right_tbl]], colWidths=[CONTENT_W - 2.0 * inch, 2.0 * inch])
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("VALIGN", (0, 0), (0, 0), "TOP"),
        ("VALIGN", (1, 0), (1, 0), "BOTTOM"),
        ("TOPPADDING", (0, 0), (-1, -1), 22),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 22),
        ("LEFTPADDING", (0, 0), (-1, -1), 24),
        ("RIGHTPADDING", (0, 0), (-1, -1), 24),
    ]))
    return box


def rates_note(data):
    parts = ", ".join(f"{r['role']} {money(r['rate'])}/hr" for r in data["hourly_rates_used"])
    txt = (
        "Methodology: Hours saved are estimated conservatively from the volume and "
        "frequency figures given in the intake questionnaire, and converted to "
        "dollars using the client's own fully-loaded hourly rates (" + parts + "). "
        "Estimates assume a human still reviews exceptions, so realized savings are "
        "typically at or above these figures once a build is tuned. Figures are "
        "planning estimates, not guarantees of specific results."
    )
    return Paragraph(txt, ST["foot"])


# ---------------------------------------------------------------------------
# Page background + footer
# ---------------------------------------------------------------------------
def on_cover(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    # subtle teal marker at top-left
    canvas.setFillColor(TEAL)
    canvas.rect(0, PAGE_H - 8, PAGE_W, 8, stroke=0, fill=1)
    canvas.restoreState()


def on_content(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(WHITE)
    canvas.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    # footer
    canvas.setFillColor(MID)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(MARGIN, 0.5 * inch, f"{BRAND}  ·  AI Operations Audit")
    canvas.drawRightString(PAGE_W - MARGIN, 0.5 * inch, f"{doc.page - 1}")
    canvas.setStrokeColor(colors.HexColor("#E1E7EF"))
    canvas.setLineWidth(0.6)
    canvas.line(MARGIN, 0.66 * inch, PAGE_W - MARGIN, 0.66 * inch)
    canvas.restoreState()


# ---------------------------------------------------------------------------
# Assemble the document
# ---------------------------------------------------------------------------
def build(data, out_path="sample-audit-report.pdf"):
    doc = BaseDocTemplate(
        out_path, pagesize=LETTER,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=0.85 * inch, bottomMargin=0.85 * inch,
        title=f"AI Operations Audit — {data['client_name']}",
        author=BRAND,
    )
    frame = Frame(MARGIN, 0.85 * inch, CONTENT_W, PAGE_H - 1.7 * inch, id="body",
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[frame], onPage=on_cover),
        PageTemplate(id="content", frames=[frame], onPage=on_content),
    ])

    story = []
    # After the cover's page break, switch to the white "content" template.
    story.append(NextPageTemplate("content"))
    # Cover (uses the first-registered "cover" template) — ends with a PageBreak.
    story += cover_flowables(data)

    # --- Findings page ---
    story.append(Paragraph("Findings", ST["h2"]))
    story.append(Spacer(1, 4))
    story.append(stat_strip(data))
    story.append(Spacer(1, 16))
    story.append(guarantee_banner(data))
    story.append(Spacer(1, 16))
    story.append(Paragraph("BUSINESS SUMMARY", ST["eyebrow"]))
    story.append(Spacer(1, 2))
    story.append(Paragraph(data["business_summary"], ST["body"]))
    story.append(Spacer(1, 16))
    story.append(Paragraph("Opportunities, ranked by monthly value", ST["eyebrow"]))
    story.append(Spacer(1, 6))
    story.append(ranking_table(data))
    story.append(PageBreak())

    # --- Opportunity detail pages ---
    story.append(Paragraph("The opportunities in detail", ST["h2"]))
    story.append(Spacer(1, 10))
    for o in data["opportunities"]:
        story.append(opportunity_block(o))

    # --- Not recommended ---
    story.append(KeepTogether([
        Paragraph("What we deliberately left alone", ST["h2"]),
        Spacer(1, 4),
        Paragraph(
            "Good automation knows its limits. These are out of scope by design — "
            "several because you told us they must stay human.", ST["body"]),
        Spacer(1, 10),
        not_recommended_block(data),
    ]))
    story.append(PageBreak())

    # --- Roadmap ---
    story.append(Paragraph("Your 90-day roadmap", ST["h2"]))
    story.append(Spacer(1, 10))
    story.append(roadmap_block(data))
    story.append(Spacer(1, 22))

    # --- CTA ---
    story.append(KeepTogether([cta_block(data), Spacer(1, 18), rates_note(data)]))

    doc.build(story)
    print(f"Wrote {out_path}")

    # sanity: totals must equal the sum of opportunities
    hsum = round(sum(o["hours_saved_monthly"] for o in data["opportunities"]), 1)
    dsum = round(sum(o["dollar_value_monthly"] for o in data["opportunities"]), 1)
    assert abs(hsum - data["total_hours_saved_monthly"]) < 0.05, (hsum, data["total_hours_saved_monthly"])
    assert abs(dsum - data["total_dollar_value_monthly"]) < 0.05, (dsum, data["total_dollar_value_monthly"])
    assert data["meets_guarantee"] == (data["total_hours_saved_monthly"] >= 10.0)
    names = {o["name"] for o in data["opportunities"]}
    assert data["recommended_first_build"]["opportunity"] in names
    print(f"Self-check OK: {hsum} hrs, {money(dsum)}/mo, guarantee={data['meets_guarantee']}")


if __name__ == "__main__":
    build(AUDIT, "sample-audit-report.pdf")
