from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .jwt_utils import get_user_from_token

class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return None
        
        try:
            # expected: "bearer (token)"
            parts = auth_header.split()
            
            if len(parts) != 2 or parts[0].lower() != 'bearer':
                raise AuthenticationFailed('Invalid authorization header')
            
            token = parts[1]
            user = get_user_from_token(token)
            
            if not user:
                raise AuthenticationFailed('Invalid or expired token')
            
            return (user, token)
            
        except Exception as e:
            raise AuthenticationFailed(f'Authentication fail: {str(e)}')
    
    def authenticate_header(self, request):
        return 'Bearer realm="api"'