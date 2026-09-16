import os
import smtplib
import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger("it_support_mailer")
logging.basicConfig(level=logging.INFO)

LOG_FILE = Path(__file__).resolve().parent / "email_notifications.log"


def get_smtp_config():
    dotenv_path = Path(__file__).resolve().parent / ".env"
    if dotenv_path.is_file():
        load_dotenv(dotenv_path=dotenv_path, override=True)

    raw_password = os.getenv("SMTP_PASSWORD", "").strip()
    clean_password = raw_password.replace(" ", "")

    raw_port = os.getenv("SMTP_PORT", "587")
    try:
        port = int(raw_port.strip()) if raw_port and raw_port.strip().isdigit() else 587
    except Exception:
        port = 587

    return {
        "host": os.getenv("SMTP_HOST", "").strip(),
        "port": port,
        "user": os.getenv("SMTP_USER", "").strip(),
        "password": clean_password,
        "from_email": os.getenv("SMTP_FROM_EMAIL", "").strip() or os.getenv("SMTP_USER", "").strip() or "support@itsupport.local",
        "from_name": os.getenv("SMTP_FROM_NAME", "IT Support Desk").strip(),
        "use_tls": os.getenv("SMTP_USE_TLS", "true").lower() in ("true", "1", "yes"),
    }



def record_email_log(to_email: str, subject: str, text_body: str, recipient_type: str = "USER", status: str = "SIMULATED / LOGGED"):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    log_entry = (
        f"================================================================================\n"
        f"TIMESTAMP:      {timestamp}\n"
        f"RECIPIENT TYPE: {recipient_type}\n"
        f"STATUS:         {status}\n"
        f"TO:             {to_email}\n"
        f"SUBJECT:        {subject}\n"
        f"--------------------------------------------------------------------------------\n"
        f"{text_body}\n"
        f"================================================================================\n\n"
    )
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        logger.error(f"Failed to write to email log file: {e}")


def send_email(to_email: str, subject: str, html_body: str, text_body: str, recipient_type: str = "USER") -> bool:
    """
    Sends an email using configured SMTP credentials.
    If SMTP credentials are not configured or connection fails, records email to local log.
    """
    config = get_smtp_config()

    # Check if SMTP is configured
    if not config["host"] or not config["user"] or not config["password"]:
        logger.info(f"[EMAIL NOTIFICATION - {recipient_type}] SMTP credentials not set. Logging email to {LOG_FILE.name}")
        record_email_log(to_email, subject, text_body, recipient_type=recipient_type, status="SIMULATED (SMTP credentials not configured in .env)")
        return True

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{config['from_name']} <{config['from_email']}>"
    msg["To"] = to_email

    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        if config["port"] == 465:
            server = smtplib.SMTP_SSL(config["host"], config["port"], timeout=10)
        else:
            server = smtplib.SMTP(config["host"], config["port"], timeout=10)
            if config["use_tls"]:
                server.starttls()

        server.login(config["user"], config["password"])
        server.send_message(msg)
        server.quit()

        logger.info(f"[EMAIL NOTIFICATION - {recipient_type}] Successfully sent email to {to_email} with subject: '{subject}'")
        record_email_log(to_email, subject, text_body, recipient_type=recipient_type, status="DELIVERED VIA SMTP")
        return True

    except Exception as e:
        logger.error(f"[EMAIL NOTIFICATION - {recipient_type}] Failed to deliver email via SMTP: {e}")
        record_email_log(to_email, subject, f"[ERROR: {e}]\n\n{text_body}", recipient_type=recipient_type, status="FAILED TO DELIVER (Fallback logged)")
        return False


def get_status_color(status: str) -> str:
    status_lower = status.lower()
    if "open" in status_lower:
        return "#2563eb"
    elif "progress" in status_lower:
        return "#d97706"
    elif "resolved" in status_lower:
        return "#16a34a"
    elif "closed" in status_lower:
        return "#475569"
    return "#6b7280"


# ==============================================================================
# WELCOME / SIGNUP EMAIL
# ==============================================================================

def send_welcome_signup_email(user_name: str, user_email: str):
    """Notification sent to an employee when they create a new account."""
    subject = "[CollarCheck IT Support] Welcome to the IT Support Portal"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 24px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.06); }}
        .header {{ background: #2563eb; color: #ffffff; padding: 24px 32px; }}
        .content {{ padding: 32px; color: #1e293b; }}
        .footer {{ padding: 20px 32px; background: #f8fafc; border-top: 1px solid #e2e8f0; text-align: center; font-size: 13px; color: #94a3b8; }}
        .button {{ display: inline-block; padding: 12px 24px; background: #2563eb; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; margin-top: 20px; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h2 style="margin: 0; font-size: 20px; color: #ffffff;">Welcome to IT Support Portal</h2>
        </div>
        <div class="content">
          <p style="font-size: 16px; margin-top: 0;">Hello <strong>{user_name}</strong>,</p>
          <p style="color: #475569; font-size: 15px; line-height: 1.5;">
            Your account has been created successfully on the <strong>IT Support Portal</strong> with the email: <strong>{user_email}</strong>.
          </p>
          <p style="color: #475569; font-size: 15px; line-height: 1.5;">
            Whenever you encounter hardware, software, or network issues, you can log in to submit a ticket. You will receive email notifications at every step of your ticket resolution.
          </p>
          <div style="text-align: center; margin-top: 25px;">
            <a href="http://localhost:3000" class="button" style="color: #ffffff;">Open IT Support Portal</a>
          </div>
        </div>
        <div class="footer">
          CollarCheck IT Support Ticketing System
        </div>
      </div>
    </body>
    </html>
    """

    text_content = f"""
Welcome to IT Support Portal
--------------------------------------------------
Hello {user_name},

Your account has been created successfully with email: {user_email}.
You can log in at http://localhost:3000 to submit IT support tickets and track their status.

IT Support Helpdesk
"""
    return send_email(user_email, subject, html_content, text_content, recipient_type="USER")


# ==============================================================================
# USER TICKET NOTIFICATIONS
# ==============================================================================

def send_ticket_created_email(
    ticket_id: int,
    user_name: str,
    user_email: str,
    company: str,
    issue_type: str,
    location: str,
    issue: str
):
    """Notification sent to the User when they submit a new ticket."""
    subject = f"[IT Support Ticket #{ticket_id}] Ticket Created Successfully"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 24px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.06); }}
        .header {{ background: #2563eb; color: #ffffff; padding: 24px 32px; }}
        .content {{ padding: 32px; color: #1e293b; }}
        .ticket-info {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .ticket-info td {{ padding: 10px 14px; border-bottom: 1px solid #f1f5f9; font-size: 14px; }}
        .ticket-info td.label {{ color: #64748b; font-weight: 600; width: 35%; }}
        .ticket-info td.value {{ color: #0f172a; font-weight: 500; }}
        .footer {{ padding: 20px 32px; background: #f8fafc; border-top: 1px solid #e2e8f0; text-align: center; font-size: 13px; color: #94a3b8; }}
        .button {{ display: inline-block; padding: 12px 24px; background: #2563eb; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; margin-top: 20px; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h2 style="margin: 0; font-size: 20px; color: #ffffff;">Ticket Received</h2>
          <span style="font-size: 14px; opacity: 0.9;">Token #{ticket_id}</span>
        </div>
        <div class="content">
          <p style="font-size: 16px; margin-top: 0;">Hello <strong>{user_name}</strong>,</p>
          <p style="color: #475569; font-size: 15px; line-height: 1.5;">
            Your IT support request has been logged successfully with Token ID <strong>#{ticket_id}</strong>.
            Our technical support team will attend to it shortly.
          </p>

          <table class="ticket-info">
            <tr>
              <td class="label">Token ID:</td>
              <td class="value">#{ticket_id}</td>
            </tr>
            <tr>
              <td class="label">Initial Status:</td>
              <td class="value"><span style="background: #e0f2fe; color: #0369a1; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 12px;">OPEN</span></td>
            </tr>
            <tr>
              <td class="label">Company:</td>
              <td class="value">{company}</td>
            </tr>
            <tr>
              <td class="label">Issue Type:</td>
              <td class="value">{issue_type}</td>
            </tr>
            <tr>
              <td class="label">Location / Floor:</td>
              <td class="value">{location}</td>
            </tr>
            <tr>
              <td class="label">Issue:</td>
              <td class="value">{issue}</td>
            </tr>
          </table>

          <div style="text-align: center; margin-top: 25px;">
            <a href="http://localhost:3000" class="button" style="color: #ffffff;">Check Ticket Status</a>
          </div>
        </div>
        <div class="footer">
          This is an automated notification from your IT Support Ticketing System.
        </div>
      </div>
    </body>
    </html>
    """

    text_content = f"""
IT Support Ticket Created
--------------------------------------------------
Hello {user_name},

Your IT support ticket #{ticket_id} has been logged successfully with status 'Open'.

Ticket Details:
  Token ID:     #{ticket_id}
  Status:       Open
  Company:      {company}
  Issue Type:   {issue_type}
  Location:     {location}
  Issue:        {issue}

Track status at: http://localhost:3000
--------------------------------------------------
"""
    return send_email(user_email, subject, html_content, text_content, recipient_type="USER")


def send_ticket_status_email(
    ticket_id: int,
    user_name: str,
    user_email: str,
    company: str,
    issue_type: str,
    location: str,
    issue: str,
    old_status: str,
    new_status: str,
    remarks: str | None = None
):
    """Notification sent to the User when their ticket status or remarks change."""
    subject = f"[IT Support Ticket #{ticket_id}] Status Updated to: {new_status}"
    status_color = get_status_color(new_status)
    old_color = get_status_color(old_status)
    remarks_section_html = ""
    remarks_section_text = ""

    if remarks:
        remarks_section_html = f"""
        <div style="margin-top: 20px; padding: 14px 18px; background-color: #f8fafc; border-left: 4px solid #3b82f6; border-radius: 6px;">
            <p style="margin: 0 0 6px 0; font-size: 13px; font-weight: bold; color: #1e293b; text-transform: uppercase; letter-spacing: 0.5px;">IT Support Remarks / Notes:</p>
            <p style="margin: 0; color: #334155; font-size: 14px; line-height: 1.5;">{remarks}</p>
        </div>
        """
        remarks_section_text = f"\nIT Support Remarks:\n{remarks}\n"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 24px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.06); }}
        .header {{ background: #1e293b; color: #ffffff; padding: 24px 32px; display: flex; align-items: center; justify-content: space-between; }}
        .badge {{ display: inline-block; padding: 6px 14px; font-weight: 700; font-size: 13px; border-radius: 20px; color: #ffffff; text-transform: uppercase; letter-spacing: 0.5px; }}
        .content {{ padding: 32px; color: #1e293b; }}
        .ticket-info {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .ticket-info td {{ padding: 10px 14px; border-bottom: 1px solid #f1f5f9; font-size: 14px; }}
        .ticket-info td.label {{ color: #64748b; font-weight: 600; width: 35%; }}
        .ticket-info td.value {{ color: #0f172a; font-weight: 500; }}
        .footer {{ padding: 20px 32px; background: #f8fafc; border-top: 1px solid #e2e8f0; text-align: center; font-size: 13px; color: #94a3b8; }}
        .button {{ display: inline-block; padding: 12px 24px; background: #2563eb; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; margin-top: 20px; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h2 style="margin: 0; font-size: 20px; color: #ffffff;">IT Support Notification</h2>
          <span style="font-size: 14px; color: #94a3b8;">Token #{ticket_id}</span>
        </div>
        <div class="content">
          <p style="font-size: 16px; margin-top: 0;">Hello <strong>{user_name}</strong>,</p>
          <p style="color: #475569; font-size: 15px; line-height: 1.5;">The status of your IT support ticket <strong>#{ticket_id}</strong> has been updated.</p>
          
          <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px 20px; margin: 20px 0;">
            <table style="width: 100%;">
              <tr>
                <td style="color: #64748b; font-size: 13px; font-weight: 600;">PREVIOUS STATUS</td>
                <td style="text-align: center; color: #94a3b8; font-size: 18px;">&rarr;</td>
                <td style="color: #64748b; font-size: 13px; font-weight: 600; text-align: right;">NEW STATUS</td>
              </tr>
              <tr>
                <td><span class="badge" style="background-color: {old_color};">{old_status}</span></td>
                <td></td>
                <td style="text-align: right;"><span class="badge" style="background-color: {status_color};">{new_status}</span></td>
              </tr>
            </table>
          </div>

          {remarks_section_html}

          <h4 style="margin: 24px 0 10px 0; color: #334155; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">Ticket Summary</h4>
          <table class="ticket-info">
            <tr>
              <td class="label">Token / Ticket ID:</td>
              <td class="value">#{ticket_id}</td>
            </tr>
            <tr>
              <td class="label">Company:</td>
              <td class="value">{company}</td>
            </tr>
            <tr>
              <td class="label">Issue Type:</td>
              <td class="value">{issue_type}</td>
            </tr>
            <tr>
              <td class="label">Location / Floor:</td>
              <td class="value">{location}</td>
            </tr>
            <tr>
              <td class="label">Issue Description:</td>
              <td class="value">{issue}</td>
            </tr>
          </table>

          <div style="text-align: center; margin-top: 25px;">
            <a href="http://localhost:3000" class="button" style="color: #ffffff;">View in Support Portal</a>
          </div>
        </div>
        <div class="footer">
          This is an automated notification from your IT Support Ticketing System.<br>
          Please do not reply directly to this email.
        </div>
      </div>
    </body>
    </html>
    """

    text_content = f"""
IT Support Ticket Status Update
--------------------------------------------------
Hello {user_name},

Your IT support ticket #{ticket_id} has been updated.

Status Change:
  Previous Status: {old_status}
  New Status:      {new_status}
{remarks_section_text}
Ticket Details:
  Ticket ID:    #{ticket_id}
  Company:      {company}
  Issue Type:   {issue_type}
  Location:     {location}
  Description:  {issue}

You can track your ticket at: http://localhost:3000
--------------------------------------------------
IT Support Helpdesk
"""
    return send_email(user_email, subject, html_content, text_content, recipient_type="USER")


# ==============================================================================
# ADMIN NOTIFICATIONS
# ==============================================================================

def send_admin_new_ticket_email(
    admin_email: str,
    ticket_id: int,
    user_name: str,
    user_email: str,
    company: str,
    issue_type: str,
    location: str,
    issue: str
):
    """Notification sent to IT Admin when any user submits a new ticket."""
    subject = f"[Admin Alert] New Ticket #{ticket_id} Logged - {company} ({issue_type})"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 24px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.06); }}
        .header {{ background: #dc2626; color: #ffffff; padding: 24px 32px; display: flex; align-items: center; justify-content: space-between; }}
        .content {{ padding: 32px; color: #1e293b; }}
        .ticket-info {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .ticket-info td {{ padding: 10px 14px; border-bottom: 1px solid #f1f5f9; font-size: 14px; }}
        .ticket-info td.label {{ color: #64748b; font-weight: 600; width: 35%; }}
        .ticket-info td.value {{ color: #0f172a; font-weight: 500; }}
        .footer {{ padding: 20px 32px; background: #f8fafc; border-top: 1px solid #e2e8f0; text-align: center; font-size: 13px; color: #94a3b8; }}
        .button {{ display: inline-block; padding: 12px 24px; background: #dc2626; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; margin-top: 20px; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h2 style="margin: 0; font-size: 20px; color: #ffffff;">New Ticket Submitted</h2>
          <span style="font-size: 16px; font-weight: bold;">Token #{ticket_id}</span>
        </div>
        <div class="content">
          <p style="font-size: 16px; margin-top: 0;">Hello <strong>IT Support Team</strong>,</p>
          <p style="color: #475569; font-size: 15px; line-height: 1.5;">
            A new IT support ticket has been submitted by <strong>{user_name}</strong> and is awaiting assignment.
          </p>

          <table class="ticket-info">
            <tr>
              <td class="label">Token / Ticket ID:</td>
              <td class="value"><strong>#{ticket_id}</strong></td>
            </tr>
            <tr>
              <td class="label">Requester Name:</td>
              <td class="value">{user_name}</td>
            </tr>
            <tr>
              <td class="label">Requester Email:</td>
              <td class="value"><a href="mailto:{user_email}" style="color: #2563eb;">{user_email}</a></td>
            </tr>
            <tr>
              <td class="label">Company:</td>
              <td class="value">{company}</td>
            </tr>
            <tr>
              <td class="label">Issue Type:</td>
              <td class="value">{issue_type}</td>
            </tr>
            <tr>
              <td class="label">Location / Floor:</td>
              <td class="value">{location}</td>
            </tr>
            <tr>
              <td class="label">Issue Description:</td>
              <td class="value" style="background: #f8fafc; border-radius: 6px; padding: 10px;">{issue}</td>
            </tr>
          </table>

          <div style="text-align: center; margin-top: 25px;">
            <a href="http://localhost:3000" class="button" style="color: #ffffff;">Open Admin Dashboard</a>
          </div>
        </div>
        <div class="footer">
          IT Support Admin Notification System
        </div>
      </div>
    </body>
    </html>
    """

    text_content = f"""
[ADMIN NOTIFICATION] New Support Ticket Logged
--------------------------------------------------
Ticket #{ticket_id} requires attention.

Requester:    {user_name} ({user_email})
Company:      {company}
Location:     {location}
Issue Type:   {issue_type}
Description:  {issue}

Status:       Open
Review at:    http://localhost:3000
--------------------------------------------------
"""
    return send_email(admin_email, subject, html_content, text_content, recipient_type="ADMIN")


def send_admin_ticket_status_email(
    admin_email: str,
    ticket_id: int,
    user_name: str,
    user_email: str,
    company: str,
    issue_type: str,
    location: str,
    issue: str,
    old_status: str,
    new_status: str,
    remarks: str | None = None,
    updated_by_admin_name: str = "Admin"
):
    """Notification sent to IT Admin team when a ticket status is modified."""
    subject = f"[Admin Alert] Ticket #{ticket_id} Status: {old_status} -> {new_status}"
    status_color = get_status_color(new_status)
    old_color = get_status_color(old_status)
    remarks_section_html = ""
    remarks_section_text = ""

    if remarks:
        remarks_section_html = f"""
        <div style="margin-top: 18px; padding: 12px 16px; background-color: #f8fafc; border-left: 4px solid #475569; border-radius: 4px;">
            <p style="margin: 0 0 4px 0; font-size: 12px; font-weight: bold; color: #475569; text-transform: uppercase;">Remarks Added:</p>
            <p style="margin: 0; color: #1e293b; font-size: 14px;">{remarks}</p>
        </div>
        """
        remarks_section_text = f"\nRemarks: {remarks}\n"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 24px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.06); }}
        .header {{ background: #334155; color: #ffffff; padding: 20px 32px; display: flex; align-items: center; justify-content: space-between; }}
        .badge {{ display: inline-block; padding: 5px 12px; font-weight: 700; font-size: 12px; border-radius: 20px; color: #ffffff; text-transform: uppercase; }}
        .content {{ padding: 28px 32px; color: #1e293b; }}
        .ticket-info {{ width: 100%; border-collapse: collapse; margin: 18px 0; }}
        .ticket-info td {{ padding: 8px 12px; border-bottom: 1px solid #f1f5f9; font-size: 14px; }}
        .ticket-info td.label {{ color: #64748b; font-weight: 600; width: 35%; }}
        .ticket-info td.value {{ color: #0f172a; }}
        .footer {{ padding: 18px 32px; background: #f8fafc; border-top: 1px solid #e2e8f0; text-align: center; font-size: 13px; color: #94a3b8; }}
        .button {{ display: inline-block; padding: 10px 20px; background: #334155; color: #ffffff; text-decoration: none; border-radius: 6px; font-weight: 600; margin-top: 15px; font-size: 14px; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h3 style="margin: 0; font-size: 18px; color: #ffffff;">Ticket Status Updated</h3>
          <span style="font-size: 14px; color: #cbd5e1;">Token #{ticket_id}</span>
        </div>
        <div class="content">
          <p style="font-size: 15px; margin-top: 0;">
            Ticket <strong>#{ticket_id}</strong> (User: <strong>{user_name}</strong>) status was modified by <strong>{updated_by_admin_name}</strong>.
          </p>

          <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 18px; margin: 15px 0;">
            <table style="width: 100%;">
              <tr>
                <td style="color: #64748b; font-size: 12px; font-weight: bold;">OLD STATUS</td>
                <td style="text-align: center; color: #94a3b8; font-size: 16px;">&rarr;</td>
                <td style="color: #64748b; font-size: 12px; font-weight: bold; text-align: right;">NEW STATUS</td>
              </tr>
              <tr>
                <td><span class="badge" style="background-color: {old_color};">{old_status}</span></td>
                <td></td>
                <td style="text-align: right;"><span class="badge" style="background-color: {status_color};">{new_status}</span></td>
              </tr>
            </table>
          </div>

          {remarks_section_html}

          <table class="ticket-info">
            <tr>
              <td class="label">Requester:</td>
              <td class="value">{user_name} ({user_email})</td>
            </tr>
            <tr>
              <td class="label">Company / Floor:</td>
              <td class="value">{company} - {location}</td>
            </tr>
            <tr>
              <td class="label">Issue Type:</td>
              <td class="value">{issue_type}</td>
            </tr>
            <tr>
              <td class="label">Issue:</td>
              <td class="value">{issue}</td>
            </tr>
          </table>

          <div style="text-align: center; margin-top: 20px;">
            <a href="http://localhost:3000" class="button" style="color: #ffffff;">View in Admin Dashboard</a>
          </div>
        </div>
        <div class="footer">
          IT Support Admin Notification System
        </div>
      </div>
    </body>
    </html>
    """

    text_content = f"""
[ADMIN NOTIFICATION] Ticket Status Updated
--------------------------------------------------
Ticket:       #{ticket_id}
User:         {user_name} ({user_email})
Updated By:   {updated_by_admin_name}
Status:       {old_status} -> {new_status}
{remarks_section_text}
Company:      {company} ({location})
Issue:        {issue}

Admin portal: http://localhost:3000
--------------------------------------------------
"""
    return send_email(admin_email, subject, html_content, text_content, recipient_type="ADMIN")


# ==============================================================================
# DISPATCHERS
# ==============================================================================

def notify_ticket_created(
    ticket_id: int,
    user_name: str,
    user_email: str,
    company: str,
    issue_type: str,
    location: str,
    issue: str,
    admin_emails: list[str]
):
    """Sends confirmation to user AND action alert to all admins."""
    send_ticket_created_email(
        ticket_id=ticket_id,
        user_name=user_name,
        user_email=user_email,
        company=company,
        issue_type=issue_type,
        location=location,
        issue=issue
    )

    for admin_email in admin_emails:
        if admin_email and admin_email != user_email:
            send_admin_new_ticket_email(
                admin_email=admin_email,
                ticket_id=ticket_id,
                user_name=user_name,
                user_email=user_email,
                company=company,
                issue_type=issue_type,
                location=location,
                issue=issue
            )


def notify_ticket_status_change(
    ticket_id: int,
    user_name: str,
    user_email: str,
    company: str,
    issue_type: str,
    location: str,
    issue: str,
    old_status: str,
    new_status: str,
    remarks: str | None,
    admin_emails: list[str] = None,
    updated_by_admin_name: str = "Admin"
):
    """
    Sends status update email ONLY to the employee/user whose ticket it is.
    The admin does NOT receive this email since they are the one making the update.
    """
    send_ticket_status_email(
        ticket_id=ticket_id,
        user_name=user_name,
        user_email=user_email,
        company=company,
        issue_type=issue_type,
        location=location,
        issue=issue,
        old_status=old_status,
        new_status=new_status,
        remarks=remarks
    )

