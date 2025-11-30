import jwt
from datetime import datetime, timedelta
from django.conf import settings
from typing import Optional, Dict, Any

JWT_SECRET = getattr(settings, 'JWT_SECRET_KEY')
JWT_ALGORITHM = getattr(settings, 'JWT_ALGORITHM')
JWT_EXPIRATION_DELTA = timedelta(days=getattr(settings, 'JWT_EXPIRATION_DELTA'))

def generate_jwt_token(user_id: str, email: str) -> str:
    payload = {
        'user_id': str(user_id),
        'email': email,
        'exp': datetime.utcnow() + JWT_EXPIRATION_DELTA,
        'iat': datetime.utcnow(),
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

def decode_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        # Token has expired
        return None
    except jwt.InvalidTokenError:
        # Invalid token
        return None

def get_user_from_token(token: str):
    from .models import UserProfile
    
    payload = decode_jwt_token(token)
    if not payload:
        return None
    
    user_id = payload.get('user_id')
    if not user_id:
        return None
    
    try:
        user = UserProfile.objects(id=user_id).first()
        return user
    except Exception:
        return None