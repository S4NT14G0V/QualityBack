from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

class RootView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            "status": "OK",
            "message": "Welcome to the Sync Activity API",
            "docs": "/api/docs"
        })

