
import firebase_admin
from firebase_admin import credentials

cred = credentials.Certificate("firebase.json")
firebase_admin.initialize_app(cred)

# import os
# import firebase_admin
# from firebase_admin import credentials

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# cred_path = os.path.join(BASE_DIR, "firebase.json")

# cred = credentials.Certificate(cred_path)

# def init_firebase():
#     if not firebase_admin._apps:
#         firebase_admin.initialize_app(cred)
