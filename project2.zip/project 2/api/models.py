from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import re


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(max_length=100, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    avatar_url = models.URLField(blank=True, default='')
    cover_image = models.URLField(blank=True, default='')
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    interests = models.CharField(max_length=255, blank=True, help_text="Comma-separated interests (e.g. Technology, Education, Gaming)")
    is_private = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    profile_views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        if self.avatar_url:
            return self.avatar_url
        # Fallback dynamic avatar
        name = self.display_name or self.user.username
        return f"https://api.dicebear.com/7.x/avataaars/svg?seed={name}"

    def __str__(self):
        return f"Profile of {self.user.username}"


class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following_relations')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='follower_relations')
    is_accepted = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')
        indexes = [
            models.Index(fields=['follower', 'following']),
        ]

    def __str__(self):
        status = "Following" if self.is_accepted else "Requested"
        return f"{self.follower.username} -> {self.following.username} ({status})"


class Block(models.Model):
    blocker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_relations')
    blocked = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_by_relations')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('blocker', 'blocked')

    def __str__(self):
        return f"{self.blocker.username} blocked {self.blocked.username}"


class Hashtag(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    usage_count = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"#{self.name} ({self.usage_count})"


class Post(models.Model):
    CATEGORY_CHOICES = [
        ('General', 'General'),
        ('Technology', 'Technology'),
        ('Education', 'Education'),
        ('Gaming', 'Gaming'),
        ('Photography', 'Photography'),
        ('Lifestyle', 'Lifestyle'),
        ('Design', 'Design'),
        ('Business', 'Business'),
    ]

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(max_length=3000)
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    image_url = models.URLField(blank=True, default='')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='General')
    hashtags = models.ManyToManyField(Hashtag, blank=True, related_name='posts')
    is_recommended = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def get_image_url(self):
        if self.image:
            return self.image.url
        return self.image_url

    def update_hashtags(self):
        # Extract hashtags from content
        tags = set(re.findall(r'#(\w+)', self.content.lower()))
        self.hashtags.clear()
        for tag in tags:
            hashtag_obj, created = Hashtag.objects.get_or_create(name=tag)
            if not created:
                hashtag_obj.usage_count += 1
                hashtag_obj.save(update_fields=['usage_count', 'updated_at'])
            self.hashtags.add(hashtag_obj)

    def __str__(self):
        return f"Post by @{self.author.username} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class Poll(models.Model):
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='poll')
    question = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Poll: {self.question}"


class PollOption(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=150)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.text


class PollVote(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='votes')
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='poll_votes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('poll', 'user')

    def __str__(self):
        return f"{self.user.username} voted on {self.poll.question}"


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on Post {self.post.id}"


class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')

    def __str__(self):
        return f"{self.user.username} liked Post {self.post.id}"


def default_story_expiry():
    return timezone.now() + timedelta(hours=24)


class Story(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories')
    media_url = models.URLField(blank=True, default='')
    image = models.ImageField(upload_to='stories/', blank=True, null=True)
    text_content = models.CharField(max_length=300, blank=True)
    background_gradient = models.CharField(
        max_length=120, 
        default='linear-gradient(135deg, #6366f1, #8b5cf6)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_story_expiry, db_index=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    def get_media_url(self):
        if self.image:
            return self.image.url
        return self.media_url

    def __str__(self):
        return f"Story by {self.user.username} ({self.created_at})"


class Reel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reels')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    video_url = models.URLField(help_text="Direct link to mp4 or video")
    thumbnail_url = models.URLField(blank=True, default='')
    song_title = models.CharField(max_length=150, default='Original Audio - CodeGram')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Reel: {self.title} by {self.user.username}"


class ReelLike(models.Model):
    reel = models.ForeignKey(Reel, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reel_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('reel', 'user')


class ReelComment(models.Model):
    reel = models.ForeignKey(Reel, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reel_comments')
    content = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']


class Collection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collections')
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'name')
        ordering = ['name']

    def __str__(self):
        return f"{self.user.username}'s Collection: {self.name}"


class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='bookmarked_by')
    collection = models.ForeignKey(Collection, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookmarks')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} saved Post {self.post.id}"


class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Conversation #{self.id}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Msg {self.id} from {self.sender.username}"


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('follow', 'Follow'),
        ('follow_request', 'Follow Request'),
        ('poll_vote', 'Poll Vote'),
        ('mention', 'Mention'),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    reel = models.ForeignKey(Reel, on_delete=models.CASCADE, null=True, blank=True)
    text = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification to {self.recipient.username} ({self.notification_type})"


class Report(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('reviewed', 'Reviewed'),
        ('dismissed', 'Dismissed'),
        ('action_taken', 'Action Taken'),
    ]

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_filed')
    reported_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports_received')
    reported_post = models.ForeignKey(Post, on_delete=models.SET_NULL, null=True, blank=True)
    reason = models.CharField(max_length=300)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report #{self.id} by {self.reporter.username} - {self.status}"
