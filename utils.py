import random
import smtplib
from email.message import EmailMessage

def generate_otp():
    """Generates a 6-digit OTP as a string."""
    return str(random.randint(100000, 999999))

def send_email(receiver_email, subject, body):
    """
    Sends an email using Gmail SMTP.
    Replace sender_email and sender_password with your actual credentials or app password.
    """
    sender_email = "your-email@gmail.com"  # Update this
    sender_password = "your-app-password"  # Update this (use an app password if 2FA is enabled)

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print("Error sending email:", e)
        return False

def send_email_otp(receiver_email, otp):
    subject = "NeuroGenius - Password Reset OTP"
    body = f"Your OTP for password reset is: {otp}"
    return send_email(receiver_email, subject, body)

def send_welcome_email(receiver_email):
    subject = "Welcome to NeuroGenius GPT"
    body = (
        "Hello!\n\n"
        "Thank you for registering an account with NeuroGenius GPT.\n"
        "We look forward to helping you explore advanced AI capabilities.\n\n"
        "Best Regards,\nNeuroGenius Team"
    )
    return send_email(receiver_email, subject, body)
