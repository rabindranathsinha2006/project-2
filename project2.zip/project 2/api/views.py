import json
import os
import re
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q, Count
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from rest_framework import status, views, permissions
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import (
    Profile, Follow, Block, Post, Poll, PollOption, PollVote,
    Comment, Like, Hashtag, Story, Reel, ReelLike, ReelComment,
    Collection, Bookmark, Conversation, Message, Notification, Report
)
from .serializers import (
    ProfileSerializer, UserBasicSerializer, UserDetailSerializer,
    PostSerializer, CommentSerializer, PollSerializer, StorySerializer,
    ReelSerializer, ReelCommentSerializer, CollectionSerializer,
    BookmarkSerializer, ConversationSerializer, MessageSerializer,
    NotificationSerializer, HashtagSerializer, ReportSerializer
)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


# ==============================================================================
# AUTHENTICATION VIEWS
# ==============================================================================

class RegisterView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username', '').strip()
        email = request.data.get('email', '').strip()
        password = request.data.get('password', '').strip()
        display_name = request.data.get('display_name', '').strip()

        if not username or not password:
            return Response({'error': 'Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)
        if len(password) < 6:
            return Response({'error': 'Password must be at least 6 characters.'}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username__iexact=username).exists():
            return Response({'error': 'A user with that username already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        if email and User.objects.filter(email__iexact=email).exists():
            return Response({'error': 'A user with that email already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, email=email, password=password)
        if hasattr(user, 'profile'):
            user.profile.display_name = display_name or username
            user.profile.save()

        # Log in newly registered user
        login(request, user)
        serializer = UserDetailSerializer(user, context={'request': request})
        return Response({'message': 'Registration successful.', 'user': serializer.data}, status=status.HTTP_201_CREATED)


class LoginView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '').strip()

        if not username or not password:
            return Response({'error': 'Please enter both username and password.'}, status=status.HTTP_400_BAD_REQUEST)

        # Allow login by email or username
        if '@' in username:
            user_obj = User.objects.filter(email__iexact=username).first()
            if user_obj:
                username = user_obj.username

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            serializer = UserDetailSerializer(user, context={'request': request})
            return Response({'message': 'Logged in successfully.', 'user': serializer.data})
        else:
            return Response({'error': 'Invalid username or password.'}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({'message': 'Logged out successfully.'})


class CurrentUserView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if request.user.is_authenticated:
            serializer = UserDetailSerializer(request.user, context={'request': request})
            return Response({'authenticated': True, 'user': serializer.data})
        return Response({'authenticated': False, 'user': None})


# ==============================================================================
# USER PROFILES & SETTINGS
# ==============================================================================

class UserProfileDetailView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, username):
        user = User.objects.filter(username__iexact=username).first()
        if not user:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Increment views if viewer is not the profile owner
        if request.user.is_authenticated and request.user != user:
            user.profile.profile_views += 1
            user.profile.save(update_fields=['profile_views'])

        serializer = UserDetailSerializer(user, context={'request': request})
        data = serializer.data

        # Check privacy settings
        is_private = user.profile.is_private
        is_owner = request.user.is_authenticated and request.user == user
        is_following = data.get('is_following', False)

        if is_private and not is_owner and not is_following:
            data['is_restricted'] = True
            data['posts'] = []
            return Response(data)

        data['is_restricted'] = False
        user_posts = Post.objects.filter(author=user).select_related('author', 'author__profile').prefetch_related('likes', 'comments', 'hashtags')[:20]
        data['posts'] = PostSerializer(user_posts, many=True, context={'request': request}).data

        return Response(data)


class UpdateProfileView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def patch(self, request):
        profile = request.user.profile
        data = request.data

        if 'display_name' in data:
            profile.display_name = data['display_name'].strip()
        if 'bio' in data:
            profile.bio = data['bio'].strip()
        if 'location' in data:
            profile.location = data['location'].strip()
        if 'website' in data:
            profile.website = data['website'].strip()
        if 'interests' in data:
            profile.interests = data['interests'].strip()
        if 'is_private' in data:
            is_priv = data['is_private']
            profile.is_private = is_priv in [True, 'true', 'True', 1, '1']
        if 'cover_image' in data:
            profile.cover_image = data['cover_image']
        if 'avatar_url' in data:
            profile.avatar_url = data['avatar_url']
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']

        profile.save()
        serializer = UserDetailSerializer(request.user, context={'request': request})
        return Response({'message': 'Profile updated successfully.', 'user': serializer.data})


# ==============================================================================
# FOLLOW & FOLLOW REQUESTS & BLOCKING
# ==============================================================================

class FollowToggleView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, username):
        target_user = User.objects.filter(username__iexact=username).first()
        if not target_user:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        if target_user == request.user:
            return Response({'error': 'You cannot follow yourself.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check block
        if Block.objects.filter(blocker=target_user, blocked=request.user).exists() or \
           Block.objects.filter(blocker=request.user, blocked=target_user).exists():
            return Response({'error': 'Unable to follow this account.'}, status=status.HTTP_403_FORBIDDEN)

        follow_relation = Follow.objects.filter(follower=request.user, following=target_user).first()
        if follow_relation:
            follow_relation.delete()
            # Also clean up notification if pending
            Notification.objects.filter(sender=request.user, recipient=target_user, notification_type__in=['follow', 'follow_request']).delete()
            return Response({
                'is_following': False,
                'has_pending_request': False,
                'message': f'Unfollowed @{target_user.username}'
            })

        # Check if target profile is private
        if target_user.profile.is_private:
            Follow.objects.create(follower=request.user, following=target_user, is_accepted=False)
            Notification.objects.create(
                sender=request.user,
                recipient=target_user,
                notification_type='follow_request',
                text=f'@{request.user.username} requested to follow you.'
            )
            return Response({
                'is_following': False,
                'has_pending_request': True,
                'message': f'Follow request sent to @{target_user.username}'
            })
        else:
            Follow.objects.create(follower=request.user, following=target_user, is_accepted=True)
            Notification.objects.create(
                sender=request.user,
                recipient=target_user,
                notification_type='follow',
                text=f'@{request.user.username} started following you.'
            )
            return Response({
                'is_following': True,
                'has_pending_request': False,
                'message': f'Now following @{target_user.username}'
            })


class FollowRequestsListView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        pending = Follow.objects.filter(following=request.user, is_accepted=False).select_related('follower', 'follower__profile')
        data = [{
            'id': req.id,
            'user': UserBasicSerializer(req.follower).data,
            'created_at': req.created_at
        } for req in pending]
        return Response(data)


class HandleFollowRequestView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, follow_id, action):
        follow_req = Follow.objects.filter(id=follow_id, following=request.user, is_accepted=False).first()
        if not follow_req:
            return Response({'error': 'Follow request not found.'}, status=status.HTTP_404_NOT_FOUND)

        if action == 'accept':
            follow_req.is_accepted = True
            follow_req.save(update_fields=['is_accepted'])
            # Notify the follower that request was accepted
            Notification.objects.create(
                sender=request.user,
                recipient=follow_req.follower,
                notification_type='follow',
                text=f'@{request.user.username} accepted your follow request.'
            )
            return Response({'message': f'Accepted follow request from @{follow_req.follower.username}'})
        elif action == 'reject':
            follow_req.delete()
            return Response({'message': 'Follow request rejected.'})
        return Response({'error': 'Invalid action.'}, status=status.HTTP_400_BAD_REQUEST)


class UserFollowersListView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, username):
        user = User.objects.filter(username__iexact=username).first()
        if not user:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        followers = User.objects.filter(following_relations__following=user, following_relations__is_accepted=True)
        return Response(UserBasicSerializer(followers, many=True).data)


class UserFollowingListView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, username):
        user = User.objects.filter(username__iexact=username).first()
        if not user:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        following = User.objects.filter(follower_relations__follower=user, follower_relations__is_accepted=True)
        return Response(UserBasicSerializer(following, many=True).data)


class BlockToggleView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, username):
        target_user = User.objects.filter(username__iexact=username).first()
        if not target_user:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        if target_user == request.user:
            return Response({'error': 'You cannot block yourself.'}, status=status.HTTP_400_BAD_REQUEST)

        block = Block.objects.filter(blocker=request.user, blocked=target_user).first()
        if block:
            block.delete()
            return Response({'is_blocked': False, 'message': f'Unblocked @{target_user.username}'})

        # Create block & sever follow connections in both directions
        Block.objects.create(blocker=request.user, blocked=target_user)
        Follow.objects.filter(
            Q(follower=request.user, following=target_user) |
            Q(follower=target_user, following=request.user)
        ).delete()
        return Response({'is_blocked': True, 'message': f'Blocked @{target_user.username}'})


class ReportView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        reason = request.data.get('reason', '').strip()
        user_id = request.data.get('user_id')
        post_id = request.data.get('post_id')

        if not reason:
            return Response({'error': 'Please provide a reason for the report.'}, status=status.HTTP_400_BAD_REQUEST)

        reported_user = User.objects.filter(id=user_id).first() if user_id else None
        reported_post = Post.objects.filter(id=post_id).first() if post_id else None

        Report.objects.create(
            reporter=request.user,
            reported_user=reported_user,
            reported_post=reported_post,
            reason=reason
        )
        return Response({'message': 'Thank you. Your report has been submitted for review.'}, status=status.HTTP_201_CREATED)


# ==============================================================================
# POSTS, COMMENTS, LIKES & POLLS
# ==============================================================================

class FeedView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        user = request.user
        blocked_user_ids = []
        if user.is_authenticated:
            blocked_by_me = Block.objects.filter(blocker=user).values_list('blocked_id', flat=True)
            blocked_me = Block.objects.filter(blocked=user).values_list('blocker_id', flat=True)
            blocked_user_ids = list(blocked_by_me) + list(blocked_me)

        # Base query excluding blocked users
        qs = Post.objects.exclude(author_id__in=blocked_user_ids).select_related('author', 'author__profile').prefetch_related('likes', 'comments', 'hashtags')

        if user.is_authenticated:
            # Users the current user follows
            followed_ids = Follow.objects.filter(follower=user, is_accepted=True).values_list('following_id', flat=True)
            # Match user interests if available
            user_interests = [i.strip() for i in user.profile.interests.split(',') if i.strip()]

            # Feed priority: followed users OR matching interests OR highly liked/recommended
            # Private profiles posts are only shown if followed or if author is self
            qs = qs.filter(
                Q(author=user) |
                Q(author_id__in=followed_ids) |
                (Q(author__profile__is_private=False) & (Q(category__in=user_interests) | Q(is_recommended=True) | Q(created_at__gte=timezone.now() - timedelta(days=7))))
            )
        else:
            # For guests: public posts
            qs = qs.filter(author__profile__is_private=False)

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = PostSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)


class ExploreView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        category = request.query_params.get('category', '').strip()
        search_query = request.query_params.get('q', '').strip()
        tag = request.query_params.get('tag', '').strip()

        qs = Post.objects.filter(author__profile__is_private=False).select_related('author', 'author__profile').prefetch_related('likes', 'comments', 'hashtags')

        if request.user.is_authenticated:
            blocked_user_ids = Block.objects.filter(blocker=request.user).values_list('blocked_id', flat=True)
            qs = qs.exclude(author_id__in=blocked_user_ids)

        if category and category.lower() != 'all':
            qs = qs.filter(category__iexact=category)

        if tag:
            qs = qs.filter(hashtags__name__iexact=tag.lstrip('#'))

        if search_query:
            qs = qs.filter(
                Q(content__icontains=search_query) |
                Q(hashtags__name__icontains=search_query.lstrip('#')) |
                Q(author__username__icontains=search_query)
            ).distinct()

        # Popular accounts recommendations
        suggested_users_qs = User.objects.filter(profile__is_private=False)
        if request.user.is_authenticated:
            followed = Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
            suggested_users_qs = suggested_users_qs.exclude(id__in=list(followed) + [request.user.id])
        suggested_users = suggested_users_qs.annotate(num_followers=Count('follower_relations')).order_by('-num_followers')[:5]

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(qs, request)
        posts_data = PostSerializer(page, many=True, context={'request': request}).data

        return paginator.get_paginated_response({
            'posts': posts_data,
            'suggested_users': UserBasicSerializer(suggested_users, many=True).data
        })


class PostCreateView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        content = request.data.get('content', '').strip()
        category = request.data.get('category', 'General')
        image_url = request.data.get('image_url', '').strip()
        poll_question = request.data.get('poll_question', '').strip()
        poll_options = request.data.get('poll_options')

        if not content and not ('image' in request.FILES or image_url) and not poll_question:
            return Response({'error': 'Please provide content, an image, or a poll.'}, status=status.HTTP_400_BAD_REQUEST)

        post = Post.objects.create(
            author=request.user,
            content=content,
            category=category,
            image_url=image_url
        )

        if 'image' in request.FILES:
            post.image = request.FILES['image']
            post.save()

        # Update Hashtags
        post.update_hashtags()

        # Check Poll
        if poll_question:
            if isinstance(poll_options, str):
                try:
                    poll_options = json.loads(poll_options)
                except Exception:
                    poll_options = [opt.strip() for opt in poll_options.split(',') if opt.strip()]

            if isinstance(poll_options, list) and len(poll_options) >= 2:
                poll = Poll.objects.create(post=post, question=poll_question)
                for idx, opt_text in enumerate(poll_options):
                    if str(opt_text).strip():
                        PollOption.objects.create(poll=poll, text=str(opt_text).strip()[:150], order=idx)

        serializer = PostSerializer(post, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PostDetailView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        post = Post.objects.filter(pk=pk).select_related('author', 'author__profile').prefetch_related('likes', 'comments', 'hashtags').first()
        if not post:
            return Response({'error': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Check private author permissions
        if post.author.profile.is_private and request.user != post.author:
            if not request.user.is_authenticated or not Follow.objects.filter(follower=request.user, following=post.author, is_accepted=True).exists():
                return Response({'error': 'This post is from a private account.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = PostSerializer(post, context={'request': request})
        return Response(serializer.data)

    def put(self, request, pk):
        return self.patch(request, pk)

    def patch(self, request, pk):
        post = Post.objects.filter(pk=pk).first()
        if not post:
            return Response({'error': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)
        if post.author != request.user:
            return Response({'error': 'You do not have permission to edit this post.'}, status=status.HTTP_403_FORBIDDEN)

        content = request.data.get('content')
        category = request.data.get('category')
        image_url = request.data.get('image_url')

        if content is not None:
            post.content = content.strip()
        if category is not None:
            post.category = category
        if image_url is not None:
            post.image_url = image_url.strip()
        if 'image' in request.FILES:
            post.image = request.FILES['image']

        post.save()
        post.update_hashtags()

        serializer = PostSerializer(post, context={'request': request})
        return Response(serializer.data)

    def delete(self, request, pk):
        post = Post.objects.filter(pk=pk).first()
        if not post:
            return Response({'error': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)
        if post.author != request.user:
            return Response({'error': 'You do not have permission to delete this post.'}, status=status.HTTP_403_FORBIDDEN)

        post.delete()
        return Response({'message': 'Post deleted successfully.'}, status=status.HTTP_200_OK)


class PostLikeToggleView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        post = Post.objects.filter(pk=pk).first()
        if not post:
            return Response({'error': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)

        like = Like.objects.filter(post=post, user=request.user).first()
        if like:
            like.delete()
            is_liked = False
        else:
            Like.objects.create(post=post, user=request.user)
            is_liked = True
            # Notify author if not self
            if post.author != request.user:
                Notification.objects.create(
                    recipient=post.author,
                    sender=request.user,
                    notification_type='like',
                    post=post,
                    text=f'@{request.user.username} liked your post.'
                )

        return Response({
            'is_liked': is_liked,
            'likes_count': post.likes.count()
        })


class PostCommentsView(views.APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, pk):
        post = Post.objects.filter(pk=pk).first()
        if not post:
            return Response({'error': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)
        comments = post.comments.select_related('author', 'author__profile').all()
        serializer = CommentSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request, pk):
        post = Post.objects.filter(pk=pk).first()
        if not post:
            return Response({'error': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)

        content = request.data.get('content', '').strip()
        if not content:
            return Response({'error': 'Comment content cannot be empty.'}, status=status.HTTP_400_BAD_REQUEST)

        comment = Comment.objects.create(
            post=post,
            author=request.user,
            content=content
        )

        if post.author != request.user:
            Notification.objects.create(
                recipient=post.author,
                sender=request.user,
                notification_type='comment',
                post=post,
                text=f'@{request.user.username} commented: "{content[:60]}"'
            )

        serializer = CommentSerializer(comment, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CommentDeleteView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        comment = Comment.objects.filter(pk=pk).select_related('post').first()
        if not comment:
            return Response({'error': 'Comment not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Allowed if author of comment OR author of post
        if comment.author != request.user and comment.post.author != request.user:
            return Response({'error': 'You do not have permission to delete this comment.'}, status=status.HTTP_403_FORBIDDEN)

        comment.delete()
        return Response({'message': 'Comment deleted successfully.'})


class PollVoteView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, poll_id):
        poll = Poll.objects.filter(pk=poll_id).first()
        if not poll:
            return Response({'error': 'Poll not found.'}, status=status.HTTP_404_NOT_FOUND)

        option_id = request.data.get('option_id')
        option = PollOption.objects.filter(id=option_id, poll=poll).first()
        if not option:
            return Response({'error': 'Invalid poll option.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if already voted
        existing_vote = PollVote.objects.filter(poll=poll, user=request.user).first()
        if existing_vote:
            return Response({'error': 'You have already voted in this poll.'}, status=status.HTTP_400_BAD_REQUEST)

        PollVote.objects.create(poll=poll, option=option, user=request.user)

        serializer = PollSerializer(poll, context={'request': request})
        return Response(serializer.data)


# ==============================================================================
# STORIES (24h Ephemeral)
# ==============================================================================

class StoriesListView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        now = timezone.now()
        # Active stories
        active_stories = Story.objects.filter(expires_at__gt=now).select_related('user', 'user__profile')

        if request.user.is_authenticated:
            blocked_user_ids = Block.objects.filter(blocker=request.user).values_list('blocked_id', flat=True)
            active_stories = active_stories.exclude(user_id__in=blocked_user_ids)

        serializer = StorySerializer(active_stories, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

        text_content = request.data.get('text_content', '').strip()
        media_url = request.data.get('media_url', '').strip()
        background_gradient = request.data.get('background_gradient', 'linear-gradient(135deg, #6366f1, #8b5cf6)')

        story = Story.objects.create(
            user=request.user,
            text_content=text_content,
            media_url=media_url,
            background_gradient=background_gradient
        )
        if 'image' in request.FILES:
            story.image = request.FILES['image']
            story.save()

        serializer = StorySerializer(story, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class StoryDeleteView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        story = Story.objects.filter(pk=pk).first()
        if not story:
            return Response({'error': 'Story not found.'}, status=status.HTTP_404_NOT_FOUND)
        if story.user != request.user:
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        story.delete()
        return Response({'message': 'Story deleted.'})


# ==============================================================================
# REELS / SHORT VIDEOS
# ==============================================================================

class ReelsListView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        reels = Reel.objects.select_related('user', 'user__profile').prefetch_related('likes', 'comments')
        serializer = ReelSerializer(reels, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

        title = request.data.get('title', '').strip()
        description = request.data.get('description', '').strip()
        video_url = request.data.get('video_url', '').strip()
        thumbnail_url = request.data.get('thumbnail_url', '').strip()
        song_title = request.data.get('song_title', 'Original Audio - CodeGram').strip()

        if not video_url:
            return Response({'error': 'Video URL is required.'}, status=status.HTTP_400_BAD_REQUEST)

        reel = Reel.objects.create(
            user=request.user,
            title=title or 'Untitled Reel',
            description=description,
            video_url=video_url,
            thumbnail_url=thumbnail_url,
            song_title=song_title
        )
        serializer = ReelSerializer(reel, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ReelLikeToggleView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        reel = Reel.objects.filter(pk=pk).first()
        if not reel:
            return Response({'error': 'Reel not found.'}, status=status.HTTP_404_NOT_FOUND)

        like = ReelLike.objects.filter(reel=reel, user=request.user).first()
        if like:
            like.delete()
            is_liked = False
        else:
            ReelLike.objects.create(reel=reel, user=request.user)
            is_liked = True

        return Response({
            'is_liked': is_liked,
            'likes_count': reel.likes.count()
        })


class ReelCommentsView(views.APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, pk):
        reel = Reel.objects.filter(pk=pk).first()
        if not reel:
            return Response({'error': 'Reel not found.'}, status=status.HTTP_404_NOT_FOUND)
        comments = reel.comments.select_related('author', 'author__profile').all()
        return Response(ReelCommentSerializer(comments, many=True, context={'request': request}).data)

    def post(self, request, pk):
        reel = Reel.objects.filter(pk=pk).first()
        if not reel:
            return Response({'error': 'Reel not found.'}, status=status.HTTP_404_NOT_FOUND)

        content = request.data.get('content', '').strip()
        if not content:
            return Response({'error': 'Content cannot be empty.'}, status=status.HTTP_400_BAD_REQUEST)

        comment = ReelComment.objects.create(reel=reel, author=request.user, content=content)
        return Response(ReelCommentSerializer(comment, context={'request': request}).data, status=status.HTTP_201_CREATED)


# ==============================================================================
# BOOKMARKS & COLLECTIONS
# ==============================================================================

class CollectionsListView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        collections = Collection.objects.filter(user=request.user)
        return Response(CollectionSerializer(collections, many=True).data)

    def post(self, request):
        name = request.data.get('name', '').strip()
        if not name:
            return Response({'error': 'Collection name is required.'}, status=status.HTTP_400_BAD_REQUEST)
        collection, created = Collection.objects.get_or_create(user=request.user, name=name)
        return Response(CollectionSerializer(collection).data, status=status.HTTP_201_CREATED)


class BookmarkToggleView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        post = Post.objects.filter(pk=pk).first()
        if not post:
            return Response({'error': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)

        collection_name = request.data.get('collection_name', '').strip()
        collection = None
        if collection_name:
            collection, _ = Collection.objects.get_or_create(user=request.user, name=collection_name)

        bookmark = Bookmark.objects.filter(user=request.user, post=post).first()
        if bookmark:
            bookmark.delete()
            is_bookmarked = False
            msg = 'Post removed from saved.'
        else:
            Bookmark.objects.create(user=request.user, post=post, collection=collection)
            is_bookmarked = True
            msg = 'Post saved privately.'

        return Response({'is_bookmarked': is_bookmarked, 'message': msg})


class BookmarksListView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        collection_id = request.query_params.get('collection')
        qs = Bookmark.objects.filter(user=request.user).select_related('post', 'post__author', 'post__author__profile', 'collection')

        if collection_id:
            qs = qs.filter(collection_id=collection_id)

        serializer = BookmarkSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)


# ==============================================================================
# TRENDING HASHTAGS & SEARCH
# ==============================================================================

class TrendingHashtagsView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        hashtags = Hashtag.objects.order_by('-usage_count', '-updated_at')[:10]
        return Response(HashtagSerializer(hashtags, many=True).data)


class SearchView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response({'users': [], 'posts': [], 'hashtags': []})

        clean_tag = query.lstrip('#')

        # Users matching username or display_name
        users = User.objects.filter(
            Q(username__icontains=query) | Q(profile__display_name__icontains=query)
        ).select_related('profile')[:8]

        # Posts matching content or hashtags
        posts = Post.objects.filter(
            Q(content__icontains=query) | Q(hashtags__name__icontains=clean_tag)
        ).filter(author__profile__is_private=False).distinct()[:10]

        # Hashtags matching name
        hashtags = Hashtag.objects.filter(name__icontains=clean_tag)[:8]

        return Response({
            'users': UserBasicSerializer(users, many=True).data,
            'posts': PostSerializer(posts, many=True, context={'request': request}).data,
            'hashtags': HashtagSerializer(hashtags, many=True).data
        })


# ==============================================================================
# DIRECT MESSAGING
# ==============================================================================

class ConversationsListView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        convos = request.user.conversations.prefetch_related('participants', 'messages').order_by('-updated_at')
        serializer = ConversationSerializer(convos, many=True, context={'request': request})
        return Response(serializer.data)


class StartConversationView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, username):
        target_user = User.objects.filter(username__iexact=username).first()
        if not target_user:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        if target_user == request.user:
            return Response({'error': 'Cannot start a conversation with yourself.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check existing 2-person conversation
        conv = Conversation.objects.filter(participants=request.user).filter(participants=target_user).first()
        if not conv:
            conv = Conversation.objects.create()
            conv.participants.add(request.user, target_user)

        serializer = ConversationSerializer(conv, context={'request': request})
        return Response(serializer.data)


class MessagesListView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, conversation_id):
        conv = Conversation.objects.filter(pk=conversation_id, participants=request.user).first()
        if not conv:
            return Response({'error': 'Conversation not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Mark other participants' unread messages as read
        conv.messages.exclude(sender=request.user).filter(is_read=False).update(is_read=True)

        messages = conv.messages.select_related('sender', 'sender__profile').order_by('created_at')[:100]
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request, conversation_id):
        conv = Conversation.objects.filter(pk=conversation_id, participants=request.user).first()
        if not conv:
            return Response({'error': 'Conversation not found.'}, status=status.HTTP_404_NOT_FOUND)

        content = request.data.get('content', '').strip()
        if not content:
            return Response({'error': 'Message content cannot be empty.'}, status=status.HTTP_400_BAD_REQUEST)

        message = Message.objects.create(
            conversation=conv,
            sender=request.user,
            content=content
        )
        conv.updated_at = timezone.now()
        conv.save(update_fields=['updated_at'])

        serializer = MessageSerializer(message, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ==============================================================================
# NOTIFICATIONS & UNREAD COUNTS
# ==============================================================================

class NotificationsListView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        notifs = request.user.notifications.select_related('sender', 'sender__profile')[:30]
        serializer = NotificationSerializer(notifs, many=True)
        return Response(serializer.data)

    def post(self, request):
        # Mark all as read
        request.user.notifications.filter(is_read=False).update(is_read=True)
        return Response({'message': 'All notifications marked as read.'})


class UnreadCountsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        notifs_count = request.user.notifications.filter(is_read=False).count()
        messages_count = Message.objects.filter(conversation__participants=request.user, is_read=False).exclude(sender=request.user).count()
        follow_requests_count = Follow.objects.filter(following=request.user, is_accepted=False).count()

        return Response({
            'unread_notifications': notifs_count,
            'unread_messages': messages_count,
            'pending_follow_requests': follow_requests_count
        })


# ==============================================================================
# ACTIVITY DASHBOARD
# ==============================================================================

class ActivityDashboardView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        posts = user.posts.all()
        total_posts = posts.count()
        total_likes_received = Like.objects.filter(post__author=user).count()
        total_comments_received = Comment.objects.filter(post__author=user).count()
        total_followers = Follow.objects.filter(following=user, is_accepted=True).count()
        total_following = Follow.objects.filter(follower=user, is_accepted=True).count()
        profile_views = user.profile.profile_views

        # Generate 7-day stats
        days = []
        likes_series = []
        posts_series = []
        now = timezone.now()

        for i in range(6, -1, -1):
            day_date = (now - timedelta(days=i)).date()
            day_label = day_date.strftime('%a')
            days.append(day_label)

            likes_on_day = Like.objects.filter(post__author=user, created_at__date=day_date).count()
            posts_on_day = Post.objects.filter(author=user, created_at__date=day_date).count()

            likes_series.append(likes_on_day)
            posts_series.append(posts_on_day)

        # Engagement rate estimate
        engagement_rate = 0.0
        if total_posts > 0 and total_followers > 0:
            avg_eng_per_post = (total_likes_received + total_comments_received) / total_posts
            engagement_rate = round((avg_eng_per_post / total_followers) * 100, 2)
        elif total_posts > 0:
            engagement_rate = round(((total_likes_received + total_comments_received) / total_posts) * 10, 1)

        return Response({
            'stats': {
                'total_posts': total_posts,
                'total_likes_received': total_likes_received,
                'total_comments_received': total_comments_received,
                'total_followers': total_followers,
                'total_following': total_following,
                'profile_views': profile_views,
                'engagement_rate': f"{engagement_rate}%",
            },
            'chart_data': {
                'labels': days,
                'likes': likes_series,
                'posts': posts_series
            }
        })


# ==============================================================================
# AI-POWERED CAPTION ASSISTANT
# ==============================================================================

class AICaptionAssistantView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        topic = request.data.get('prompt', '').strip()
        tone = request.data.get('tone', 'engaging').lower()
        category = request.data.get('category', 'General')

        if not topic:
            return Response({'error': 'Please provide a topic or idea for the caption.'}, status=status.HTTP_400_BAD_REQUEST)

        gemini_api_key = os.environ.get('GEMINI_API_KEY')
        openai_api_key = os.environ.get('OPENAI_API_KEY')

        # If a real API key is configured, invoke it; otherwise use the local intelligent engine
        if gemini_api_key:
            try:
                import requests
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_api_key}"
                prompt_text = (
                    f"You are a social media specialist for CodeGram. Write 3 alternative high-engagement captions for a post about '{topic}' with a {tone} tone in the {category} category. "
                    f"Include 3-5 relevant hashtags and emojis. Return JSON format with keys: caption1, caption2, caption3, suggested_hashtags."
                )
                payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
                resp = requests.post(url, json=payload, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    text = data['candidates'][0]['content']['parts'][0]['text']
                    return Response({
                        'engine': 'Google Gemini AI',
                        'raw_suggestions': text,
                        'is_demo': False
                    })
            except Exception as e:
                pass  # Fall through to local demo engine

        # Smart Local Engine Fallback (Guaranteed to work reliably out-of-the-box)
        tone_templates = {
            'engaging': [
                f"✨ Big moves happening today: {topic}! What's your take on this? Drop your thoughts below 👇",
                f"🚀 Taking a deep dive into {topic}. The journey is just getting started, and I can't wait to share more with you all! 💡",
                f"🔥 Unlocking new perspectives on {topic}. Double tap if you agree that consistency is everything! 🎯"
            ],
            'professional': [
                f"Excited to share insights regarding {topic}. Continuous learning and iteration drive meaningful progress in our industry. 📈",
                f"Reflecting on the impact of {topic}. As technology and workflows evolve, staying adaptive remains crucial. What trends are you observing? 💼",
                f"Key takeaways from our work with {topic}: Clarity, resilience, and focus always pay dividends in execution. 🌐"
            ],
            'funny': [
                f"Me trying to explain {topic} to anyone who makes eye contact with me for more than 2 seconds 😂💀",
                f"90% of dealing with {topic} is just staring at the screen and saying 'wait, really?' out loud. Who else? 🤦‍♂️☕",
                f"Started doing {topic} for fun. Now it's my entire personality. Send snacks. 🍕✨"
            ],
            'minimalist': [
                f"{topic}. Simple as that. 🖤",
                f"Focus on what moves the needle: {topic}. 🌿",
                f"Less noise, more {topic}. ⚡"
            ],
            'poetic': [
                f"In the quiet space where ideas meet reality: {topic} unfolds like dawn over an open horizon. 🌅🌙",
                f"Moments woven with intention and curiosity — discovering {topic} in all its subtle beauty. ✨🍃",
                f"Every step forward is a verse written in dedication: embracing {topic} with open eyes. 🕊️💫"
            ]
        }

        selected_templates = tone_templates.get(tone, tone_templates['engaging'])

        # Auto-generate contextual hashtags
        tag_words = re.findall(r'\b[A-Za-z]{3,}\b', f"{topic} {category}")
        hashtags = [f"#{w.capitalize()}" for w in set(tag_words[:4])]
        hashtags += ["#CodeGram", f"#{category.capitalize()}"]
        hashtags_str = " ".join(hashtags[:5])

        results = [
            f"{selected_templates[0]}\n\n{hashtags_str}",
            f"{selected_templates[1]}\n\n{hashtags_str}",
            f"{selected_templates[2]}\n\n{hashtags_str}",
        ]

        return Response({
            'engine': 'CodeGram Local AI Assistant (Demo Mode)',
            'tone': tone,
            'topic': topic,
            'captions': results,
            'suggested_hashtags': hashtags[:5],
            'is_demo': True,
            'note': 'To enable cloud AI generation, set GEMINI_API_KEY or OPENAI_API_KEY in .env.'
        })
