# CodeGram — Modern Social Media Platform

CodeGram is a full-stack, responsive, modern social media platform crafted with a clean purple-blue brand aesthetic, seamless Single-Page Application (SPA) architecture, interactive feed features, and a Django REST Framework backend.

---

## 🌟 Key Features

### 1. Core Social Media Capabilities
* **User Profiles:** Display name, bio, location, website, custom interests pills, profile views counter, followers/following counts, cover photos, and avatars.
* **Rich Posts:** Share text posts, attach photos via URL or file upload, edit own posts, delete own posts.
* **Interactive Polls:** Attach multi-option polls directly to posts, cast one vote per account with real-time percentage progress bars.
* **Comments:** Add and view comments with author avatar and timestamp; author/post owner deletion rights.
* **Like System:** Like and unlike posts and reels with live counter feedback and heart animation.
* **Follow System:** Follow/unfollow users with support for Private Accounts and pending follow request approvals.
* **Home Feed:** Intelligent feed combining followed creator posts, relevant interest categories, and trending posts.
* **Global Search:** Search users by username/name, posts by keywords, and hashtags.

### 2. Unique & Premium Features
* **24-Hour Ephemeral Stories:** Publish gradient-based or image-backed stories with a 24-hour expiration window. Features a horizontal story ring bar above the feed and a modal story viewer with an animated progress bar.
* **Reels / Short Videos:** Dedicated vertical video section with scroll snapping, play/pause controls, sound mute/unmute, like counters, and custom audio credits.
* **Saved Collections & Bookmarks:** Privately bookmark favorite posts and organize them into named collections (e.g., *Inspiration*, *Design Systems*).
* **Trending Hashtags:** Auto-extracted `#hashtags` from post captions, ranked and displayed in real-time in the sidebar.
* **Direct Messaging (DM):** Real-time private chat interface with conversation threads, message timestamps, unread notification counts, and instant send.
* **Explore Page:** Filter posts by category pills (*Technology*, *Design*, *Education*, *Gaming*, *Photography*, *Lifestyle*), live search, and creator recommendations.
* **Dark & Light Mode:** System-wide theme switcher with persistence in `localStorage`.
* **Activity & Creator Dashboard:** Interactive performance dashboard tracking total posts, likes received, profile impressions, follower count, and a 7-day engagement chart powered by Chart.js.
* **AI-Powered Caption Assistant:** Built-in AI helper that generates creative captions, tone variations (*Engaging*, *Professional*, *Funny*, *Minimalist*, *Poetic*), and relevant hashtags. Integrates with Google Gemini / OpenAI when configured, or runs automatically via an intelligent local generator fallback.
* **Content Safety & Moderation:** Report content modal and user blocking mechanisms.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | HTML5, Modern CSS3 (Variables, Flexbox/Grid, Dark Mode), Vanilla JavaScript (ES6+ Modules, REST API Client) |
| **Backend** | Python 3, Django 6+, Django REST Framework (DRF), django-cors-headers |
| **Database** | SQLite (Default for development) / PostgreSQL (via `DATABASE_URL`) |
| **Visuals & Charts**| Plus Jakarta Sans typography, SVG icons, Chart.js 4.4 |

---

## 📂 Project Directory Structure

```
project 2/
├── api/
│   ├── management/
│   │   └── commands/
│   │       └── seed_data.py       # Seeds 6 rich creator accounts, posts, polls, stories, reels
│   ├── migrations/                # Database migrations
│   ├── models.py                  # Database models (User, Post, Poll, Story, Reel, etc.)
│   ├── serializers.py             # DRF serializers
│   ├── views.py                   # REST API controllers
│   ├── urls.py                    # REST API route definitions
│   ├── signals.py                 # Profile auto-creation signals
│   └── tests.py                   # Automated test suite (9 test cases)
├── connectsphere_backend/
│   ├── settings.py                # Django settings (DRF, CORS, Auth, Static/Media)
│   ├── urls.py                    # Project root URLs and SPA fallback
│   └── wsgi.py
├── static/
│   ├── css/
│   │   └── style.css              # Custom styling, dark/light theme, responsive layout
│   └── js/
│       ├── api.js                 # Unified REST client with CSRF support
│       ├── components.js          # Component templates (Posts, Stories, Polls, Reels)
│       └── app.js                 # Single-page router, modals, interactions, chart logic
├── templates/
│   └── index.html                 # Main SPA template shell
├── manage.py
├── .env.example                   # Environment configuration template
└── README.md
```

---

## 🚀 Getting Started

### 1. Prerequisites
* Python 3.10+ installed
* Pip package manager

### 2. Install Dependencies
```bash
pip install django djangorestframework django-cors-headers pillow requests
```

### 3. Run Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Seed Rich Demo Data (Recommended)
Populate the platform with 6 realistic creator profiles, posts with polls, stories, reels, bookmarks, and chat history:
```bash
python manage.py seed_data
```

**Pre-seeded Demo Accounts:**
* **Demo User:** `demo_user` | Password: `password123`
* **Sophia (Designer):** `sophia_art` | Password: `password123`
* **Marcus (AI Researcher):** `marcus_tech` | Password: `password123`
* **Elena (Photographer):** `elena_travel` | Password: `password123`
* **Liam (Fitness Coach):** `liam_fitness` | Password: `password123`
* **Zara (Game Dev):** `zara_gamer` | Password: `password123`

*(You can also click the **"1-Click Demo"** button on the Sign In modal to log in instantly).*

### 5. Start the Development Server
```bash
python manage.py runserver
```
Visit **`http://127.0.0.1:8000/`** in your browser.

---

## 📡 API Reference Overview

| Endpoint | Method | Description |
|---|---|---|
| `/api/auth/register/` | POST | Register new user |
| `/api/auth/login/` | POST | User authentication |
| `/api/auth/logout/` | POST | User logout |
| `/api/auth/me/` | GET | Retrieve authenticated user profile |
| `/api/posts/feed/` | GET | Paginated home feed |
| `/api/posts/explore/` | GET | Explore feed with category and tag filters |
| `/api/posts/` | POST | Create post (supports image & poll) |
| `/api/posts/<id>/like/` | POST | Toggle like on post |
| `/api/posts/<id>/comments/` | GET, POST | List comments or add comment |
| `/api/polls/<id>/vote/` | POST | Vote on a poll option (1 vote per user) |
| `/api/stories/` | GET, POST | List active 24h stories or create a new story |
| `/api/reels/` | GET, POST | List vertical short reels or publish a reel |
| `/api/reels/<id>/like/` | POST | Like/unlike reel |
| `/api/bookmarks/` | GET | List saved posts |
| `/api/posts/<id>/bookmark/` | POST | Save or unsave post |
| `/api/collections/` | GET, POST | Manage bookmark collections |
| `/api/messages/conversations/`| GET | List active chat conversations |
| `/api/messages/start/<user>/` | POST | Start conversation with user |
| `/api/messages/conversations/<id>/` | GET, POST | Get messages or send new message |
| `/api/notifications/` | GET, POST | List notifications or mark all read |
| `/api/dashboard/stats/` | GET | Profile view metrics and 7-day stats |
| `/api/ai/caption-assistant/` | POST | Generate AI captions and hashtags |
| `/api/hashtags/trending/` | GET | Retrieve trending hashtags |
| `/api/users/<user>/follow/` | POST | Follow/unfollow or send follow request |

---

## 🧪 Running Automated Tests

Run the full Django test suite verifying authentication, post lifecycles, poll single-vote constraints, follow requests, direct messaging, bookmarks, and search:

```bash
python manage.py test
```

---

## 🔒 Security & Privacy Features
* **Password Hashing:** Uses Django's PBKDF2 algorithm.
* **Input Validation:** Strict validation across all serializer and view endpoints.
* **Ownership Verification:** Users cannot edit or delete posts or comments created by others.
* **Private Account Controls:** Posts belonging to private accounts are shielded from non-followers.
* **CSRF Protection:** Managed via token verification in API client requests.
