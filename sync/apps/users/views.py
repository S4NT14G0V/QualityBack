from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from urllib.parse import quote_plus, urlencode
from django.http import JsonResponse
from django.conf import settings
from mongoengine import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter
from datetime import datetime

from apps.auth0_service import create_auth0_user, login_auth0_user, callback
from .models import UserProfile, FriendRequest, Activity, LiveDataPoint
from .serializers import (
    RegisterUserSerializer, LoginUserSerializer, UserProfileSerializer, 
    UserProfileBasicSerializer, FriendRequestSerializer, ActivitySerializer, 
    ActivityCreateSerializer, ActivityUpdateSerializer
)
from .jwt_utils import generate_jwt_token

class RegisterUserView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        request=RegisterUserSerializer,
        responses={201: {'type': 'object', 'properties': {
            'access_token': {'type': 'string'},
            'token_type': {'type': 'string'},
            'user': UserProfileSerializer
        }}}
    )
    def post(self, request):
        serializer = RegisterUserSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        username = serializer.validated_data.get("username")
        full_name = serializer.validated_data.get("full_name", "")
        age = serializer.validated_data.get("age")
        gender = serializer.validated_data.get("gender")

        try:
            # check if existing username
            if UserProfile.objects(username=username).first():
                return Response(
                    {"error": "Username already exists"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # check if existing email
            if UserProfile.objects(email=email).first():
                return Response(
                    {"error": "Email already exists"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create auth0 user (optional - for OAuth)
            try:
                auth0_user = create_auth0_user(email, password, full_name)
                auth0_id = auth0_user["user_id"]
            except Exception as auth0_error:
                # If Auth0 fails, create a local user with a generated auth0_id
                import uuid
                auth0_id = f"local_{uuid.uuid4().hex}"

            # Create user profile
            profile = UserProfile(
                auth0_id=auth0_id,
                email=email,
                username=username,
                full_name=full_name,
                age=age,
                gender=gender
            )
            
            # Hash and set password
            profile.set_password(password)
            profile.save()

            # generate token
            access_token = generate_jwt_token(str(profile.id), profile.email)

            # Prepare response with token and user data
            response_serializer = UserProfileSerializer(profile)
            return Response({
                "access_token": access_token,
                "token_type": "Bearer",
                "user": response_serializer.data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LoginUserView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        request={'application/json': {'type': 'object', 'properties': {
            'email': {'type': 'string'}, 
            'password': {'type': 'string'}
        }}},
        responses={200: {'type': 'object', 'properties': {
            'access_token': {'type': 'string'},
            'token_type': {'type': 'string'},
            'user': UserProfileSerializer
        }}}
    )
    def post(self, request):
        """Login with email and password"""
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {"error": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Find user by email
            user = UserProfile.objects(email=email).first()
            
            if not user:
                return Response(
                    {"error": "Invalid email or password"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Check password
            if not user.check_password(password):
                return Response(
                    {"error": "Invalid email or password"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Generate JWT token
            access_token = generate_jwt_token(str(user.id), user.email)
            
            user_serializer = UserProfileSerializer(user)
            
            return Response({
                "access_token": access_token,
                "token_type": "Bearer",
                "user": user_serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def get(self, request):
        """Get OAuth login URL (Auth0)"""
        try:
            url = login_auth0_user(request)
            return Response({"login_url": url})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        code = request.query_params.get("code")
        state = request.query_params.get("state")
        code_verifier = request.session.get("code_verifier")

        if not code:
            return Response({"error": "Authorization code missing"}, status=status.HTTP_400_BAD_REQUEST)
        if state != request.session.get("app_state"):
            return Response({"error": "Invalid state"}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            tokens = callback(code, code_verifier)
            if "access_token" not in tokens:
                return Response({"error": tokens}, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                "access_token": tokens["access_token"],
                "id_token": tokens.get("id_token"),
                "token_type": tokens["token_type"]
            })
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LogoutUserView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        request.session.flush()
        return_to_url = settings.AUTH0_LOGOUT_URL
        logout_url = f"https://{settings.AUTH0_DOMAIN}/v2/logout?" + urlencode({
            "returnTo": request.build_absolute_uri(return_to_url),
            "client_id": settings.AUTH0_CLIENT_ID 
        }, quote_via=quote_plus)
        return JsonResponse({"logout_url": logout_url})


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: UserProfileSerializer})
    def get(self, request):
        user = request.user
        
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)

    @extend_schema(
        request=UserProfileSerializer,
        responses={200: UserProfileSerializer}
    )
    def put(self, request):
        user = request.user

        # only allow updating full_name and username
        new_full_name = request.data.get("full_name")
        new_username = request.data.get("username")

        if new_username:
            existing_user = UserProfile.objects(username=new_username).first()
            if existing_user and str(existing_user.id) != str(user.id):
                return Response(
                    {"error": "Username already exists"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.username = new_username

        if new_full_name:
            user.full_name = new_full_name

        user.save()

        serializer = UserProfileSerializer(user)
        return Response(serializer.data)


class SearchUsersView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[OpenApiParameter(name='q', type=str, location=OpenApiParameter.QUERY)],
        responses={200: UserProfileBasicSerializer(many=True)}
    )
    def get(self, request):
        # username, email, or ID
        query = request.query_params.get('q', '')
        
        if not query:
            return Response(
                {"error": "Search query required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ID first
        try:
            user_by_id = UserProfile.objects.get(id=query)
            serializer = UserProfileBasicSerializer([user_by_id], many=True)
            return Response(serializer.data)
        except (UserProfile.DoesNotExist, Exception):
            pass

        # search by username, full_name, or email
        users = UserProfile.objects.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(full_name__icontains=query)
        )[:20]

        serializer = UserProfileBasicSerializer(users, many=True)
        return Response(serializer.data)

class FriendsListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: UserProfileBasicSerializer(many=True)})
    def get(self, request):
        user = request.user
        
        serializer = UserProfileBasicSerializer(user.friends, many=True)
        return Response(serializer.data)


class PendingFriendRequestsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: FriendRequestSerializer(many=True)})
    def get(self, request):
        user = request.user
        
        # get pending requests where user is either sender OR receiver
        pending_requests = FriendRequest.objects(
            Q(receiver=user, status='pending') | Q(sender=user, status='pending')
        ).order_by('-created_at')
        
        serializer = FriendRequestSerializer(pending_requests, many=True)
        return Response(serializer.data)

class SendFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request={'application/json': {'type': 'object', 'properties': {'receiver_id': {'type': 'string'}}}},
        responses={201: FriendRequestSerializer}
    )
    def post(self, request):
        sender = request.user
        receiver_id = request.data.get('receiver_id')
        
        if not receiver_id:
            return Response(
                {"error": "receiver_id required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        receiver = UserProfile.objects(id=receiver_id).first()
        
        if not receiver:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if sender == receiver:
            return Response(
                {"error": "Cannot send friend request to yourself"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # check if already friends
        if receiver in sender.friends:
            return Response(
                {"error": "Already friends"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # check if request already exists
        existing_request = FriendRequest.objects(
            Q(sender=sender, receiver=receiver) | Q(sender=receiver, receiver=sender),
            status='pending'
        ).first()
        
        if existing_request:
            return Response(
                {"error": "Friend request already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # create new friend request
        friend_request = FriendRequest(
            sender=sender,
            receiver=receiver,
            status='pending'
        )
        friend_request.save()
        
        serializer = FriendRequestSerializer(friend_request)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AcceptFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: FriendRequestSerializer})
    def post(self, request, request_id):
        user = request.user
        
        friend_request = FriendRequest.objects(id=request_id).first()
        if not friend_request:
            return Response(
                {"error": "Friend request not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # validate that the user is the receiver
        if friend_request.receiver != user:
            return Response(
                {"error": "Unauthorized to accept this request"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if friend_request.status != 'pending':
            return Response(
                {"error": "Request already processed"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        sender = friend_request.sender
        receiver = friend_request.receiver
        
        friend_request.status = 'accepted'
        friend_request.updated_at = datetime.utcnow()
        friend_request.save()
        
        # add each other as friends
        if receiver not in sender.friends:
            sender.friends.append(receiver)
            sender.save()
        
        if sender not in receiver.friends:
            receiver.friends.append(sender)
            receiver.save()
        
        serializer = FriendRequestSerializer(friend_request)
        return Response(serializer.data)

class RejectFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: FriendRequestSerializer})
    def post(self, request, request_id):
        user = request.user
        
        friend_request = FriendRequest.objects(id=request_id).first()
        if not friend_request:
            return Response(
                {"error": "Friend request not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # validate that the user is the receiver
        if friend_request.receiver != user:
            return Response(
                {"error": "Unauthorized to reject this request"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if friend_request.status != 'pending':
            return Response(
                {"error": "Request already processed"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        sender = friend_request.sender
        receiver = friend_request.receiver
        
        all_requests = FriendRequest.objects(
            Q(sender=sender, receiver=receiver) | Q(sender=receiver, receiver=sender)
        )
        
        for req in all_requests:
            req.delete()
                
        return Response(
            {"message": "Friend request rejected"},
            status=status.HTTP_200_OK
        )


class UnfriendView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}}
    )
    def delete(self, request, friend_id):
        user = request.user
        friend = UserProfile.objects(id=friend_id).first()
        
        if not friend:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # remove from both friend lists
        if friend in user.friends:
            user.friends.remove(friend)
            user.save()
        
        if user in friend.friends:
            friend.friends.remove(user)
            friend.save()
        
        # delete all existining friend requests to allow new requests
        friend_requests = FriendRequest.objects(
            Q(sender=user, receiver=friend) | Q(sender=friend, receiver=user)
        )
        for friend_request in friend_requests:
            friend_request.delete()
        
        return Response({"message": "Friend removed successfully"})

class ActivitiesListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: ActivitySerializer(many=True)})
    def get(self, request):
        user = request.user
        
        activities = Activity.objects(user_id=user).order_by('-created_at')
        serializer = ActivitySerializer(activities, many=True)
        return Response(serializer.data)

    @extend_schema(
        request=ActivityCreateSerializer,
        responses={201: ActivitySerializer}
    )
    def post(self, request):
        user = request.user
        
        serializer = ActivityCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # create the activity
        activity = Activity(
            activity_name=serializer.validated_data['activity_name'],
            user_id=user,
            type=serializer.validated_data['type'],
            start_time=serializer.validated_data.get('start_time', datetime.utcnow()),
            status='in_progress'
        )
        
        # add participants if its possible
        participant_ids = serializer.validated_data.get('participant_ids', [])
        for participant_id in participant_ids:
            participant = UserProfile.objects(id=participant_id).first()
            if participant:
                activity.participants.append(participant)
        
        activity.save()
        
        response_serializer = ActivitySerializer(activity)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

class ActivityDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: ActivitySerializer})
    def get(self, request, activity_id):
        activity = Activity.objects(id=activity_id).first()
        
        if not activity:
            return Response(
                {"error": "Activity not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ActivitySerializer(activity)
        return Response(serializer.data)

    @extend_schema(
        request=ActivityUpdateSerializer,
        responses={200: ActivitySerializer}
    )
    def patch(self, request, activity_id):
        activity = Activity.objects(id=activity_id).first()
        
        if not activity:
            return Response(
                {"error": "Activity not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ActivityUpdateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        if 'activity_name' in serializer.validated_data:
            activity.activity_name = serializer.validated_data['activity_name']
        if 'status' in serializer.validated_data:
            activity.status = serializer.validated_data['status']
        if 'end_time' in serializer.validated_data:
            activity.end_time = serializer.validated_data['end_time']
        if 'distance' in serializer.validated_data:
            activity.distance = serializer.validated_data['distance']
        if 'calories' in serializer.validated_data:
            activity.calories = serializer.validated_data['calories']
        if 'avg_time' in serializer.validated_data:
            activity.avg_time = serializer.validated_data['avg_time']
        if 'live_data' in serializer.validated_data:
            live_data_points = []
            for data_point in serializer.validated_data['live_data']:
                point = LiveDataPoint(**data_point)
                live_data_points.append(point)
            activity.live_data = live_data_points
        
        activity.updated_at = datetime.utcnow()
        activity.save()
        
        response_serializer = ActivitySerializer(activity)
        return Response(response_serializer.data)

    @extend_schema(
        responses={204: None}
    )
    def delete(self, request, activity_id):
        activity = Activity.objects(id=activity_id).first()
        
        if not activity:
            return Response(
                {"error": "Activity not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        activity.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class FriendsActivitiesView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: ActivitySerializer(many=True)})
    def get(self, request):
        user = request.user
        
        friend_activities = Activity.objects(
            user_id__in=user.friends
        ).order_by('-created_at')[:50]
        
        serializer = ActivitySerializer(friend_activities, many=True)
        return Response(serializer.data)