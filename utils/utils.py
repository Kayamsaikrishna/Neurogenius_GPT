import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def generate_otp(length=6):
    """
    Generate a random OTP (One-Time Password) of the specified length.
    """
    return ''.join(random.choices('0123456789', k=length))

def send_email_otp(recipient_email, otp):
    """
    Send an OTP to the specified email address.
    """
    try:
        sender_email = "your_email@example.com"  # Replace with your email
        sender_password = "your_password"        # Replace with your email password
        subject = "Your OTP Code"
        body = f"Your OTP code is: {otp}"

        # Create the email
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Connect to the SMTP server and send the email
        server = smtplib.SMTP('smtp.gmail.com', 587)  # Replace with your SMTP server
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()

        print(f"OTP sent to {recipient_email}")
        return True
    except Exception as e:
        print(f"Failed to send OTP: {str(e)}")
        return False

def send_welcome_email(recipient_email, username):
    """
    Send a welcome email to the specified email address.
    """
    try:
        sender_email = "your_email@example.com"  # Replace with your email
        sender_password = "your_password"        # Replace with your email password
        subject = "Welcome to NeuroGenius"
        body = f"Hello {username},\n\nWelcome to NeuroGenius! We're excited to have you on board."

        # Create the email
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Connect to the SMTP server and send the email
        server = smtplib.SMTP('smtp.gmail.com', 587)  # Replace with your SMTP server
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()

        print(f"Welcome email sent to {recipient_email}")
        return True
    except Exception as e:
        print(f"Failed to send welcome email: {str(e)}")
        return False