# FastAPI + Firebase Authentication

This project demonstrates a secure authentication system using FastAPI (Python backend), Firebase (for authentication and SSO), and a modern HTML/JS frontend.

## What does this project do?

- **Email/Password Auth:** Users can register and log in with email and password. All authentication is handled by the backend (not the frontend).
- **Email Verification:** Users must verify their email address before they can log in and use the app.
- **Google SSO:** Users can sign in with Google. The frontend gets a Firebase ID token, sends it to the backend, and the backend verifies it with Firebase before issuing its own JWT.
- **User Management:** The backend stores user profiles in its own database (PostgreSQL via SQLModel), including info from Firebase.
- **JWT Sessions:** The backend issues its own JWT tokens for session management after verifying credentials or ID tokens.
- **Security Best Practices:** Minimal user info is sent in login/register responses. Passwords are never sent to the frontend or stored in plaintext.

## Project Structure

```
app/
  core/           # Config, DB setup
  models/         # SQLModel user model
  routes/         # FastAPI endpoints
  schemas/        # Pydantic/SQLModel schemas
  services/       # Firebase, user, and dependency services
  utils/          # Security, JWT, and email validation helpers

test/auth/        # Frontend (HTML/CSS/JS)
```

## How to run the backend

1. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
2. **Set up your `.env` file** (see `app/core/config.py` for required variables):

   ```env
   DATABASE_URL=postgresql://username:password@localhost:5432/db_name
   FIREBASE_SERVICE_ACCOUNT_PATH=./firebase-service-account.json
   JWT_SECRET_KEY=secret-key

   # Email configuration (optional - for custom email sending)
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   FROM_EMAIL=noreply@yourapp.com
   APP_NAME=Your App Name
   ```

3. **Set up Firebase Service Account:**

   - Go to [Firebase Console](https://console.firebase.google.com/)
   - Select your project → Project Settings → Service Accounts
   - Click "Generate new private key" to download your service account JSON
   - Copy `firebase-service-account.template.json` to `firebase-service-account.json`
   - Replace the placeholder values with your actual Firebase service account credentials

   **⚠️ Important:** Never commit `firebase-service-account.json` to version control!

4. **Configure Firebase Email Verification:**
   - Go to Firebase Console → Authentication → Settings → User actions
   - Enable "Email verification"
   - Set Action URL to: `http://localhost:3001/verify-email` (for development)
   - Customize email templates with your branding
5. **Run the FastAPI server:**
   ```sh
   uvicorn app.main:app --reload
   ```
   The API will be available at `http://localhost:8000`.

## How to run the frontend

1. **Navigate to the frontend directory:**
   ```sh
   cd test
   python test/serve_frontend.py
   ```
   This will serve the frontend at `http://localhost:3001` and open it in your browser.

## Main Endpoints

- `POST /api/auth/email-register` — Register with email/password (sends verification email)
- `POST /api/auth/email-login` — Login with email/password (requires verified email)
- `POST /api/auth/login-google` — Login with Google (send Firebase ID token)
- `POST /api/auth/resend-verification` — Resend verification email

## How the System Works: End-to-End Flow

### 1. Registration (Email/Password)

- User fills out the registration form on the frontend and submits their email, password, and display name.
- **Frontend** sends these credentials to the backend (`/api/auth/email-register`).
- **Backend**:
  - Validates the email (format, MX, disposable check).
  - Creates the user in Firebase Auth (using the Admin SDK).
  - Hashes and stores the password and user profile in its own database.
  - Generates a Firebase email verification link and sends it to the user via SMTP (custom email template).
  - Returns a JWT and user info (but user cannot log in until verified).
- **Frontend** shows a 'waiting for verification' screen with a resend verification button.

### 2. Email Verification

- User receives a verification email with a link (e.g., `/verify-user?...`).
- Clicking the link opens the frontend's verification page, which uses the Firebase JS SDK to apply the verification code (`applyActionCode`).
- **No backend API is called during this step**; verification is handled directly with Firebase.
- After successful verification, the user is prompted to log in.
- If the user did not receive the email, they can click 'Resend Verification' on the frontend, which calls the backend to send a new verification email.

### 3. Login (Email/Password)

- User enters their email and password on the frontend.
- **Frontend** uses Firebase JS SDK to sign in and checks if the email is verified.
- If verified, the frontend sends the credentials to the backend (`/api/auth/email-login`).
- **Backend**:
  - Verifies the password against its database.
  - Fetches the latest user info from Firebase to sync the `is_email_verified` status in its own DB.
  - If the email is verified, issues a JWT and returns user info.
  - If not verified, login is blocked and the user is prompted to verify their email.

### 4. Google SSO

- User clicks 'Continue with Google' on the frontend.
- **Frontend** uses Firebase JS SDK to sign in with Google and obtains a Firebase ID token.
- **Frontend** sends the ID token to the backend (`/api/auth/login-google`).
- **Backend**:
  - Verifies the ID token with Firebase.
  - Gets user info from Firebase and creates/updates the user in its own database.
  - Issues a JWT and returns user info.
- Google users are always considered verified (as per Firebase).

### 5. Resend Verification

- If a user needs a new verification email, the frontend calls `/api/auth/resend-verification` with the user's email.
- **Backend** generates a new verification link and sends it via SMTP.

## Backend Responsibilities

- Handles all user registration, login, and Google SSO logic.
- Manages user records in its own database (syncs with Firebase).
- Sends verification emails using Firebase Admin SDK and custom SMTP.
- Validates emails (format, MX, disposable domains).
- Hashes and stores passwords securely.
- Issues JWTs for authenticated sessions.
- Ensures email verification before allowing login.
- Provides endpoints for registration, login, Google SSO, and resending verification.

## Frontend Responsibilities

- Provides a modern, responsive UI for registration, login, and Google SSO.
- Uses Firebase JS SDK for Google SSO and email verification (not for registration/login).
- Handles the email verification link and applies the verification code using Firebase JS SDK.
- Shows appropriate UI states: registration, waiting for verification, login, and error/success messages.
- Calls backend APIs for registration, login, and resending verification emails.
- Never handles or stores passwords directly (except to send to backend for registration/login).

## Security and Best Practices

- Passwords are always hashed and never sent back to the frontend.
- JWTs contain only minimal user info (user id, sub, exp).
- Email verification is required before login is allowed.
- All email sending is handled by the backend using secure SMTP credentials.
- The frontend and backend are decoupled, with clear responsibilities.
- CORS is configured for secure frontend-backend communication.

## Summary

This project provides a robust, secure authentication system with:

- Email/password registration and login
- Google SSO
- Email verification (with custom resend flow)
- Modern frontend and secure backend
- Best practices for user management and security

## Email Configuration Options

### Option 1: Firebase Built-in Email (Recommended for development)

- Uses Firebase's email service
- No additional setup required
- Good for development and small apps

### Option 2: Custom SMTP (Recommended for production)

- Set up SMTP credentials in `.env`
- Better deliverability and branding
- Supports custom email templates

---

## Codebase Cleanliness and Final Notes

- All obsolete endpoints and code related to backend email verification have been removed.
- Email verification is now handled **entirely by the frontend** using the Firebase JS SDK (`applyActionCode`).
- The backend is only responsible for sending verification emails and checking verification status on login.
- There are **no unnecessary files or dead code** remaining in the backend or frontend.
- This documentation is fully up-to-date and matches the actual implementation and workflow.

You can now confidently use, extend, or deploy this project knowing it follows modern best practices and is free of legacy or unused code.
