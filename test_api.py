"""
Test script for SyncActivity API endpoints
Run this after starting the Django server to test the API
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api"


def print_response(response, title):
    """Pretty print response"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")


def test_user_registration():
    """Test user registration"""
    url = f"{BASE_URL}/auth/register/"
    data = {
        "email": "test@example.com",
        "password": "SecurePass123!",
        "username": "testuser",
        "full_name": "Test User",
        "age": 25,
        "gender": "M"
    }
    response = requests.post(url, json=data)
    print_response(response, "User Registration")
    
    if response.status_code == 201:
        return response.json()["_id"]
    return None


def test_search_users(query):
    """Test user search"""
    url = f"{BASE_URL}/users/search/"
    params = {"q": query}
    response = requests.get(url, params=params)
    print_response(response, f"Search Users: {query}")
    return response.json()


def test_send_friend_request(sender_id, receiver_id):
    """Test sending friend request"""
    url = f"{BASE_URL}/friends/requests/send/"
    data = {
        "sender_id": sender_id,
        "receiver_id": receiver_id
    }
    response = requests.post(url, json=data)
    print_response(response, "Send Friend Request")
    
    if response.status_code == 201:
        return response.json()["_id"]
    return None


def test_pending_requests(user_id):
    """Test getting pending friend requests"""
    url = f"{BASE_URL}/friends/requests/pending/"
    params = {"user_id": user_id}
    response = requests.get(url, params=params)
    print_response(response, "Pending Friend Requests")
    return response.json()


def test_accept_friend_request(request_id, user_id):
    """Test accepting friend request"""
    url = f"{BASE_URL}/friends/requests/{request_id}/accept/"
    data = {"user_id": user_id}
    response = requests.post(url, json=data)
    print_response(response, "Accept Friend Request")


def test_list_friends(user_id):
    """Test listing friends"""
    url = f"{BASE_URL}/friends/"
    params = {"user_id": user_id}
    response = requests.get(url, params=params)
    print_response(response, "List Friends")
    return response.json()


def test_create_activity(user_id):
    """Test creating an activity"""
    url = f"{BASE_URL}/activities/"
    data = {
        "user_id": user_id,
        "activity_name": "Morning Run",
        "type": "running",
        "start_time": datetime.utcnow().isoformat() + "Z"
    }
    response = requests.post(url, json=data)
    print_response(response, "Create Activity")
    
    if response.status_code == 201:
        return response.json()["_id"]
    return None


def test_update_activity(activity_id):
    """Test updating an activity"""
    url = f"{BASE_URL}/activities/{activity_id}/"
    data = {
        "status": "completed",
        "end_time": datetime.utcnow().isoformat() + "Z",
        "distance": 5.2,
        "calories": 350.5,
        "avg_time": 5.8
    }
    response = requests.patch(url, json=data)
    print_response(response, "Update Activity")


def test_list_activities(user_id):
    """Test listing user activities"""
    url = f"{BASE_URL}/activities/"
    params = {"user_id": user_id}
    response = requests.get(url, params=params)
    print_response(response, "List User Activities")
    return response.json()


def test_friends_activities(user_id):
    """Test viewing friends' activities"""
    url = f"{BASE_URL}/activities/friends/"
    params = {"user_id": user_id}
    response = requests.get(url, params=params)
    print_response(response, "Friends' Activities")
    return response.json()


def test_unfriend(user_id, friend_id):
    """Test unfriending"""
    url = f"{BASE_URL}/friends/{friend_id}/unfriend/"
    params = {"user_id": user_id}
    response = requests.delete(url, params=params)
    print_response(response, "Unfriend")


def run_all_tests():
    """Run all tests in sequence"""
    print("\n" + "="*60)
    print("STARTING API TESTS")
    print("="*60)
    
    try:
        # Test 1: Register two users
        print("\n>>> Test 1: Register Users")
        user1_id = test_user_registration()
        
        if not user1_id:
            print("❌ Failed to register user 1. Exiting tests.")
            return
        
        # Register second user (modify data)
        url = f"{BASE_URL}/auth/register/"
        data = {
            "email": "test2@example.com",
            "password": "SecurePass123!",
            "username": "testuser2",
            "full_name": "Test User 2",
            "age": 28,
            "gender": "F"
        }
        response = requests.post(url, json=data)
        print_response(response, "User 2 Registration")
        user2_id = response.json()["_id"] if response.status_code == 201 else None
        
        if not user2_id:
            print("❌ Failed to register user 2. Continuing with available tests.")
        
        # Test 2: Search users
        print("\n>>> Test 2: Search Users")
        test_search_users("test")
        
        # Test 3: Send friend request
        if user2_id:
            print("\n>>> Test 3: Send Friend Request")
            request_id = test_send_friend_request(user1_id, user2_id)
            
            # Test 4: View pending requests
            if request_id:
                print("\n>>> Test 4: View Pending Requests")
                test_pending_requests(user2_id)
                
                # Test 5: Accept friend request
                print("\n>>> Test 5: Accept Friend Request")
                test_accept_friend_request(request_id, user2_id)
                
                # Test 6: List friends
                print("\n>>> Test 6: List Friends")
                test_list_friends(user1_id)
        
        # Test 7: Create activity
        print("\n>>> Test 7: Create Activity")
        activity_id = test_create_activity(user1_id)
        
        # Test 8: Update activity
        if activity_id:
            print("\n>>> Test 8: Update Activity")
            test_update_activity(activity_id)
            
            # Test 9: List activities
            print("\n>>> Test 9: List Activities")
            test_list_activities(user1_id)
        
        # Test 10: View friends' activities
        if user2_id:
            print("\n>>> Test 10: Create Activity for User 2")
            test_create_activity(user2_id)
            
            print("\n>>> Test 11: View Friends' Activities")
            test_friends_activities(user1_id)
            
            # Test 12: Unfriend
            print("\n>>> Test 12: Unfriend")
            test_unfriend(user1_id, user2_id)
            
            print("\n>>> Test 13: Verify Friends List After Unfriend")
            test_list_friends(user1_id)
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to the server.")
        print("Make sure the Django server is running: python manage.py runserver")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║         SyncActivity API Test Suite                      ║
    ║                                                          ║
    ║  Make sure the Django server is running before testing: ║
    ║  > cd BACKEND/sync                                       ║
    ║  > python manage.py runserver                           ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    run_all_tests()
