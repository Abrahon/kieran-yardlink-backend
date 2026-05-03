# import firebase_admin
# from firebase_admin import credentials

# cred = credentials.Certificate("firebase-key.json")

# if not firebase_admin._apps:
#     firebase_admin.initialize_app(cred)

# notifications/firebase.py

import firebase_admin
from firebase_admin import credentials

cred = credentials.Certificate("firebase.json")
firebase_admin.initialize_app(cred)


# production 
# import firebase_admin
# from firebase_admin import credentials
# from django.conf import settings

# if not firebase_admin._apps:
#     cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
#     firebase_admin.initialize_app(cred)