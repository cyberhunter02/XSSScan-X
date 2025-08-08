from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                PageBreak, Image, HRFlowable, BaseDocTemplate, Frame, PageTemplate)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.lib import colors
from datetime import datetime
import os
import html

# --- Helper function for drawing footer on each page ---
def draw_footer(canvas, doc):
    """Draws a footer with page number and company name on each page."""
    canvas.saveState()
    canvas.setFont('Helvetica-Bold', 10)
    canvas.setFillColor(colors.HexColor('#1E2A53'))
    footer_text = f"Page {doc.page} | {doc.company_name} Security Report | Generated: {doc.generation_date}"
    canvas.drawCentredString(A4[0] / 2.0, 30, footer_text)
    canvas.restoreState()

def create_pdf_report(results, company_name, folder="reports", target_url="N/A"):
    """
    Generates a professional and attractive PDF report with detailed test results.
    """
    os.makedirs(folder, exist_ok=True)
    file_name = f"Security_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = os.path.join(folder, file_name)

    # --- Document Setup with Header/Footer ---
    doc = BaseDocTemplate(file_path, pagesize=A4,
                            leftMargin=54, rightMargin=54,
                            topMargin=72, bottomMargin=72)
    
    doc.company_name = company_name
    doc.generation_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    main_frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='main_frame')
    
    main_template = PageTemplate(id='main_template', frames=[main_frame], onPage=draw_footer)
    doc.addPageTemplates([main_template])
    
    story = []

    # --- Professional Styles ---
    PRIMARY_COLOR = colors.HexColor('#1E2A53')
    SECONDARY_COLOR = colors.HexColor('#3D52A0')
    ACCENT_COLOR = colors.HexColor('#4ECDC4')
    DANGER_COLOR = colors.HexColor('#E74C3C')
    SUCCESS_COLOR = colors.HexColor('#2ECC71')
    TEXT_COLOR = colors.HexColor('#333333')
    LIGHT_GREY = colors.HexColor('#F5F5F5')
    WHITE = colors.HexColor('#FFFFFF')

    styles = getSampleStyleSheet()
    
    cover_title_style = ParagraphStyle('CoverTitle', parent=styles['Heading1'],
                                     fontName='Helvetica-Bold', fontSize=28,
                                     textColor=PRIMARY_COLOR, alignment=TA_CENTER,
                                     spaceAfter=12, leading=36)
    
    cover_subtitle_style = ParagraphStyle('CoverSubtitle', parent=styles['Heading2'],
                                         fontName='Helvetica', fontSize=18,
                                         textColor=SECONDARY_COLOR, alignment=TA_CENTER,
                                         spaceAfter=36, leading=24)
    
    h1_style = ParagraphStyle('H1', parent=styles['Heading1'], fontName='Helvetica-Bold',
                              fontSize=20, textColor=PRIMARY_COLOR, alignment=TA_LEFT,
                              spaceBefore=20, spaceAfter=12, leading=24)
    
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontName='Helvetica',
                                fontSize=12, textColor=TEXT_COLOR, alignment=TA_JUSTIFY,
                                leading=16, spaceAfter=12)
    
    code_style = ParagraphStyle('Code', parent=body_style, fontName='Courier',
                                fontSize=10, backColor=LIGHT_GREY, textColor=colors.black,
                                leading=14, borderPadding=8, leftIndent=12, rightIndent=12)
    
    footer_style = ParagraphStyle('Footer', parent=body_style, alignment=TA_CENTER,
                                  textColor=PRIMARY_COLOR, fontSize=10, fontName='Helvetica-Bold')
    
    signature_style = ParagraphStyle('Signature', parent=body_style, alignment=TA_LEFT,
                                    fontName='Helvetica', spaceBefore=6, fontSize=11, leftIndent=12)

    # --- Cover Page ---
    try:
        logo_path = os.path.join("static", "images", "logo.png")
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=150, height=150)
            logo.hAlign = 'CENTER'
            story.append(logo)
            story.append(Spacer(1, 36))
    except Exception as e:
        print(f"Error adding logo to PDF: {e}")
        pass
    
    story.append(HRFlowable(width="60%", thickness=2, color=ACCENT_COLOR, spaceBefore=0, spaceAfter=24, hAlign='CENTER'))
    story.append(Paragraph(company_name.upper(), cover_title_style))
    story.append(Paragraph("SECURITY VULNERABILITY ASSESSMENT REPORT", cover_subtitle_style))
    story.append(HRFlowable(width="60%", thickness=2, color=ACCENT_COLOR, spaceBefore=24, spaceAfter=36, hAlign='CENTER'))
    story.append(Paragraph("<b>TARGET OF EVALUATION:</b>", body_style))
    story.append(Paragraph(f"<font color='{PRIMARY_COLOR.hexval()}'><b>{html.escape(target_url)}</b></font>",
                            ParagraphStyle('Target', parent=body_style, fontSize=14, spaceAfter=24)))
    story.append(Paragraph("<b>REPORT DATE:</b>", body_style))
    story.append(Paragraph(f"<font color='{PRIMARY_COLOR.hexval()}'><b>{datetime.now().strftime('%d %B %Y')}</b></font>",
                            ParagraphStyle('Date', parent=body_style, fontSize=14)))
    
    story.append(PageBreak())

    # --- Executive Summary Section ---
    story.append(Paragraph("1. EXECUTIVE SUMMARY", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT_COLOR, spaceAfter=16))
    
    vulnerable_findings = [r for r in results if r['vulnerable']]
    safe_findings = [r for r in results if not r['vulnerable']]

    summary_intro = f"""
    This report presents the findings of a comprehensive security assessment conducted on the target application:
    <font color="{PRIMARY_COLOR.hexval()}"><b>{html.escape(target_url)}</b></font>. The assessment focused on identifying
    Cross-Site Scripting (XSS) vulnerabilities through systematic testing with various payloads.
    <br/><br/>
    A total of <font color="{PRIMARY_COLOR.hexval()}"><b>{len(results)}</b></font> test cases were executed
    against the application, with the following results:
    """
    story.append(Paragraph(summary_intro, body_style))
    story.append(Spacer(1, 16))

    summary_data = [
        ['FINDING CATEGORY', 'COUNT', 'SEVERITY LEVEL'],
        [
            'VULNERABILITIES IDENTIFIED',
            Paragraph(f'<font color="{DANGER_COLOR.hexval()}" size="14"><b>{len(vulnerable_findings)}</b></font>', styles['Normal']),
            Paragraph(f'<font color="{DANGER_COLOR.hexval()}">HIGH RISK</font>', styles['Normal'])
        ],
        [
            'SECURE CHECKS',
            Paragraph(f'<font color="{SUCCESS_COLOR.hexval()}" size="14"><b>{len(safe_findings)}</b></font>', styles['Normal']),
            'LOW RISK'
        ],
        [
            'TOTAL TESTS EXECUTED',
            Paragraph(f'<font color="{PRIMARY_COLOR.hexval()}"><b>{len(results)}</b></font>', styles['Normal']),
            'N/A'
        ]
    ]
    
    summary_table = Table(summary_data, colWidths=[200, 100, 120])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 11),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), WHITE),
        ('GRID', (0,0), (-1,-1), 1, colors.lightgrey),
        ('FONTSIZE', (0,1), (-1,-1), 11),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 24))

    story.append(Paragraph("<b>KEY OBSERVATIONS:</b>", body_style))
    observations = [
        f"• {len(vulnerable_findings)} out of {len(results)} test cases ({len(vulnerable_findings)/len(results)*100:.1f}%) resulted in potential vulnerabilities",
        "• The most common vulnerability type identified was Cross-Site Scripting (XSS)",
        "• Immediate remediation is recommended for all identified vulnerabilities",
        "• Regular security testing should be implemented as part of the development lifecycle"
    ]
    
    for obs in observations:
        story.append(Paragraph(obs, ParagraphStyle('Bullet', parent=body_style, leftIndent=18, bulletIndent=0, spaceAfter=6)))
    
    story.append(Spacer(1, 24))

    # --- Vulnerability Details Section ---
    story.append(Paragraph("2. VULNERABILITY DETAILS", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT_COLOR, spaceAfter=16))

    if vulnerable_findings:
        for i, r in enumerate(vulnerable_findings):
            vuln_header = [
                [
                    Paragraph(
                        f'<font color="{WHITE.hexval()}">VULNERABILITY {i+1}: {html.escape(r.get("type", "N/A").upper())}</font>',
                        ParagraphStyle('VulnHeader', parent=body_style, fontName='Helvetica-Bold', fontSize=12, textColor=WHITE)
                    )
                ]
            ]
            
            header_table = Table(vuln_header, colWidths=[doc.width])
            header_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), DANGER_COLOR),
                ('BOX', (0,0), (-1,0), 1, DANGER_COLOR),
                ('VALIGN', (0,0), (-1,0), 'MIDDLE'),
                ('ALIGN', (0,0), (-1,0), 'LEFT'),
                ('LEFTPADDING', (0,0), (-1,0), 10),
                ('RIGHTPADDING', (0,0), (-1,0), 10),
            ]))
            story.append(header_table)
            story.append(Spacer(1, 12))
            
            vuln_data = [
                ['<b>Category</b>', 'Cross-Site Scripting (XSS)'],
                ['<b>HTTP Status</b>', str(r.get('status_code', 'N/A'))],
                ['<b>Tested URL</b>', Paragraph(f'<font name="Courier-Bold">{html.escape(r.get("url_tested", ""))}</font>', styles['Normal'])],
                ['<b>Payload Used</b>', Paragraph(f'<font name="Courier-Bold">{html.escape(r.get("payload", ""))}</font>', styles['Normal'])],
                ['<b>Impact</b>', Paragraph('''
                    Successful exploitation of this vulnerability could allow an attacker to:
                    <br/>• Execute malicious scripts in the victim's browser context
                    <br/>• Steal sensitive information (session tokens, cookies)
                    <br/>• Perform actions on behalf of the victim
                    <br/>• Deface the website or redirect users
                    ''', body_style)],
                ['<b>Remediation</b>', Paragraph('''
                    Recommended mitigation steps:
                    <br/>• Implement strict input validation for all user-supplied data
                    <br/>• Use context-aware output encoding
                    <br/>• Employ Content Security Policy (CSP) headers
                    <br/>• Consider using modern frameworks that automatically escape XSS by design
                    ''', body_style)],
                ['<b>Response Snippet</b>', Paragraph(f"<pre>{html.escape(r.get('response_text', 'No response'))[:500]}...</pre>", code_style)]
            ]
            
            vuln_table = Table(vuln_data, colWidths=[120, 380])
            vuln_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('ALIGN', (0,0), (0,-1), 'RIGHT'),
                ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 11),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('LEFTPADDING', (1,0), (1,-1), 6),
                ('RIGHTPADDING', (1,0), (1,-1), 6),
            ]))
            story.append(vuln_table)
            story.append(Spacer(1, 24))
    else:
        story.append(Paragraph("No XSS vulnerabilities were identified with the tested payloads. The application appears to be secure against these specific tests.", body_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph("While no vulnerabilities were detected, it's important to note that:", body_style))
        story.append(Paragraph("• Automated tools cannot guarantee complete coverage of all possible vulnerabilities", body_style))
        story.append(Paragraph("• Regular security testing should still be part of your development lifecycle", body_style))
        story.append(Paragraph("• Defense-in-depth measures like CSP should still be implemented", body_style))
        story.append(Spacer(1, 24))

    # --- Secure Test Cases Section ---
    if safe_findings:
        story.append(Paragraph("3. SECURE TEST CASES", h1_style))
        story.append(HRFlowable(width="100%", thickness=1, color=ACCENT_COLOR, spaceAfter=16))
        
        story.append(Paragraph(f"The following {len(safe_findings)} test cases did not result in vulnerabilities:", body_style))
        story.append(Spacer(1, 12))

        table_data = [["<b>Payload</b>", "<b>Status</b>", "<b>Tested URL</b>"]]
        
        for r in safe_findings:
            safe_payload = html.escape(r.get('payload', ''))
            safe_url = html.escape(r.get('url_tested', ''))
            
            table_data.append([
                Paragraph(f"<font name='Courier-Bold' size='10'>{safe_payload}</font>", styles['Normal']),
                Paragraph(f"<font color='{SUCCESS_COLOR.hexval()}'><b>SECURE</b></font>", styles['Normal']),
                Paragraph(f"<font name='Courier' size='10'>{safe_url}</font>", styles['Normal']),
            ])
        
        safe_table = Table(table_data, colWidths=[200, 80, 220], repeatRows=1)
        safe_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), PRIMARY_COLOR),
            ('TEXTCOLOR', (0,0), (-1,0), WHITE),
            ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('ALIGN', (1,1), (1,-1), 'CENTER'),
            ('BACKGROUND', (0,1), (-1,-1), WHITE),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LIGHT_GREY]),
        ]))
        story.append(safe_table)
        story.append(Spacer(1, 24))

    # --- Final Page (Disclaimer & Signature) ---
    story.append(PageBreak())
    story.append(Paragraph("4. REPORT VALIDATION & DISCLAIMER", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT_COLOR, spaceAfter=16))
    
    disclaimer_text = """
    This report is generated by an automated security scanning tool. The findings are based on a predefined set of tests and are intended to provide a high-level overview of potential vulnerabilities. It is crucial to note that this automated assessment is not a substitute for a comprehensive manual penetration test. Findings should be manually verified, and regular security assessments are recommended as part of a robust security posture.
    """
    story.append(Paragraph(disclaimer_text, body_style))
    story.append(Spacer(1, 36))
    
    # Signature section for a clean, professional look
    # Using a table with a blank cell to create a "line" under the text.
    signature_data = [
        [Paragraph("<b>Signature:</b>", styles['Normal']), Paragraph("", styles['Normal'])],
        [Paragraph("<b>Name:</b>", styles['Normal']), Paragraph("", styles['Normal'])],
        [Paragraph("<b>Position:</b> (Optional)", styles['Normal']), Paragraph("", styles['Normal'])]
    ]

    signature_table = Table(signature_data, colWidths=[100, doc.width - 100])
    signature_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('LINEBELOW', (1,0), (1,0), 0.5, colors.black),
        ('LINEBELOW', (1,1), (1,1), 0.5, colors.black),
        ('LINEBELOW', (1,2), (1,2), 0.5, colors.black),
        ('BOTTOMPADDING', (0,0), (-1,-1), 18),
    ]))
    
    story.append(signature_table)
    story.append(Spacer(1, 24))
    
    # Final date
    story.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%d %B %Y')}", signature_style))

    doc.build(story)
    return file_path
