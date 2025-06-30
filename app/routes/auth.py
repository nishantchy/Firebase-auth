from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, SQLModel
from datetime import datetime, timedelta
from app.core.database import get_session
from app.core.config import settings
from app.utils.security import hash_password
from app.services.dependencies import get_firebase_service
from app.utils.jwt_utils import create_access_token
from app.services.user_service import get_or_create_user
from app.utils.email_validator import EmailValidator

from app.models.user import User, AuthProvider
from app.schemas.user import UserCreate, UserLogin, UserLoginResponse, TokenResponse, GoogleAuthRequest, PasswordResetRequest, SetNewPasswordRequest
from app.services.firebase import FirebaseService

router = APIRouter(
    prefix="/api/auth", 
    tags=["Authentication"]
    )


@router.post("/email-register", response_model=TokenResponse)
async def register_with_email(
    user_data: UserCreate,
    session: Session = Depends(get_session),
    firebase_service: FirebaseService = Depends(get_firebase_service)
):
    """Register user with email and password"""
    try:
        # Validate email
        email_validator = EmailValidator()
        email_validation = await email_validator.validate_email_existence(user_data.email)
        if not email_validation['is_valid']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email validation failed: {email_validation['message']}"
            )
        # Create user in Firebase from backend
        firebase_user = await firebase_service.create_user_with_email_password(
            email=user_data.email,
            password=user_data.password,
            display_name=user_data.display_name
        )
        # Hash password for storage
        hashed_password = hash_password(user_data.password)
        # Check if user already exists in our database
        statement = select(User).where(User.email == user_data.email)
        existing_user = session.exec(statement).first()
        if existing_user:
            # User exists, update their info
            existing_user.firebase_uid = firebase_user["uid"]
            existing_user.display_name = user_data.display_name
            existing_user.password = hashed_password
            existing_user.updated_at = datetime.now()
            session.add(existing_user)
            session.commit()
            session.refresh(existing_user)
            user = existing_user
        else:
            # Create new user in our database
            user = User(
                firebase_uid=firebase_user["uid"],
                email=user_data.email,
                password=hashed_password,
                display_name=user_data.display_name,
                auth_provider=AuthProvider.EMAIL,
                is_email_verified=firebase_user["email_verified"]  # Will be False initially
            )
            session.add(user)
            session.commit()
            session.refresh(user)
        # Create access token (but user needs to verify email to use the app)
        access_token_expires = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.firebase_uid, "user_id": user.id},
            secret_key=settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
            expires_delta=access_token_expires
        )
        return TokenResponse(
            access_token=access_token,
            user=UserLoginResponse.model_validate(user)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to register user: {str(e)}"
        )

@router.post("/email-login", response_model=TokenResponse)
async def login_with_email(
    user_data: UserLogin,
    session: Session = Depends(get_session),
    firebase_service: FirebaseService = Depends(get_firebase_service)
):
    """Login user with email and password"""
    # Find user in database
    statement = select(User).where(User.email == user_data.email)
    user = session.exec(statement).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    if not user.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not set up for email/password login"
        )
    # Verify password
    from app.utils.security import verify_password
    if not verify_password(user_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    # Fetch latest Firebase user info and sync verification status
    firebase_user = await firebase_service.get_user_by_uid(user.firebase_uid)
    if firebase_user["email_verified"] and not user.is_email_verified:
        user.is_email_verified = True
        user.updated_at = datetime.now()
        session.add(user)
        session.commit()
        session.refresh(user)
    if not user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email address before logging in"
        )
    # Create access token
    access_token_expires = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.firebase_uid, "user_id": user.id},
        secret_key=settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
        expires_delta=access_token_expires
    )
    return TokenResponse(
        access_token=access_token,
        user=UserLoginResponse.model_validate(user)
    )

@router.post("/login-google", response_model=TokenResponse)
async def login_with_google(
    auth_data: GoogleAuthRequest,
    session: Session = Depends(get_session),
    firebase_service: FirebaseService = Depends(get_firebase_service)
):
    """Login/Register user with Google via Firebase ID token"""
    # Verify the ID token
    decoded_token = await firebase_service.verify_id_token(auth_data.id_token)
    # Get user info from Firebase
    firebase_user = await firebase_service.get_user_by_uid(decoded_token["uid"])
    # Determine if this is a Google sign-in
    is_google_provider = any(
        provider.provider_id == "google.com" 
        for provider in firebase_user.get("provider_data", [])
    )
    if not is_google_provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint is only for Google authentication"
        )
    # Get or create user in our database
    user = get_or_create_user(
        session=session,
        firebase_uid=firebase_user["uid"],
        email=firebase_user["email"],
        display_name=firebase_user["display_name"],
        photo_url=firebase_user.get("photo_url"),
        auth_provider=AuthProvider.GOOGLE,
        is_email_verified=firebase_user["email_verified"]  # Google emails are pre-verified
    )
    # Create access token
    access_token_expires = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.firebase_uid, "user_id": user.id},
        secret_key=settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
        expires_delta=access_token_expires
    )
    return TokenResponse(
        access_token=access_token,
        user=UserLoginResponse.model_validate(user)
    )

@router.post("/resend-verification")
async def resend_verification_email(
    email: str,
    session: Session = Depends(get_session),
    firebase_service: FirebaseService = Depends(get_firebase_service)
):
    """Resend email verification link using custom SMTP."""
    # Find user in database
    statement = select(User).where(User.email == email)
    user = session.exec(statement).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified"
        )
    # Send verification email
    await firebase_service.send_verification_email(user.email, user.display_name)
    return {"message": "Verification email sent successfully"}

@router.post("/password-reset")
async def password_reset(
    request: PasswordResetRequest,
    session: Session = Depends(get_session),
    firebase_service: FirebaseService = Depends(get_firebase_service)
):
    email = request.email
    # Find user in database
    statement = select(User).where(User.email == email)
    user = session.exec(statement).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    # Send password reset email
    await firebase_service.send_password_reset_email(user.email, user.display_name)
    return {"message": "Password reset email sent successfully"}

@router.post("/set-new-password")
async def set_new_password(
    request: SetNewPasswordRequest,
    session: Session = Depends(get_session),
    firebase_service: FirebaseService = Depends(get_firebase_service)
):
    """Set a new password using oobCode and update local DB."""
    import requests
    try:
        firebase_api_key = settings.FIREBASE_API_KEY
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:resetPassword?key={firebase_api_key}"
        payload = {
            "oobCode": request.oobCode,
            "newPassword": request.new_password
        }
        resp = requests.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        email = data["email"]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to reset password: {str(e)}")

    from app.utils.security import hash_password
    statement = select(User).where(User.email == email)
    user = session.exec(statement).first()
    if user:
        user.password = hash_password(request.new_password)
        session.add(user)
        session.commit()
        session.refresh(user)
    else:
        raise HTTPException(status_code=404, detail="User not found in local database")

    return {"message": "Password has been reset successfully."}