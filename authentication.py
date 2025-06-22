import hashlib
from database import register_user, get_user_by_identifier, update_password
from utils import generate_otp, send_email_otp, send_welcome_email

def hash_password(password):
    """Hashes the password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def register(username, email, phone, password):
    password_hash = hash_password(password)
    return register_user(username, email, phone, password_hash)

def login(identifier, password):
    user = get_user_by_identifier(identifier)
    if user and user["password"] == hash_password(password):  # Use the correct key
        return True
    return False

def request_password_reset(identifier):
    """
    Requests a password reset OTP for the user identified by username/email/phone.
    Returns (True, otp) if successful, otherwise (False, error message).
    """
    user = get_user_by_identifier(identifier)
    if not user:
        return False, "User not found"
    
    otp = generate_otp()
    # Assuming user[2] is email
    if send_email_otp(user[2], otp):
        return True, otp
    else:
        return False, "Failed to send OTP"

def reset_password(identifier, otp, new_password):
    # In a production app, verify the OTP before resetting.
    new_password_hash = hash_password(new_password)
    update_password(identifier, new_password_hash)
    return True

def send_welcome(identifier):
    user = get_user_by_identifier(identifier)
    if user:
        # Assuming user[2] is email
        send_welcome_email(user[2])
