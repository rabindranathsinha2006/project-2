from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random

from api.models import (
    Profile, Follow, Post, Poll, PollOption, PollVote,
    Comment, Like, Hashtag, Story, Reel, ReelLike,
    Collection, Bookmark, Conversation, Message, Notification
)


class Command(BaseCommand):
    help = 'Seeds CodeGram database with realistic, rich demo data.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting CodeGram database seed...")

        # 1. Create or get demo users
        users_info = [
            {
                'username': 'demo_user',
                'email': 'demo@codegram.io',
                'first_name': 'Alex',
                'last_name': 'Morgan',
                'display_name': 'Alex Morgan',
                'bio': 'Full-Stack Software Engineer & Open Source Explorer 🚀 Building modern real-time platforms. Passionate about clean code, UX, and AI tools.',
                'location': 'San Francisco, CA',
                'website': 'https://github.com/codegram',
                'interests': 'Technology, Education, Design',
                'is_verified': True,
                'avatar_url': 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=400&q=80',
                'cover_image': 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1200&q=80',
            },
            {
                'username': 'sophia_art',
                'email': 'sophia@codegram.io',
                'first_name': 'Sophia',
                'last_name': 'Chen',
                'display_name': 'Sophia Chen',
                'bio': 'Digital Artist & Minimalist Product Designer 🎨 Exploring 3D generative art, design systems, and serene color palettes.',
                'location': 'Tokyo, Japan',
                'website': 'https://sophiaart.design',
                'interests': 'Design, Photography, Art',
                'is_verified': True,
                'avatar_url': 'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=400&q=80',
                'cover_image': 'https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?auto=format&fit=crop&w=1200&q=80',
            },
            {
                'username': 'marcus_tech',
                'email': 'marcus@codegram.io',
                'first_name': 'Marcus',
                'last_name': 'Vance',
                'display_name': 'Marcus Vance',
                'bio': 'AI Research Engineer @ NeuroLabs 🤖 Sharing breakthroughs in neural interfaces, autonomous agents, and cloud computing.',
                'location': 'Seattle, WA',
                'website': 'https://marcusvance.ai',
                'interests': 'Technology, Gaming, Education',
                'is_verified': True,
                'avatar_url': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=400&q=80',
                'cover_image': 'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=1200&q=80',
            },
            {
                'username': 'elena_travel',
                'email': 'elena@codegram.io',
                'first_name': 'Elena',
                'last_name': 'Rostova',
                'display_name': 'Elena Rostova',
                'bio': 'Global Nomad & Visual Storyteller ✈️ Finding beauty in unseen corners of the Earth. 42 countries and counting.',
                'location': 'Lisbon, Portugal',
                'website': 'https://elenatravels.blog',
                'interests': 'Photography, Lifestyle',
                'is_verified': False,
                'avatar_url': 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=400&q=80',
                'cover_image': 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80',
            },
            {
                'username': 'liam_fitness',
                'email': 'liam@codegram.io',
                'first_name': 'Liam',
                'last_name': 'Davies',
                'display_name': 'Liam Davies',
                'bio': 'Longevity & Performance Coach 🏋️‍♂️ Science-backed micro-habits, mobility routines, and sustained human performance.',
                'location': 'Melbourne, Australia',
                'website': 'https://liamfit.co',
                'interests': 'Lifestyle, Education',
                'is_verified': False,
                'avatar_url': 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=400&q=80',
                'cover_image': 'https://images.unsplash.com/photo-1517838277536-f5f99be501cd?auto=format&fit=crop&w=1200&q=80',
            },
            {
                'username': 'zara_gamer',
                'email': 'zara@codegram.io',
                'first_name': 'Zara',
                'last_name': 'Nova',
                'display_name': 'Zara Nova',
                'bio': 'Indie Game Architect & Creator 🎮 Crafting surreal atmospheric adventures in Unreal Engine 5. Coffee enthusiast ☕',
                'location': 'Austin, TX',
                'website': 'https://zaranova.dev',
                'interests': 'Gaming, Technology, Design',
                'is_verified': True,
                'avatar_url': 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=400&q=80',
                'cover_image': 'https://images.unsplash.com/photo-1550745165-9bc0b252726f?auto=format&fit=crop&w=1200&q=80',
            }
        ]

        created_users = {}
        for u_data in users_info:
            user, created = User.objects.get_or_create(
                username=u_data['username'],
                defaults={
                    'email': u_data['email'],
                    'first_name': u_data['first_name'],
                    'last_name': u_data['last_name']
                }
            )
            # Default password for all seed accounts
            user.set_password('password123')
            user.save()

            profile, _ = Profile.objects.get_or_create(user=user)
            profile.display_name = u_data['display_name']
            profile.bio = u_data['bio']
            profile.location = u_data['location']
            profile.website = u_data['website']
            profile.interests = u_data['interests']
            profile.is_verified = u_data['is_verified']
            profile.avatar_url = u_data['avatar_url']
            profile.cover_image = u_data['cover_image']
            profile.profile_views = random.randint(120, 2400)
            profile.save()

            created_users[user.username] = user

        demo_user = created_users['demo_user']
        sophia = created_users['sophia_art']
        marcus = created_users['marcus_tech']
        elena = created_users['elena_travel']
        liam = created_users['liam_fitness']
        zara = created_users['zara_gamer']

        # 2. Setup Follow Relations
        all_user_list = list(created_users.values())
        for u1 in all_user_list:
            for u2 in all_user_list:
                if u1 != u2:
                    Follow.objects.get_or_create(follower=u1, following=u2, defaults={'is_accepted': True})

        # 3. Create Posts
        posts_data = [
            {
                'author': demo_user,
                'content': "Excited to welcome everyone to CodeGram! 🌐✨ A platform built from the ground up for authentic connections, seamless interactions, and creative expression. Let me know what feature you love most!\n\n#CodeGram #webdev #innovation",
                'category': 'Technology',
                'image_url': 'https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=1000&q=80',
                'is_recommended': True,
                'poll': {
                    'question': "What is your favorite social media format?",
                    'options': ["Classic Rich Posts", "Short Videos / Reels", "24h Stories", "Interactive Polls"]
                }
            },
            {
                'author': sophia,
                'content': "Just wrapped up the design system overhaul for our upcoming spatial audio project! Minimalist lines, subtle glowing gradients, and fluid micro-interactions make all the difference. 🎨📐\n\n#design #uiux #creativity #minimalism",
                'category': 'Design',
                'image_url': 'https://images.unsplash.com/photo-1507238691740-187a5b1d37b8?auto=format&fit=crop&w=1000&q=80',
                'is_recommended': True,
            },
            {
                'author': marcus,
                'content': "Today's breakthrough: multimodal agent orchestration latency dropped by 45%. We're moving closer to assistive computing that feels like an effortless natural conversation. What AI development surprised you the most this year?\n\n#Technology #AI #machinelearning #future",
                'category': 'Technology',
                'image_url': 'https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=1000&q=80',
                'is_recommended': True,
                'poll': {
                    'question': "Which AI capability will transform workflows faster?",
                    'options': ["Autonomous Code Generation", "Real-time Multimodal Voice", "Automated Research & Synthesis"]
                }
            },
            {
                'author': elena,
                'content': "Golden hour over the cliffs of Sintra, Portugal 🏰🌅 The mist rolling through centuries-old pine forests is something right out of a dream. Never stop wandering!\n\n#Photography #travel #wanderlust #sunset",
                'category': 'Photography',
                'image_url': 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1000&q=80',
                'is_recommended': True,
            },
            {
                'author': liam,
                'content': "The 3 Non-Negotiable Pillars of Daily Longevity:\n1. 20-minute morning sunlight exposure ☀️\n2. Zone 2 aerobic base cardio 3x weekly 🏃\n3. High-protein nutrient-dense whole foods 🥗\nConsistency always beats sporadic intensity!\n\n#Lifestyle #fitness #wellness #health",
                'category': 'Lifestyle',
                'image_url': 'https://images.unsplash.com/photo-1517838277536-f5f99be501cd?auto=format&fit=crop&w=1000&q=80',
                'is_recommended': False,
            },
            {
                'author': zara,
                'content': "New lighting test in Unreal Engine 5 with procedural volumetrics! 🎮✨ Our indie studio is building an atmospheric puzzle game set in an overgrown observatory. Sound on for ambience!\n\n#Gaming #gamedev #indiedev #unrealengine",
                'category': 'Gaming',
                'image_url': 'https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=1000&q=80',
                'is_recommended': True,
            },
            {
                'author': demo_user,
                'content': "Building with modular component architecture keeps software clean and enjoyable to scale. Remember: premature optimization is the root of all evil, but thoughtful architecture pays dividends forever. 💻💡\n\n#webdev #coding #tech #softwareengineering",
                'category': 'Education',
                'image_url': 'https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=1000&q=80',
                'is_recommended': True,
            }
        ]

        created_posts = []
        for p_info in posts_data:
            post, created = Post.objects.get_or_create(
                author=p_info['author'],
                content=p_info['content'],
                defaults={
                    'category': p_info['category'],
                    'image_url': p_info.get('image_url', ''),
                    'is_recommended': p_info.get('is_recommended', False)
                }
            )
            post.update_hashtags()
            created_posts.append(post)

            # Add poll if specified
            if 'poll' in p_info and not hasattr(post, 'poll'):
                poll_data = p_info['poll']
                poll = Poll.objects.create(post=post, question=poll_data['question'])
                for idx, opt_title in enumerate(poll_data['options']):
                    opt = PollOption.objects.create(poll=poll, text=opt_title, order=idx)
                    # Add some votes
                    for voter in random.sample(all_user_list, k=random.randint(1, 4)):
                        if not PollVote.objects.filter(poll=poll, user=voter).exists():
                            PollVote.objects.create(poll=poll, option=opt, user=voter)

        # 4. Add Likes and Comments to Posts
        sample_comments = [
            "This looks absolutely stunning! Brilliant work. 🙌",
            "Totally agree with this perspective. Consistency is key!",
            "Such crisp visuals and great attention to detail. 🚀",
            "Bookmarked this for inspiration! Keep them coming.",
            "Incredible vibe here. Which tool did you use for the rendering?",
            "Count me in! This is exactly what the community needed. 🔥"
        ]

        for post in created_posts:
            # Add random likes
            for voter in random.sample(all_user_list, k=random.randint(2, 5)):
                Like.objects.get_or_create(post=post, user=voter)

            # Add comments
            for commenter in random.sample(all_user_list, k=random.randint(1, 3)):
                if commenter != post.author:
                    Comment.objects.create(
                        post=post,
                        author=commenter,
                        content=random.choice(sample_comments)
                    )

        # 5. Stories (Expiring in 24h)
        stories_data = [
            {
                'user': demo_user,
                'text_content': 'Morning coffee + code sprint ☕💻',
                'media_url': 'https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?auto=format&fit=crop&w=600&q=80',
                'gradient': 'linear-gradient(135deg, #6366f1, #8b5cf6)'
            },
            {
                'user': sophia,
                'text_content': 'Palette moodboard for sprint 3 🎨',
                'media_url': 'https://images.unsplash.com/photo-1541701494587-cb58502866ab?auto=format&fit=crop&w=600&q=80',
                'gradient': 'linear-gradient(135deg, #ec4899, #8b5cf6)'
            },
            {
                'user': marcus,
                'text_content': 'Deploying model checkpoint 94 🤖🚀',
                'media_url': 'https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=600&q=80',
                'gradient': 'linear-gradient(135deg, #3b82f6, #2dd4bf)'
            },
            {
                'user': elena,
                'text_content': 'Exploring coastal cliffs at sunrise 🌊',
                'media_url': 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=600&q=80',
                'gradient': 'linear-gradient(135deg, #f59e0b, #ef4444)'
            },
            {
                'user': zara,
                'text_content': 'Late night shader tweaking 🎮✨',
                'media_url': 'https://images.unsplash.com/photo-1511512578047-dfb367046420?auto=format&fit=crop&w=600&q=80',
                'gradient': 'linear-gradient(135deg, #8b5cf6, #ec4899)'
            }
        ]

        for s in stories_data:
            Story.objects.get_or_create(
                user=s['user'],
                text_content=s['text_content'],
                defaults={
                    'media_url': s['media_url'],
                    'background_gradient': s['gradient'],
                    'expires_at': timezone.now() + timedelta(hours=22)
                }
            )

        # 6. Reels / Short Videos
        # Sample web-optimized vertical MP4 clips and previews
        reels_data = [
            {
                'user': sophia,
                'title': 'Color Harmony in Product Design 🎨',
                'description': 'How we pick contrasting yet harmonious palettes for dark & light UI themes.',
                'video_url': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4',
                'thumbnail_url': 'https://images.unsplash.com/photo-1507238691740-187a5b1d37b8?auto=format&fit=crop&w=600&q=80',
                'song_title': 'Lo-Fi Chillbeats • Summer Vibes'
            },
            {
                'user': elena,
                'title': 'Secret Lagoon Walkthrough 🌊',
                'description': 'Trekking down to the hidden crystal cove at morning tide.',
                'video_url': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4',
                'thumbnail_url': 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=600&q=80',
                'song_title': 'Acoustic Journeys • Wanderlust'
            },
            {
                'user': zara,
                'title': 'Physics & Volumetric Fog Test 🕹️',
                'description': 'Interactive particle collision in dynamic lighting conditions.',
                'video_url': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4',
                'thumbnail_url': 'https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=600&q=80',
                'song_title': 'Synthwave Nights • Neon Horizon'
            },
            {
                'user': liam,
                'title': 'Morning Mobility Flow in 3 Minutes 🧘‍♂️',
                'description': 'Unlock hip and spine tension right after waking up.',
                'video_url': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyBlazes.mp4',
                'thumbnail_url': 'https://images.unsplash.com/photo-1517838277536-f5f99be501cd?auto=format&fit=crop&w=600&q=80',
                'song_title': 'Mindful Movement • Daily Habit'
            }
        ]

        for r in reels_data:
            reel, created = Reel.objects.get_or_create(
                user=r['user'],
                title=r['title'],
                defaults={
                    'description': r['description'],
                    'video_url': r['video_url'],
                    'thumbnail_url': r['thumbnail_url'],
                    'song_title': r['song_title']
                }
            )
            # Add likes
            for u in random.sample(all_user_list, k=3):
                ReelLike.objects.get_or_create(reel=reel, user=u)

        # 7. Bookmarks and Collections for demo_user
        col_design, _ = Collection.objects.get_or_create(user=demo_user, name='Design Systems')
        col_tech, _ = Collection.objects.get_or_create(user=demo_user, name='AI & Tech Articles')

        if created_posts:
            Bookmark.objects.get_or_create(user=demo_user, post=created_posts[1], defaults={'collection': col_design})
            Bookmark.objects.get_or_create(user=demo_user, post=created_posts[2], defaults={'collection': col_tech})

        # 8. Direct Messaging Conversation
        conv, _ = Conversation.objects.get_or_create(id=1)
        conv.participants.add(demo_user, sophia)
        
        if not conv.messages.exists():
            Message.objects.create(
                conversation=conv,
                sender=sophia,
                content="Hey Alex! Loved your initial post on CodeGram. How is the architecture coming along?",
                is_read=True,
                created_at=timezone.now() - timedelta(minutes=45)
            )
            Message.objects.create(
                conversation=conv,
                sender=demo_user,
                content="Thanks Sophia! It's super smooth — real-time feeds, stories, reels, and custom collections are working nicely.",
                is_read=True,
                created_at=timezone.now() - timedelta(minutes=30)
            )
            Message.objects.create(
                conversation=conv,
                sender=sophia,
                content="Awesome! I'll prep a few more design mockups and UI tokens for the dark mode toggle.",
                is_read=False,
                created_at=timezone.now() - timedelta(minutes=10)
            )

        # 9. Notifications for demo_user
        if created_posts:
            Notification.objects.get_or_create(
                recipient=demo_user,
                sender=sophia,
                notification_type='like',
                post=created_posts[0],
                defaults={'text': '@sophia_art liked your post.'}
            )
            Notification.objects.get_or_create(
                recipient=demo_user,
                sender=marcus,
                notification_type='comment',
                post=created_posts[0],
                defaults={'text': '@marcus_tech commented on your post.'}
            )
            Notification.objects.get_or_create(
                recipient=demo_user,
                sender=zara,
                notification_type='follow',
                defaults={'text': '@zara_gamer started following you.'}
            )

        self.stdout.write(self.style.SUCCESS("CodeGram seed data generated successfully!"))
        self.stdout.write(self.style.SUCCESS("Demo User: 'demo_user' | Password: 'password123'"))
