# FastAPI + Firebase Authentication Example

This project demonstrates a secure authentication system using FastAPI (Python backend), Firebase (for authentication and SSO), and a modern HTML/JS frontend.

## What does this project do?

- **Email/Password Auth:** Users can register and log in with email and password. All authentication is handled by the backend (not the frontend).
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
  utils/          # Security and JWT helpers

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
   ```
3. **Run the FastAPI server:**
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

- `POST /api/auth/email-register` — Register with email/password
- `POST /api/auth/email-login` — Login with email/password
- `POST /api/auth/login/google` — Login with Google (send Firebase ID token)

## How Google SSO works (secure flow)

1. User clicks "Continue with Google" on the frontend
2. Frontend uses Firebase JS SDK to get a Google ID token
3. Frontend sends the ID token to `/api/auth/login/google`
4. Backend verifies the token with Firebase, creates/updates the user, and returns a JWT

## How Email/Password works

1. User registers or logs in via the frontend
2. Frontend sends credentials to backend
3. Backend creates/verifies user in Firebase and its own DB, then returns a JWT

## Security

- Passwords are hashed and never sent to the frontend
- JWT tokens only contain minimal info (user id, sub, exp)
- Only public profile info is sent in login/register responses

---

**This project is a great starting point for secure, modern authentication with FastAPI and Firebase!**
