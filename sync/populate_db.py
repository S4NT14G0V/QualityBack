"""
Database Population Script for SyncActivity
Creates sample users, friend relationships, and activities for testing
"""

import os
import sys
import django
from datetime import datetime, timedelta
import random

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import UserProfile, FriendRequest, Activity, LiveDataPoint
from pymongo import MongoClient
from django.conf import settings


def drop_indexes():
    """Drop all indexes to avoid conflicts"""
    print("Dropping existing indexes...")
    try:
        # Get MongoDB connection from Django settings
        from mongoengine import connect
        from mongoengine.connection import get_db
        
        db = get_db()
        
        # Drop indexes for each collection
        collections = ['users', 'friend_requests', 'activities']
        for collection_name in collections:
            try:
                collection = db[collection_name]
                # Drop all indexes except _id
                collection.drop_indexes()
                print(f"   ✓ Dropped indexes for {collection_name}")
            except Exception as e:
                print(f"   ⚠ Could not drop indexes for {collection_name}: {e}")
        
        print("Indexes dropped!\n")
    except Exception as e:
        print(f"Warning: Could not drop indexes: {e}\n")


def clear_database():
    """Clear all existing data"""
    print("Clearing existing data...")
    try:
        Activity.objects.all().delete()
        print("   ✓ Activities cleared")
    except Exception as e:
        print(f"   ⚠ Activities: {e}")
    
    try:
        FriendRequest.objects.all().delete()
        print("   ✓ Friend requests cleared")
    except Exception as e:
        print(f"   ⚠ Friend requests: {e}")
    
    try:
        UserProfile.objects.all().delete()
        print("   ✓ User profiles cleared")
    except Exception as e:
        print(f"   ⚠ User profiles: {e}")
    
    print("Database cleared!\n")


def create_users():
    """Create sample users"""
    print("Creating users...")
    
    users_data = [
        {
            "auth0_id": "auth0|user001",
            "username": "john_runner",
            "email": "john@example.com",
            "full_name": "John Doe",
            "password": "hashed_password_123",
            "age": 28,
            "gender": "M"
        },
        {
            "auth0_id": "auth0|user002",
            "username": "sarah_cyclist",
            "email": "sarah@example.com",
            "full_name": "Sarah Johnson",
            "password": "hashed_password_456",
            "age": 25,
            "gender": "F"
        },
        {
            "auth0_id": "auth0|user003",
            "username": "mike_swimmer",
            "email": "mike@example.com",
            "full_name": "Mike Wilson",
            "password": "hashed_password_789",
            "age": 32,
            "gender": "M"
        },
        {
            "auth0_id": "auth0|user004",
            "username": "emma_yoga",
            "email": "emma@example.com",
            "full_name": "Emma Davis",
            "password": "hashed_password_abc",
            "age": 27,
            "gender": "F"
        }
    ]
    
    created_users = []
    for user_data in users_data:
        user = UserProfile(**user_data)
        user.save()
        created_users.append(user)
        print(f"   Created user: {user.username} ({user.full_name})")
    
    print(f"Created {len(created_users)} users!\n")
    return created_users


def create_friendships(users):
    """Create friend relationships"""
    print("Creating friendships...")
    
    # Define friend pairs (index based)
    friendships = [
        (0, 1),  # John & Sarah
        (0, 2),  # John & Mike
        (1, 3),  # Sarah & Emma
    ]
    
    for i, j in friendships:
        user1 = users[i]
        user2 = users[j]
        
        # Add to friends list (bidirectional)
        if user2 not in user1.friends:
            user1.friends.append(user2)
            user1.save()
        
        if user1 not in user2.friends:
            user2.friends.append(user1)
            user2.save()
        
        print(f"   ✓ {user1.username} ↔ {user2.username}")
    
    print(f"Created {len(friendships)} friendships!\n")
    return friendships


def create_friend_requests(users):
    """Create pending friend requests"""
    print("Creating friend requests...")
    
    # Pending requests (sender_idx, receiver_idx)
    pending_requests = [
        (2, 3),  # Mike → Emma
        (0, 3),  # John → Emma
        (3, 0),  # Emma → John (bidirectional example)
        (1, 2),  # Sarah → Mike
        (2, 0),  # Mike → John
    ]
    
    created_requests = []
    for sender_idx, receiver_idx in pending_requests:
        sender = users[sender_idx]
        receiver = users[receiver_idx]
        
        # Skip if already friends
        if receiver in sender.friends:
            print(f"   ⚠ Skipped: {sender.username} and {receiver.username} are already friends")
            continue
        
        # Check if request already exists
        existing = FriendRequest.objects(
            sender=sender,
            receiver=receiver,
            status='pending'
        ).first()
        
        if existing:
            print(f"   ⚠ Skipped: Request from {sender.username} → {receiver.username} already exists")
            continue
        
        friend_request = FriendRequest(
            sender=sender,
            receiver=receiver,
            status='pending'
        )
        friend_request.save()
        created_requests.append(friend_request)
        print(f"   ✓ {sender.username} → {receiver.username} (pending)")
    
    print(f"Created {len(created_requests)} pending requests!\n")
    return created_requests


def create_activities(users):
    """Create sample activities"""
    print("Creating activities...")
    
    activity_types = ['running', 'cycling', 'walking', 'swimming', 'gym']
    activity_names = {
        'running': ['Morning Run', 'Evening Jog', '5K Training', 'Park Run', 'Trail Run'],
        'cycling': ['City Ride', 'Mountain Biking', 'Evening Cycle', 'Weekend Tour', 'Speed Training'],
        'walking': ['Morning Walk', 'Park Stroll', 'City Walk', 'Evening Walk', 'Nature Walk'],
        'swimming': ['Pool Session', 'Open Water Swim', 'Lap Swimming', 'Beach Swim', 'Training Session'],
        'gym': ['Strength Training', 'Cardio Session', 'Full Body Workout', 'Leg Day', 'Upper Body']
    }
    
    created_activities = []
    
    # Create activities for each user
    for user in users:
        num_activities = random.randint(2, 5)
        
        for i in range(num_activities):
            activity_type = random.choice(activity_types)
            activity_name = random.choice(activity_names[activity_type])
            
            # Random date in the last 30 days
            days_ago = random.randint(1, 30)
            start_time = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(6, 20))
            duration_minutes = random.randint(20, 120)
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            # Calculate stats based on activity type and duration
            if activity_type == 'running':
                distance = round(random.uniform(3.0, 15.0), 2)
                calories = round(distance * 65, 1)
                avg_time = round(duration_minutes / distance, 2)
            elif activity_type == 'cycling':
                distance = round(random.uniform(10.0, 50.0), 2)
                calories = round(distance * 35, 1)
                avg_time = round(duration_minutes / distance, 2)
            elif activity_type == 'walking':
                distance = round(random.uniform(2.0, 10.0), 2)
                calories = round(distance * 45, 1)
                avg_time = round(duration_minutes / distance, 2)
            elif activity_type == 'swimming':
                distance = round(random.uniform(0.5, 3.0), 2)
                calories = round(distance * 400, 1)
                avg_time = round(duration_minutes / distance, 2)
            else:  # gym
                distance = 0
                calories = round(random.uniform(200, 600), 1)
                avg_time = duration_minutes
            
            # Decide status (70% completed, 20% in_progress, 10% planned)
            status_choice = random.random()
            if status_choice < 0.7:
                status = 'completed'
            elif status_choice < 0.9:
                status = 'in_progress'
                end_time = None
            else:
                status = 'planned'
                start_time = datetime.utcnow() + timedelta(days=random.randint(1, 7))
                end_time = None
                distance = 0
                calories = 0
            
            # Create activity
            activity = Activity(
                activity_name=activity_name,
                user_id=user,
                calories=calories,
                status=status,
                start_time=start_time,
                end_time=end_time,
                distance=distance,
                type=activity_type,
                avg_time=avg_time
            )
            
            # Add live data for completed activities (some of them)
            if status == 'completed' and random.random() > 0.6:
                num_points = random.randint(3, 8)
                for point_idx in range(num_points):
                    timestamp = start_time + timedelta(minutes=duration_minutes * point_idx / num_points)
                    live_point = LiveDataPoint(
                        timestamp=timestamp,
                        latitude=40.7128 + random.uniform(-0.05, 0.05),
                        longitude=-74.0060 + random.uniform(-0.05, 0.05),
                        speed=random.uniform(5.0, 25.0),
                        heart_rate=random.randint(100, 170),
                        calories=calories * point_idx / num_points
                    )
                    activity.live_data.append(live_point)
            
            # Add participants (some activities are group activities with friends)
            if status == 'completed' and random.random() > 0.7 and len(user.friends) > 0:
                num_participants = min(random.randint(1, 2), len(user.friends))
                participants = random.sample(user.friends, num_participants)
                for participant in participants:
                    activity.participants.append(participant)
            
            activity.save()
            created_activities.append(activity)
            
            participants_str = f" (with {len(activity.participants)} friends)" if activity.participants else ""
            live_data_str = f" [{len(activity.live_data)} data points]" if activity.live_data else ""
            print(f"   ✓ {user.username}: {activity_name} - {status}{participants_str}{live_data_str}")
    
    print(f"Created {len(created_activities)} activities!\n")
    return created_activities


def main():
    """Main execution function"""
    print("\n" + "="*60)
    print("SYNCACTIVITY DATABASE POPULATION")
    print("="*60 + "\n")
    
    try:
        # Drop indexes first to avoid conflicts
        drop_indexes()
        
        # Clear existing data
        clear_database()
        
        # Create new data
        users = create_users()
        friendships = create_friendships(users)
        friend_requests = create_friend_requests(users)
        activities = create_activities(users)
        
        # Print summary
        print("\n" + "="*60)
        print("📊 DATABASE SUMMARY")
        print("="*60)
        
        print(f"\n👥 Users: {len(users)}")
        for user in users:
            print(f"   • {user.username} ({user.full_name}) - {len(user.friends)} friends")
        
        print(f"\n🤝 Friendships: {len(friendships)}")
        
        print(f"\n📬 Friend Requests: {len(friend_requests)} pending")
        
        print(f"\n🏃 Activities: {len(activities)}")
        status_counts = {}
        type_counts = {}
        for activity in activities:
            status_counts[activity.status] = status_counts.get(activity.status, 0) + 1
            type_counts[activity.type] = type_counts.get(activity.type, 0) + 1
        
        print("   By Status:")
        for status, count in status_counts.items():
            print(f"      • {status}: {count}")
        
        print("   By Type:")
        for activity_type, count in type_counts.items():
            print(f"      • {activity_type}: {count}")
        
        print("\n" + "="*60)
        print("✅ Database populated successfully!")
        print("="*60)
        
        print("\n💡 Test Users:")
        for user in users:
            print(f"   • Username: {user.username}")
        
        print("\n📝 To get user IDs for testing:")
        print("   curl http://localhost:8000/api/users/search/?q=john")
        print("\n🔑 Use X-User-ID header for authenticated endpoints")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
