from rest_framework import serializers
from .models import UserProfile, FriendRequest, Activity, LiveDataPoint


class RegisterUserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    username = serializers.CharField(max_length=50)
    full_name = serializers.CharField(max_length=200, required=False)
    age = serializers.IntegerField(required=False, allow_null=True)
    gender = serializers.ChoiceField(choices=['M', 'F', 'Other'], required=False)


class LoginUserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserProfileBasicSerializer(serializers.Serializer):
    _id = serializers.SerializerMethodField()
    username = serializers.CharField()
    full_name = serializers.CharField()
    profile_picture = serializers.CharField(allow_null=True)
    
    def get__id(self, obj):
        return str(obj.id)


class UserProfileSerializer(serializers.Serializer):
    _id = serializers.SerializerMethodField()
    auth0_id = serializers.CharField(read_only=True)
    username = serializers.CharField()
    email = serializers.EmailField()
    full_name = serializers.CharField(allow_blank=True)
    profile_picture = serializers.CharField(allow_null=True, required=False)
    age = serializers.IntegerField(allow_null=True, required=False)
    gender = serializers.ChoiceField(choices=['M', 'F', 'Other'])
    join_date = serializers.DateTimeField(read_only=True)
    friends = serializers.SerializerMethodField()
    challenges = serializers.ListField(child=serializers.CharField(), required=False)
    
    def get__id(self, obj):
        return str(obj.id)
    
    def get_friends(self, obj):
        friends_data = []
        for friend in obj.friends:
            friends_data.append({
                '_id': str(friend.id),
                'username': friend.username,
                'full_name': friend.full_name,
                'profile_picture': friend.profile_picture
            })
        return friends_data


class FriendRequestSerializer(serializers.Serializer):
    _id = serializers.SerializerMethodField()
    sender = serializers.SerializerMethodField()
    receiver = serializers.SerializerMethodField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    def get__id(self, obj):
        return str(obj.id)
    
    def get_sender(self, obj):
        return {
            '_id': str(obj.sender.id),
            'username': obj.sender.username,
            'full_name': obj.sender.full_name,
            'profile_picture': obj.sender.profile_picture
        }
    
    def get_receiver(self, obj):
        return {
            '_id': str(obj.receiver.id),
            'username': obj.receiver.username,
            'full_name': obj.receiver.full_name,
            'profile_picture': obj.receiver.profile_picture
        }


class LiveDataPointSerializer(serializers.Serializer):
    timestamp = serializers.DateTimeField()
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)
    speed = serializers.FloatField(required=False, allow_null=True)
    heart_rate = serializers.IntegerField(required=False, allow_null=True)
    calories = serializers.FloatField(required=False, allow_null=True)


class ActivitySerializer(serializers.Serializer):
    _id = serializers.SerializerMethodField()
    activity_name = serializers.CharField(max_length=200)
    user_id = serializers.SerializerMethodField()
    calories = serializers.FloatField(default=0.0)
    status = serializers.ChoiceField(
        choices=['planned', 'in_progress', 'completed', 'cancelled'],
        default='planned'
    )
    start_time = serializers.DateTimeField(required=False, allow_null=True)
    end_time = serializers.DateTimeField(required=False, allow_null=True)
    distance = serializers.FloatField(default=0.0)
    type = serializers.ChoiceField(
        choices=['running', 'cycling', 'walking', 'swimming', 'gym', 'other']
    )
    avg_time = serializers.FloatField(default=0.0)
    live_data = LiveDataPointSerializer(many=True, required=False)
    participants = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    def get__id(self, obj):
        return str(obj.id)
    
    def get_user_id(self, obj):
        if obj.user_id:
            return {
                '_id': str(obj.user_id.id),
                'username': obj.user_id.username,
                'full_name': obj.user_id.full_name
            }
        return None
    
    def get_participants(self, obj):
        participants_data = []
        for participant in obj.participants:
            participants_data.append({
                '_id': str(participant.id),
                'username': participant.username,
                'full_name': participant.full_name,
                'profile_picture': participant.profile_picture
            })
        return participants_data


class ActivityCreateSerializer(serializers.Serializer):
    activity_name = serializers.CharField(max_length=200)
    type = serializers.ChoiceField(
        choices=['running', 'cycling', 'walking', 'hiking', 'swimming', 'gym', 'other']
    )
    start_time = serializers.DateTimeField(required=False, allow_null=True)
    participant_ids = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )


class ActivityUpdateSerializer(serializers.Serializer):
    activity_name = serializers.CharField(max_length=200, required=False)
    status = serializers.ChoiceField(
        choices=['planned', 'in_progress', 'completed', 'cancelled'],
        required=False
    )
    end_time = serializers.DateTimeField(required=False, allow_null=True)
    distance = serializers.FloatField(required=False)
    calories = serializers.FloatField(required=False)
    avg_time = serializers.FloatField(required=False)
    live_data = LiveDataPointSerializer(many=True, required=False)