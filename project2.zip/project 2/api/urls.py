from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/me/', views.CurrentUserView.as_view(), name='current_user'),

    # Users & Profiles
    path('users/profile/update/', views.UpdateProfileView.as_view(), name='update_profile'),
    path('users/follow-requests/', views.FollowRequestsListView.as_view(), name='follow_requests_list'),
    path('users/follow-requests/<int:follow_id>/<str:action>/', views.HandleFollowRequestView.as_view(), name='handle_follow_request'),
    path('users/<str:username>/', views.UserProfileDetailView.as_view(), name='user_profile'),
    path('users/<str:username>/follow/', views.FollowToggleView.as_view(), name='follow_toggle'),
    path('users/<str:username>/block/', views.BlockToggleView.as_view(), name='block_toggle'),
    path('users/<str:username>/followers/', views.UserFollowersListView.as_view(), name='user_followers'),
    path('users/<str:username>/following/', views.UserFollowingListView.as_view(), name='user_following'),

    # Posts & Feeds
    path('posts/', views.PostCreateView.as_view(), name='post_create'),
    path('posts/feed/', views.FeedView.as_view(), name='feed'),
    path('posts/explore/', views.ExploreView.as_view(), name='explore'),
    path('posts/<int:pk>/', views.PostDetailView.as_view(), name='post_detail'),
    path('posts/<int:pk>/like/', views.PostLikeToggleView.as_view(), name='post_like_toggle'),
    path('posts/<int:pk>/comments/', views.PostCommentsView.as_view(), name='post_comments'),
    path('posts/<int:pk>/bookmark/', views.BookmarkToggleView.as_view(), name='post_bookmark_toggle'),
    path('comments/<int:pk>/', views.CommentDeleteView.as_view(), name='comment_delete'),

    # Polls
    path('polls/<int:poll_id>/vote/', views.PollVoteView.as_view(), name='poll_vote'),

    # Stories
    path('stories/', views.StoriesListView.as_view(), name='stories_list'),
    path('stories/<int:pk>/', views.StoryDeleteView.as_view(), name='story_delete'),

    # Reels
    path('reels/', views.ReelsListView.as_view(), name='reels_list'),
    path('reels/<int:pk>/like/', views.ReelLikeToggleView.as_view(), name='reel_like_toggle'),
    path('reels/<int:pk>/comments/', views.ReelCommentsView.as_view(), name='reel_comments'),

    # Collections & Bookmarks
    path('collections/', views.CollectionsListView.as_view(), name='collections_list'),
    path('bookmarks/', views.BookmarksListView.as_view(), name='bookmarks_list'),

    # Trending & Search
    path('hashtags/trending/', views.TrendingHashtagsView.as_view(), name='trending_hashtags'),
    path('search/', views.SearchView.as_view(), name='search'),

    # Direct Messaging
    path('messages/conversations/', views.ConversationsListView.as_view(), name='conversations_list'),
    path('messages/start/<str:username>/', views.StartConversationView.as_view(), name='start_conversation'),
    path('messages/conversations/<int:conversation_id>/', views.MessagesListView.as_view(), name='conversation_messages'),

    # Notifications
    path('notifications/', views.NotificationsListView.as_view(), name='notifications_list'),
    path('notifications/unread-count/', views.UnreadCountsView.as_view(), name='unread_counts'),

    # Dashboard, Reports & AI
    path('dashboard/stats/', views.ActivityDashboardView.as_view(), name='dashboard_stats'),
    path('reports/', views.ReportView.as_view(), name='report'),
    path('ai/caption-assistant/', views.AICaptionAssistantView.as_view(), name='ai_caption_assistant'),
]
