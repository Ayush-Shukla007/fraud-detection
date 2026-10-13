import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from config import settings

logger = logging.getLogger(__name__)

def send_high_risk_alert_email(transaction_id: str, amount: float, probability: float):
    """
    Sends an automated email notification if a transaction is high risk.
    Executed as a background task.
    """
    if not all([settings.SMTP_HOST, settings.SMTP_USER, settings.SMTP_PASSWORD, settings.ALERT_EMAIL]):
        logger.warning("Email settings not fully configured. Skipping email alert.")
        return

    try:
        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_USER
        msg['To'] = settings.ALERT_EMAIL
        msg['Subject'] = "⚠️ High Risk Transaction Detected"

        body = f"""A potentially fraudulent transaction has been detected.

Transaction Details:
--------------------
Transaction ID: {transaction_id}
Transaction Amount: ₹{amount:.2f}
Risk Score: {probability * 100:.2f}%
Status: HIGH RISK

Please review this transaction immediately in the FraudGuard AI Dashboard.
"""
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(settings.SMTP_USER, settings.ALERT_EMAIL, text)
        server.quit()
        
        logger.info(f"High risk alert email sent for transaction {transaction_id}")
    except Exception as e:
        logger.error(f"Failed to send alert email: {e}")
