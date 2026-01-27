import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.config import settings
import logging

logger = logging.getLogger(__name__)

class MailService:
    @staticmethod
    def _send_email(email: str, subject: str, html_content: str):
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            logger.warning(f"--- DEVELOPER MODE --- Email to {email} | Subject: {subject}")
            logger.info(f"Content Body: {html_content[:200]}...")
            return True, "Success (Developer Mode)"

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"Timesheet Manager <{settings.SYSTEM_EMAIL}>"
            msg["To"] = email
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP_SSL(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {email}")
            return True, "Success"
        except Exception as e:
            logger.error(f"Failed to send email to {email}: {str(e)}")
            return False, str(e)


    @staticmethod
    def send_timesheet_status_notification(email: str, week_start: str, action: str, reason: str = ""):
        is_approval = action.lower() == "approve"
        subject = f"Timesheet {'Approved' if is_approval else 'Status Update: Action Required'} - Week of {week_start}"
        
        status_color = "#10b981" if is_approval else "#ef4444"
        title = "Timesheet Approved" if is_approval else "Action Required"
        
        message_body = f"""
            <p>Hello, your timesheet submission for the week of <strong>{week_start}</strong> has been successfully <strong>Approved</strong>. No further action is required.</p>
            <p>Thank you for your timely submission!</p>
        """ if is_approval else f"""
            <p>Hello, your timesheet submission for the week of <strong>{week_start}</strong> has been <strong>Returned for Correction</strong>.</p>
            <div style="background: #fef2f2; border-left: 4px solid #ef4444; padding: 15px; margin: 20px 0;">
                <p style="margin: 0; font-weight: bold; color: #991b1b;">Admin Feedback:</p>
                <p style="margin: 5px 0 0 0; color: #b91c1c;">{reason}</p>
            </div>
            <p>Your timesheet has been <strong>unlocked</strong>. Please log in to your dashboard to review the feedback, make the necessary adjustments, and <strong>resubmit</strong> your hours for approval.</p>
        """

        html = f"""
        <html>
            <body style="font-family: sans-serif; color: #333;">
                <div style="max-width: 600px; margin: auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
                    <h2 style="color: {status_color};">{title}</h2>
                    {message_body}
                    <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                    <p style="font-size: 12px; color: #94a3b8; text-align: center;">Timesheet Manager App &bull; Secure Portal</p>
                </div>
            </body>
        </html>
        """
        return MailService._send_email(email, subject, html)
