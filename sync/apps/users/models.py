from mongoengine import (
    Document, StringField, EmailField, IntField, 
    DateTimeField, ListField, ReferenceField, FloatField,
    DictField, EmbeddedDocument, EmbeddedDocumentField
)
from datetime import datetime
from django.contrib.auth.hashers import make_password, check_password

class UserProfile(Document):
    auth0_id = StringField(required=True, unique=True)
    username = StringField(required=True, unique=True)
    email = EmailField(required=True, unique=True)
    full_name = StringField()
    password = StringField()  # hashed password
    profile_picture = StringField()
    age = IntField()
    gender = StringField(choices=['M', 'F', 'Other'])
    join_date = DateTimeField(default=datetime.utcnow)
    friends = ListField(ReferenceField('self'))
    challenges = ListField(StringField())

    meta = {
        'collection': 'users',
        'indexes': [
            {'fields': ['username'], 'unique': True},
            {'fields': ['email'], 'unique': True},
            {'fields': ['auth0_id'], 'unique': True}
        ]
    }

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
    @property
    def is_authenticated(self):
        return True


class FriendRequest(Document):
    sender = ReferenceField('UserProfile', required=True)
    receiver = ReferenceField('UserProfile', required=True)
    status = StringField(choices=['pending', 'accepted', 'rejected'], default='pending')
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'friend_requests',
        'indexes': [
            'sender',
            'receiver',
            'status',
            ('sender', 'receiver')
        ]
    }


class LiveDataPoint(EmbeddedDocument):
    timestamp = DateTimeField(required=True)
    latitude = FloatField()
    longitude = FloatField()
    speed = FloatField()
    heart_rate = IntField()
    calories = FloatField()


class Activity(Document):
    activity_name = StringField(required=True)
    user_id = ReferenceField('UserProfile', required=True)
    calories = FloatField(default=0.0)
    status = StringField(
        choices=['planned', 'in_progress', 'completed', 'cancelled'],
        default='planned'
    )
    start_time = DateTimeField()
    end_time = DateTimeField()
    distance = FloatField(default=0.0)
    type = StringField(
        required=True,
        choices=['running', 'cycling', 'walking', 'hiking', 'swimming', 'gym', 'other']
    )
    avg_time = FloatField(default=0.0)
    live_data = ListField(EmbeddedDocumentField(LiveDataPoint))
    participants = ListField(ReferenceField('UserProfile'))
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'activities',
        'indexes': [
            'user_id',
            'status',
            'type',
            'start_time',
            '-created_at'
        ]
    }