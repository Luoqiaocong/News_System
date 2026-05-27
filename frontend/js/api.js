// ==================== API Configuration ====================
const API_BASE = 'http://localhost:8000';

// ==================== Token Management ====================
function getToken() {
  return localStorage.getItem('token');
}

function setToken(token) {
  if (token) {
    localStorage.setItem('token', token);
  } else {
    localStorage.removeItem('token');
  }
}

function isLoggedIn() {
  return !!getToken();
}

function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
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

  const res = await fetch(API_BASE + url, {
    ...options,
    headers,
  });

  const data = await res.json();

  if (!res.ok || (data.code && data.code !== 20000 && data.code !== 0 && data.code !== 20100)) {
    const message = data.message || data.detail || '请求失败';
    throw new Error(message);
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
  deleteAccount() {
    return request('/api/user/delete', { method: 'DELETE' });
  },
};

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
    return request('/api/common/sendCode', { method: 'POST', body: JSON.stringify({ email }) });
  },
};
