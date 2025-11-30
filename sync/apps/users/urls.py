from django.urls import path
from .views import (
    RegisterUserView, LoginUserView, CallbackView, LogoutUserView,
    ProfileView, SearchUsersView,
    FriendsListView, PendingFriendRequestsView, SendFriendRequestView,
    AcceptFriendRequestView, RejectFriendRequestView, UnfriendView,
    ActivitiesListView, ActivityDetailView, FriendsActivitiesView
)

urlpatterns = [
    path("auth/register/", RegisterUserView.as_view(), name='register_user'),
    path("auth/login/", LoginUserView.as_view(), name='login'),
    path("auth/callback/", CallbackView.as_view(), name="callback"),
    path("auth/logout/", LogoutUserView.as_view(), name="logout"),
    
    path("profile/", ProfileView.as_view(), name='profile'),
    path("users/search/", SearchUsersView.as_view(), name='search_users'),
    
    path("friends/", FriendsListView.as_view(), name='friends_list'),
    path("friends/requests/pending/", PendingFriendRequestsView.as_view(), name='pending_friend_requests'),
    path("friends/requests/send/", SendFriendRequestView.as_view(), name='send_friend_request'),
    path("friends/requests/<str:request_id>/accept/", AcceptFriendRequestView.as_view(), name='accept_friend_request'),
    path("friends/requests/<str:request_id>/reject/", RejectFriendRequestView.as_view(), name='reject_friend_request'),
    path("friends/<str:friend_id>/unfriend/", UnfriendView.as_view(), name='unfriend'),
    
    path("activities/", ActivitiesListView.as_view(), name='activities_list'),
    path("activities/friends/", FriendsActivitiesView.as_view(), name='friends_activities'),
    path("activities/<str:activity_id>/", ActivityDetailView.as_view(), name='activity_detail'),
]