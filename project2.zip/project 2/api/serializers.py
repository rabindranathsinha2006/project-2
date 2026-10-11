from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Profile, Follow, Block, Post, Poll, PollOption, PollVote,
    Comment, Like, Hashtag, Story, Reel, ReelLike, ReelComment,
    Collection, Bookmark, Conversation, Message, Notification, Report
)


class ProfileSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'display_name', 'bio', 'avatar', 'avatar_url', 'cover_image',
            'location', 'website', 'interests', 'is_private', 'is_verified',
            'profile_views', 'created_at', 'updated_at'
        ]
        read_only_fields = ['profile_views', 'created_at', 'updated_at']

    def get_avatar_url(self, obj):
        return obj.get_avatar_url()


class UserBasicSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(source='profile.display_name', read_only=True)
    avatar_url = serializers.SerializerMethodField()
    is_verified = serializers.BooleanField(source='profile.is_verified', read_only=True)
    is_private = serializers.BooleanField(source='profile.is_private', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'display_name', 'avatar_url', 'is_verified', 'is_private']

    def get_avatar_url(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.get_avatar_url()
        return f"https://api.dicebear.com/7.x/avataaars/svg?seed={obj.username}"


class UserDetailSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    posts_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    has_pending_request = serializers.SerializerMethodField()
    is_blocked = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'profile', 'followers_count', 'following_count', 'posts_count',
            'is_following', 'has_pending_request', 'is_blocked'
        ]

    def get_followers_count(self, obj):
        return Follow.objects.filter(following=obj, is_accepted=True).count()

    def get_following_count(self, obj):
        return Follow.objects.filter(follower=obj, is_accepted=True).count()

    def get_posts_count(self, obj):
        return obj.posts.count()

    def get_is_following(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated or request.user == obj:
            return False
        return Follow.objects.filter(follower=request.user, following=obj, is_accepted=True).exists()

    def get_has_pending_request(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated or request.user == obj:
            return False
        return Follow.objects.filter(follower=request.user, following=obj, is_accepted=False).exists()

    def get_is_blocked(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated or request.user == obj:
            return False
        return Block.objects.filter(blocker=request.user, blocked=obj).exists()


class CommentSerializer(serializers.ModelSerializer):
    author = UserBasicSerializer(read_only=True)
    is_author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'content', 'created_at', 'is_author']
        read_only_fields = ['author', 'created_at']

    def get_is_author(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.author == request.user


class PollOptionSerializer(serializers.ModelSerializer):
    votes_count = serializers.SerializerMethodField()
    percentage = serializers.SerializerMethodField()

    class Meta:
        model = PollOption
        fields = ['id', 'text', 'order', 'votes_count', 'percentage']

    def get_votes_count(self, obj):
        return obj.votes.count()

    def get_percentage(self, obj):
        total_votes = obj.poll.votes.count()
        if total_votes == 0:
            return 0
        return round((obj.votes.count() / total_votes) * 100, 1)


class PollSerializer(serializers.ModelSerializer):
    options = PollOptionSerializer(many=True, read_only=True)
    total_votes = serializers.SerializerMethodField()
    user_voted_option_id = serializers.SerializerMethodField()

    class Meta:
        model = Poll
        fields = ['id', 'question', 'options', 'total_votes', 'user_voted_option_id']

    def get_total_votes(self, obj):
        return obj.votes.count()

    def get_user_voted_option_id(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        vote = PollVote.objects.filter(poll=obj, user=request.user).first()
        return vote.option_id if vote else None


class HashtagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hashtag
        fields = ['id', 'name', 'usage_count']


class PostSerializer(serializers.ModelSerializer):
    author = UserBasicSerializer(read_only=True)
    image_display_url = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    poll = PollSerializer(read_only=True)
    comments = serializers.SerializerMethodField()
    hashtags = HashtagSerializer(many=True, read_only=True)
    is_author = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'author', 'content', 'image', 'image_url', 'image_display_url',
            'category', 'hashtags', 'is_recommended', 'created_at', 'updated_at',
            'likes_count', 'comments_count', 'is_liked', 'is_bookmarked',
            'poll', 'comments', 'is_author'
        ]
        read_only_fields = ['author', 'created_at', 'updated_at', 'hashtags']

    def get_image_display_url(self, obj):
        return obj.get_image_url()

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Like.objects.filter(post=obj, user=request.user).exists()

    def get_is_bookmarked(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Bookmark.objects.filter(post=obj, user=request.user).exists()

    def get_comments(self, obj):
        # return the top 3 latest comments for quick feed preview
        comments_qs = obj.comments.all().select_related('author', 'author__profile').order_by('-created_at')[:3]
        return CommentSerializer(comments_qs, many=True, context=self.context).data

    def get_is_author(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.author == request.user


class StorySerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    media_display_url = serializers.SerializerMethodField()
    is_expired = serializers.BooleanField(read_only=True)
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Story
        fields = [
            'id', 'user', 'media_url', 'media_display_url', 'text_content',
            'background_gradient', 'created_at', 'expires_at', 'is_expired', 'is_mine'
        ]
        read_only_fields = ['user', 'created_at', 'expires_at', 'is_expired']

    def get_media_display_url(self, obj):
        return obj.get_media_url()

    def get_is_mine(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.user == request.user


class ReelCommentSerializer(serializers.ModelSerializer):
    author = UserBasicSerializer(read_only=True)
    is_author = serializers.SerializerMethodField()

    class Meta:
        model = ReelComment
        fields = ['id', 'reel', 'author', 'content', 'created_at', 'is_author']
        read_only_fields = ['author', 'created_at']

    def get_is_author(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.author == request.user


class ReelSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_author = serializers.SerializerMethodField()

    class Meta:
        model = Reel
        fields = [
            'id', 'user', 'title', 'description', 'video_url', 'thumbnail_url',
            'song_title', 'created_at', 'likes_count', 'comments_count',
            'is_liked', 'is_author'
        ]
        read_only_fields = ['user', 'created_at']

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return ReelLike.objects.filter(reel=obj, user=request.user).exists()

    def get_is_author(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.user == request.user


class CollectionSerializer(serializers.ModelSerializer):
    bookmarks_count = serializers.SerializerMethodField()

    class Meta:
        model = Collection
        fields = ['id', 'name', 'bookmarks_count', 'created_at']
        read_only_fields = ['created_at']

    def get_bookmarks_count(self, obj):
        return obj.bookmarks.count()


class BookmarkSerializer(serializers.ModelSerializer):
    post = PostSerializer(read_only=True)
    collection_name = serializers.CharField(source='collection.name', read_only=True, default=None)

    class Meta:
        model = Bookmark
        fields = ['id', 'post', 'collection', 'collection_name', 'created_at']
        read_only_fields = ['created_at']


class MessageSerializer(serializers.ModelSerializer):
    sender = UserBasicSerializer(read_only=True)
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'content', 'is_read', 'created_at', 'is_mine']
        read_only_fields = ['sender', 'created_at']

    def get_is_mine(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.sender == request.user


class ConversationSerializer(serializers.ModelSerializer):
    other_participant = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'other_participant', 'last_message', 'unread_count', 'updated_at']

    def get_other_participant(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            first_user = obj.participants.first()
            return UserBasicSerializer(first_user).data if first_user else None
        other = obj.participants.exclude(id=request.user.id).first()
        if not other:
            other = request.user
        return UserBasicSerializer(other).data

    def get_last_message(self, obj):
        msg = obj.messages.order_by('-created_at').first()
        if msg:
            return {
                'id': msg.id,
                'content': msg.content,
                'sender_username': msg.sender.username,
                'is_mine': (self.context.get('request') and msg.sender == self.context['request'].user),
                'created_at': msg.created_at
            }
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0
        return obj.messages.filter(is_read=False).exclude(sender=request.user).count()


class NotificationSerializer(serializers.ModelSerializer):
    sender = UserBasicSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'sender', 'notification_type', 'post', 'reel',
            'text', 'is_read', 'created_at'
        ]
        read_only_fields = ['sender', 'notification_type', 'created_at']


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['id', 'reported_user', 'reported_post', 'reason', 'status', 'created_at']
        read_only_fields = ['id', 'status', 'created_at']
