from django.core.mail import send_mail
from django.conf import settings

try:
    from twilio.rest import Client as TwilioClient
except ImportError:
    TwilioClient = None


def send_session_email(exchange, subject, body_lines):
    recipients = list(filter(None, [exchange.requester.email, exchange.receiver.email]))
    if not recipients:
        return
    body = "\n".join(body_lines)
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, recipients, fail_silently=True)
        print(f"✅ Email sent to: {', '.join(recipients)}")
    except Exception as e:
        print(f"❌ Email error: {e}")


def send_email_to_user(email, subject, body):
    if not email:
        return
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=True)
        print(f"✅ Email sent to: {email}")
    except Exception as e:
        print(f"❌ Email error: {e}")


def send_whatsapp_to_user(phone, message_body):
    if not phone or not TwilioClient:
        return
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        print("⚠️ Twilio credentials not configured, skipping WhatsApp")
        return
    try:
        client = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)  # type: ignore
        clean_phone = phone.strip()
        if not clean_phone.startswith("+"):
            clean_phone = f"+91{clean_phone}"
        client.messages.create(
            body=message_body,
            from_=settings.TWILIO_WHATSAPP_FROM,
            to=f"whatsapp:{clean_phone}",
        )
        print(f"✅ WhatsApp sent to: {clean_phone}")
    except Exception as e:
        print(f"❌ WhatsApp error: {e}")


def send_schedule_notification(exchange, triggered_by_user):
    partner = exchange.receiver if exchange.requester == triggered_by_user else exchange.requester

    date_str = exchange.scheduled_date.strftime("%B %d, %Y") if exchange.scheduled_date else "Not set"
    time_str = exchange.scheduled_time.strftime("%I:%M %p") if exchange.scheduled_time else "Not set"
    platform_display = exchange.get_meeting_platform_display() if exchange.meeting_platform else "Not set"

    scheduled_by = triggered_by_user.first_name or triggered_by_user.username
    subject = f"Session Confirmed: {exchange.skill.name} | Skill Exchange Network"
    body_lines = [
        f"Hi {partner.first_name or partner.username},",
        "",
        "Great news! Your skill exchange session has been scheduled.",
        "",
        f"  Skill    : {exchange.skill.name}",
        f"  Date     : {date_str}",
        f"  Time     : {time_str}",
        f"  Platform : {platform_display}",
    ]

    if exchange.meeting_link:
        body_lines += ["", "  Meeting Link:", f"  {exchange.meeting_link}", "",
                       "Click the link above to join the session at the scheduled time."]
    else:
        body_lines.append("")
        body_lines.append("A meeting link will be shared with you before the session.")

    body_lines += ["", f"Scheduled by: {scheduled_by}", "",
                   "If you have any questions, please reply to this email.",
                   "", "Best regards,", "Skill Exchange Network"]

    send_email_to_user(partner.email, subject, "\n".join(body_lines))

    whatsapp_msg = (
        f"*Hello {partner.first_name or partner.username}!*\n\n"
        f"Your skill exchange session has been scheduled.\n\n"
        f"*Skill:* {exchange.skill.name}\n"
        f"*Date:* {date_str}\n"
        f"*Time:* {time_str}\n"
        f"*Platform:* {platform_display}\n"
    )
    if exchange.meeting_link:
        whatsapp_msg += f"\n*Meeting Link:*\n{exchange.meeting_link}\n"
    else:
        whatsapp_msg += "\nA meeting link will be shared before the session.\n"
    whatsapp_msg += "\nSee you there!\n\n- Skill Exchange Network"

    send_whatsapp_to_user(partner.phone, whatsapp_msg)


def send_meeting_link_notification(exchange, triggered_by_user):
    partner = exchange.receiver if exchange.requester == triggered_by_user else exchange.requester

    platform_display = exchange.get_meeting_platform_display() if exchange.meeting_platform else "Online"
    date_str = exchange.scheduled_date.strftime("%B %d, %Y") if exchange.scheduled_date else "To be confirmed"
    time_str = exchange.scheduled_time.strftime("%I:%M %p") if exchange.scheduled_time else "To be confirmed"

    created_by = triggered_by_user.first_name or triggered_by_user.username
    subject = f"Meeting Link Ready: {exchange.skill.name} | Skill Exchange Network"
    body = (
        f"Hi {partner.first_name or partner.username},\n\n"
        f"Your meeting link for the skill exchange session is ready!\n\n"
        f"  Skill    : {exchange.skill.name}\n"
        f"  Date     : {date_str}\n"
        f"  Time     : {time_str}\n"
        f"  Platform : {platform_display}\n\n"
        f"  Meeting Link:\n"
        f"  {exchange.meeting_link}\n\n"
        f"Click the link above to join the session at the scheduled time.\n\n"
        f"Added by: {created_by}\n\n"
        f"Best regards,\nSkill Exchange Network"
    )
    send_email_to_user(partner.email, subject, body)

    whatsapp_msg = (
        f"*Hello {partner.first_name or partner.username}!*\n\n"
        f"Your meeting link is ready!\n\n"
        f"*Skill:* {exchange.skill.name}\n"
        f"*Date:* {date_str}\n"
        f"*Time:* {time_str}\n"
        f"*Platform:* {platform_display}\n\n"
        f"*Meeting Link:*\n"
        f"{exchange.meeting_link}\n\n"
        f"See you there!\n\n- Skill Exchange Network"
    )
    send_whatsapp_to_user(partner.phone, whatsapp_msg)


def send_custom_notification(partner_email, partner_phone, subject, body, whatsapp_body=None):
    send_email_to_user(partner_email, subject, body)
    if whatsapp_body:
        send_whatsapp_to_user(partner_phone, whatsapp_body)
