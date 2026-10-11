/**
 * CodeGram — Main Application Controller & Router
 */

class CodeGramApp {
  constructor() {
    this.currentUser = null;
    this.currentView = 'feed';
    this.activeConversationId = null;
    this.activePollPostId = null;
    this.selectedAiTone = 'engaging';
    this.storyViewerTimer = null;
    this.currentStoryIndex = 0;
    this.activeStories = [];
    this.dashboardChart = null;

    // Theme initialization
    this.theme = localStorage.getItem('cs_theme') || 'light';
    this.applyTheme(this.theme);
  }

  async init() {
    console.log("Initializing CodeGram...");
    // 1. Fetch current user
    await this.fetchCurrentUser();

    // 2. Setup Route Listener
    window.addEventListener('hashchange', () => this.handleRoute());

    // 3. Load Right Widgets (Trending Tags & Suggested Creators)
    this.loadTrendingTags();
    this.loadSuggestedCreators();

    // 4. Initial Route
    if (!window.location.hash) {
      window.location.hash = this.currentUser ? '#feed' : '#feed';
    } else {
      this.handleRoute();
    }

    // 5. Periodic unread count check
    if (this.currentUser) {
      this.checkUnreadCounts();
      setInterval(() => this.checkUnreadCounts(), 30000);
    }
  }

  // ============================================================================
  // THEME MANAGEMENT
  // ============================================================================

  applyTheme(theme) {
    this.theme = theme;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('cs_theme', theme);
  }

  toggleTheme() {
    const nextTheme = this.theme === 'dark' ? 'light' : 'dark';
    this.applyTheme(nextTheme);
    this.showToast(`Switched to ${nextTheme} theme`, 'info');
  }

  // ============================================================================
  // AUTHENTICATION
  // ============================================================================

  async fetchCurrentUser() {
    try {
      const res = await window.api.getCurrentUser();
      if (res.authenticated && res.user) {
        this.currentUser = res.user;
        this.updateUserUI(res.user);
      } else {
        this.currentUser = null;
        this.updateUserUI(null);
      }
    } catch (e) {
      this.currentUser = null;
      this.updateUserUI(null);
    }
  }

  updateUserUI(user) {
    const sidebarAvatar = document.getElementById('sidebar-avatar');
    const sidebarName = document.getElementById('sidebar-name');
    const sidebarHandle = document.getElementById('sidebar-handle');
    const authHeaderBtn = document.getElementById('auth-header-btn');
    const profileNavLink = document.getElementById('profile-nav-link');

    if (user) {
      sidebarAvatar.src = user.profile.avatar_url;
      sidebarName.innerText = user.profile.display_name || user.username;
      sidebarHandle.innerText = `@${user.username}`;
      if (profileNavLink) profileNavLink.href = `#profile/${user.username}`;

      authHeaderBtn.innerHTML = `
        <button class="btn-primary" style="padding: 6px 14px; font-size: 0.85rem; background: var(--bg-surface-alt); color: var(--text-main); border: 1px solid var(--border-subtle);" onclick="window.app.logout()">
          Sign Out
        </button>
      `;
    } else {
      sidebarAvatar.src = 'https://api.dicebear.com/7.x/avataaars/svg?seed=guest';
      sidebarName.innerText = 'Guest Visitor';
      sidebarHandle.innerText = 'Sign In / Register';
      if (profileNavLink) profileNavLink.href = '#auth';

      authHeaderBtn.innerHTML = `
        <button class="btn-primary" style="padding: 6px 16px; font-size: 0.85rem;" onclick="window.app.openAuthModal('login')">
          Sign In
        </button>
      `;
    }
  }

  handleSidebarUserClick() {
    if (this.currentUser) {
      window.location.hash = `#profile/${this.currentUser.username}`;
    } else {
      this.openAuthModal('login');
    }
  }

  openAuthModal(tab = 'login') {
    this.switchAuthTab(tab);
    document.getElementById('auth-modal').classList.add('open');
  }

  closeAuthModal() {
    document.getElementById('auth-modal').classList.remove('open');
  }

  switchAuthTab(tab) {
    const isLogin = tab === 'login';
    document.getElementById('tab-login-btn').className = isLogin ? 'category-chip active' : 'category-chip';
    document.getElementById('tab-register-btn').className = isLogin ? 'category-chip' : 'category-chip active';
    document.getElementById('auth-name-group').style.display = isLogin ? 'none' : 'block';
    document.getElementById('auth-email-group').style.display = isLogin ? 'none' : 'block';
    document.getElementById('auth-submit-btn').innerText = isLogin ? 'Sign In' : 'Create Account';
    document.getElementById('auth-modal-title').innerText = isLogin ? 'Welcome Back to CodeGram' : 'Join CodeGram';
    this.authMode = tab;
  }

  async quickDemoLogin() {
    try {
      const res = await window.api.login('demo_user', 'password123');
      this.currentUser = res.user;
      this.updateUserUI(res.user);
      this.closeAuthModal();
      this.showToast(`Signed in as @${res.user.username}!`, 'success');
      this.handleRoute();
      this.checkUnreadCounts();
    } catch (e) {
      this.showToast(e.message, 'error');
    }
  }

  async handleAuthSubmit(e) {
    e.preventDefault();
    const username = document.getElementById('auth-username').value.trim();
    const password = document.getElementById('auth-password').value.trim();

    try {
      if (this.authMode === 'register') {
        const email = document.getElementById('auth-email').value.trim();
        const displayName = document.getElementById('auth-display-name').value.trim();
        const res = await window.api.register(username, email, password, displayName);
        this.currentUser = res.user;
        this.showToast('Account created successfully!', 'success');
      } else {
        const res = await window.api.login(username, password);
        this.currentUser = res.user;
        this.showToast(`Welcome back, @${this.currentUser.username}!`, 'success');
      }
      this.updateUserUI(this.currentUser);
      this.closeAuthModal();
      this.handleRoute();
      this.checkUnreadCounts();
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  }

  async logout() {
    try {
      await window.api.logout();
      this.currentUser = null;
      this.updateUserUI(null);
      this.showToast('Signed out successfully.', 'info');
      window.location.hash = '#feed';
      this.handleRoute();
    } catch (e) {
      this.currentUser = null;
      this.updateUserUI(null);
      this.handleRoute();
    }
  }

  async checkUnreadCounts() {
    if (!this.currentUser) return;
    try {
      const data = await window.api.getUnreadCounts();
      const notifBadge = document.getElementById('notif-badge');
      const msgBadge = document.getElementById('messages-badge');

      if (data.unread_notifications > 0) {
        notifBadge.innerText = data.unread_notifications;
        notifBadge.style.display = 'inline-block';
      } else {
        notifBadge.style.display = 'none';
      }

      if (data.unread_messages > 0) {
        msgBadge.innerText = data.unread_messages;
        msgBadge.style.display = 'inline-block';
      } else {
        msgBadge.style.display = 'none';
      }
    } catch (e) {
      // quiet catch
    }
  }

  // ============================================================================
  // ROUTER & NAVIGATION
  // ============================================================================

  handleRoute() {
    const rawHash = window.location.hash.slice(1) || 'feed';
    const [path, queryStr] = rawHash.split('?');
    const pathParts = path.split('/');
    const mainRoute = pathParts[0];

    // Highlight nav item
    document.querySelectorAll('.nav-item').forEach(el => {
      const nav = el.getAttribute('data-nav');
      if (nav === mainRoute) el.classList.add('active');
      else el.classList.remove('active');
    });

    // Update Page title
    const titles = {
      feed: 'Home Feed',
      explore: 'Explore & Discover',
      reels: 'Reels & Short Clips',
      messages: 'Direct Messages',
      notifications: 'Notifications',
      bookmarks: 'Saved Collections',
      dashboard: 'Creator Analytics',
      settings: 'Profile & Settings',
      profile: 'User Profile',
    };
    document.getElementById('page-title').innerText = titles[mainRoute] || 'CodeGram';

    // Route rendering
    switch (mainRoute) {
      case 'feed':
        this.renderFeedView();
        break;
      case 'explore':
        const urlParams = new URLSearchParams(queryStr);
        this.renderExploreView(urlParams.get('category'), urlParams.get('tag'), urlParams.get('q'));
        break;
      case 'reels':
        this.renderReelsView();
        break;
      case 'messages':
        this.renderMessagesView();
        break;
      case 'notifications':
        this.renderNotificationsView();
        break;
      case 'bookmarks':
        this.renderBookmarksView();
        break;
      case 'dashboard':
        this.renderDashboardView();
        break;
      case 'profile':
        const username = pathParts[1] || (this.currentUser ? this.currentUser.username : 'demo_user');
        this.renderProfileView(username);
        break;
      case 'settings':
        this.renderSettingsView();
        break;
      default:
        this.renderFeedView();
    }
  }

  // ============================================================================
  // VIEW: HOME FEED
  // ============================================================================

  async renderFeedView() {
    const container = document.getElementById('view-content');
    container.innerHTML = `
      <!-- Stories Bar -->
      <section class="stories-tray" id="stories-tray">
        <div style="font-size: 0.88rem; color: var(--text-muted); padding: 10px;">Loading stories...</div>
      </section>

      <!-- Create Post Box -->
      ${this.renderPostComposerHTML()}

      <!-- Posts Stream -->
      <div id="posts-stream">
        ${Components.renderSkeletonCard()}
        ${Components.renderSkeletonCard()}
      </div>
    `;

    // Load Stories
    this.loadStoriesTray();
    // Load Posts
    this.loadFeedPosts();
  }

  renderPostComposerHTML() {
    const avatar = this.currentUser ? this.currentUser.profile.avatar_url : 'https://api.dicebear.com/7.x/avataaars/svg?seed=guest';
    return `
      <section class="create-post-card" id="post-composer">
        <div class="create-post-top">
          <img class="create-post-avatar" src="${avatar}" alt="You">
          <div class="create-post-input-box">
            <textarea id="composer-content" class="create-post-textarea" placeholder="What's happening in your code today? Share your thoughts, snippets, or discoveries..."></textarea>
            
            <!-- Optional image URL input -->
            <div id="image-url-box" style="display:none; margin-top: 10px;">
              <input type="url" id="composer-image-url" class="poll-option-input" placeholder="Paste image URL (e.g. Unsplash, imgur...)" oninput="window.app.previewImageUrl(this.value)">
            </div>

            <!-- Optional Image Preview -->
            <div class="media-preview-container" id="composer-preview-container">
              <img id="composer-preview-img" class="media-preview-img" src="">
              <button class="media-preview-remove" onclick="window.app.clearMediaPreview()">✕</button>
            </div>

            <!-- Optional Poll Builder -->
            <div class="poll-create-box" id="composer-poll-box">
              <div style="font-weight: 700; font-size: 0.88rem; margin-bottom: 8px;">Create an Interactive Poll</div>
              <input type="text" id="poll-question-input" class="poll-option-input" placeholder="Poll question (e.g. Which framework in 2026?)">
              <input type="text" class="poll-option-input poll-opt" placeholder="Option 1">
              <input type="text" class="poll-option-input poll-opt" placeholder="Option 2">
              <input type="text" class="poll-option-input poll-opt" placeholder="Option 3 (optional)">
              <input type="text" class="poll-option-input poll-opt" placeholder="Option 4 (optional)">
            </div>
          </div>
        </div>

        <div class="create-post-bottom">
          <div class="post-action-buttons">
            <button class="action-icon-btn" onclick="window.app.toggleImageInput()" title="Add Image URL">
              <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
              <span>Photo</span>
            </button>
            <button class="action-icon-btn" onclick="window.app.togglePollBox()" title="Add Poll">
              <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
              <span>Poll</span>
            </button>
            <button class="action-icon-btn ai-assistant-btn" onclick="window.app.openAiModal()" title="AI Caption & Hashtag Assistant">
              <span>✨ AI Assistant</span>
            </button>
          </div>

          <div style="display: flex; align-items: center; gap: 10px;">
            <select id="composer-category" class="category-pill" style="border: 1px solid var(--border-subtle); outline: none; cursor: pointer;">
              <option value="General">General</option>
              <option value="Technology">Technology</option>
              <option value="Design">Design</option>
              <option value="Education">Education</option>
              <option value="Gaming">Gaming</option>
              <option value="Photography">Photography</option>
              <option value="Lifestyle">Lifestyle</option>
            </select>
            <button class="btn-primary" onclick="window.app.submitNewPost()">Publish</button>
          </div>
        </div>
      </section>
    `;
  }

  async loadStoriesTray() {
    const tray = document.getElementById('stories-tray');
    if (!tray) return;

    try {
      const stories = await window.api.getStories();
      this.activeStories = stories;
      
      let html = Components.renderStoryBubble(null, true);
      stories.forEach(s => {
        html += Components.renderStoryBubble(s, false);
      });
      tray.innerHTML = html;
    } catch (e) {
      tray.innerHTML = `<div style="font-size: 0.82rem; color: var(--text-muted); padding: 10px;">Unable to load stories.</div>`;
    }
  }

  async loadFeedPosts() {
    const stream = document.getElementById('posts-stream');
    if (!stream) return;

    try {
      const res = await window.api.getFeed(1);
      const posts = res.results || res;

      if (!posts || posts.length === 0) {
        stream.innerHTML = `
          <div style="padding: 40px 20px; text-align: center; color: var(--text-muted);">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin-bottom: 12px; opacity: 0.6;"><circle cx="12" cy="12" r="10"></circle><line x1="8" y1="12" x2="16" y2="12"></line></svg>
            <div style="font-weight: 700; font-size: 1.1rem; margin-bottom: 4px;">No posts in your feed yet</div>
            <p style="font-size: 0.9rem;">Follow creators or explore categories to discover trending posts!</p>
          </div>
        `;
        return;
      }

      stream.innerHTML = posts.map(p => Components.renderPostCard(p, this.currentUser)).join('');
    } catch (e) {
      stream.innerHTML = `<div style="padding: 24px; color: var(--accent-rose); text-align: center;">Error loading feed: ${e.message}</div>`;
    }
  }

  toggleImageInput() {
    const box = document.getElementById('image-url-box');
    box.style.display = box.style.display === 'none' ? 'block' : 'none';
  }

  previewImageUrl(url) {
    const container = document.getElementById('composer-preview-container');
    const img = document.getElementById('composer-preview-img');
    if (url && url.startsWith('http')) {
      img.src = url;
      container.style.display = 'block';
    } else {
      container.style.display = 'none';
    }
  }

  clearMediaPreview() {
    document.getElementById('composer-preview-container').style.display = 'none';
    document.getElementById('composer-image-url').value = '';
  }

  togglePollBox() {
    const box = document.getElementById('composer-poll-box');
    box.style.display = box.style.display === 'none' ? 'block' : 'none';
  }

  focusPostCreator() {
    window.location.hash = '#feed';
    setTimeout(() => {
      const txt = document.getElementById('composer-content');
      if (txt) {
        txt.focus();
        txt.scrollIntoView({ behavior: 'smooth' });
      }
    }, 150);
  }

  async submitNewPost() {
    if (!this.currentUser) {
      this.openAuthModal('login');
      return;
    }

    const content = document.getElementById('composer-content').value.trim();
    const category = document.getElementById('composer-category').value;
    const imageUrl = document.getElementById('composer-image-url') ? document.getElementById('composer-image-url').value.trim() : '';

    const pollQuestion = document.getElementById('poll-question-input') ? document.getElementById('poll-question-input').value.trim() : '';
    let pollOptions = [];
    if (pollQuestion) {
      const optInputs = document.querySelectorAll('.poll-opt');
      optInputs.forEach(input => {
        if (input.value.trim()) pollOptions.push(input.value.trim());
      });
      if (pollOptions.length < 2) {
        this.showToast('A poll requires at least 2 options.', 'error');
        return;
      }
    }

    if (!content && !imageUrl && !pollQuestion) {
      this.showToast('Please enter post text, an image, or a poll.', 'error');
      return;
    }

    const formData = new FormData();
    formData.append('content', content);
    formData.append('category', category);
    if (imageUrl) formData.append('image_url', imageUrl);
    if (pollQuestion) {
      formData.append('poll_question', pollQuestion);
      formData.append('poll_options', JSON.stringify(pollOptions));
    }

    try {
      const newPost = await window.api.createPost(formData);
      this.showToast('Post published to CodeGram!', 'success');
      
      // Reset composer
      document.getElementById('composer-content').value = '';
      if (document.getElementById('composer-image-url')) document.getElementById('composer-image-url').value = '';
      this.clearMediaPreview();
      const pollBox = document.getElementById('composer-poll-box');
      if (pollBox) {
        pollBox.style.display = 'none';
        document.getElementById('poll-question-input').value = '';
        document.querySelectorAll('.poll-opt').forEach(i => i.value = '');
      }

      // Prepend to feed
      const stream = document.getElementById('posts-stream');
      if (stream) {
        stream.insertAdjacentHTML('afterbegin', Components.renderPostCard(newPost, this.currentUser));
      }
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  }

  // ============================================================================
  // POST ACTIONS: LIKE, COMMENT, DELETE, POLL VOTE, BOOKMARK
  // ============================================================================

  async toggleLike(postId) {
    if (!this.currentUser) {
      this.openAuthModal('login');
      return;
    }

    const postCard = document.getElementById(`post-${postId}`);
    const likeBtn = postCard.querySelector('.post-action-btn:nth-child(1)');
    const countSpan = likeBtn.querySelector('.likes-count');

    try {
      const res = await window.api.toggleLike(postId);
      if (res.is_liked) {
        likeBtn.classList.add('liked');
      } else {
        likeBtn.classList.remove('liked');
      }
      countSpan.innerText = res.likes_count;
    } catch (e) {
      this.showToast(e.message, 'error');
    }
  }

  async votePoll(pollId, optionId, postId) {
    if (!this.currentUser) {
      this.openAuthModal('login');
      return;
    }

    try {
      const updatedPoll = await window.api.votePoll(pollId, optionId);
      this.showToast('Vote recorded!', 'success');
      
      // Update the poll widget UI
      const postCard = document.getElementById(`post-${postId}`);
      if (postCard) {
        const pollWidget = postCard.querySelector('.poll-widget');
        if (pollWidget) {
          const userVotedId = updatedPoll.user_voted_option_id;
          const optionsHtml = updatedPoll.options.map(opt => `
            <div class="poll-option-row ${userVotedId === opt.id ? 'voted' : ''}" data-option-id="${opt.id}">
              <div class="poll-fill-bar" style="width: ${opt.percentage}%"></div>
              <div class="poll-option-content">
                <span>${opt.text} ${userVotedId === opt.id ? '✓' : ''}</span>
                <span>${opt.percentage}% (${opt.votes_count})</span>
              </div>
            </div>
          `).join('');

          pollWidget.querySelector('.poll-options-list').innerHTML = optionsHtml;
          pollWidget.querySelector('.poll-footer').innerHTML = `<span>${updatedPoll.total_votes} total votes • You voted</span>`;
        }
      }
    } catch (e) {
      this.showToast(e.message, 'error');
    }
  }

  toggleCommentBox(postId) {
    const box = document.getElementById(`comments-section-${postId}`);
    if (box) {
      const input = box.querySelector('.comment-input');
      if (input) input.focus();
    }
  }

  async submitComment(e, postId) {
    e.preventDefault();
    if (!this.currentUser) {
      this.openAuthModal('login');
      return;
    }

    const form = e.target;
    const input = form.querySelector('.comment-input');
    const content = input.value.trim();
    if (!content) return;

    try {
      const comment = await window.api.addComment(postId, content);
      input.value = '';

      // Append comment
      const list = document.getElementById(`comments-list-${postId}`);
      if (list) {
        list.insertAdjacentHTML('beforeend', `
          <div class="comment-item" id="comment-${comment.id}">
            <img class="comment-avatar" src="${comment.author.avatar_url}" alt="${comment.author.username}">
            <div class="comment-bubble">
              <div class="comment-author-name">
                <a href="#profile/${comment.author.username}">@${comment.author.username}</a>
                <span style="font-weight: 400; color: var(--text-light); font-size: 0.78rem; margin-left: 6px;">just now</span>
              </div>
              <div>${Components.formatContent(comment.content)}</div>
            </div>
          </div>
        `);
      }

      // Update count
      const postCard = document.getElementById(`post-${postId}`);
      if (postCard) {
        const commentCountSpan = postCard.querySelector('.comments-count');
        if (commentCountSpan) {
          commentCountSpan.innerText = parseInt(commentCountSpan.innerText || 0) + 1;
        }
      }
      this.showToast('Comment posted.', 'success');
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  }

  async deletePost(postId) {
    if (!confirm('Are you sure you want to delete this post?')) return;
    try {
      await window.api.deletePost(postId);
      const postCard = document.getElementById(`post-${postId}`);
      if (postCard) postCard.remove();
      this.showToast('Post deleted.', 'info');
    } catch (e) {
      this.showToast(e.message, 'error');
    }
  }

  async toggleBookmark(postId) {
    if (!this.currentUser) {
      this.openAuthModal('login');
      return;
    }

    const postCard = document.getElementById(`post-${postId}`);
    const bookmarkBtn = postCard.querySelector('.post-action-btn:nth-child(3)');

    try {
      const res = await window.api.toggleBookmark(postId);
      if (res.is_bookmarked) {
        bookmarkBtn.classList.add('bookmarked');
      } else {
        bookmarkBtn.classList.remove('bookmarked');
      }
      this.showToast(res.message, 'info');
    } catch (e) {
      this.showToast(e.message, 'error');
    }
  }

  sharePost(postId) {
    const url = `${window.location.origin}/#post/${postId}`;
    navigator.clipboard.writeText(url);
    this.showToast('Post link copied to clipboard!', 'success');
  }

  openImagePreview(url) {
    window.open(url, '_blank');
  }

  // ============================================================================
  // VIEW: EXPLORE
  // ============================================================================

  async renderExploreView(activeCategory = 'All', activeTag = '', searchQuery = '') {
    const container = document.getElementById('view-content');
    const categories = ['All', 'Technology', 'Design', 'Education', 'Gaming', 'Photography', 'Lifestyle'];

    container.innerHTML = `
      <div style="padding: 16px 20px; background: var(--bg-surface); border-bottom: 1px solid var(--border-subtle);">
        <div class="search-box">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--text-muted);"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
          <input type="text" id="explore-search-input" value="${searchQuery || (activeTag ? '#' + activeTag : '')}" placeholder="Search posts, hashtags, or creators..." onkeydown="if(event.key==='Enter') window.app.executeExploreSearch(this.value)">
        </div>
      </div>

      <div class="category-filter-bar">
        ${categories.map(c => `
          <button class="category-chip ${((!activeCategory && c === 'All') || (activeCategory && activeCategory.toLowerCase() === c.toLowerCase())) ? 'active' : ''}" 
                  onclick="window.location.hash = '#explore?category=${c}'">
            ${c}
          </button>
        `).join('')}
      </div>

      <div id="explore-stream">
        ${Components.renderSkeletonCard()}
        ${Components.renderSkeletonCard()}
      </div>
    `;

    try {
      const res = await window.api.getExplore(activeCategory === 'All' ? '' : activeCategory, searchQuery, activeTag);
      const data = res.results || res;
      const posts = data.posts || [];
      const stream = document.getElementById('explore-stream');

      if (posts.length === 0) {
        stream.innerHTML = `
          <div style="padding: 40px 20px; text-align: center; color: var(--text-muted);">
            <div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 4px;">No posts found</div>
            <p style="font-size: 0.9rem;">Try selecting another category or searching for another term.</p>
          </div>
        `;
        return;
      }

      stream.innerHTML = posts.map(p => Components.renderPostCard(p, this.currentUser)).join('');
    } catch (e) {
      document.getElementById('explore-stream').innerHTML = `<div style="padding:20px; color:var(--accent-rose);">${e.message}</div>`;
    }
  }

  executeExploreSearch(val) {
    if (!val.trim()) return;
    window.location.hash = `#explore?q=${encodeURIComponent(val.trim())}`;
  }

  handleSearchSubmit(val) {
    if (!val.trim()) return;
    window.location.hash = `#explore?q=${encodeURIComponent(val.trim())}`;
  }

  // ============================================================================
  // VIEW: REELS / SHORT VIDEOS
  // ============================================================================

  async renderReelsView() {
    const container = document.getElementById('view-content');
    container.innerHTML = `
      <div style="display: flex; justify-content: flex-end; padding: 12px 20px; background: var(--bg-surface); border-bottom: 1px solid var(--border-subtle);">
        <button class="btn-primary" onclick="window.app.openCreateReelModal()" style="display: flex; align-items: center; gap: 6px;">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
          <span>Create Reel</span>
        </button>
      </div>

      <div class="reels-container" id="reels-scroller">
        <div style="color: white; padding: 40px; text-align: center;">Loading Reels...</div>
      </div>
    `;

    try {
      const reels = await window.api.getReels();
      const scroller = document.getElementById('reels-scroller');

      if (!reels || reels.length === 0) {
        scroller.innerHTML = `<div style="color: white; padding: 40px; text-align: center;">No reels yet. Be the first to share one!</div>`;
        return;
      }

      scroller.innerHTML = reels.map(r => Components.renderReelCard(r, this.currentUser)).join('');

      // Auto play first reel
      setTimeout(() => {
        const firstVid = scroller.querySelector('video');
        if (firstVid) firstVid.play().catch(() => {});
      }, 300);
    } catch (e) {
      document.getElementById('reels-scroller').innerHTML = `<div style="color:white; padding:20px;">${e.message}</div>`;
    }
  }

  toggleVideoPlay(videoEl) {
    if (videoEl.paused) {
      videoEl.play().catch(() => {});
    } else {
      videoEl.pause();
    }
  }

  toggleReelMute(btn) {
    const reelCard = btn.closest('.reel-card');
    const vid = reelCard.querySelector('video');
    vid.muted = !vid.muted;
    btn.innerHTML = vid.muted
      ? `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="1" y1="1" x2="23" y2="23"></line><path d="M9 9v3a3 3 0 0 0 5.12 2.12M15 9.34V4a3 3 0 0 0-5.94-.6"></path><path d="M17 16.95A7 7 0 0 1 5 12v-2m14 0v2a7 7 0 0 1-.11 1.23"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg>`
      : `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>`;
  }

  async toggleReelLike(reelId) {
    if (!this.currentUser) {
      this.openAuthModal('login');
      return;
    }
    try {
      const res = await window.api.toggleReelLike(reelId);
      const reelCard = document.getElementById(`reel-${reelId}`);
      const btn = reelCard.querySelector('.reel-action-btn:nth-child(1)');
      const count = document.getElementById(`reel-likes-${reelId}`);

      if (res.is_liked) btn.classList.add('liked');
      else btn.classList.remove('liked');
      count.innerText = res.likes_count;
    } catch (e) {
      this.showToast(e.message, 'error');
    }
  }

  openCreateReelModal() {
    if (!this.currentUser) {
      this.openAuthModal('login');
      return;
    }
    this.openModal('create-reel-modal');
  }

  async submitNewReel(e) {
    e.preventDefault();
    const title = document.getElementById('reel-title-input').value.trim();
    const videoUrl = document.getElementById('reel-video-input').value.trim();
    const thumbUrl = document.getElementById('reel-thumb-input').value.trim();
    const song = document.getElementById('reel-song-input').value.trim();
    const desc = document.getElementById('reel-desc-input').value.trim();

    try {
      await window.api.createReel({
        title, video_url: videoUrl, thumbnail_url: thumbUrl, song_title: song, description: desc
      });
      this.closeModal('create-reel-modal');
      this.showToast('Reel published!', 'success');
      this.renderReelsView();
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  }

  // ============================================================================
  // VIEW: DIRECT MESSAGING
  // ============================================================================

  async renderMessagesView() {
    if (!this.currentUser) {
      this.openAuthModal('login');
      return;
    }

    const container = document.getElementById('view-content');
    container.innerHTML = `
      <div class="messages-layout">
        <!-- Threads List -->
        <div class="messages-threads-list" id="chat-threads-list">
          <div style="padding: 20px; color: var(--text-muted);">Loading conversations...</div>
        </div>

        <!-- Active Chat Window -->
        <div class="active-chat-view" id="active-chat-window">
          <div style="flex-grow: 1; display: flex; align-items: center; justify-content: center; color: var(--text-muted); flex-direction: column; gap: 8px;">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
            <div style="font-weight: 700;">Select a conversation to start chatting</div>
          </div>
        </div>
      </div>
    `;

    try {
      const convos = await window.api.getConversations();
      const listEl = document.getElementById('chat-threads-list');

      if (!convos || convos.length === 0) {
        listEl.innerHTML = `<div style="padding: 24px; color: var(--text-muted); text-align: center;">No active messages yet. Visit a user's profile to start a chat!</div>`;
        return;
      }

      listEl.innerHTML = convos.map(c => `
        <div class="thread-item ${this.activeConversationId === c.id ? 'active' : ''}" onclick="window.app.selectConversation(${c.id}, '${c.other_participant.username}', '${c.other_participant.display_name}', '${c.other_participant.avatar_url}')">
          <img class="thread-avatar" src="${c.other_participant.avatar_url}" alt="${c.other_participant.username}">
          <div class="thread-meta">
            <div class="thread-name">${c.other_participant.display_name || c.other_participant.username}</div>
            <div class="thread-preview">${c.last_message ? c.last_message.content : 'No messages yet'}</div>
          </div>
          ${c.unread_count > 0 ? `<span class="badge">${c.unread_count}</span>` : ''}
        </div>
      `).join('');

      // Auto open first conversation if available
      if (convos.length > 0 && !this.activeConversationId) {
        const first = convos[0];
        this.selectConversation(first.id, first.other_participant.username, first.other_participant.display_name, first.other_participant.avatar_url);
      }
    } catch (e) {
      document.getElementById('chat-threads-list').innerHTML = `<div style="padding: 20px; color: var(--accent-rose);">${e.message}</div>`;
    }
  }

  async selectConversation(convoId, otherUsername, otherDisplayName, otherAvatar) {
    this.activeConversationId = convoId;
    const chatWin = document.getElementById('active-chat-window');
    if (!chatWin) return;

    chatWin.innerHTML = `
      <div class="chat-header">
        <img src="${otherAvatar}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover;">
        <div>
          <div style="font-weight: 700; font-size: 0.95rem;">${otherDisplayName || otherUsername}</div>
          <a href="#profile/${otherUsername}" style="font-size: 0.8rem; color: var(--primary);">@${otherUsername}</a>
        </div>
      </div>
      <div class="chat-messages-container" id="chat-stream">
        <div style="text-align: center; color: var(--text-muted);">Loading message history...</div>
      </div>
      <form class="chat-input-bar" onsubmit="window.app.sendChatMessage(event, ${convoId})">
        <input type="text" id="chat-msg-input" class="comment-input" placeholder="Type a message..." required autocomplete="off">
        <button type="submit" class="btn-primary" style="padding: 8px 18px;">Send</button>
      </form>
    `;

    try {
      const messages = await window.api.getMessages(convoId);
      const stream = document.getElementById('chat-stream');
      stream.innerHTML = messages.map(m => `
        <div class="message-bubble ${m.is_mine ? 'outgoing' : 'incoming'}">
          ${Components.formatContent(m.content)}
          <div style="font-size: 0.72rem; opacity: 0.75; text-align: right; margin-top: 3px;">
            ${new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        </div>
      `).join('');
      stream.scrollTop = stream.scrollHeight;
    } catch (e) {
      document.getElementById('chat-stream').innerHTML = `<div style="color: var(--accent-rose);">${e.message}</div>`;
    }
  }

  async sendChatMessage(e, convoId) {
    e.preventDefault();
    const input = document.getElementById('chat-msg-input');
    const content = input.value.trim();
    if (!content) return;

    try {
      const newMsg = await window.api.sendMessage(convoId, content);
      input.value = '';
      const stream = document.getElementById('chat-stream');
      if (stream) {
        stream.insertAdjacentHTML('beforeend', `
          <div class="message-bubble outgoing">
            ${Components.formatContent(newMsg.content)}
            <div style="font-size: 0.72rem; opacity: 0.75; text-align: right; margin-top: 3px;">just now</div>
          </div>
        `);
        stream.scrollTop = stream.scrollHeight;
      }
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  }

  // ============================================================================
  // VIEW: NOTIFICATIONS
  // ============================================================================

  async renderNotificationsView() {
    if (!this.currentUser) {
      this.openAuthModal('login');
      return;
    }

    const container = document.getElementById('view-content');
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; background: var(--bg-surface); border-bottom: 1px solid var(--border-subtle);">
        <div style="font-weight: 700; font-size: 1rem;">Activity & Alerts</div>
        <button class="action-icon-btn" onclick="window.app.markAllNotificationsRead()">Mark all as read</button>
      </div>

      <!-- Pending Follow Requests Section -->
      <div id="follow-requests-tray"></div>

      <div id="notifications-stream">
        <div style="padding: 24px; color: var(--text-muted); text-align: center;">Loading notifications...</div>
      </div>
    `;

    // Load Pending Follow Requests
    this.loadPendingFollowRequests();

    try {
      const notifs = await window.api.getNotifications();
      const stream = document.getElementById('notifications-stream');

      if (!notifs || notifs.length === 0) {
        stream.innerHTML = `
          <div style="padding: 40px; text-align: center; color: var(--text-muted);">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin-bottom: 8px;"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"></path></svg>
            <div style="font-weight: 700;">No notifications yet</div>
          </div>
        `;
        return;
      }

      stream.innerHTML = notifs.map(n => `
        <div class="post-card" style="display: flex; align-items: center; justify-content: space-between; gap: 14px; padding: 16px 20px; ${!n.is_read ? 'background: var(--primary-light);' : ''}">
          <div style="display: flex; align-items: center; gap: 12px;">
            <img src="${n.sender.avatar_url}" style="width: 44px; height: 44px; border-radius: 50%; object-fit: cover;">
            <div>
              <div style="font-size: 0.94rem;">
                <strong>@${n.sender.username}</strong> ${n.text || n.notification_type}
              </div>
              <div style="font-size: 0.78rem; color: var(--text-light);">${Components.timeAgo(n.created_at)}</div>
            </div>
          </div>
          <div>
            ${n.post ? `<a href="#feed" class="action-icon-btn" style="padding: 5px 12px; font-size: 0.8rem;">View</a>` : ''}
          </div>
        </div>
      `).join('');
    } catch (e) {
      document.getElementById('notifications-stream').innerHTML = `<div style="padding: 20px; color: var(--accent-rose);">${e.message}</div>`;
    }
  }

  async loadPendingFollowRequests() {
    try {
      const reqs = await window.api.getFollowRequests();
      const tray = document.getElementById('follow-requests-tray');
      if (!tray || !reqs || reqs.length === 0) return;

      tray.innerHTML = `
        <div style="padding: 14px 20px; background: var(--bg-surface-alt); border-bottom: 1px solid var(--border-subtle);">
          <div style="font-weight: 700; font-size: 0.9rem; margin-bottom: 10px;">Follow Requests (${reqs.length})</div>
          ${reqs.map(r => `
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
              <div style="display: flex; align-items: center; gap: 10px;">
                <img src="${r.user.avatar_url}" style="width: 36px; height: 36px; border-radius: 50%;">
                <div>
                  <div style="font-weight: 700; font-size: 0.9rem;">@${r.user.username}</div>
                  <div style="font-size: 0.78rem; color: var(--text-muted);">${r.user.display_name}</div>
                </div>
              </div>
              <div style="display: flex; gap: 6px;">
                <button class="btn-primary" style="padding: 4px 12px; font-size: 0.8rem;" onclick="window.app.handleFollowRequest(${r.id}, 'accept')">Accept</button>
                <button class="action-icon-btn" style="padding: 4px 12px; font-size: 0.8rem;" onclick="window.app.handleFollowRequest(${r.id}, 'reject')">Reject</button>
              </div>
            </div>
          `).join('')}
        </div>
      `;
    } catch (e) {}
  }

  async handleFollowRequest(id, action) {
    try {
      const res = await window.api.handleFollowRequest(id, action);
      this.showToast(res.message, 'info');
      this.renderNotificationsView();
    } catch (e) {
      this.showToast(e.message, 'error');
    }
  }

  async markAllNotificationsRead() {
    try {
      await window.api.markNotificationsRead();
      this.showToast('All notifications marked as read', 'info');
      document.getElementById('notif-badge').style.display = 'none';
      this.renderNotificationsView();
    } catch (e) {
      this.showToast(e.message, 'error');
    }
  }

  // ============================================================================
  // VIEW: BOOKMARKS & COLLECTIONS
  // ============================================================================

  async renderBookmarksView() {
    if (!this.currentUser) {
      this.openAuthModal('login');
      return;
    }

    const container = document.getElementById('view-content');
    container.innerHTML = `
      <div style="padding: 16px 20px; background: var(--bg-surface); border-bottom: 1px solid var(--border-subtle); display: flex; align-items: center; justify-content: space-between;">
        <div style="font-weight: 700; font-size: 1rem;">Saved Posts & Collections</div>
        <button class="btn-primary" style="padding: 6px 14px; font-size: 0.84rem;" onclick="window.app.promptNewCollection()">+ New Collection</button>
      </div>

      <div class="category-filter-bar" id="collections-tabs">
        <button class="category-chip active" onclick="window.app.loadBookmarksByCollection(null)">All Saved</button>
      </div>

      <div id="bookmarks-stream">
        <div style="padding: 24px; color: var(--text-muted); text-align: center;">Loading saved items...</div>
      </div>
    `;

    // Load user collections
    try {
      const cols = await window.api.getCollections();
      const tabs = document.getElementById('collections-tabs');
      cols.forEach(c => {
        tabs.insertAdjacentHTML('beforeend', `
          <button class="category-chip" onclick="window.app.loadBookmarksByCollection(${c.id})">${c.name} (${c.bookmarks_count})</button>
        `);
      });
    } catch (e) {}

    this.loadBookmarksByCollection(null);
  }

  async loadBookmarksByCollection(colId) {
    const stream = document.getElementById('bookmarks-stream');
    if (!stream) return;

    try {
      const bookmarks = await window.api.getBookmarks(colId);
      if (!bookmarks || bookmarks.length === 0) {
        stream.innerHTML = `
          <div style="padding: 40px; text-align: center; color: var(--text-muted);">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"></path></svg>
            <div style="font-weight: 700; margin-top: 8px;">No saved posts in this collection</div>
          </div>
        `;
        return;
      }

      stream.innerHTML = bookmarks.map(b => Components.renderPostCard(b.post, this.currentUser)).join('');
    } catch (e) {
      stream.innerHTML = `<div style="padding: 20px; color: var(--accent-rose);">${e.message}</div>`;
    }
  }

  async promptNewCollection() {
    const name = prompt('Enter a name for the new collection:');
    if (name && name.trim()) {
      try {
        await window.api.createCollection(name.trim());
        this.showToast(`Collection "${name}" created.`, 'success');
        this.renderBookmarksView();
      } catch (e) {
        this.showToast(e.message, 'error');
      }
    }
  }

  // ============================================================================
  // VIEW: ACTIVITY DASHBOARD
  // ============================================================================

  async renderDashboardView() {
    if (!this.currentUser) {
      this.openAuthModal('login');
      return;
    }

    const container = document.getElementById('view-content');
    container.innerHTML = `
      <div class="dashboard-container">
        <!-- Overview Grid -->
        <div class="metrics-grid" id="dashboard-metrics">
          <div class="metric-card"><div class="metric-card-header">Loading analytics...</div></div>
        </div>

        <!-- Weekly Activity Chart Card -->
        <div class="chart-card">
          <div style="font-weight: 700; font-size: 1.1rem; margin-bottom: 16px;">Engagement & Activity (Last 7 Days)</div>
          <div style="height: 260px; position: relative;">
            <canvas id="activity-chart-canvas"></canvas>
          </div>
        </div>
      </div>
    `;

    try {
      const res = await window.api.getDashboardStats();
      const stats = res.stats;
      const chartData = res.chart_data;

      // Render Metrics Cards
      document.getElementById('dashboard-metrics').innerHTML = `
        <div class="metric-card">
          <div class="metric-card-header">
            <span>Total Followers</span>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle></svg>
          </div>
          <div class="metric-card-value">${stats.total_followers}</div>
        </div>

        <div class="metric-card">
          <div class="metric-card-header">
            <span>Likes Received</span>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--accent-rose);"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>
          </div>
          <div class="metric-card-value">${stats.total_likes_received}</div>
        </div>

        <div class="metric-card">
          <div class="metric-card-header">
            <span>Profile Impressions</span>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
          </div>
          <div class="metric-card-value">${stats.profile_views}</div>
        </div>

        <div class="metric-card">
          <div class="metric-card-header">
            <span>Engagement Rate</span>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--accent-emerald);"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline></svg>
          </div>
          <div class="metric-card-value" style="color: var(--accent-emerald);">${stats.engagement_rate}</div>
        </div>
      `;

      // Render Chart.js
      const canvas = document.getElementById('activity-chart-canvas');
      if (canvas && window.Chart) {
        if (this.dashboardChart) this.dashboardChart.destroy();
        const ctx = canvas.getContext('2d');
        const isDark = this.theme === 'dark';

        this.dashboardChart = new window.Chart(ctx, {
          type: 'bar',
          data: {
            labels: chartData.labels,
            datasets: [
              {
                label: 'Likes Received',
                data: chartData.likes,
                backgroundColor: 'rgba(99, 102, 241, 0.85)',
                borderRadius: 8,
              },
              {
                label: 'Posts Published',
                data: chartData.posts,
                backgroundColor: 'rgba(236, 72, 153, 0.85)',
                borderRadius: 8,
              }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                labels: {
                  color: isDark ? '#f8fafc' : '#0f172a'
                }
              }
            },
            scales: {
              x: {
                grid: { display: false },
                ticks: { color: isDark ? '#94a3b8' : '#64748b' }
              },
              y: {
                beginAtZero: true,
                grid: { color: isDark ? '#1f2937' : '#e2e8f0' },
                ticks: { color: isDark ? '#94a3b8' : '#64748b' }
              }
            }
          }
        });
      }
    } catch (e) {
      document.getElementById('dashboard-metrics').innerHTML = `<div style="color: var(--accent-rose);">${e.message}</div>`;
    }
  }

  // ============================================================================
  // VIEW: USER PROFILE
  // ============================================================================

  async renderProfileView(username) {
    const container = document.getElementById('view-content');
    container.innerHTML = `
      <div style="padding: 24px; text-align: center; color: var(--text-muted);">
        ${Components.renderSkeletonCard()}
      </div>
    `;

    try {
      const user = await window.api.getProfile(username);
      const profile = user.profile;
      const isOwner = this.currentUser && this.currentUser.username === user.username;
      const isFollowing = user.is_following;
      const hasPending = user.has_pending_request;

      container.innerHTML = `
        <!-- Profile Banner -->
        <div style="height: 180px; background: ${profile.cover_image ? `url('${profile.cover_image}') center/cover` : 'var(--gradient-brand)'}; position: relative;"></div>

        <!-- Profile Header Area -->
        <div style="padding: 0 24px 20px 24px; background: var(--bg-surface); border-bottom: 1px solid var(--border-subtle); position: relative;">
          <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-top: -55px; margin-bottom: 16px;">
            <img src="${profile.avatar_url}" style="width: 105px; height: 105px; border-radius: 50%; object-fit: cover; border: 4px solid var(--bg-surface); box-shadow: var(--shadow-md);">
            
            <div style="display: flex; gap: 8px;">
              ${isOwner ? `
                <button class="action-icon-btn" onclick="window.location.hash = '#settings'" style="padding: 8px 18px; font-weight: 700;">Edit Profile</button>
              ` : `
                <button class="btn-primary" style="padding: 8px 20px;" onclick="window.app.toggleProfileFollow('${user.username}')">
                  ${isFollowing ? 'Following' : (hasPending ? 'Requested' : 'Follow')}
                </button>
                <button class="action-icon-btn" onclick="window.app.startDirectMessage('${user.username}')" title="Message">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
                </button>
                <button class="action-icon-btn" onclick="window.app.toggleBlockUser('${user.username}')" title="Block/Unblock">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"></line></svg>
                </button>
              `}
            </div>
          </div>

          <div>
            <div style="display: flex; align-items: center; gap: 6px;">
              <h2 style="font-size: 1.35rem; font-weight: 800;">${profile.display_name || user.username}</h2>
              ${profile.is_verified ? Components.renderVerifiedBadge() : ''}
              ${profile.is_private ? `<span style="font-size: 0.75rem; background: var(--bg-surface-alt); padding: 2px 8px; border-radius: 12px; color: var(--text-muted);">🔒 Private</span>` : ''}
            </div>
            <div style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 10px;">@${user.username}</div>
            
            <p style="font-size: 0.95rem; line-height: 1.5; margin-bottom: 14px;">${profile.bio || 'No bio provided yet.'}</p>

            <div style="display: flex; flex-wrap: wrap; gap: 16px; font-size: 0.85rem; color: var(--text-muted); margin-bottom: 14px;">
              ${profile.location ? `<span>📍 ${profile.location}</span>` : ''}
              ${profile.website ? `<span>🔗 <a href="${profile.website}" target="_blank" style="color: var(--primary);">${profile.website}</a></span>` : ''}
              <span>👁️ ${profile.profile_views} profile views</span>
            </div>

            <!-- Interests Chips -->
            ${profile.interests ? `
              <div style="display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 16px;">
                ${profile.interests.split(',').map(i => `<span class="category-pill" style="font-size: 0.8rem;">${i.trim()}</span>`).join('')}
              </div>
            ` : ''}

            <!-- Stats Counts -->
            <div style="display: flex; gap: 24px; font-size: 0.95rem;">
              <span><strong>${user.posts_count}</strong> Posts</span>
              <span style="cursor: pointer;"><strong>${user.followers_count}</strong> Followers</span>
              <span style="cursor: pointer;"><strong>${user.following_count}</strong> Following</span>
            </div>
          </div>
        </div>

        <!-- Posts or Restricted State -->
        <div id="profile-posts-stream">
          ${user.is_restricted ? `
            <div style="padding: 40px; text-align: center; color: var(--text-muted);">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin-bottom: 8px;"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
              <div style="font-weight: 700; font-size: 1.1rem;">This account is private</div>
              <p style="font-size: 0.9rem;">Follow this account to see their posts and photos.</p>
            </div>
          ` : (user.posts && user.posts.length > 0) ? user.posts.map(p => Components.renderPostCard(p, this.currentUser)).join('') : `
            <div style="padding: 40px; text-align: center; color: var(--text-muted);">
              <div style="font-weight: 700;">No posts shared yet</div>
            </div>
          `}
        </div>
      `;
    } catch (e) {
      container.innerHTML = `<div style="padding: 24px; color: var(--accent-rose);">${e.message}</div>`;
    }
  }

  async toggleProfileFollow(username) {
    if (!this.currentUser) {
      this.openAuthModal('login');
      return;
    }
    try {
      const res = await window.api.toggleFollow(username);
      this.showToast(res.message, 'info');
      this.renderProfileView(username);
    } catch (e) {
      this.showToast(e.message, 'error');
    }
  }

  async startDirectMessage(username) {
    if (!this.currentUser) {
      this.openAuthModal('login');
      return;
    }
    try {
      const convo = await window.api.startConversation(username);
      window.location.hash = '#messages';
      this.activeConversationId = convo.id;
    } catch (e) {
      this.showToast(e.message, 'error');
    }
  }

  async toggleBlockUser(username) {
    if (!confirm(`Are you sure you want to block/unblock @${username}?`)) return;
    try {
      const res = await window.api.toggleBlock(username);
      this.showToast(res.message, 'info');
      this.renderProfileView(username);
    } catch (e) {
      this.showToast(e.message, 'error');
    }
  }

  // ============================================================================
  // VIEW: SETTINGS & PRIVACY
  // ============================================================================

  async renderSettingsView() {
    if (!this.currentUser) {
      this.openAuthModal('login');
      return;
    }

    const container = document.getElementById('view-content');
    const p = this.currentUser.profile;

    container.innerHTML = `
      <div style="padding: 24px; max-width: 620px;">
        <h2 style="font-size: 1.35rem; font-weight: 800; margin-bottom: 20px;">Edit Profile & Privacy Settings</h2>

        <form onsubmit="window.app.saveProfileSettings(event)" style="display: flex; flex-direction: column; gap: 16px;">
          <div>
            <label style="display: block; font-size: 0.88rem; font-weight: 700; margin-bottom: 6px;">Display Name</label>
            <input type="text" id="setting-display-name" class="poll-option-input" value="${p.display_name || ''}">
          </div>

          <div>
            <label style="display: block; font-size: 0.88rem; font-weight: 700; margin-bottom: 6px;">Bio</label>
            <textarea id="setting-bio" class="poll-option-input" style="height: 80px; resize: vertical;">${p.bio || ''}</textarea>
          </div>

          <div>
            <label style="display: block; font-size: 0.88rem; font-weight: 700; margin-bottom: 6px;">Avatar Image URL</label>
            <input type="url" id="setting-avatar-url" class="poll-option-input" value="${p.avatar_url || ''}">
          </div>

          <div>
            <label style="display: block; font-size: 0.88rem; font-weight: 700; margin-bottom: 6px;">Cover Photo URL</label>
            <input type="url" id="setting-cover-url" class="poll-option-input" value="${p.cover_image || ''}">
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
            <div>
              <label style="display: block; font-size: 0.88rem; font-weight: 700; margin-bottom: 6px;">Location</label>
              <input type="text" id="setting-location" class="poll-option-input" value="${p.location || ''}">
            </div>
            <div>
              <label style="display: block; font-size: 0.88rem; font-weight: 700; margin-bottom: 6px;">Website</label>
              <input type="url" id="setting-website" class="poll-option-input" value="${p.website || ''}">
            </div>
          </div>

          <div>
            <label style="display: block; font-size: 0.88rem; font-weight: 700; margin-bottom: 6px;">Interests (comma separated)</label>
            <input type="text" id="setting-interests" class="poll-option-input" value="${p.interests || ''}" placeholder="Technology, Education, Design">
          </div>

          <!-- Privacy Toggle -->
          <div style="padding: 16px; background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); display: flex; align-items: center; justify-content: space-between;">
            <div>
              <div style="font-weight: 700; font-size: 0.95rem;">Private Account</div>
              <div style="font-size: 0.82rem; color: var(--text-muted);">When your account is private, only people you approve can see your posts.</div>
            </div>
            <input type="checkbox" id="setting-private-toggle" ${p.is_private ? 'checked' : ''} style="width: 20px; height: 20px; accent-color: var(--primary); cursor: pointer;">
          </div>

          <button type="submit" class="btn-primary" style="padding: 14px; font-size: 1rem; margin-top: 10px;">Save Profile Changes</button>
        </form>
      </div>
    `;
  }

  async saveProfileSettings(e) {
    e.preventDefault();
    const displayName = document.getElementById('setting-display-name').value.trim();
    const bio = document.getElementById('setting-bio').value.trim();
    const avatarUrl = document.getElementById('setting-avatar-url').value.trim();
    const coverUrl = document.getElementById('setting-cover-url').value.trim();
    const location = document.getElementById('setting-location').value.trim();
    const website = document.getElementById('setting-website').value.trim();
    const interests = document.getElementById('setting-interests').value.trim();
    const isPrivate = document.getElementById('setting-private-toggle').checked;

    try {
      const res = await window.api.updateProfile({
        display_name: displayName,
        bio: bio,
        avatar_url: avatarUrl,
        cover_image: coverUrl,
        location: location,
        website: website,
        interests: interests,
        is_private: isPrivate
      });
      this.currentUser = res.user;
      this.updateUserUI(res.user);
      this.showToast('Profile updated successfully!', 'success');
      window.location.hash = `#profile/${this.currentUser.username}`;
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  }

  // ============================================================================
  // STORIES VIEWER & CREATOR
  // ============================================================================

  openCreateStoryModal() {
    if (!this.currentUser) {
      this.openAuthModal('login');
      return;
    }
    this.openModal('create-story-modal');
  }

  async submitNewStory(e) {
    e.preventDefault();
    const text = document.getElementById('story-text-input').value.trim();
    const imgUrl = document.getElementById('story-image-input').value.trim();
    const grad = document.getElementById('story-gradient-input').value;

    const fd = new FormData();
    fd.append('text_content', text);
    if (imgUrl) fd.append('media_url', imgUrl);
    fd.append('background_gradient', grad);

    try {
      await window.api.createStory(fd);
      this.closeModal('create-story-modal');
      this.showToast('Story published for 24 hours!', 'success');
      this.loadStoriesTray();
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  }

  openStoryViewer(storyId) {
    const idx = this.activeStories.findIndex(s => s.id === storyId);
    if (idx === -1) return;
    this.currentStoryIndex = idx;
    this.showStorySlide();
    this.openModal('story-viewer-modal');
  }

  showStorySlide() {
    const story = this.activeStories[this.currentStoryIndex];
    if (!story) {
      this.closeStoryViewer();
      return;
    }

    const card = document.getElementById('story-viewer-card');
    const content = document.getElementById('story-viewer-content');
    const avatar = document.getElementById('story-viewer-avatar');
    const user = document.getElementById('story-viewer-user');
    const time = document.getElementById('story-viewer-time');
    const prog = document.getElementById('story-viewer-progress');

    avatar.src = story.user.avatar_url;
    user.innerText = `@${story.user.username}`;
    time.innerText = Components.timeAgo(story.created_at);

    if (story.media_display_url) {
      content.style.backgroundImage = `url('${story.media_display_url}')`;
      content.innerHTML = `<div style="background: rgba(0,0,0,0.45); padding: 12px 18px; border-radius: 12px; backdrop-filter: blur(4px);">${story.text_content}</div>`;
    } else {
      content.style.backgroundImage = 'none';
      content.style.background = story.background_gradient || 'var(--gradient-brand)';
      content.innerHTML = `<div>${story.text_content}</div>`;
    }

    // Progress bar animation
    if (this.storyViewerTimer) clearInterval(this.storyViewerTimer);
    let pct = 0;
    prog.style.width = '0%';

    this.storyViewerTimer = setInterval(() => {
      pct += 2;
      prog.style.width = `${pct}%`;
      if (pct >= 100) {
        clearInterval(this.storyViewerTimer);
        this.currentStoryIndex++;
        if (this.currentStoryIndex < this.activeStories.length) {
          this.showStorySlide();
        } else {
          this.closeStoryViewer();
        }
      }
    }, 100);
  }

  closeStoryViewer() {
    if (this.storyViewerTimer) clearInterval(this.storyViewerTimer);
    this.closeModal('story-viewer-modal');
  }

  // ============================================================================
  // AI CAPTION ASSISTANT
  // ============================================================================

  openAiModal() {
    this.openModal('ai-modal');
  }

  closeAiModal() {
    this.closeModal('ai-modal');
  }

  selectAiTone(btn) {
    document.querySelectorAll('.tone-chip').forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    this.selectedAiTone = btn.getAttribute('data-tone');
  }

  async generateAiCaptions() {
    const prompt = document.getElementById('ai-prompt-input').value.trim();
    if (!prompt) {
      this.showToast('Please type a topic or key message.', 'error');
      return;
    }

    const container = document.getElementById('ai-results-container');
    container.innerHTML = `<div style="padding: 16px; text-align: center; color: var(--text-muted);">Thinking & generating creative options...</div>`;

    try {
      const res = await window.api.generateCaption(prompt, this.selectedAiTone, 'General');
      
      let html = `<div style="font-size: 0.82rem; color: var(--primary); font-weight: 700; margin-bottom: 10px;">${res.engine}</div>`;
      
      if (res.captions && res.captions.length > 0) {
        res.captions.forEach((cap, i) => {
          html += `
            <div class="ai-suggestion-card">
              <div class="ai-suggestion-text">${cap}</div>
              <div style="display: flex; justify-content: flex-end;">
                <button class="ai-use-btn" onclick="window.app.applyAiCaption(\`${encodeURIComponent(cap)}\`)">Use this Caption</button>
              </div>
            </div>
          `;
        });
      }

      container.innerHTML = html;
    } catch (e) {
      container.innerHTML = `<div style="color: var(--accent-rose);">${e.message}</div>`;
    }
  }

  applyAiCaption(encodedText) {
    const text = decodeURIComponent(encodedText);
    const composer = document.getElementById('composer-content');
    if (composer) {
      composer.value = text;
      composer.focus();
    }
    this.closeAiModal();
    this.showToast('Caption inserted into composer!', 'success');
  }

  // ============================================================================
  // RIGHT WIDGETS: TRENDING & CREATORS
  // ============================================================================

  async loadTrendingTags() {
    const container = document.getElementById('trending-tags-container');
    if (!container) return;

    try {
      const tags = await window.api.getTrendingHashtags();
      if (!tags || tags.length === 0) {
        container.innerHTML = `<div style="font-size: 0.85rem; color: var(--text-muted);">No tags trending yet.</div>`;
        return;
      }

      container.innerHTML = tags.map(t => `
        <div class="trending-item" onclick="window.location.hash = '#explore?tag=${t.name}'">
          <span class="trending-tag">#${t.name}</span>
          <span class="trending-count">${t.usage_count} post${t.usage_count === 1 ? '' : 's'}</span>
        </div>
      `).join('');
    } catch (e) {
      container.innerHTML = `<div style="font-size: 0.85rem; color: var(--text-muted);">Trending tags unavailable.</div>`;
    }
  }

  async loadSuggestedCreators() {
    const container = document.getElementById('suggested-users-container');
    if (!container) return;

    try {
      const res = await window.api.getExplore('All');
      const data = res.results || res;
      const creators = data.suggested_users || [];

      if (creators.length === 0) {
        container.innerHTML = `<div style="font-size: 0.85rem; color: var(--text-muted);">No suggestions right now.</div>`;
        return;
      }

      container.innerHTML = creators.map(c => `
        <div style="display: flex; align-items: center; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid var(--border-subtle);">
          <div style="display: flex; align-items: center; gap: 8px; cursor: pointer;" onclick="window.location.hash = '#profile/${c.username}'">
            <img src="${c.avatar_url}" style="width: 34px; height: 34px; border-radius: 50%; object-fit: cover;">
            <div>
              <div style="font-weight: 700; font-size: 0.88rem;">@${c.username}</div>
              <div style="font-size: 0.76rem; color: var(--text-muted);">${c.display_name || ''}</div>
            </div>
          </div>
          <button class="btn-primary" style="padding: 4px 12px; font-size: 0.8rem;" onclick="window.app.toggleProfileFollow('${c.username}')">Follow</button>
        </div>
      `).join('');
    } catch (e) {}
  }

  // ============================================================================
  // REPORTING & MODAL HELPERS
  // ============================================================================

  openReportModal(userId = null, postId = null) {
    if (!this.currentUser) {
      this.openAuthModal('login');
      return;
    }
    document.getElementById('report-user-id').value = userId || '';
    document.getElementById('report-post-id').value = postId || '';
    this.openModal('report-modal');
  }

  async submitReport(e) {
    e.preventDefault();
    const reason = document.getElementById('report-reason-select').value;
    const details = document.getElementById('report-details').value.trim();
    const userId = document.getElementById('report-user-id').value || null;
    const postId = document.getElementById('report-post-id').value || null;

    const fullReason = details ? `${reason}: ${details}` : reason;

    try {
      const res = await window.api.submitReport(fullReason, userId, postId);
      this.closeModal('report-modal');
      this.showToast(res.message, 'success');
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  }

  openModal(modalId) {
    const el = document.getElementById(modalId);
    if (el) el.classList.add('open');
  }

  closeModal(modalId) {
    const el = document.getElementById(modalId);
    if (el) el.classList.remove('open');
  }

  showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
      <span>${type === 'success' ? '✓' : (type === 'error' ? '✕' : 'ℹ')}</span>
      <span>${message}</span>
    `;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }
}

// Global initialization
window.addEventListener('DOMContentLoaded', () => {
  window.app = new CodeGramApp();
  window.app.init();
});
