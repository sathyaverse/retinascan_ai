import os
import json
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT


RISK_COLORS = {
    'No DR':            colors.HexColor('#27AE60'),
    'Mild DR':          colors.HexColor('#F39C12'),
    'Moderate DR':      colors.HexColor('#E67E22'),
    'Severe DR':        colors.HexColor('#E74C3C'),
    'Proliferative DR': colors.HexColor('#922B21'),
}

DESCRIPTIONS = {
    'No DR': 'No signs of diabetic retinopathy detected. Continue regular annual screening.',
    'Mild DR': 'Microaneurysms only. Monitor every 6–12 months.',
    'Moderate DR': 'More than microaneurysms but less than severe. Ophthalmology referral advised.',
    'Severe DR': 'Any of the following: 20+ hemorrhages in all 4 quadrants, venous beading, IRMA. Urgent referral required.',
    'Proliferative DR': 'Neovascularisation present. Immediate treatment required to prevent vision loss.',
}


def generate_pdf_report(scan, user, output_path, upload_folder):
    """
    Generate a clinical PDF report for a given scan.

    Args:
        scan: Scan model instance
        user: User model instance
        output_path: Where to save the PDF
        upload_folder: Base folder for uploaded images
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle('Title', fontSize=18, fontName='Helvetica-Bold',
                                  alignment=TA_CENTER, spaceAfter=6)
    subtitle_style = ParagraphStyle('Subtitle', fontSize=11, fontName='Helvetica',
                                     alignment=TA_CENTER, textColor=colors.grey, spaceAfter=20)
    story.append(Paragraph('RetinaScan AI', title_style))
    story.append(Paragraph('Diabetic Retinopathy Diagnostic Report', subtitle_style))
    story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#2C3E50')))
    story.append(Spacer(1, 0.4*cm))

    # Report metadata
    meta_data = [
        ['Report ID', f'RS-{scan.id:05d}', 'Date', scan.created_at.strftime('%d %B %Y')],
        ['Patient Name', user.name, 'Age', str(user.age or 'N/A')],
        ['Email', user.email, 'Eye Side', scan.eye_side],
        ['Diabetes Type', user.diabetes_type or 'N/A', 'Gender', user.gender or 'N/A'],
    ]
    meta_table = Table(meta_data, colWidths=[3.5*cm, 6*cm, 3.5*cm, 4*cm])
    meta_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8F9FA')),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.white, colors.HexColor('#F8F9FA')]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#DEE2E6')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.5*cm))

    # Diagnosis result box
    predicted = scan.predicted_class or 'Pending'
    risk_color = RISK_COLORS.get(predicted, colors.grey)
    confidence_pct = f"{round(scan.confidence * 100, 1)}%" if scan.confidence else "N/A"

    diag_data = [
        ['DIAGNOSIS', predicted],
        ['CONFIDENCE', confidence_pct],
        ['RISK LEVEL', predicted],
    ]
    diag_table = Table(diag_data, colWidths=[5*cm, 12*cm])
    diag_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 12),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#2C3E50')),
        ('TEXTCOLOR', (0,0), (0,-1), colors.white),
        ('BACKGROUND', (1,0), (1,-1), risk_color),
        ('TEXTCOLOR', (1,0), (1,-1), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('GRID', (0,0), (-1,-1), 0.5, colors.white),
    ]))
    story.append(diag_table)
    story.append(Spacer(1, 0.4*cm))

    # Description
    desc = DESCRIPTIONS.get(predicted, '')
    desc_style = ParagraphStyle('Desc', fontSize=10, fontName='Helvetica',
                                 leftIndent=10, leading=14)
    story.append(Paragraph(f'<b>Clinical Note:</b> {desc}', desc_style))
    story.append(Spacer(1, 0.5*cm))

    # Images side by side
    original_path = os.path.join(upload_folder, os.path.basename(scan.original_image))
    gradcam_path = os.path.join(upload_folder, os.path.basename(scan.gradcam_image)) if scan.gradcam_image else None

    img_row = []
    if os.path.exists(original_path):
        img_row.append(RLImage(original_path, width=7*cm, height=7*cm))
    if gradcam_path and os.path.exists(gradcam_path):
        img_row.append(RLImage(gradcam_path, width=7*cm, height=7*cm))

    if img_row:
        label_row = [Paragraph('<b>Original Fundus Image</b>', styles['Normal'])]
        if len(img_row) > 1:
            label_row.append(Paragraph('<b>Grad-CAM Heatmap</b>', styles['Normal']))
        img_table = Table([label_row, img_row], colWidths=[8.5*cm, 8.5*cm])
        img_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(img_table)
        story.append(Spacer(1, 0.5*cm))

    # 1. Multi-Disease Prediction Table
    story.append(Paragraph('<b>Multi-Disease Screening Analysis</b>', ParagraphStyle(
        'SectionHead1', fontSize=12, fontName='Helvetica-Bold', spaceAfter=6
    )))
    disease_data = [
        ['Retinal Condition', 'AI Probability', 'Risk Status'],
        ['Diabetic Retinopathy (DR)', f"{round((scan.dr_prob or 0) * 100, 1)}%", 'High Risk' if scan.is_dr else 'Low Risk'],
        ['Glaucoma', f"{round((scan.glaucoma_prob or 0) * 100, 1)}%", 'High Risk' if scan.is_glaucoma else 'Low Risk'],
        ['Age-Related Macular Degeneration (AMD)', f"{round((scan.amd_prob or 0) * 100, 1)}%", 'High Risk' if scan.is_amd else 'Low Risk'],
        ['Normal / Healthy Retina', f"{round((scan.normal_prob or 0) * 100, 1)}%", 'Normal' if scan.is_normal else 'Abnormalities Detected'],
    ]
    disease_table = Table(disease_data, colWidths=[8.5*cm, 4.0*cm, 4.5*cm])
    disease_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2C3E50')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8F9FA')]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#DEE2E6')),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(disease_table)
    story.append(Spacer(1, 0.4*cm))

    # 2. Clinical markers
    story.append(Paragraph('<b>Diabetic Retinopathy Clinical Markers</b>', ParagraphStyle(
        'SectionHead2', fontSize=12, fontName='Helvetica-Bold', spaceAfter=6
    )))
    markers = [
        ('Microaneurysms', scan.microaneurysms),
        ('Hemorrhages', scan.hemorrhages),
        ('Hard Exudates', scan.hard_exudates),
        ('Soft Exudates', scan.soft_exudates),
        ('Neovascularization', scan.neovascularization),
    ]
    marker_data = [['Marker', 'Status']] + [
        [m[0], 'Detected ✓' if m[1] else 'Not Detected'] for m in markers
    ]
    marker_table = Table(marker_data, colWidths=[9*cm, 8*cm])
    marker_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2C3E50')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8F9FA')]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#DEE2E6')),
        ('ALIGN', (1,0), (1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(marker_table)
    story.append(Spacer(1, 0.4*cm))

    # 3. Clinical insights (Recommendations, Nutrition, Tips)
    from utils.inference import get_clinical_insights
    insights = get_clinical_insights(
        scan.dr_prob or 0.0,
        scan.glaucoma_prob or 0.0,
        scan.amd_prob or 0.0,
        scan.cataract_prob or 0.0,
        scan.normal_prob or 0.0
    )

    story.append(Paragraph('<b>Clinical Insights & Guidance</b>', ParagraphStyle(
        'SectionHead3', fontSize=12, fontName='Helvetica-Bold', spaceAfter=6
    )))
    
    insight_style = ParagraphStyle('Insight', fontSize=9, fontName='Helvetica', leading=12)
    insight_data = [
        ['Medical Advice', Paragraph(insights['medical'], insight_style)],
        ['Nutritional Guidelines', Paragraph(insights['nutrition'], insight_style)],
        ['Retinal Wellness Tips', Paragraph(insights['tips'], insight_style)]
    ]
    insight_table = Table(insight_data, colWidths=[4.5*cm, 12.5*cm])
    insight_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#DEE2E6')),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#F1F3F5')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(insight_table)
    story.append(Spacer(1, 0.4*cm))

    # Admin notes
    if scan.admin_notes:
        story.append(Paragraph('<b>Ophthalmologist Notes:</b>', styles['Normal']))
        story.append(Paragraph(scan.admin_notes, desc_style))
        story.append(Spacer(1, 0.3*cm))

    # Footer
    story.append(HRFlowable(width='100%', thickness=0.5, color=colors.grey))
    
    footer_text_style = ParagraphStyle('FooterLeft', fontSize=8, textColor=colors.grey,
                                       alignment=TA_LEFT, leading=11)
    footer_p1 = Paragraph(
        '<b>Clinical Disclaimer:</b> This report is generated automatically by the RetinaScan AI screening system '
        'and is intended to assist clinicians in diagnostic validation. It does not replace a full dilated fundus exam. '
        'Please consult a qualified visual specialist for treatment planning.',
        footer_text_style
    )
    footer_p2 = Paragraph(
        f'<b>System Integrity Verification:</b> Generated on {datetime.utcnow().strftime("%d %B %Y, %H:%M UTC")}',
        footer_text_style
    )
    story.append(footer_p1)
    story.append(Spacer(1, 0.15*cm))
    story.append(footer_p2)

    doc.build(story)
    return output_path
