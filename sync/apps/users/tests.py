import unittest
from mongoengine import connect, disconnect
import mongomock
from .models import UserProfile

class UserProfileModelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Connect to an in-memory MongoDB mock
        connect(
            "test_db",
            host="mongodb://localhost",
            alias="default",
            mongo_client_class=mongomock.MongoClient
        )

    @classmethod
    def tearDownClass(cls):
        # Disconnect once after all tests
        disconnect(alias="default")

    def setUp(self):
        # Clear data before each test
        UserProfile.objects.delete()
        # Create some sample users
        self.user1 = UserProfile(auth0_id="auth0|12345", email="john@example.com", name="John Doe").save()
        self.user2 = UserProfile(auth0_id="auth0|67890", email="jane@example.com", name="Jane Roe").save()

    def tearDown(self):
        # Clean up after each test (important when using MongoDB)
        UserProfile.objects.delete()

    def test_userprofile_creation(self):
        user = UserProfile.objects.get(auth0_id="auth0|12345")
        self.assertEqual(user.email, "john@example.com")
        self.assertEqual(user.name, "John Doe")

    def test_unique_auth0_id(self):
        with self.assertRaises(Exception):
            # Try to create another user with same auth0_id — should raise an error
            UserProfile(auth0_id="auth0|12345", email="duplicate@example.com").save()

