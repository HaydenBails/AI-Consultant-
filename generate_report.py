#!/usr/bin/env python3
"""
generate_report.py — data-driven generator for the AI Operations Audit PDF.

This is the production refactor of build_report.py. It consumes an audit JSON that
conforms to the canonical schema in master-analysis-prompt.md and renders it using
the approved visual design system (navy #16243D, teal #12A594, light #F2F5F9,
Helvetica; cover -> stat strip -> guarantee banner -> business summary ->
ranking table -> opportunity detail blocks -> not-recommended -> 90-day roadmap ->
navy CTA box -> methodology footnote).

Usage:
  python3 generate_report.py audit.json --brand "Northstar Automation Co." --out report.pdf
  python3 generate_report.py audit.json --brand "Northstar Automation Co." --out report.pdf --price 2500
  python3 generate_report.py sample.json --brand "Northstar Automation Co." --out sample.pdf --sample

Flags:
  --brand   Brand name shown on the cover and footer (default "Northstar Automation Co.").
  --out     Output PDF path (default "report.pdf").
  --price   Override the fixed-price implementation quote in the CTA box. If omitted,
            the price comes from recommended_first_build.price in the JSON, or $1,500
            if that field is absent.
  --sample  Render the "fictional business" disclaimer on the cover. Real client
            reports omit it; pass this flag only for the demonstration sample.

The input JSON is validated against the canonical schema before rendering; if any
required field is missing or the wrong type, generation aborts with a clear list of
problems instead of producing a broken PDF.
"""

import argparse
import datetime
import json
import sys

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
# Brand / design system (canonical — must match build_report.py pixel-close)
# ---------------------------------------------------------------------------
DEFAULT_BRAND = "Northstar Automation Co."
DEFAULT_PRICE = 1500

# Set at runtime by main(); the page-background/footer callbacks and the cover
# read these module globals, mirroring build_report.py's structure.
BRAND = DEFAULT_BRAND
REPORT_DATE = datetime.date.today().strftime("%B %Y")

NAVY = colors.HexColor("#16243D")
TEAL = colors.HexColor("#12A594")
LIGHT = colors.HexColor("#F2F5F9")
MID = colors.HexColor("#5B6B82")   # muted slate for secondary text
WHITE = colors.white

PAGE_W, PAGE_H = LETTER
MARGIN = 0.85 * inch
CONTENT_W = PAGE_W - 2 * MARGIN


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------
def _is_num(x):
    """True for a JSON number (int or float) but not bool."""
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _type_name(x):
    return type(x).__name__


def validate_audit(data):
    """Validate `data` against the canonical schema in master-analysis-prompt.md.

    Returns a list of human-readable error strings; an empty list means valid.
    """
    errors = []

    if not isinstance(data, dict):
        return [f"top-level JSON must be an object, got {_type_name(data)}"]

    def check(container, key, predicate, expected, path):
        if key not in container:
            errors.append(f"missing required field: {path}")
            return False
        if not predicate(container[key]):
            errors.append(
                f"{path} must be {expected}, got {_type_name(container[key])}")
            return False
        return True

    is_str = lambda v: isinstance(v, str)
    is_bool = lambda v: isinstance(v, bool)
    is_list = lambda v: isinstance(v, list)

    # --- top-level scalar fields ---
    check(data, "client_name", is_str, "a string", "client_name")
    check(data, "business_summary", is_str, "a string", "business_summary")
    check(data, "meets_guarantee", is_bool, "a boolean", "meets_guarantee")
    check(data, "total_hours_saved_monthly", _is_num, "a number",
          "total_hours_saved_monthly")
    check(data, "total_dollar_value_monthly", _is_num, "a number",
          "total_dollar_value_monthly")

    # --- hourly_rates_used ---
    if check(data, "hourly_rates_used", is_list, "an array", "hourly_rates_used"):
        for i, r in enumerate(data["hourly_rates_used"]):
            p = f"hourly_rates_used[{i}]"
            if not isinstance(r, dict):
                errors.append(f"{p} must be an object, got {_type_name(r)}")
                continue
            check(r, "role", is_str, "a string", f"{p}.role")
            check(r, "rate", _is_num, "a number", f"{p}.rate")

    # --- opportunities ---
    if check(data, "opportunities", is_list, "an array", "opportunities"):
        opps = data["opportunities"]
        if len(opps) == 0:
            errors.append("opportunities must contain at least one opportunity")
        for i, o in enumerate(opps):
            p = f"opportunities[{i}]"
            if not isinstance(o, dict):
                errors.append(f"{p} must be an object, got {_type_name(o)}")
                continue
            check(o, "rank", lambda v: isinstance(v, int) and not isinstance(v, bool),
                  "an integer", f"{p}.rank")
            check(o, "name", is_str, "a string", f"{p}.name")
            check(o, "current_process", is_str, "a string", f"{p}.current_process")
            check(o, "recommended_solution", is_str, "a string",
                  f"{p}.recommended_solution")
            if check(o, "tools", is_list, "an array", f"{p}.tools"):
                if not all(isinstance(t, str) for t in o["tools"]):
                    errors.append(f"{p}.tools must be an array of strings")
            check(o, "hours_saved_monthly", _is_num, "a number",
                  f"{p}.hours_saved_monthly")
            check(o, "dollar_value_monthly", _is_num, "a number",
                  f"{p}.dollar_value_monthly")
            check(o, "complexity", is_str, "a string", f"{p}.complexity")
            check(o, "basis", is_str, "a string", f"{p}.basis")

    # --- not_recommended (may be empty, but must be a list of {name, reason}) ---
    if check(data, "not_recommended", is_list, "an array", "not_recommended"):
        for i, nr in enumerate(data["not_recommended"]):
            p = f"not_recommended[{i}]"
            if not isinstance(nr, dict):
                errors.append(f"{p} must be an object, got {_type_name(nr)}")
                continue
            check(nr, "name", is_str, "a string", f"{p}.name")
            check(nr, "reason", is_str, "a string", f"{p}.reason")

    # --- roadmap ---
    if check(data, "roadmap", lambda v: isinstance(v, dict), "an object", "roadmap"):
        for key in ("days_1_30", "days_31_60", "days_61_90"):
            check(data["roadmap"], key, is_str, "a string", f"roadmap.{key}")

    # --- recommended_first_build ---
    if check(data, "recommended_first_build", lambda v: isinstance(v, dict),
             "an object", "recommended_first_build"):
        fb = data["recommended_first_build"]
        check(fb, "opportunity", is_str, "a string",
              "recommended_first_build.opportunity")
        check(fb, "why", is_str, "a string", "recommended_first_build.why")
        check(fb, "price", _is_num, "a number", "recommended_first_build.price")
        check(fb, "estimated_timeline", is_str, "a string",
              "recommended_first_build.estimated_timeline")
        # cross-field: first build must name a real opportunity
        if isinstance(fb.get("opportunity"), str) and isinstance(
                data.get("opportunities"), list):
            names = {o.get("name") for o in data["opportunities"]
                     if isinstance(o, dict)}
            if fb["opportunity"] not in names:
                errors.append(
                    "recommended_first_build.opportunity "
                    f"({fb['opportunity']!r}) must match one opportunities[].name")

    return errors


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
def cover_flowables(data, sample=False):
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
    if sample:
        out.append(Paragraph(
            f"SAMPLE REPORT — {data['client_name']} is a fictional business "
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


def cta_block(data, price):
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
        Paragraph(money(price), ST["cta_price"]),
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
def build(data, out_path, price, sample=False):
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
    story += cover_flowables(data, sample=sample)

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
    if data["not_recommended"]:
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
    story.append(KeepTogether([cta_block(data, price), Spacer(1, 18), rates_note(data)]))

    doc.build(story)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate an AI Operations Audit PDF from a canonical audit JSON.")
    parser.add_argument("audit_json", help="Path to the audit JSON file.")
    parser.add_argument("--brand", default=DEFAULT_BRAND,
                        help='Brand name (default "%(default)s").')
    parser.add_argument("--out", default="report.pdf",
                        help='Output PDF path (default "%(default)s").')
    parser.add_argument("--price", type=float, default=None,
                        help="Override the fixed-price implementation quote in the CTA "
                             "box. Defaults to recommended_first_build.price, or "
                             f"{DEFAULT_PRICE} if absent.")
    parser.add_argument("--sample", action="store_true",
                        help="Render the fictional-business disclaimer on the cover "
                             "(for the demonstration sample only).")
    args = parser.parse_args(argv)

    # --- load JSON ---
    try:
        with open(args.audit_json, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        print(f"error: file not found: {args.audit_json}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        print(f"error: {args.audit_json} is not valid JSON: {e}", file=sys.stderr)
        return 2

    # --- validate against canonical schema ---
    errors = validate_audit(data)
    if errors:
        print(f"error: {args.audit_json} does not match the canonical audit schema "
              f"({len(errors)} problem(s)):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    # --- resolve brand, date, price ---
    global BRAND, REPORT_DATE
    BRAND = args.brand
    REPORT_DATE = datetime.date.today().strftime("%B %Y")

    if args.price is not None:
        price = args.price
    else:
        price = data["recommended_first_build"].get("price", DEFAULT_PRICE)

    build(data, args.out, price, sample=args.sample)

    # --- post-build integrity note (does not block; the model's guard enforces) ---
    hsum = round(sum(o["hours_saved_monthly"] for o in data["opportunities"]), 1)
    dsum = round(sum(o["dollar_value_monthly"] for o in data["opportunities"]), 1)
    print(f"Wrote {args.out}")
    print(f"  {hours(data['total_hours_saved_monthly'])} hrs/mo, "
          f"{money(data['total_dollar_value_monthly'])}/mo, "
          f"guarantee={data['meets_guarantee']}, "
          f"{len(data['opportunities'])} opportunities, first-build {money(price)}")
    if abs(hsum - data["total_hours_saved_monthly"]) >= 0.05:
        print(f"  warning: total_hours_saved_monthly ({data['total_hours_saved_monthly']}) "
              f"!= sum of opportunities ({hsum})", file=sys.stderr)
    if abs(dsum - data["total_dollar_value_monthly"]) >= 0.05:
        print(f"  warning: total_dollar_value_monthly ({data['total_dollar_value_monthly']}) "
              f"!= sum of opportunities ({dsum})", file=sys.stderr)
    if data["meets_guarantee"] != (data["total_hours_saved_monthly"] >= 10.0):
        print("  warning: meets_guarantee is inconsistent with the 10-hour floor",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
