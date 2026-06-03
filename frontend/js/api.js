// ==================== API Configuration ====================
const API_BASE = 'http://localhost:8000';

// ==================== Token Management ====================
function getToken() {
  return localStorage.getItem('access_token');
}

function getRefreshToken() {
  return localStorage.getItem('refresh_token');
}

function setTokens(accessToken, refreshToken) {
  if (accessToken) {
    localStorage.setItem('access_token', accessToken);
  } else {
    localStorage.removeItem('access_token');
  }
  if (refreshToken) {
    localStorage.setItem('refresh_token', refreshToken);
  } else {
    localStorage.removeItem('refresh_token');
  }
}

function isLoggedIn() {
  return !!getToken();
}

function logout() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
}

function parseJwtSub(token) {
  try {
    var payload = token.split('.')[1];
    payload = payload.replace(/-/g, '+').replace(/_/g, '/');
    while (payload.length % 4) payload += '=';
    return JSON.parse(atob(payload)).sub;
  } catch (e) {
    return null;
  }
}

async function refreshAccessToken() {
  const refreshToken = getRefreshToken();
  if (!refreshToken) throw new Error('No refresh token');

  const token = getToken();
  let userId = parseJwtSub(token);
  if (!userId) {
    try { userId = JSON.parse(localStorage.getItem('user') || '{}').id; } catch (e) {}
  }
  if (!userId) throw new Error('缺少用户信息，请重新登录');

  const res = await fetch(API_BASE + '/api/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, refresh_token: refreshToken }),
  });
  const data = await res.json();

  if (data.code !== 20000) {
    throw new Error(data.message || '刷新失败');
  }

  const result = data.data;
  if (result && result.access_token) {
    localStorage.setItem('access_token', result.access_token);
    return result.access_token;
  }
  throw new Error('刷新失败');
}

// ==================== Cache-busted avatar helper ====================
function avatarUrl(url) {
  if (!url) return 'https://via.placeholder.com/100';
  const sep = url.includes('?') ? '&' : '?';
  return url + sep + 't=' + Date.now();
}

// ==================== HTTP Request Helper ====================
async function request(url, options = {}) {
  const isFormData = options.body instanceof FormData;

  let headers = { ...options.headers };

  // 非 FormData 请求才设置 JSON Content-Type
  // FormData 由浏览器自动设置 multipart/form-data
  if (!isFormData) {
    headers['Content-Type'] = 'application/json';
  }

  const token = getToken();
  if (token) {
    headers['Authorization'] = 'Bearer ' + token;
  }

  let res = await fetch(API_BASE + url, {
    ...options,
    headers,
  });

  let data = await res.json();

  // Token invalid (10103) — 直接登出，不刷新
  if (data.code === 10103) {
    logout();
    window.location.href = 'index.html';
    throw new Error('登录已失效，请重新登录');
  }

  // Auto-refresh: token expired (10102) or missing (401)
  const shouldRefresh = getRefreshToken() && (
    data.code === 10102 ||
    (!res.ok && res.status === 401)
  );

  if (shouldRefresh) {
    try {
      const newToken = await refreshAccessToken();
      headers['Authorization'] = 'Bearer ' + newToken;
      res = await fetch(API_BASE + url, { ...options, headers });
      data = await res.json();
    } catch (e) {
      logout();
      window.location.href = 'index.html';
      throw new Error('登录已过期，请重新登录');
    }
  }

  if (!res.ok || (data.code && data.code !== 20000 && data.code !== 0 && data.code !== 20100)) {
    const message = data.message || data.detail || '请求失败';
    const err = new Error(message);
    err.code = data.code;
    throw err;
  }

  return data.data !== undefined ? data.data : data;
}

// ==================== News APIs ====================
const NewsAPI = {
  getCategories(categoryId) {
    const params = categoryId ? '?category_id=' + categoryId : '';
    return request('/api/news/categories' + params);
  },
  getList(categoryId, page, pageSize) {
    page = page || 1;
    pageSize = pageSize || 12;
    const params = new URLSearchParams({ page: String(page), pagesize: String(pageSize) });
    params.set('categoryId', String(categoryId || 0));
    return request('/api/news/list?' + params.toString());
  },
  getDetail(newsId) {
    return request('/api/news/detail/' + newsId);
  },
  search(keyword, page, startDate, endDate, categoryId) {
    page = page || 1;
    let url = '/api/news/search?q=' + encodeURIComponent(keyword || '') + '&page=' + page;
    if (categoryId) url += '&categoryId=' + categoryId;
    if (startDate) url += '&startDate=' + startDate;
    if (endDate) url += '&endDate=' + endDate;
    return request(url);
  },
};

// ==================== User APIs ====================
const UserAPI = {
  register(data) {
    return request('/api/user/reg', { method: 'POST', body: JSON.stringify(data) });
  },
  login(data) {
    return request('/api/user/login', { method: 'POST', body: JSON.stringify(data) });
  },
  resetPwd(data) {
    return request('/api/user/resetpwd', { method: 'POST', body: JSON.stringify(data) });
  },
  getInfo() {
    return request('/api/user/info');
  },
  updateInfo(formData) {
    return request('/api/user/update', { method: 'PUT', body: formData });
  },
  updatePwd(data) {
    return request('/api/user/updatepwd', { method: 'PUT', body: JSON.stringify(data) });
  },
  deleteAccount(code) {
    return request('/api/user/delete', { method: 'DELETE', body: JSON.stringify({ code }) });
  },
  logout(refreshToken) {
    return request('/api/user/logout', { method: 'POST', body: JSON.stringify({ refresh_token: refreshToken }) });
  },
};

async function loadUserData() {
  try {
    const userData = await UserAPI.getInfo();
    localStorage.setItem('user', JSON.stringify(userData));
    return userData;
  } catch (e) {
    setTokens(null, null);
    return null;
  }
}

// ==================== Favorite APIs ====================
const FavAPI = {
  add(newsId) {
    return request('/api/user/news/fav/' + newsId, { method: 'POST' });
  },
  remove(newsIds) {
    return request('/api/user/news/fav/delete', { method: 'DELETE', body: JSON.stringify({ news_ids: newsIds }) });
  },
  check(newsId) {
    return request('/api/user/news/fav/check/' + newsId);
  },
  getAll(page, pageSize) {
    page = page || 1;
    pageSize = pageSize || 10;
    return request('/api/user/news/fav/?page=' + page + '&pagesize=' + pageSize);
  },
  clearAll() {
    return request('/api/user/news/fav/', { method: 'DELETE' });
  },
};

// ==================== History APIs ====================
const HistAPI = {
  deleteHistory(newsIds) {
    return request('/api/user/news/hist/delete', { method: 'DELETE', body: JSON.stringify({ news_ids: newsIds }) });
  },
  getAll(page, pageSize) {
    page = page || 1;
    pageSize = pageSize || 10;
    return request('/api/user/news/hist/?page=' + page + '&pagesize=' + pageSize);
  },
  clearAll() {
    return request('/api/user/news/hist/', { method: 'DELETE' });
  },
};

// ==================== Theme Management ====================
function getTheme() {
  return localStorage.getItem('theme') || 'light';
}
function setTheme(theme) {
  localStorage.setItem('theme', theme);
  document.documentElement.setAttribute('data-theme', theme);
  updateThemeBtn();
}
function toggleTheme() {
  setTheme(getTheme() === 'dark' ? 'light' : 'dark');
}
function updateThemeBtn() {
  document.querySelectorAll('.theme-toggle-btn').forEach(function(btn) {
    btn.textContent = getTheme() === 'dark' ? '\u2600\uFE0F' : '\uD83C\uDF19';
  });
}
function initTheme() {
  var t = getTheme();
  document.documentElement.setAttribute('data-theme', t);
  updateThemeBtn();
}

// ==================== Common APIs ====================
const CommonAPI = {
  sendCode(email) {
    return request('/api/auth/sendCode', { method: 'POST', body: JSON.stringify({ email }) });
  },
};
