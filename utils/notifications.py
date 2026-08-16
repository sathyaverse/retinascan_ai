import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

def send_email_report(user_email, scan, user, results_url, pdf_path=None):
    """
    Sends an email report (both plain text and HTML versions) of the retinal scan results,
    along with the generated PDF report as an attachment.
    If SMTP credentials are not configured, falls back to logging a simulated dispatch.
    """
    subject = f"RetinaScan AI Diagnostic Report - Scan #{scan.id:05d}"
    
    # Dynamically resolve clinical insights
    from utils.inference import get_clinical_insights
    insights = get_clinical_insights(
        scan.dr_prob or 0.0,
        scan.glaucoma_prob or 0.0,
        scan.amd_prob or 0.0,
        scan.cataract_prob or 0.0,
        scan.normal_prob or 0.0
    )

    # Format clinical markers
    detected_markers = []
    if scan.microaneurysms: detected_markers.append("Microaneurysms")
    if scan.hemorrhages: detected_markers.append("Hemorrhages")
    if scan.hard_exudates: detected_markers.append("Hard Exudates")
    if scan.soft_exudates: detected_markers.append("Soft Exudates")
    if scan.neovascularization: detected_markers.append("Neovascularization")
    markers_str = ", ".join(detected_markers) if detected_markers else "None Detected"

    # Clean plain text version of the email summary
    text_content = f"""
RetinaScan AI Diagnostic Summary
=================================
Patient Name: {user.name}
Report Date: {scan.created_at.strftime('%d %b %Y, %I:%M %p')}
Eye Side: {scan.eye_side}

AI Screening Findings:
---------------------
- Diabetic Retinopathy: {scan.predicted_class} ({round((scan.dr_prob or 0.0) * 100, 1)}% Probability)
- Glaucoma Risk: {'High Risk' if scan.is_glaucoma else 'Low Risk'} ({round((scan.glaucoma_prob or 0.0) * 100, 1)}% Probability)
- AMD Risk: {'High Risk' if scan.is_amd else 'Low Risk'} ({round((scan.amd_prob or 0.0) * 100, 1)}% Probability)
- Cataract Risk: {'High Risk' if scan.is_cataract else 'Low Risk'} ({round((scan.cataract_prob or 0.0) * 100, 1)}% Probability)
- Healthy Retina: {round((scan.normal_prob or 0.0) * 100, 1)}% Probability

Clinical Markers:
-----------------
{markers_str}

Clinical Guidance & Recommendations:
-----------------------------------
- Medical Advice: {insights['medical']}
- Nutritional Guidelines: {insights['nutrition']}
- Retinal Wellness Tips: {insights['tips']}

To view the full digital report, review interactive heatmaps, or start a telemedicine consultation, please visit:
{results_url}

This is an automated report summary. Please consult your physician for final medical decisions.
"""

    # Beautiful HTML Email template
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f6fb; padding: 20px; color: #1c2130; }}
            .card {{ background: #ffffff; border-radius: 12px; padding: 25px; max-width: 600px; margin: 0 auto; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border-top: 5px solid #1a73e8; }}
            .header {{ text-align: center; border-bottom: 1px solid #e5e7eb; padding-bottom: 15px; margin-bottom: 20px; }}
            .logo {{ font-size: 24px; font-weight: bold; color: #1a73e8; }}
            .title {{ font-size: 18px; margin-top: 5px; color: #6b7280; }}
            .section {{ margin-bottom: 20px; }}
            .section-title {{ font-weight: bold; color: #1a73e8; margin-bottom: 8px; font-size: 14px; text-transform: uppercase; }}
            .meta-table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; }}
            .meta-table td {{ padding: 8px; border-bottom: 1px solid #f0f0f0; font-size: 14px; }}
            .meta-table td.label {{ font-weight: bold; color: #6b7280; width: 35%; }}
            .badge {{ display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; }}
            .badge-success {{ background: #dcfce7; color: #166534; }}
            .badge-warning {{ background: #fef3c7; color: #92400e; }}
            .badge-danger {{ background: #fee2e2; color: #991b1b; }}
            .btn {{ display: inline-block; background-color: #1a73e8; color: #ffffff !important; padding: 10px 20px; border-radius: 6px; text-decoration: none; font-size: 14px; font-weight: bold; margin-top: 15px; text-align: center; }}
            .btn:hover {{ background-color: #1557b0; }}
            .footer {{ text-align: center; font-size: 11px; color: #9ca3af; margin-top: 30px; border-top: 1px solid #e5e7eb; padding-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="header">
                <div class="logo">👁 RetinaScan AI</div>
                <div class="title">Clinical AI Diagnostic Summary</div>
            </div>
            
            <div class="section">
                <div class="section-title">Patient Information</div>
                <table class="meta-table">
                    <tr><td class="label">Patient Name</td><td>{user.name}</td></tr>
                    <tr><td class="label">Report Date</td><td>{scan.created_at.strftime('%d %b %Y, %I:%M %p')}</td></tr>
                    <tr><td class="label">Eye Side</td><td>{scan.eye_side}</td></tr>
                </table>
            </div>
 
            <div class="section">
                <div class="section-title">AI Screening Findings</div>
                <table class="meta-table">
                    <tr><td class="label">Diabetic Retinopathy</td><td>{scan.predicted_class} ({round((scan.dr_prob or 0.0) * 100, 1)}% Probability)</td></tr>
                    <tr><td class="label">Glaucoma Risk</td><td>{'High Risk' if scan.is_glaucoma else 'Low Risk'} ({round((scan.glaucoma_prob or 0.0) * 100, 1)}% Probability)</td></tr>
                    <tr><td class="label">AMD Risk</td><td>{'High Risk' if scan.is_amd else 'Low Risk'} ({round((scan.amd_prob or 0.0) * 100, 1)}% Probability)</td></tr>
                    <tr><td class="label">Cataract Risk</td><td>{'High Risk' if scan.is_cataract else 'Low Risk'} ({round((scan.cataract_prob or 0.0) * 100, 1)}% Probability)</td></tr>
                    <tr><td class="label">Healthy Retina</td><td>{round((scan.normal_prob or 0.0) * 100, 1)}% Probability</td></tr>
                </table>
            </div>

            <div class="section">
                <div class="section-title">Clinical Markers Detected</div>
                <table class="meta-table">
                    <tr><td class="label">Markers</td><td>{markers_str}</td></tr>
                </table>
            </div>

            <div class="section">
                <div class="section-title">Clinical Guidance & Insights</div>
                <table class="meta-table">
                    <tr><td class="label">Medical Advice</td><td>{insights['medical']}</td></tr>
                    <tr><td class="label">Nutrition</td><td>{insights['nutrition']}</td></tr>
                    <tr><td class="label">Wellness Tips</td><td>{insights['tips']}</td></tr>
                </table>
            </div>
 
            <div class="section" style="text-align: center;">
                <p style="font-size: 14px;">To view the full digital report, review interactive heatmaps, or start a telemedicine consultation with an ophthalmologist, please click below:</p>
                <a href="{results_url}" class="btn">Access Patient Portal</a>
            </div>
 
            <div class="footer">
                This is an automated report summary. Please consult your physician for final medical decisions.<br/>
                &copy; 2024 RetinaScan AI Clinical Systems.
            </div>
        </div>
    </body>
    </html>
    """

    # Check if PDF path is missing or does not exist and auto-generate if possible
    if not pdf_path or not os.path.exists(pdf_path):
        try:
            from utils.pdf_report import generate_pdf_report
            reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')
            os.makedirs(reports_dir, exist_ok=True)
            pdf_filename = f"report_{scan.id}.pdf"
            generated_path = os.path.join(reports_dir, pdf_filename)
            upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads')
            
            generate_pdf_report(scan, user, generated_path, upload_dir)
            pdf_path = generated_path
            
            # Save the newly generated PDF path to the scan in DB if in Flask application context
            from flask import current_app
            if current_app:
                scan.report_path = pdf_filename
                from models import db
                db.session.commit()
            print(f"[Email Dispatch] Auto-generated PDF on the fly: {pdf_path}")
        except Exception as pdf_gen_err:
            print(f"[Email Dispatch] Failed to auto-generate PDF report on the fly: {pdf_gen_err}")
 
    # Read SMTP Config
    smtp_server = os.environ.get('SMTP_SERVER')
    smtp_port = os.environ.get('SMTP_PORT', 587)
    smtp_user = os.environ.get('SMTP_USER')
    smtp_password = os.environ.get('SMTP_PASSWORD')
 
    if smtp_server and smtp_user and smtp_password:
        try:
            print(f"[Email Dispatch] Connecting to SMTP server {smtp_server}:{smtp_port}...")
            # Outer mixed container for attachments
            msg = MIMEMultipart('mixed')
            msg['Subject'] = subject
            msg['From'] = smtp_user
            msg['To'] = user_email
            
            # Inner alternative container for text/HTML email bodies
            body_container = MIMEMultipart('alternative')
            
            part_text = MIMEText(text_content, 'plain')
            part_html = MIMEText(html_content, 'html')
            
            body_container.attach(part_text)
            body_container.attach(part_html)
            msg.attach(body_container)
            
            if pdf_path and os.path.exists(pdf_path):
                try:
                    with open(pdf_path, 'rb') as f:
                        part_pdf = MIMEBase('application', 'octet-stream')
                        part_pdf.set_payload(f.read())
                        encoders.encode_base64(part_pdf)
                        part_pdf.add_header(
                            'Content-Disposition',
                            f'attachment; filename="{os.path.basename(pdf_path)}"'
                        )
                        msg.attach(part_pdf)
                    print(f"[Email Dispatch] Attached PDF: {pdf_path}")
                except Exception as attachment_err:
                    print(f"[Email Dispatch] Failed to attach PDF: {attachment_err}")
            
            # Attach text report summary as a .txt file attachment
            try:
                part_txt_file = MIMEText(text_content, 'plain', 'utf-8')
                part_txt_file.add_header(
                    'Content-Disposition',
                    f'attachment; filename="report_{scan.id}.txt"'
                )
                msg.attach(part_txt_file)
                print(f"[Email Dispatch] Attached text summary: report_{scan.id}.txt")
            except Exception as txt_attachment_err:
                print(f"[Email Dispatch] Failed to attach text summary: {txt_attachment_err}")
            
            with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, user_email, msg.as_string())
            
            print(f"[Email Dispatch] Report email successfully dispatched to {user_email} via SMTP.")
            return True
        except Exception as e:
            print(f"[Email Dispatch] SMTP error: {e}. Falling back to simulation.")
    
    # Fallback / Simulation logging
    print("\n" + "="*80)
    print(f"[SIMULATED EMAIL DISPATCH] To: {user_email}")
    print(f"Subject: {subject}")
    
    attachments = []
    if pdf_path and os.path.exists(pdf_path):
        attachments.append(f"{os.path.basename(pdf_path)} (PDF Report)")
    else:
        attachments.append("None (PDF Report generation failed)")
    attachments.append(f"report_{scan.id}.txt (Text Summary)")
    print(f"Attachments: {', '.join(attachments)}")
    
    print("--------------------------------------------------------------------------------")
    print("Email Summary (Plain Text):")
    print(text_content.strip())
    print("--------------------------------------------------------------------------------")
    print("Email Body (HTML Content):")
    print(html_content.strip())
    print("="*80 + "\n")
    return True


def send_sms_report(phone_number, scan, results_url):
    """
    Sends an SMS report to the patient.
    1. Attempts Twilio SMS (if TWILIO credentials are configured in .env).
    2. Attempts Textbelt SMS (if Twilio is not configured).
    3. Falls back to simulated print logging.
    """
    import urllib.request
    import urllib.parse
    import json
    import base64

    severity_note = scan.predicted_class
    if scan.is_glaucoma:
        severity_note += " & Glaucoma Detected"
    elif scan.is_amd:
        severity_note += " & Macular Degeneration Detected"

    sms_body = (
        f"RetinaScan AI: Hello, your screening report #{scan.id:05d} has been processed.\n"
        f"Diagnosis: {severity_note}\n"
        f"View report & book consultation: {results_url}"
    )

    twilio_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    twilio_token = os.environ.get('TWILIO_AUTH_TOKEN')
    twilio_number = os.environ.get('TWILIO_PHONE_NUMBER')

    # 1. Try Twilio
    if twilio_sid and twilio_token and twilio_number:
        try:
            print(f"[SMS Dispatch] Transmitting via Twilio API to {phone_number}...")
            url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json"
            
            data = urllib.parse.urlencode({
                'To': phone_number,
                'From': twilio_number,
                'Body': sms_body
            }).encode('utf-8')
            
            req = urllib.request.Request(url, data=data)
            auth_str = f"{twilio_sid}:{twilio_token}"
            auth_b64 = base64.b64encode(auth_str.encode('utf-8')).decode('utf-8')
            req.add_header("Authorization", f"Basic {auth_b64}")
            
            with urllib.request.urlopen(req, timeout=8) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                if res_data.get('sid'):
                    print(f"[SMS Dispatch] Twilio message successfully sent. SID: {res_data.get('sid')}")
                    return True
                else:
                    print(f"[SMS Dispatch] Twilio API error: {res_data.get('error_message')}. Trying Textbelt...")
        except Exception as e:
            print(f"[SMS Dispatch] Twilio failed: {e}. Trying Textbelt...")

    # 2. Try Textbelt
    textbelt_key = os.environ.get('TEXTBELT_API_KEY', 'textbelt')
    try:
        print(f"[SMS Dispatch] Transmitting via Textbelt API to {phone_number}...")
        data = urllib.parse.urlencode({
            'phone': phone_number,
            'message': sms_body,
            'key': textbelt_key
        }).encode('utf-8')
        
        req = urllib.request.Request('https://textbelt.com/text', data=data)
        with urllib.request.urlopen(req, timeout=8) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            if res_data.get('success'):
                print(f"[SMS Dispatch] SMS successfully sent via Textbelt.")
                return True
            else:
                print(f"[SMS Dispatch] Textbelt API error: {res_data.get('error')}. Falling back to simulation.")
    except Exception as e:
        print(f"[SMS Dispatch] Textbelt connection failed: {e}. Falling back to simulation.")

    # 3. Fallback / Simulation logging
    print("\n" + "="*80)
    print(f"[SIMULATED SMS DISPATCH] To: {phone_number}")
    print(f"Message Content: {sms_body}")
    print("="*80 + "\n")
    return True
