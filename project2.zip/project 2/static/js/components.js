/**
 * CodeGram Component Generators
 */

const Components = {
  timeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);

    if (seconds < 60) return 'just now';
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    if (days < 30) return `${days}d ago`;
    return date.toLocaleDateString();
  },

  formatContent(text) {
    if (!text) return '';
    // Escape HTML first
    const div = document.createElement('div');
    div.innerText = text;
    let safe = div.innerHTML;

    // Convert hashtags to links
    safe = safe.replace(/#(\w+)/g, '<a href="#explore?tag=$1" class="hashtag-link" style="color: var(--primary); font-weight: 600;">#$1</a>');
    // Convert mentions
    safe = safe.replace(/@(\w+)/g, '<a href="#profile/$1" class="mention-link" style="color: var(--accent-purple); font-weight: 600;">@$1</a>');
    return safe;
  },

  renderVerifiedBadge() {
    return `
      <svg class="verified-badge" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
      </svg>
    `;
  },

  renderPostCard(post, currentUser) {
    const isOwner = currentUser && (currentUser.id === post.author.id);
    const isLiked = post.is_liked;
    const isBookmarked = post.is_bookmarked;
    const author = post.author;

    // Poll HTML
    let pollHtml = '';
    if (post.poll) {
      const poll = post.poll;
      const userVotedId = poll.user_voted_option_id;
      const hasVoted = !!userVotedId;

      pollHtml = `
        <div class="poll-widget" data-poll-id="${poll.id}">
          <div class="poll-question">📊 ${poll.question}</div>
          <div class="poll-options-list">
            ${poll.options.map(opt => {
              const isSelected = userVotedId === opt.id;
              return `
                <div class="poll-option-row ${isSelected ? 'voted' : ''}" 
                     data-option-id="${opt.id}" 
                     onclick="window.app.votePoll(${poll.id}, ${opt.id}, ${post.id})">
                  <div class="poll-fill-bar" style="width: ${hasVoted ? opt.percentage : 0}%"></div>
                  <div class="poll-option-content">
                    <span>${opt.text} ${isSelected ? '✓' : ''}</span>
                    ${hasVoted ? `<span>${opt.percentage}% (${opt.votes_count})</span>` : ''}
                  </div>
                </div>
              `;
            }).join('')}
          </div>
          <div class="poll-footer">
            <span>${poll.total_votes} total vote${poll.total_votes === 1 ? '' : 's'}</span>
            ${hasVoted ? ' • You voted' : ' • Tap an option to vote'}
          </div>
        </div>
      `;
    }

    // Comments preview
    const commentsList = (post.comments || []).map(c => `
      <div class="comment-item" id="comment-${c.id}">
        <img class="comment-avatar" src="${c.author.avatar_url}" alt="${c.author.username}">
        <div class="comment-bubble">
          <div class="comment-author-name">
            <a href="#profile/${c.author.username}">@${c.author.username}</a>
            ${c.author.is_verified ? Components.renderVerifiedBadge() : ''}
            <span style="font-weight: 400; color: var(--text-light); font-size: 0.78rem; margin-left: 6px;">
              ${Components.timeAgo(c.created_at)}
            </span>
          </div>
          <div>${Components.formatContent(c.content)}</div>
        </div>
      </div>
    `).join('');

    return `
      <article class="post-card" id="post-${post.id}">
        <div class="post-header">
          <div class="post-author-info" onclick="window.location.hash = '#profile/${author.username}'">
            <img class="author-avatar" src="${author.avatar_url}" alt="${author.username}">
            <div class="author-meta">
              <div class="author-name-row">
                <span class="author-name">${author.display_name || author.username}</span>
                ${author.is_verified ? Components.renderVerifiedBadge() : ''}
                <span class="author-username">@${author.username}</span>
              </div>
              <span class="post-timestamp">${Components.timeAgo(post.created_at)}</span>
            </div>
          </div>
          <div style="display: flex; align-items: center; gap: 8px;">
            ${post.is_recommended ? `<span class="category-pill" style="background: var(--primary-light); color: var(--primary); font-weight: 700;">Recommended</span>` : ''}
            <span class="category-pill">${post.category}</span>
            ${isOwner ? `
              <button class="action-icon-btn" style="padding: 4px 8px;" onclick="window.app.deletePost(${post.id})" title="Delete post">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
              </button>
            ` : `
              <button class="action-icon-btn" style="padding: 4px 8px;" onclick="window.app.openReportModal(null, ${post.id})" title="Report post">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
              </button>
            `}
          </div>
        </div>

        <div class="post-content">${Components.formatContent(post.content)}</div>

        ${post.image_display_url ? `
          <div class="post-media-frame">
            <img src="${post.image_display_url}" alt="Post attachment" loading="lazy" onclick="window.app.openImagePreview('${post.image_display_url}')">
          </div>
        ` : ''}

        ${pollHtml}

        <div class="post-actions">
          <button class="post-action-btn ${isLiked ? 'liked' : ''}" onclick="window.app.toggleLike(${post.id})">
            <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>
            <span class="likes-count">${post.likes_count}</span>
          </button>

          <button class="post-action-btn" onclick="window.app.toggleCommentBox(${post.id})">
            <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
            <span class="comments-count">${post.comments_count}</span>
          </button>

          <button class="post-action-btn ${isBookmarked ? 'bookmarked' : ''}" onclick="window.app.toggleBookmark(${post.id})">
            <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path></svg>
            <span>Save</span>
          </button>

          <button class="post-action-btn" onclick="window.app.sharePost(${post.id})">
            <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg>
            <span>Share</span>
          </button>
        </div>

        <div class="post-comments-section" id="comments-section-${post.id}">
          <div class="comments-list" id="comments-list-${post.id}">
            ${commentsList}
          </div>
          <form class="comment-input-row" onsubmit="window.app.submitComment(event, ${post.id})">
            <input type="text" class="comment-input" placeholder="Add a comment..." required>
            <button type="submit" class="btn-primary" style="padding: 6px 16px; font-size: 0.85rem;">Post</button>
          </form>
        </div>
      </article>
    `;
  },

  renderStoryBubble(story, isCurrentUser = false) {
    if (isCurrentUser && !story) {
      return `
        <div class="story-bubble" onclick="window.app.openCreateStoryModal()">
          <div class="story-avatar-ring add-story">
            <img src="${window.app.currentUser ? window.app.currentUser.profile.avatar_url : 'https://api.dicebear.com/7.x/avataaars/svg?seed=user'}" alt="Your Story">
            <div class="story-add-badge">+</div>
          </div>
          <span class="story-username">Your Story</span>
        </div>
      `;
    }

    return `
      <div class="story-bubble" onclick="window.app.openStoryViewer(${story.id})">
        <div class="story-avatar-ring">
          <img src="${story.user.avatar_url}" alt="${story.user.username}">
        </div>
        <span class="story-username">@${story.user.username}</span>
      </div>
    `;
  },

  renderReelCard(reel, currentUser) {
    const isLiked = reel.is_liked;
    return `
      <div class="reel-card" id="reel-${reel.id}">
        <video class="reel-video" loop playsinline src="${reel.video_url}" poster="${reel.thumbnail_url || ''}" onclick="window.app.toggleVideoPlay(this)"></video>
        
        <div class="reel-sidebar-actions">
          <div style="display:flex; flex-direction:column; align-items:center;">
            <button class="reel-action-btn ${isLiked ? 'liked' : ''}" onclick="window.app.toggleReelLike(${reel.id})">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>
            </button>
            <span class="reel-count-text" id="reel-likes-${reel.id}">${reel.likes_count}</span>
          </div>

          <div style="display:flex; flex-direction:column; align-items:center;">
            <button class="reel-action-btn" onclick="window.app.openReelComments(${reel.id})">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
            </button>
            <span class="reel-count-text">${reel.comments_count}</span>
          </div>

          <button class="reel-action-btn" onclick="window.app.toggleReelMute(this)">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>
          </button>
        </div>

        <div class="reel-overlay">
          <div class="reel-user-row" onclick="window.location.hash = '#profile/${reel.user.username}'" style="cursor: pointer;">
            <img class="reel-user-avatar" src="${reel.user.avatar_url}" alt="${reel.user.username}">
            <span style="font-weight: 700; font-size: 1rem;">@${reel.user.username}</span>
            ${reel.user.is_verified ? Components.renderVerifiedBadge() : ''}
          </div>
          <div style="font-weight: 700; font-size: 1.05rem; margin-bottom: 4px;">${reel.title}</div>
          <div style="font-size: 0.92rem; opacity: 0.9; margin-bottom: 8px;">${reel.description}</div>
          <div style="font-size: 0.8rem; opacity: 0.8; display: flex; align-items: center; gap: 6px;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg>
            ${reel.song_title}
          </div>
        </div>
      </div>
    `;
  },

  renderSkeletonCard() {
    return `
      <div class="post-card" style="opacity: 0.7;">
        <div class="post-header">
          <div class="post-author-info">
            <div style="width: 44px; height: 44px; border-radius: 50%; background: var(--border-subtle);"></div>
            <div style="display:flex; flex-direction:column; gap:6px;">
              <div style="width: 120px; height: 14px; background: var(--border-subtle); border-radius: 4px;"></div>
              <div style="width: 80px; height: 10px; background: var(--border-subtle); border-radius: 4px;"></div>
            </div>
          </div>
        </div>
        <div style="width: 100%; height: 60px; background: var(--border-subtle); border-radius: 8px; margin-bottom: 12px;"></div>
        <div style="width: 100%; height: 220px; background: var(--border-subtle); border-radius: 12px;"></div>
      </div>
    `;
  }
};

window.Components = Components;
