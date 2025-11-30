import requests
from jose import jwt
from django.conf import settings
from rest_framework import authentication, exceptions

class Auth0JWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None

        parts = auth_header.split()
        if parts[0].lower() != "bearer" or len(parts) != 2:
            raise exceptions.AuthenticationFailed("Invalid Authorization header")

        token = parts[1]
        jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
        jwks = requests.get(jwks_url).json()
        unverified_header = jwt.get_unverified_header(token)

        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }

        if not rsa_key:
            raise exceptions.AuthenticationFailed("Unable to find appropriate key")

        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=settings.ALGORITHMS,
                audience=settings.API_IDENTIFIER,
                issuer=f"https://{settings.AUTH0_DOMAIN}/"
            )
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Token expired")
        except jwt.JWTClaimsError:
            raise exceptions.AuthenticationFailed("Incorrect claims.")
        except Exception:
            raise exceptions.AuthenticationFailed("Invalid token")

        # Create an in-memory user (optional: persist in DB)
        user = type("Auth0User", (), {"username": payload["sub"], "email": payload.get("email", None)})
        return (user, None)
