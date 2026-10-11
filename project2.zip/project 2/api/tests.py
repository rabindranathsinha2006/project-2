from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from api.models import (
    Profile, Follow, Block, Post, Poll, PollOption, PollVote,
    Comment, Like, Bookmark, Collection, Conversation, Message,
    Notification
)


class CodeGramCoreTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create two test users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            password='password123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@test.com',
            password='password123'
        )

        # Update profiles
        self.user1.profile.display_name = 'User One'
        self.user1.profile.save()
        self.user2.profile.display_name = 'User Two'
        self.user2.profile.save()

    def test_registration_and_login(self):
        # Register new user
        reg_response = self.client.post('/api/auth/register/', {
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'password123',
            'display_name': 'New Creator'
        }, format='json')
        self.assertEqual(reg_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(reg_response.data['user']['username'], 'newuser')

        # Logout
        self.client.post('/api/auth/logout/')

        # Login
        login_response = self.client.post('/api/auth/login/', {
            'username': 'newuser',
            'password': 'password123'
        }, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertEqual(login_response.data['user']['username'], 'newuser')

    def test_post_lifecycle_and_permissions(self):
        self.client.force_authenticate(user=self.user1)

        # 1. Create post
        create_res = self.client.post('/api/posts/', {
            'content': 'Hello CodeGram! Testing post creation with #django #webdev',
            'category': 'Technology'
        }, format='json')
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)
        post_id = create_res.data['id']

        # 2. View post
        get_res = self.client.get(f'/api/posts/{post_id}/')
        self.assertEqual(get_res.status_code, status.HTTP_200_OK)
        self.assertEqual(get_res.data['author']['username'], 'user1')

        # 3. Edit post as owner
        update_res = self.client.patch(f'/api/posts/{post_id}/', {
            'content': 'Updated post content! #django'
        }, format='json')
        self.assertEqual(update_res.status_code, status.HTTP_200_OK)
        self.assertEqual(update_res.data['content'], 'Updated post content! #django')

        # 4. Attempt edit as another user (should be 403 Forbidden)
        self.client.force_authenticate(user=self.user2)
        unauth_edit_res = self.client.patch(f'/api/posts/{post_id}/', {
            'content': 'Hacked content!'
        }, format='json')
        self.assertEqual(unauth_edit_res.status_code, status.HTTP_403_FORBIDDEN)

        # 5. Delete post as owner
        self.client.force_authenticate(user=self.user1)
        del_res = self.client.delete(f'/api/posts/{post_id}/')
        self.assertEqual(del_res.status_code, status.HTTP_200_OK)

        # Confirm post is gone
        self.assertEqual(Post.objects.filter(id=post_id).count(), 0)

    def test_likes_and_comments(self):
        post = Post.objects.create(author=self.user1, content="Test post for likes & comments")

        self.client.force_authenticate(user=self.user2)

        # 1. Like post
        like_res = self.client.post(f'/api/posts/{post.id}/like/')
        self.assertEqual(like_res.status_code, status.HTTP_200_OK)
        self.assertTrue(like_res.data['is_liked'])
        self.assertEqual(like_res.data['likes_count'], 1)

        # Verify notification created for author
        notif = Notification.objects.filter(recipient=self.user1, notification_type='like').first()
        self.assertIsNotNone(notif)

        # 2. Unlike post (toggle)
        unlike_res = self.client.post(f'/api/posts/{post.id}/like/')
        self.assertEqual(unlike_res.status_code, status.HTTP_200_OK)
        self.assertFalse(unlike_res.data['is_liked'])
        self.assertEqual(unlike_res.data['likes_count'], 0)

        # 3. Comment on post
        comment_res = self.client.post(f'/api/posts/{post.id}/comments/', {
            'content': 'Great post!'
        }, format='json')
        self.assertEqual(comment_res.status_code, status.HTTP_201_CREATED)
        comment_id = comment_res.data['id']
        self.assertEqual(Comment.objects.filter(post=post).count(), 1)

        # 4. Delete comment
        del_comment_res = self.client.delete(f'/api/comments/{comment_id}/')
        self.assertEqual(del_comment_res.status_code, status.HTTP_200_OK)
        self.assertEqual(Comment.objects.filter(post=post).count(), 0)

    def test_follow_system_and_privacy(self):
        # User 2 is private
        self.user2.profile.is_private = True
        self.user2.profile.save()

        self.client.force_authenticate(user=self.user1)

        # Follow request sent
        follow_res = self.client.post(f'/api/users/{self.user2.username}/follow/')
        self.assertEqual(follow_res.status_code, status.HTTP_200_OK)
        self.assertTrue(follow_res.data['has_pending_request'])
        self.assertFalse(follow_res.data['is_following'])

        follow_obj = Follow.objects.filter(follower=self.user1, following=self.user2).first()
        self.assertIsNotNone(follow_obj)
        self.assertFalse(follow_obj.is_accepted)

        # User 2 accepts follow request
        self.client.force_authenticate(user=self.user2)
        accept_res = self.client.post(f'/api/users/follow-requests/{follow_obj.id}/accept/')
        self.assertEqual(accept_res.status_code, status.HTTP_200_OK)

        follow_obj.refresh_from_db()
        self.assertTrue(follow_obj.is_accepted)

        # User 1 unfollows
        self.client.force_authenticate(user=self.user1)
        unfollow_res = self.client.post(f'/api/users/{self.user2.username}/follow/')
        self.assertEqual(unfollow_res.status_code, status.HTTP_200_OK)
        self.assertFalse(unfollow_res.data['is_following'])

    def test_polls_and_single_vote_constraint(self):
        self.client.force_authenticate(user=self.user1)

        # Create post with poll
        post_res = self.client.post('/api/posts/', {
            'content': 'Which frontend library?',
            'poll_question': 'Your primary stack in 2026?',
            'poll_options': ['Vanilla JS', 'React', 'Vue', 'Svelte']
        }, format='json')
        self.assertEqual(post_res.status_code, status.HTTP_201_CREATED)
        self.assertIn('poll', post_res.data)
        poll_id = post_res.data['poll']['id']
        first_opt_id = post_res.data['poll']['options'][0]['id']

        # User 2 votes
        self.client.force_authenticate(user=self.user2)
        vote_res = self.client.post(f'/api/polls/{poll_id}/vote/', {
            'option_id': first_opt_id
        }, format='json')
        self.assertEqual(vote_res.status_code, status.HTTP_200_OK)
        self.assertEqual(vote_res.data['total_votes'], 1)

        # User 2 attempts second vote on same poll -> should be rejected
        second_vote_res = self.client.post(f'/api/polls/{poll_id}/vote/', {
            'option_id': first_opt_id
        }, format='json')
        self.assertEqual(second_vote_res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bookmarks_and_collections(self):
        post = Post.objects.create(author=self.user1, content="Bookmarking test")
        self.client.force_authenticate(user=self.user2)

        # Save post
        bm_res = self.client.post(f'/api/posts/{post.id}/bookmark/', {
            'collection_name': 'Inspiration'
        }, format='json')
        self.assertEqual(bm_res.status_code, status.HTTP_200_OK)
        self.assertTrue(bm_res.data['is_bookmarked'])

        # Check bookmarks list
        list_res = self.client.get('/api/bookmarks/')
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_res.data), 1)

        # Toggle off
        unbm_res = self.client.post(f'/api/posts/{post.id}/bookmark/')
        self.assertEqual(unbm_res.status_code, status.HTTP_200_OK)
        self.assertFalse(unbm_res.data['is_bookmarked'])

    def test_direct_messaging(self):
        self.client.force_authenticate(user=self.user1)

        # Start conversation
        convo_res = self.client.post(f'/api/messages/start/{self.user2.username}/')
        self.assertEqual(convo_res.status_code, status.HTTP_200_OK)
        convo_id = convo_res.data['id']

        # Send message
        msg_res = self.client.post(f'/api/messages/conversations/{convo_id}/', {
            'content': 'Hello user 2!'
        }, format='json')
        self.assertEqual(msg_res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(msg_res.data['content'], 'Hello user 2!')

        # User 2 reads messages
        self.client.force_authenticate(user=self.user2)
        read_res = self.client.get(f'/api/messages/conversations/{convo_id}/')
        self.assertEqual(read_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(read_res.data), 1)

    def test_ai_caption_assistant_local_fallback(self):
        res = self.client.post('/api/ai/caption-assistant/', {
            'prompt': 'Building a modern full-stack social media platform',
            'tone': 'engaging',
            'category': 'Technology'
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['is_demo'])
        self.assertEqual(len(res.data['captions']), 3)
        self.assertTrue(len(res.data['suggested_hashtags']) > 0)

    def test_search_endpoint(self):
        search_res = self.client.get('/api/search/?q=user')
        self.assertEqual(search_res.status_code, status.HTTP_200_OK)
        self.assertIn('users', search_res.data)
        self.assertIn('posts', search_res.data)
        self.assertIn('hashtags', search_res.data)
