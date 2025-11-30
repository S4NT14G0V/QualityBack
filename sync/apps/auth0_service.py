import requests
import secrets
import base64
import hashlib

from urllib.parse import urlencode
from django.conf import settings

url = f"https://{settings.AUTH0_DOMAIN}/oauth/token"

def get_management_token():
    
    data = {
        "client_id": settings.AUTH0_MGMT_CLIENT_ID,
        "client_secret": settings.AUTH0_MGMT_CLIENT_SECRET,
        "audience": f"https://{settings.AUTH0_DOMAIN}/api/v2/",
        "grant_type": "client_credentials"
    }
    response = requests.post(url, json=data)
    response.raise_for_status()
    return response.json()["access_token"]

def login_auth0_user(request):
    code_verifier = secrets.token_urlsafe(64)
    state = secrets.token_urlsafe(64)

    request.session["code_verifier"] = code_verifier
    request.session["app_state"] = state

    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip("=")
    
    data = {
        "client_id": settings.AUTH0_CLIENT_ID,
        "redirect_uri": settings.AUTH0_CALLBACK_URL,
        "scope": "openid profile email",
        "response_type": "code",
        "response_mode": "query",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }
    
    url = f"https://{settings.AUTH0_DOMAIN}/authorize?{urlencode(data)}"

    return url

def create_auth0_user(email, password, name=None):
    token = get_management_token()
    url = f"https://{settings.AUTH0_DOMAIN}/api/v2/users"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "email": email,
        "password": password,
        "connection": settings.AUTH0_CONNECTION,
        "name": name or email
    }
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code != 200:
        print("Error creating user:", response.text)

    response.raise_for_status()
    return response.json()

def callback(code, code_verifier):
    token_url = f"https://{settings.AUTH0_DOMAIN}/oauth/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": settings.AUTH0_CLIENT_ID,
        "client_secret": settings.AUTH0_CLIENT_SECRET,
        "code": code,
        "redirect_uri": settings.AUTH0_CALLBACK_URL,
        "code_verifier": code_verifier
    }

    response = requests.post(token_url, data=data)

    if response.status_code != 201:
        print("Error:", response.text)

    tokens = response.json()

    return tokens