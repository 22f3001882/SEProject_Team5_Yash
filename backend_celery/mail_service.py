import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

SMTP_SERVER = "localhost"
SMTP_PORT = 1025
SENDER_EMAIL = 'notifications@pennywise.com'
PASSWORD = ''

def send_email(to: str, subject: str, content: str, content_type: str = 'html') -> bool:
    """
    Send email with error handling
    
    Args:
        to: Recipient email address
        subject: Email subject
        content: Email content
        content_type: 'html' or 'plain'
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        msg = MIMEMultipart()
        msg['To'] = to
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL

        msg.attach(MIMEText(content, content_type))

        with smtplib.SMTP(host=SMTP_SERVER, port=SMTP_PORT) as client:
            client.send_message(msg)
            client.quit()
        
        return True
    except Exception as e:
        print(f"Failed to send email to {to}: {str(e)}")
        return False

def send_notification_email(to: str, subject: str, template_content: str) -> bool:
    """
    Send notification email with consistent formatting
    
    Args:
        to: Recipient email address
        subject: Email subject
        template_content: HTML content for the email body
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    html_template = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f9f9f9; }}
            .footer {{ background-color: #333; color: white; padding: 10px; text-align: center; font-size: 12px; }}
            .highlight {{ background-color: #fff3cd; padding: 10px; border-radius: 5px; margin: 10px 0; }}
            .balance {{ font-size: 18px; font-weight: bold; color: #2196F3; }}
            .amount {{ color: #4CAF50; font-weight: bold; }}
            .spending {{ color: #f44336; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>💰 Kids Pocket Money Tracker</h2>
        </div>
        <div class="content">
            {template_content}
        </div>
        <div class="footer">
            <p>This is an automated message from Kids Pocket Money Tracker</p>
        </div>
    </body>
    </html>
    """
    
    return send_email(to, subject, html_template, 'html')