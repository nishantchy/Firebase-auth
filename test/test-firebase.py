import firebase_admin
from firebase_admin import credentials

try:
    cred = credentials.Certificate('./firebase-service-account.json')
    firebase_admin.initialize_app(cred)
    print("Firebase Admin SDK initialized successfully!")
except Exception as e:
    print(f"Error: {e}")