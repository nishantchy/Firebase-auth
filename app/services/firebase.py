import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException, status
from typing import Dict, Any
from app.core.config import settings

class FirebaseService:
    def __init__(self, service_account_path: str):
        if not firebase_admin._apps:
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
    
    async def create_user_with_email_password(self, email: str, password: str, display_name: str = None) -> Dict[str, Any]:
        """Create user in Firebase Auth with email and password"""
        try:
            user_record = auth.create_user(
                email=email,
                password=password,
                display_name=display_name,
                email_verified=False  # Always start as unverified
            )
            
            # Send verification email
            await self.send_verification_email(email, display_name)
            
            return {
                "uid": user_record.uid,
                "email": user_record.email,
                "display_name": user_record.display_name,
                "email_verified": user_record.email_verified
            }
        except auth.EmailAlreadyExistsError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create user: {str(e)}"
            )
    
    async def send_verification_email(self, email: str, display_name: str = ""):
        """Generate Firebase verification link and send it via SMTP with a custom template."""
        try:
            # 1. Generate the verification link
            verification_link = auth.generate_email_verification_link(email)
            # 2. Prepare the email
            app_name = settings.APP_NAME
            subject = f"Verify your email for {app_name}"
            html = f"""
            <html>
              <body style='font-family: Arial, sans-serif;'>
                <h2>Welcome to {app_name}!</h2>
                <p>Hi {display_name or email},</p>
                <p>Thank you for signing up. Please verify your email address by clicking the button below:</p>
                <a href='{verification_link}' style='background: #1976d2; color: #fff; padding: 10px 20px; text-decoration: none; border-radius: 4px;'>Verify Email</a>
                <p>If you did not create an account, you can ignore this email.</p>
                <p>Thanks,<br>{app_name} Team</p>
              </body>
            </html>
            """
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.EMAIL_FROM
            msg["To"] = email
            msg.attach(MIMEText(html, "html"))
            # 3. Send the email
            with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
                server.starttls()
                server.login(settings.EMAIL_USER, settings.EMAIL_PASS)
                server.sendmail(msg["From"], [email], msg.as_string())
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send verification email: {str(e)}"
            )
    
    async def send_password_reset_email(self, email: str, display_name: str = ""):
        """Generate Firebase password reset link and send it via SMTP with a custom template."""
        try:
            # 1. Generate the password reset link
            reset_link = auth.generate_password_reset_link(email)
            # 2. Prepare the email
            app_name = settings.APP_NAME
            subject = f"Reset your password for {app_name}"
            html = f"""
            <html>
              <body style='font-family: Arial, sans-serif;'>
                <h2>Password Reset for {app_name}</h2>
                <p>Hello,</p>
                <p>Follow this link to reset your {app_name} password for your {email} account.</p>
                <a href='{reset_link}' style='background: #1976d2; color: #fff; padding: 10px 20px; text-decoration: none; border-radius: 4px;'>Reset Password</a>
                <p>If you didn't ask to reset your password, you can ignore this email.</p>
                <p>Thanks,<br>Your {app_name} team</p>
              </body>
            </html>
            """
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.EMAIL_FROM
            msg["To"] = email
            msg.attach(MIMEText(html, "html"))
            # 3. Send the email
            with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
                server.starttls()
                server.login(settings.EMAIL_USER, settings.EMAIL_PASS)
                server.sendmail(msg["From"], [email], msg.as_string())
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send password reset email: {str(e)}"
            )
    
    async def verify_id_token(self, id_token: str) -> Dict[str, Any]:
        """Verify Firebase ID token and return user info"""
        try:
            decoded_token = auth.verify_id_token(id_token)
            return decoded_token
        except auth.InvalidIdTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid ID token"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token verification failed: {str(e)}"
            )
    
    async def get_user_by_uid(self, uid: str) -> Dict[str, Any]:
        """Get user info from Firebase by UID"""
        try:
            user_record = auth.get_user(uid)
            return {
                "uid": user_record.uid,
                "email": user_record.email,
                "display_name": user_record.display_name,
                "photo_url": user_record.photo_url,
                "email_verified": user_record.email_verified,
                "provider_data": user_record.provider_data
            }
        except auth.UserNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to get user: {str(e)}"
            )
    
    async def send_invitation_email(self, email: str, display_name: str = "", expiry_minutes: int = 1):
        """Generate Firebase email sign-in (magic) link and send it via SMTP with a custom template. Create user if not exists."""
        try:
            # 1. Ensure user exists in Firebase
            try:
                user_record = auth.get_user_by_email(email)
            except auth.UserNotFoundError:
                user_record = auth.create_user(email=email, display_name=display_name)
            # 2. Generate the sign-in link with custom ActionCodeSettings, including email in continueUrl
            from firebase_admin import auth as firebase_auth
            from urllib.parse import urlencode
            continue_url = f"{settings.INVITE_CONTINUE_URL}?email={email}"
            action_code_settings = firebase_auth.ActionCodeSettings(
                url=continue_url,  # e.g., your frontend registration page with email param
                handle_code_in_app=True,
            )
            sign_in_link = firebase_auth.generate_sign_in_with_email_link(email, action_code_settings)
            # 3. Prepare the email
            app_name = settings.APP_NAME
            subject = f"You're invited to join {app_name}!"
            html = f"""
            <html>
              <body style='font-family: Arial, sans-serif;'>
                <h2>Invitation to {app_name}</h2>
                <p>Hi {display_name or email},</p>
                <p>You have been invited to join {app_name}. Click the button below to set your password and activate your account. This link will expire in {expiry_minutes} minute(s).</p>
                <a href='{sign_in_link}' style='background: #1976d2; color: #fff; padding: 10px 20px; text-decoration: none; border-radius: 4px;'>Accept Invitation</a>
                <p>If you did not expect this invitation, you can ignore this email.</p>
                <p>Thanks,<br>{app_name} Team</p>
              </body>
            </html>
            """
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.EMAIL_FROM
            msg["To"] = email
            msg.attach(MIMEText(html, "html"))
            # 4. Send the email
            with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
                server.starttls()
                server.login(settings.EMAIL_USER, settings.EMAIL_PASS)
                server.sendmail(msg["From"], [email], msg.as_string())
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send invitation email: {str(e)}"
            )