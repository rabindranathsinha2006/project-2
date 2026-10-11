/**
 * CodeGram REST API Client
 */

class ApiService {
  constructor() {
    this.baseUrl = '/api';
  }

  getCsrfToken() {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, 10) === ('csrftoken=')) {
          cookieValue = decodeURIComponent(cookie.substring(10));
          break;
        }
      }
    }
    return cookieValue;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = { ...options.headers };

    const csrfToken = this.getCsrfToken();
    if (csrfToken && !options.noCsrf) {
      headers['X-CSRFToken'] = csrfToken;
    }

    // Only set Content-Type to application/json if body is not FormData
    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    const config = {
      ...options,
      headers,
      credentials: 'same-origin',
    };

    try {
      const response = await fetch(url, config);
      const isJson = (response.headers.get('content-type') || '').includes('application/json');
      const data = isJson ? await response.json() : await response.text();

      if (!response.ok) {
        const errorMsg = data && data.error ? data.error : (data.detail || `Request failed with status ${response.status}`);
        throw new Error(errorMsg);
      }

      return data;
    } catch (error) {
      console.error(`API Error on [${options.method || 'GET'}] ${endpoint}:`, error);
      throw error;
    }
  }

  // --- Auth ---
  async getCurrentUser() {
    return this.request('/auth/me/');
  }

  async login(username, password) {
    return this.request('/auth/login/', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    });
  }

  async register(username, email, password, display_name) {
    return this.request('/auth/register/', {
      method: 'POST',
      body: JSON.stringify({ username, email, password, display_name })
    });
  }

  async logout() {
    return this.request('/auth/logout/', { method: 'POST' });
  }

  // --- Users & Profiles ---
  async getProfile(username) {
    return this.request(`/users/${encodeURIComponent(username)}/`);
  }

  async updateProfile(formData) {
    return this.request('/users/profile/update/', {
      method: 'PATCH',
      body: formData instanceof FormData ? formData : JSON.stringify(formData)
    });
  }

  async toggleFollow(username) {
    return this.request(`/users/${encodeURIComponent(username)}/follow/`, { method: 'POST' });
  }

  async toggleBlock(username) {
    return this.request(`/users/${encodeURIComponent(username)}/block/`, { method: 'POST' });
  }

  async getFollowers(username) {
    return this.request(`/users/${encodeURIComponent(username)}/followers/`);
  }

  async getFollowing(username) {
    return this.request(`/users/${encodeURIComponent(username)}/following/`);
  }

  async getFollowRequests() {
    return this.request('/users/follow-requests/');
  }

  async handleFollowRequest(followId, action) {
    return this.request(`/users/follow-requests/${followId}/${action}/`, { method: 'POST' });
  }

  // --- Posts & Feeds ---
  async getFeed(page = 1) {
    return this.request(`/posts/feed/?page=${page}`);
  }

  async getExplore(category = '', search = '', tag = '', page = 1) {
    let q = `/posts/explore/?page=${page}`;
    if (category) q += `&category=${encodeURIComponent(category)}`;
    if (search) q += `&q=${encodeURIComponent(search)}`;
    if (tag) q += `&tag=${encodeURIComponent(tag)}`;
    return this.request(q);
  }

  async createPost(formData) {
    return this.request('/posts/', {
      method: 'POST',
      body: formData
    });
  }

  async getPost(id) {
    return this.request(`/posts/${id}/`);
  }

  async updatePost(id, data) {
    return this.request(`/posts/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(data)
    });
  }

  async deletePost(id) {
    return this.request(`/posts/${id}/`, { method: 'DELETE' });
  }

  async toggleLike(postId) {
    return this.request(`/posts/${postId}/like/`, { method: 'POST' });
  }

  async getComments(postId) {
    return this.request(`/posts/${postId}/comments/`);
  }

  async addComment(postId, content) {
    return this.request(`/posts/${postId}/comments/`, {
      method: 'POST',
      body: JSON.stringify({ content })
    });
  }

  async deleteComment(commentId) {
    return this.request(`/comments/${commentId}/`, { method: 'DELETE' });
  }

  async votePoll(pollId, optionId) {
    return this.request(`/polls/${pollId}/vote/`, {
      method: 'POST',
      body: JSON.stringify({ option_id: optionId })
    });
  }

  // --- Stories ---
  async getStories() {
    return this.request('/stories/');
  }

  async createStory(formData) {
    return this.request('/stories/', {
      method: 'POST',
      body: formData
    });
  }

  async deleteStory(id) {
    return this.request(`/stories/${id}/`, { method: 'DELETE' });
  }

  // --- Reels ---
  async getReels() {
    return this.request('/reels/');
  }

  async createReel(data) {
    return this.request('/reels/', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async toggleReelLike(reelId) {
    return this.request(`/reels/${reelId}/like/`, { method: 'POST' });
  }

  async getReelComments(reelId) {
    return this.request(`/reels/${reelId}/comments/`);
  }

  async addReelComment(reelId, content) {
    return this.request(`/reels/${reelId}/comments/`, {
      method: 'POST',
      body: JSON.stringify({ content })
    });
  }

  // --- Bookmarks & Collections ---
  async getCollections() {
    return this.request('/collections/');
  }

  async createCollection(name) {
    return this.request('/collections/', {
      method: 'POST',
      body: JSON.stringify({ name })
    });
  }

  async getBookmarks(collectionId = null) {
    const q = collectionId ? `/bookmarks/?collection=${collectionId}` : '/bookmarks/';
    return this.request(q);
  }

  async toggleBookmark(postId, collectionName = '') {
    return this.request(`/posts/${postId}/bookmark/`, {
      method: 'POST',
      body: JSON.stringify({ collection_name: collectionName })
    });
  }

  // --- Hashtags & Search ---
  async getTrendingHashtags() {
    return this.request('/hashtags/trending/');
  }

  async search(query) {
    return this.request(`/search/?q=${encodeURIComponent(query)}`);
  }

  // --- Direct Messaging ---
  async getConversations() {
    return this.request('/messages/conversations/');
  }

  async startConversation(username) {
    return this.request(`/messages/start/${encodeURIComponent(username)}/`, { method: 'POST' });
  }

  async getMessages(conversationId) {
    return this.request(`/messages/conversations/${conversationId}/`);
  }

  async sendMessage(conversationId, content) {
    return this.request(`/messages/conversations/${conversationId}/`, {
      method: 'POST',
      body: JSON.stringify({ content })
    });
  }

  // --- Notifications ---
  async getNotifications() {
    return this.request('/notifications/');
  }

  async markNotificationsRead() {
    return this.request('/notifications/', { method: 'POST' });
  }

  async getUnreadCounts() {
    return this.request('/notifications/unread-count/');
  }

  // --- Dashboard & Analytics ---
  async getDashboardStats() {
    return this.request('/dashboard/stats/');
  }

  // --- Reports ---
  async submitReport(reason, userId = null, postId = null) {
    return this.request('/reports/', {
      method: 'POST',
      body: JSON.stringify({ reason, user_id: userId, post_id: postId })
    });
  }

  // --- AI Assistant ---
  async generateCaption(prompt, tone, category) {
    return this.request('/ai/caption-assistant/', {
      method: 'POST',
      body: JSON.stringify({ prompt, tone, category })
    });
  }
}

window.api = new ApiService();
