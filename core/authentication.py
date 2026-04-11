import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
from rest_framework import authentication, exceptions
from django.conf import settings
from .models import User

if settings.FIREBASE_SERVICE_ACCOUNT and not firebase_admin._apps:
    cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT)
    firebase_admin.initialize_app(cred)


class FirebaseAuthentication(authentication.BaseAuthentication):

    def authenticate(self, request):
        if not settings.FIREBASE_SERVICE_ACCOUNT:
            return None

        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        parts = auth_header.split()

        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        token = parts[1]

        try:
            decoded = firebase_auth.verify_id_token(token)
        except Exception:
            raise exceptions.AuthenticationFailed("Invalid Firebase token")

        firebase_uid = decoded["uid"]
        email = decoded.get("email", "")

        user, _ = User.objects.get_or_create(
            firebase_uid=firebase_uid,
            defaults={"username": email or firebase_uid, "email": email},
        )

        return (user, None)
