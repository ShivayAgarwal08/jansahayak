import io
from datetime import datetime, timezone
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

# Custom Palette matching JanSahayak Design System
NAVY = colors.HexColor("#192A46")
GREEN = colors.HexColor("#18794E")
SAFFRON = colors.HexColor("#E9A23B")
WARM_IVORY = colors.HexColor("#FAF8F2")
LIGHT_GREY = colors.HexColor("#E2E8F0")
TEXT_MUTED = colors.HexColor("#4A5568")

def get_base_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="JanHeader",
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=NAVY,
        alignment=1  # Center
    ))
    styles.add(ParagraphStyle(
        name="JanSubHeader",
        fontName="Helvetica",
        fontSize=11,
        leading=14,
        textColor=GREEN,
        alignment=1
    ))
    styles.add(ParagraphStyle(
        name="SectionHeading",
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=NAVY,
        spaceBefore=12,
        spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        name="BodyTextCustom",
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#2D3748")
    ))
    styles.add(ParagraphStyle(
        name="BodyTextBold",
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=NAVY
    ))
    styles.add(ParagraphStyle(
        name="DisclaimerText",
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=11,
        textColor=TEXT_MUTED,
        alignment=1
    ))
    return styles

def generate_citizen_report_pdf(
    citizen_name: str,
    scheme_name: str,
    eligibility_status: str,
    summary_explanation: str,
    satisfied_conditions: list,
    unsatisfied_conditions: list,
    required_documents: list,
    official_portal_url: str
) -> bytes:
    """
    Generate a printable Citizen Welfare Summary Report for Common Service Centre (CSC) submission.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    styles = get_base_styles()
    story = []

    # Header
    story.append(Paragraph("JanSahayak (जनसहायक) Citizen Services", styles["JanHeader"]))
    story.append(Paragraph("Citizen Scheme Eligibility & Preparation Report", styles["JanSubHeader"]))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=GREEN, spaceBefore=4, spaceAfter=12))

    # Meta Table
    status_label = eligibility_status.replace("_", " ").title()
    meta_data = [
        [Paragraph("Applicant Name:", styles["BodyTextBold"]), Paragraph(citizen_name, styles["BodyTextCustom"])],
        [Paragraph("Scheme:", styles["BodyTextBold"]), Paragraph(scheme_name, styles["BodyTextCustom"])],
        [Paragraph("Eligibility Assessment:", styles["BodyTextBold"]), Paragraph(f"<b>{status_label}</b>", styles["BodyTextBold"])],
        [Paragraph("Report Generated On:", styles["BodyTextBold"]), Paragraph(datetime.now(timezone.utc).strftime("%d %B %Y, %H:%M UTC"), styles["BodyTextCustom"])],
        [Paragraph("Official Portal:", styles["BodyTextBold"]), Paragraph(official_portal_url, styles["BodyTextCustom"])]
    ]
    meta_table = Table(meta_data, colWidths=[150, 370])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFC")),
        ('BOX', (0,0), (-1,-1), 1, LIGHT_GREY),
        ('INNERGRID', (0,0), (-1,-1), 0.5, LIGHT_GREY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # Assessment Explanation
    story.append(Paragraph("Eligibility Summary", styles["SectionHeading"]))
    story.append(Paragraph(summary_explanation, styles["BodyTextCustom"]))
    story.append(Spacer(1, 10))

    # Satisfied criteria
    if satisfied_conditions:
        story.append(Paragraph("Verified Qualifying Conditions Met", styles["SectionHeading"]))
        for cond in satisfied_conditions:
            text = f"• <b>{cond.get('criterion')}:</b> {cond.get('citizen_value')} <i>(Official rule: {cond.get('official_rule')})</i>"
            story.append(Paragraph(text, styles["BodyTextCustom"]))
            story.append(Spacer(1, 4))
        story.append(Spacer(1, 8))

    # Unsatisfied / Missing
    if unsatisfied_conditions:
        story.append(Paragraph("Unsatisfied Conditions", styles["SectionHeading"]))
        for cond in unsatisfied_conditions:
            text = f"• <b>{cond.get('criterion')}:</b> {cond.get('reason', '')}"
            story.append(Paragraph(text, styles["BodyTextCustom"]))
            story.append(Spacer(1, 4))
        story.append(Spacer(1, 8))

    # Document Readiness Checklist
    if required_documents:
        story.append(Paragraph("Required Documents Checklist", styles["SectionHeading"]))
        doc_data = [["Status", "Required Document", "Accepted Alternatives"]]
        for d in required_documents:
            name = d.get("name", "")
            alts = ", ".join(d.get("alternatives", [])) or "None"
            doc_data.append(["[   ]", name, alts])
        
        doc_table = Table(doc_data, colWidths=[60, 260, 200])
        doc_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), NAVY),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, LIGHT_GREY),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(doc_table)
        story.append(Spacer(1, 16))

    # Disclaimer
    story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT_GREY, spaceBefore=10, spaceAfter=8))
    story.append(Paragraph(
        "Important Notice: JanSahayak is an independent public digital service platform. "
        "This report is generated for informational guidance and preparation assistance. "
        "Final approval and sanction of benefits rests solely with the competent government authority.",
        styles["DisclaimerText"]
    ))

    doc.build(story)
    return buffer.getvalue()

def generate_rti_petition_pdf(
    applicant_name: str,
    public_authority: str,
    subject: str,
    information_requested: str,
    time_period: str,
    state: str
) -> bytes:
    """
    Generate a formal RTI Application (under Right to Information Act, 2005) ready to print and sign.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = get_base_styles()
    story = []

    # Title
    story.append(Paragraph("APPLICATION UNDER SECTION 6(1) OF THE RIGHT TO INFORMATION ACT, 2005", styles["JanHeader"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=NAVY, spaceBefore=8, spaceAfter=14))

    # To block
    to_text = (
        "<b>To,</b><br/>"
        "The Central / State Public Information Officer (CPIO / SPIO),<br/>"
        f"<b>Department / Public Authority:</b> {public_authority}<br/>"
        f"<b>State / Location:</b> {state}<br/>"
    )
    story.append(Paragraph(to_text, styles["BodyTextCustom"]))
    story.append(Spacer(1, 14))

    # Applicant details
    applicant_text = (
        f"<b>1. Full Name of the Applicant:</b> {applicant_name}<br/>"
        f"<b>2. Nationality / Citizenship:</b> Citizen of India<br/>"
        f"<b>3. Date of Application:</b> {datetime.now(timezone.utc).strftime('%d %B %Y')}<br/>"
    )
    story.append(Paragraph(applicant_text, styles["BodyTextCustom"]))
    story.append(Spacer(1, 10))

    # Subject & Details
    story.append(Paragraph("<b>4. Particulars of Information Solicited:</b>", styles["SectionHeading"]))
    story.append(Paragraph(f"<b>Subject:</b> {subject}", styles["BodyTextBold"]))
    if time_period:
        story.append(Paragraph(f"<b>Relevant Time Period:</b> {time_period}", styles["BodyTextCustom"]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>Specific Information Sought:</b>", styles["BodyTextBold"]))
    story.append(Paragraph(information_requested.replace("\n", "<br/>"), styles["BodyTextCustom"]))
    story.append(Spacer(1, 14))

    # Legal Declarations
    declaration = (
        "<b>5. Declaration:</b><br/>"
        "I hereby declare that I am a citizen of India and the information sought falls within "
        "the purview of Section 2(f) and 2(j) of the RTI Act, 2005 and does not fall under the "
        "exemptions specified in Section 8 or 9 of the Act.<br/><br/>"
        "<b>6. Application Fee:</b><br/>"
        "I have attached / tendered the statutory application fee of Rs. 10/- as prescribed by the "
        "appropriate Government rules (via IPO / Court Fee Stamp / Online Payment receipt where applicable).<br/>"
    )
    story.append(Paragraph(declaration, styles["BodyTextCustom"]))
    story.append(Spacer(1, 30))

    # Signature Block
    sig_block = [
        ["Date: " + datetime.now(timezone.utc).strftime("%d/%m/%Y"), "___________________________________"],
        ["Place: " + state, "Signature / Thumb Impression of Applicant"]
    ]
    sig_table = Table(sig_block, colWidths=[260, 260])
    sig_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
    ]))
    story.append(sig_table)

    doc.build(story)
    return buffer.getvalue()

def generate_grievance_petition_pdf(
    applicant_name: str,
    department: str,
    category: str,
    description: str,
    previous_ref: str,
    desired_resolution: str
) -> bytes:
    """
    Generate a structured Public Grievance Petition for submission to CPGRAMS or state portals.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = get_base_styles()
    story = []

    story.append(Paragraph("PUBLIC GRIEVANCE REPRESENTATION", styles["JanHeader"]))
    story.append(Paragraph("Under Central / State Citizen Charter & Grievance Redressal Mechanism", styles["JanSubHeader"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=SAFFRON, spaceBefore=8, spaceAfter=14))

    info_data = [
        [Paragraph("Complainant Name:", styles["BodyTextBold"]), Paragraph(applicant_name, styles["BodyTextCustom"])],
        [Paragraph("Target Department:", styles["BodyTextBold"]), Paragraph(department, styles["BodyTextCustom"])],
        [Paragraph("Grievance Category:", styles["BodyTextBold"]), Paragraph(category, styles["BodyTextCustom"])],
        [Paragraph("Previous Reference / Token No:", styles["BodyTextBold"]), Paragraph(previous_ref or "None / Initial Representation", styles["BodyTextCustom"])],
        [Paragraph("Date of Representation:", styles["BodyTextBold"]), Paragraph(datetime.now(timezone.utc).strftime("%d %B %Y"), styles["BodyTextCustom"])]
    ]
    t = Table(info_data, colWidths=[160, 360])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FFFDF5")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E0")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 14))

    story.append(Paragraph("Factual Description of Grievance:", styles["SectionHeading"]))
    story.append(Paragraph(description.replace("\n", "<br/>"), styles["BodyTextCustom"]))
    story.append(Spacer(1, 14))

    story.append(Paragraph("Specific Relief / Resolution Sought:", styles["SectionHeading"]))
    story.append(Paragraph(desired_resolution.replace("\n", "<br/>"), styles["BodyTextCustom"]))
    story.append(Spacer(1, 25))

    sig_block = [
        ["Date: " + datetime.now(timezone.utc).strftime("%d/%m/%Y"), "___________________________________"],
        ["", "Signature of Complainant"]
    ]
    sig_table = Table(sig_block, colWidths=[260, 260])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
    ]))
    story.append(sig_table)

    doc.build(story)
    return buffer.getvalue()
