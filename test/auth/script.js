const loginForm = document.getElementById("loginForm");
const signupForm = document.getElementById("signupForm");
const googleSignInBtn = document.getElementById("googleSignIn");
const statusMessage = document.getElementById("statusMessage");

// Backend API URL
const API_BASE_URL = "http://localhost:8000";

// Form switching functions
function showLogin() {
  loginForm.style.display = "block";
  signupForm.style.display = "none";
  document
    .querySelectorAll(".toggle-btn")
    .forEach((btn) => btn.classList.remove("active"));
  document.querySelector(".toggle-btn:first-child").classList.add("active");
  clearStatus();
}

function showSignup() {
  loginForm.style.display = "none";
  signupForm.style.display = "block";
  document
    .querySelectorAll(".toggle-btn")
    .forEach((btn) => btn.classList.remove("active"));
  document.querySelector(".toggle-btn:last-child").classList.add("active");
  clearStatus();
}

// Status message functions
function showStatus(message, type = "info") {
  statusMessage.textContent = message;
  statusMessage.className = `status-message ${type}`;
  console.log(`Status: ${type} - ${message}`);
}

function clearStatus() {
  statusMessage.style.display = "none";
  statusMessage.className = "status-message";
}

// API call function
async function callBackendAPI(endpoint, data) {
  try {
    console.log(`Calling API: ${API_BASE_URL}${endpoint}`);
    console.log("Request data:", data);

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    console.log(`Response status: ${response.status} ${response.statusText}`);

    const result = await response.json();
    console.log("API Response:", result);

    if (!response.ok) {
      console.error(
        `Backend API Error: ${response.status} - ${
          result.detail || response.statusText
        }`
      );
      throw new Error(
        result.detail || `HTTP ${response.status}: ${response.statusText}`
      );
    }

    console.log("API call successful");
    return result;
  } catch (error) {
    console.error("API Error Details:", {
      message: error.message,
      stack: error.stack,
      type: error.constructor.name,
    });
    throw error;
  }
}

// Email/Password Registration (Backend Only)
signupForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const name = document.getElementById("signupName").value;
  const email = document.getElementById("signupEmail").value;
  const password = document.getElementById("signupPassword").value;

  const submitBtn = signupForm.querySelector('button[type="submit"]');
  submitBtn.disabled = true;
  submitBtn.textContent = "Creating Account...";

  try {
    // Call backend to create user and send verification email
    const result = await callBackendAPI("/api/auth/email-register", {
      email: email,
      password: password,
      display_name: name,
    });
    showWaitingForVerification(email);
  } catch (error) {
    let errorMessage = error.message;
    if (errorMessage.includes("Email already exists")) {
      errorMessage = "Email already exists. Please try logging in instead.";
    } else if (errorMessage.includes("weak-password")) {
      errorMessage = "Password is too weak. Please use at least 6 characters.";
    } else if (errorMessage.includes("invalid-email")) {
      errorMessage = "Invalid email address.";
    }
    showStatus(errorMessage, "error");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Sign Up";
  }
});

// Email/Password Login (Firebase JS SDK)
loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const email = document.getElementById("loginEmail").value;
  const password = document.getElementById("loginPassword").value;

  const submitBtn = loginForm.querySelector('button[type="submit"]');
  submitBtn.disabled = true;
  submitBtn.textContent = "Logging in...";

  try {
    // Sign in with Firebase
    const userCredential = await window.signInWithEmailAndPassword(
      window.firebaseAuth,
      email,
      password
    );
    const user = userCredential.user;
    if (!user.emailVerified) {
      showStatus(
        "Please verify your email address before logging in. Check your inbox for the verification link.",
        "error"
      );
      await window.signOut(window.firebaseAuth);
      return;
    }
    // Get Firebase ID token
    const idToken = await user.getIdToken();
    // Send credentials to backend for session/JWT
    const result = await callBackendAPI("/api/auth/email-login", {
      email,
      password,
    });
    handleLoginSuccess(result.access_token, result.user);
  } catch (error) {
    let errorMessage = error.message;
    if (
      error.code === "auth/wrong-password" ||
      error.code === "auth/user-not-found"
    ) {
      errorMessage =
        "Invalid email or password. Please check your credentials.";
    } else if (error.code === "auth/invalid-email") {
      errorMessage = "Invalid email address.";
    }
    showStatus(errorMessage, "error");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Login";
  }
});

// Google Sign In

googleSignInBtn.addEventListener("click", async () => {
  googleSignInBtn.disabled = true;
  googleSignInBtn.innerHTML = "<span>Signing in...</span>";

  try {
    const provider = new window.GoogleAuthProvider();
    const result = await window.signInWithPopup(window.firebaseAuth, provider);

    // Get the Firebase ID token
    const idToken = await result.user.getIdToken();

    // Sending ID token to backend
    const apiResult = await callBackendAPI("/api/auth/login-google", {
      id_token: idToken,
    });

    handleLoginSuccess(apiResult.access_token, apiResult.user);
  } catch (error) {
    console.error("Google sign-in error:", error);
    let errorMessage = error.message;
    if (error.code === "auth/popup-closed-by-user") {
      errorMessage = "Sign-in was cancelled.";
    } else if (error.code === "auth/popup-blocked") {
      errorMessage = "Pop-up was blocked. Please allow pop-ups for this site.";
    }
    showStatus(errorMessage, "error");
  } finally {
    googleSignInBtn.disabled = false;
    googleSignInBtn.innerHTML = `
      <svg width="20" height="20" viewBox="0 0 24 24">
        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
      </svg>
      Continue with Google
    `;
  }
});

// Test backend connectivity
async function testBackendConnection() {
  try {
    console.log("Testing backend connection...");
    const response = await fetch(`${API_BASE_URL}/`);
    if (response.ok) {
      const text = await response.text();
      console.log("Backend is reachable:", text);
      return true;
    } else {
      console.error("Backend responded with error:", response.status);
      return false;
    }
  } catch (error) {
    console.error("Backend connection failed:", error);
    showStatus(
      "Cannot connect to backend server. Please check if it's running.",
      "error"
    );
    return false;
  }
}

// Check if user is already logged in
window.addEventListener("load", async () => {
  const token = localStorage.getItem("jwt_token");
  const user = localStorage.getItem("user");

  if (token && user) {
    showStatus("You are already logged in!", "info");
    console.log("User already logged in:", JSON.parse(user));
  }

  // Test backend connection
  await testBackendConnection();

  // Add debug buttons
  const debugDiv = document.createElement("div");
  debugDiv.style.position = "fixed";
  debugDiv.style.top = "10px";
  debugDiv.style.right = "10px";
  debugDiv.style.zIndex = "1000";

  const logoutBtn = document.createElement("button");
  logoutBtn.textContent = "Logout";
  logoutBtn.onclick = logout;
  logoutBtn.style.marginRight = "10px";
  logoutBtn.style.padding = "5px 10px";

  const clearBtn = document.createElement("button");
  clearBtn.textContent = "Clear Data";
  clearBtn.onclick = clearTestData;
  clearBtn.style.padding = "5px 10px";

  const testBtn = document.createElement("button");
  testBtn.textContent = "Test Backend";
  testBtn.onclick = testBackendConnection;
  testBtn.style.marginLeft = "10px";
  testBtn.style.padding = "5px 10px";

  debugDiv.appendChild(logoutBtn);
  debugDiv.appendChild(clearBtn);
  debugDiv.appendChild(testBtn);
  document.body.appendChild(debugDiv);
});

// Logout function
function logout() {
  localStorage.removeItem("jwt_token");
  localStorage.removeItem("user");
  showStatus("Logged out successfully!", "info");
}

// Clear test data function
function clearTestData() {
  localStorage.clear();
  showStatus("Test data cleared!", "info");
}

// After successful registration, show waiting for verification section
function showWaitingForVerification(email) {
  document.getElementById("loginForm").style.display = "none";
  document.getElementById("signupForm").style.display = "none";
  document.getElementById("waitingVerification").style.display = "block";
  document.getElementById("verificationStatusMessage").textContent = "";
  // Store email for resend
  window.lastRegisteredEmail = email;
}

// Add event listener for resend verification
const resendVerificationBtn = document.getElementById("resendVerificationBtn");
if (resendVerificationBtn) {
  resendVerificationBtn.addEventListener("click", async () => {
    const email = window.lastRegisteredEmail;
    if (!email) {
      document.getElementById("verificationStatusMessage").textContent =
        "No email found. Please register again.";
      return;
    }
    resendVerificationBtn.disabled = true;
    resendVerificationBtn.textContent = "Resending...";
    try {
      const response = await callBackendAPI(
        "/api/auth/resend-verification",
        email,
        "POST",
        true
      );
      document.getElementById("verificationStatusMessage").textContent =
        "Verification email sent!";
    } catch (error) {
      document.getElementById("verificationStatusMessage").textContent =
        "Failed to resend verification email.";
    } finally {
      resendVerificationBtn.disabled = false;
      resendVerificationBtn.textContent = "Resend Verification Email";
    }
  });
}

// Add event listener for back to login
const backToLoginBtn = document.getElementById("backToLoginBtn");
if (backToLoginBtn) {
  backToLoginBtn.addEventListener("click", () => {
    document.getElementById("waitingVerification").style.display = "none";
    document.getElementById("loginForm").style.display = "block";
    document.getElementById("signupForm").style.display = "none";
    document.getElementById("verificationStatusMessage").textContent = "";
  });
}

// Forgot Password Flow
const forgotPasswordLink = document.getElementById("forgotPasswordLink");
const passwordResetRequestForm = document.getElementById(
  "passwordResetRequestForm"
);
const backToLoginFromReset = document.getElementById("backToLoginFromReset");

if (forgotPasswordLink && passwordResetRequestForm && backToLoginFromReset) {
  forgotPasswordLink.addEventListener("click", (e) => {
    e.preventDefault();
    loginForm.style.display = "none";
    signupForm.style.display = "none";
    passwordResetRequestForm.style.display = "block";
    clearStatus();
  });

  backToLoginFromReset.addEventListener("click", (e) => {
    e.preventDefault();
    passwordResetRequestForm.style.display = "none";
    loginForm.style.display = "block";
    clearStatus();
  });

  passwordResetRequestForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const resetEmail = document.getElementById("resetEmail").value;
    const submitBtn = passwordResetRequestForm.querySelector(
      'button[type="submit"]'
    );
    submitBtn.disabled = true;
    submitBtn.textContent = "Sending...";
    try {
      await callBackendAPI("/api/auth/password-reset", { email: resetEmail });
      showStatus(
        "If this email is registered, a password reset link has been sent.",
        "success"
      );
    } catch (error) {
      showStatus(
        "Failed to send password reset email. Please try again.",
        "error"
      );
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Send Reset Link";
    }
  });
}

// After successful login, redirect to invite.html
function handleLoginSuccess(token, user) {
  localStorage.setItem("access_token", token);
  localStorage.setItem("jwt_token", token);
  localStorage.setItem("user", JSON.stringify(user));
  showStatus("Login successful!", "success");
  setTimeout(() => {
    alert("Login successful! Welcome back.");
    window.location.href = "/invite.html";
  }, 2000);
}
