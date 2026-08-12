"""
app/services/email_service.py
Sends HTML email alerts to the correct government department
whenever a new report is filed.
"""
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()

SMTP_HOST  = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT  = int(os.getenv("SMTP_PORT", 587))
SMTP_USER  = os.getenv("SMTP_USER", "")
SMTP_PASS  = os.getenv("SMTP_PASS", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "GramSeva Portal <no-reply@gramseva.in>")

# ── Category → (Department Name, Env Key) ─────────────────────────────────
DEPT_MAP = {
    "Water Supply / Pipe Leakage": ("Public Health Engineering Dept", "EMAIL_WATER_SUPPLY"),
    "Roads & Pathways":            ("Rural Roads Department",         "EMAIL_ROADS"),
    "Water Management":            ("Irrigation Department",          "EMAIL_WATER_MANAGEMENT"),
    "Street Lights":               ("Rural Electrification Dept",     "EMAIL_STREET_LIGHTS"),
    "Drainage System":             ("Sanitation Department",          "EMAIL_DRAINAGE"),
    "Other Issue":                 ("Gram Panchayat",                 "EMAIL_OTHER"),
}


def _get_urgency_color(urgency: str) -> str:
    return {"high": "#DC3545", "medium": "#FFC107", "low": "#28A745"}.get(urgency, "#6C757D")


def _build_html(report: dict, dept_name: str) -> str:
    """Render a clean HTML email for the department."""
    urgency_color = _get_urgency_color(report.get("urgency", "medium"))
    image_block = ""
    if report.get("image_url"):
        image_block = f"""
        <tr>
          <td style="padding:0 30px 20px">
            <p style="margin:0 0 8px;font-weight:600;color:#333">📷 Attached Photo:</p>
            <img src="{report['image_url']}"
                 alt="Issue Photo"
                 style="max-width:100%;border-radius:8px;border:2px solid #e0e0e0"/>
          </td>
        </tr>"""

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:'Segoe UI',Arial,sans-serif">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr>
      <td align="center" style="padding:30px 10px">
        <table width="620" cellpadding="0" cellspacing="0"
               style="background:#ffffff;border-radius:12px;overflow:hidden;
                      box-shadow:0 4px 20px rgba(0,0,0,0.1)">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#2D4A22,#3D6B2E);
                        padding:28px 30px;text-align:center">
              <h1 style="margin:0;color:#ffffff;font-size:22px;letter-spacing:-0.5px">
                🌾 GramSeva — New Issue Report
              </h1>
              <p style="margin:6px 0 0;color:rgba(255,255,255,0.75);font-size:13px">
                Forwarded to: <strong>{dept_name}</strong>
              </p>
            </td>
          </tr>

          <!-- Ticket + Urgency -->
          <tr>
            <td style="padding:24px 30px 0">
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="background:#f8f9fa;border-radius:8px;padding:14px 18px">
                    <span style="font-size:13px;color:#666">Ticket ID</span><br>
                    <strong style="font-size:18px;color:#2D4A22;font-family:monospace">
                      #{report.get('ticket_id','—')}
                    </strong>
                  </td>
                  <td width="16"></td>
                  <td style="background:{urgency_color}18;border:2px solid {urgency_color};
                              border-radius:8px;padding:14px 18px;text-align:center">
                    <span style="font-size:13px;color:#666">Urgency</span><br>
                    <strong style="font-size:16px;color:{urgency_color};text-transform:uppercase">
                      {report.get('urgency','medium')}
                    </strong>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Details -->
          <tr>
            <td style="padding:20px 30px 0">
              <table width="100%" cellpadding="0" cellspacing="0"
                     style="border:1px solid #e8e8e8;border-radius:8px;overflow:hidden">
                {''.join(f"""
                <tr style="border-bottom:1px solid #f0f0f0">
                  <td style="padding:12px 16px;background:#fafafa;
                              font-weight:600;font-size:13px;color:#555;width:35%">
                    {label}
                  </td>
                  <td style="padding:12px 16px;font-size:14px;color:#222">{value}</td>
                </tr>""" for label, value in [
                    ("👤 Reporter Name",  report.get('name','—')),
                    ("📱 Mobile",         report.get('phone','—')),
                    ("📍 Village",        report.get('village','—')),
                    ("🏙️ District",       report.get('district','—')),
                    ("🗂️ Category",       report.get('category','—')),
                    ("📅 Reported On",    datetime.utcnow().strftime("%d %b %Y, %H:%M UTC")),
                ])}
              </table>
            </td>
          </tr>

          <!-- Description -->
          <tr>
            <td style="padding:20px 30px 0">
              <p style="margin:0 0 8px;font-weight:600;color:#333">📝 Issue Description:</p>
              <div style="background:#f8f9fa;border-left:4px solid #5A8C3F;
                          padding:14px 16px;border-radius:0 8px 8px 0;
                          font-size:14px;color:#444;line-height:1.6">
                {report.get('description','No description provided.')}
              </div>
            </td>
          </tr>

          {image_block}

          <!-- CTA -->
          <tr>
            <td style="padding:24px 30px 30px;text-align:center">
              <p style="margin:0 0 16px;font-size:13px;color:#888">
                Please log in to the GramSeva Admin Portal to update the status of this report.
              </p>
              <a href="#"
                 style="background:#2D4A22;color:#ffffff;padding:12px 28px;
                        border-radius:8px;text-decoration:none;font-weight:600;
                        font-size:14px;display:inline-block">
                Open Admin Portal →
              </a>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#f8f9fa;padding:16px 30px;text-align:center;
                       border-top:1px solid #e8e8e8">
              <p style="margin:0;font-size:12px;color:#aaa">
                This is an automated alert from GramSeva Rural Issue Reporting Portal.
                Do not reply to this email.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


async def send_department_alert(report: dict) -> bool:
    """
    Route the report email to the correct department based on category.
    Returns True if sent successfully.
    """
    category  = report.get("category", "Other Issue")
    dept_name, env_key = DEPT_MAP.get(category, ("Gram Panchayat", "EMAIL_OTHER"))
    dept_email = os.getenv(env_key, "")

    if not dept_email:
        print(f"⚠️  No email configured for {env_key}. Skipping.")
        return False

    # ── Build message ──────────────────────────────────────────
    msg = MIMEMultipart("alternative")
    msg["Subject"] = (
        f"[GramSeva #{report.get('ticket_id','?')}] "
        f"New {report.get('urgency','').upper()} priority issue — "
        f"{category} in {report.get('village','')}, {report.get('district','')}"
    )
    msg["From"] = EMAIL_FROM
    msg["To"]   = dept_email

    html_body = _build_html(report, dept_name)
    msg.attach(MIMEText(html_body, "html"))

    # ── Send via SMTP ──────────────────────────────────────────
    try:
        await aiosmtplib.send(
            msg,
            hostname  = SMTP_HOST,
            port      = SMTP_PORT,
            username  = SMTP_USER,
            password  = SMTP_PASS,
            start_tls = True,
        )
        print(f"✉️  Alert sent to {dept_name} ({dept_email})")
        return True
    except Exception as e:
        print(f"❌  Email failed: {e}")
        return False


async def send_citizen_confirmation(report: dict) -> bool:
    """
    Optionally send an SMS-style confirmation email to the citizen
    (if they provide an email — future enhancement placeholder).
    """
    # TODO: integrate citizen email field + send confirmation
    return True
