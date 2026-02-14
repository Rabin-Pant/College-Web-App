import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app, url_for
from utils.auth_helpers import generate_verification_token

def send_verification_email(user_email, user_name, verification_token=None):
    """Send email verification link"""
    try:
        if verification_token is None:
            verification_token = generate_verification_token()
        
        # Get email config from app
        mail_server = current_app.config.get('MAIL_SERVER', 'smtp.gmail.com')
        mail_port = current_app.config.get('MAIL_PORT', 587)
        mail_username = current_app.config.get('MAIL_USERNAME')
        mail_password = current_app.config.get('MAIL_PASSWORD')
        mail_sender = current_app.config.get('MAIL_DEFAULT_SENDER', mail_username)
        
        if not mail_username or not mail_password:
            print("⚠️ Email credentials not configured. Skipping email send.")
            print(f"Verification link would be: http://localhost:5000/api/auth/verify/{verification_token}")
            return False
        
        # Create verification link
        verification_link = f"http://localhost:5000/api/auth/verify/{verification_token}"
        
        # Email content
        msg = MIMEMultipart('alternative')
        msg['From'] = mail_sender
        msg['To'] = user_email
        msg['Subject'] = 'Verify Your Email - College App'
        
        # HTML version
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background: #f9f9f9; padding: 30px; border-radius: 10px;">
                    <h2 style="color: #333; margin-bottom: 20px;">Welcome to College App! 🎓</h2>
                    <p style="color: #666; font-size: 16px;">Hello {user_name},</p>
                    <p style="color: #666; font-size: 16px;">Please verify your email address by clicking the button below:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{verification_link}" 
                           style="background: #4CAF50; color: white; padding: 12px 30px; 
                                  text-decoration: none; border-radius: 5px; font-size: 16px;">
                            Verify Email
                        </a>
                    </div>
                    <p style="color: #666; font-size: 14px;">Or copy this link:</p>
                    <p style="background: #eee; padding: 10px; border-radius: 5px; font-size: 12px; word-break: break-all;">
                        {verification_link}
                    </p>
                    <p style="color: #999; font-size: 12px; margin-top: 30px;">
                        This link will expire in 24 hours.
                    </p>
                </div>
            </body>
        </html>
        """
        
        # Plain text version
        text = f"""
        Welcome to College App!
        
        Hello {user_name},
        
        Please verify your email address by visiting this link:
        {verification_link}
        
        This link will expire in 24 hours.
        """
        
        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))
        
        # Send email
        server = smtplib.SMTP(mail_server, mail_port)
        server.starttls()
        server.login(mail_username, mail_password)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Verification email sent to {user_email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send verification email: {e}")
        return False

def send_password_reset_email(user_email, user_name, reset_token=None):
    """Send password reset email"""
    try:
        if reset_token is None:
            reset_token = generate_verification_token()  # Reuse the same function
        
        # Get email config
        mail_username = current_app.config.get('MAIL_USERNAME')
        mail_password = current_app.config.get('MAIL_PASSWORD')
        
        if not mail_username or not mail_password:
            print("⚠️ Email credentials not configured.")
            print(f"Password reset link: http://localhost:3000/reset-password/{reset_token}")
            return False
        
        # Create reset link
        reset_link = f"http://localhost:3000/reset-password/{reset_token}"
        
        # Email content
        msg = MIMEMultipart('alternative')
        msg['From'] = mail_username
        msg['To'] = user_email
        msg['Subject'] = 'Reset Your Password - College App'
        
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background: #f9f9f9; padding: 30px; border-radius: 10px;">
                    <h2 style="color: #333;">Reset Your Password</h2>
                    <p style="color: #666;">Hello {user_name},</p>
                    <p style="color: #666;">We received a request to reset your password.</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_link}" 
                           style="background: #2196F3; color: white; padding: 12px 30px; 
                                  text-decoration: none; border-radius: 5px;">
                            Reset Password
                        </a>
                    </div>
                    <p style="color: #999; font-size: 12px;">
                        If you didn't request this, please ignore this email.
                    </p>
                </div>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(html, 'html'))
        
        # Send email
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(mail_username, mail_password)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Password reset email sent to {user_email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send password reset email: {e}")
        return False