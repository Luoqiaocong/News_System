# Seven News — 新闻管理系统

基于 **FastAPI** + **Vue 3** + **MySQL** + **Redis** 的异步新闻管理系统。

## 技术栈

| 层级 | 技术 |
|---|---|
| 后端框架 | FastAPI (async) |
| 前端 | Vue 3 (Composition API, CDN) + HTML/CSS |
| 数据库 | MySQL (SQLAlchemy 2.0 async, aiomysql) |
| 缓存 | Redis (redis-py async) |
| 认证 | JWT (python-jose) + RefreshToken + Argon2 |
| 文件存储 | 阿里云 OSS |
| 日志 | Loguru |
| 爬虫 | aiohttp + 人民网 |

## 快速开始

### 环境要求

- Python 3.11+
- MySQL 8.0+
- Redis 7.0+

### 安装

```bash
# 克隆项目后，创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 配置

创建 `.env` 文件（参考 `.env` 模板）：

```env
# 数据库
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root
DB_NAME=newsdemo

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# 阿里云 OSS（头像上传）
OSS_ACCESS_KEY_ID=your_key_id
OSS_ACCESS_KEY_SECRET=your_key_secret
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
OSS_BUCKET_NAME=your_bucket

# SMTP 邮箱（验证码发送）
SMTP_SERVER=smtp.qq.com
SMTP_PORT=465
SENDER=your_email@qq.com
AUTH_CODE=your_smtp_auth_code

# JWT
SECRET_KEY=your_jwt_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1
REFRESH_TOKEN_EXPIRE_DAYS=7

# 用户 ID 混淆盐值
HASH_SALT=your_hash_salt
```

### 初始化数据库

```bash
# 确保 MySQL 中已创建 newsdemo 数据库
# 首次启动会自动创建表结构

# 插入测试新闻数据
python Test/insert_news.py

# 预热 Redis 缓存（可选）
python Test/newsMock.py
```

### 启动

```bash
uvicorn main:app --reload --reload-exclude "logs/*"
```

访问 `http://localhost:8000` 进入前端页面，`http://localhost:8000/docs` 查看 Swagger API 文档。

## 项目结构

```
News_System/
├── main.py                    # 入口文件
├── Config/                    # 配置模块
│   ├── settings.py            # 环境变量配置
│   ├── DataBaseConfig.py      # 数据库引擎 & 会话工厂
│   ├── AliyunOssConfig.py     # OSS 客户端
│   └── LogConfig.py           # 日志配置
├── models/                    # ORM 模型
│   ├── User.py                # 用户
│   ├── News.py                # 新闻 & 分类
│   ├── UserNewsHistory.py     # 浏览历史
│   └── UserNewsFavorite.py    # 收藏
├── Schemas/                   # Pydantic 请求/响应模型
├── Repo/                      # 数据访问层
│   ├── UserRepo.py            # 用户 DB
│   ├── NewsRepo.py            # 新闻 DB
│   ├── UserFavRepo.py         # 收藏 DB
│   ├── UserHistRepo.py        # 历史 DB
│   ├── NewsCacheRepo.py       # 新闻 Redis 缓存
│   └── UserFavCacheRepo.py    # 收藏 Redis 缓存
├── Service/                   # 业务逻辑层
│   ├── UserService.py         # 注册/登录/登出/密码管理
│   ├── NewsService.py         # 浏览/搜索/缓存管理
│   ├── UserFavService.py      # 收藏管理
│   ├── UserHistService.py     # 历史管理
│   └── CommonService.py       # 验证码/Token 刷新
├── Router/                    # API 路由
│   ├── UserRouter.py          # /api/user/*
│   ├── NewsRouter.py          # /api/news/*
│   ├── UserFavRouter.py       # /api/user/news/fav/*
│   ├── UserHistRouter.py      # /api/user/news/hist/*
│   └── CommonRouter.py        # /api/auth/*
├── Dependency/                # FastAPI 依赖
│   ├── JWTAuth.py             # JWT 认证
│   └── register_exception.py  # 全局异常处理器
├── Exception/                 # 异常体系
│   ├── ResponseCode.py        # 错误码枚举
│   └── BusinessException.py   # 业务异常基类
├── Utils/                     # 工具模块
│   ├── AuthUtil.py            # Token 生成 & 设备管理
│   ├── HashUtil.py            # 用户 ID 混淆
│   ├── SecurityUtil.py        # 密码加密 & 强度校验
│   ├── RedisUtil.py           # Redis 客户端 & 缓存装饰器
│   ├── EmailUtil.py           # 异步邮件发送
│   ├── FileUtil.py            # OSS 文件上传
│   ├── LogUtil.py             # 日志配置
│   ├── SchemaUtil.py          # ORM 结果转 Pydantic
│   ├── ResponseUtil.py        # 响应构造工具
│   ├── TransactionMixin.py    # 事务控制
│   └── ServiceDecorator.py    # 自动异常处理
├── MIddleware/                # 中间件
│   └── PerformanceMiddleware.py
├── Route/                     # 自定义路由
│   └── UnifiedRoute.py        # 统一响应格式
├── frontend/                  # 前端 SPA
│   ├── index.html             # 首页
│   ├── detail.html            # 详情页
│   ├── favorites.html         # 收藏页
│   ├── history.html           # 历史页
│   └── js/css/                # 脚本 & 样式
├── Test/                      # 测试 & 数据
│   ├── insert_news.py         # 插入测试数据
│   └── newsMock.py            # 预热 Redis
└── SpiderMode/                # 爬虫
    └── spidernews.py          # 人民网新闻爬虫
```

## 架构设计

### 分层架构

```
前端 (Vue 3 SPA)
    │  HTTP REST JSON
    ▼
Router (CBV 路由层)
    │  Depends() 依赖注入
    ▼
Service (业务逻辑层)
    │  Depends() 依赖注入
    ▼
Repo (数据访问层)
    │
    ├── MySQL (SQLAlchemy ORM)
    └── Redis (缓存)
```

### 请求生命周期

1. **PerformanceMiddleware** — 记录请求耗时日志
2. **UnifiedRoute** — 自动包裹响应为 `{code, message, data}` 统一格式
3. **认证依赖** — JWTAuth 解析 JWT，注入当前用户对象
4. **Service** — 执行业务逻辑（事务、缓存、校验）
5. **Repo** — 执行数据库查询或 Redis 操作

### 认证流程

```
登录 → 颁发 AccessToken(1min) + RefreshToken(7天)
  │
  ├── 每次 API 请求携带 AccessToken
  ├── AccessToken 过期 → RefreshToken 换新
  │     ├── 检查黑名单 → 被踢下线则拒绝
  │     └── 检查活跃列表 → 不在前三则拒绝
  └── 登出     → 从活跃列表移除 + 加入黑名单
```

- 用户 ID 经 Hashids 混淆后存入 JWT `sub` 字段
- RefreshToken 为 64 位随机十六进制字符串
- 最多同时登录 3 台设备（Redis List 控制）
- 密码使用 Argon2 加密存储

### 缓存策略

#### 新闻列表
- Redis ZSet 存储分类下所有新闻 ID，按发布时间排序
- 先查 ZSet 获取分页 ID，再批量 MGET 详情缓存
- 缓存未命中降级到 DB，并异步预热

#### 新闻详情
- Redis String 存储 JSON 序列化的新闻详情
- 浏览量更新时原地修改缓存中的 `views` 字段

#### 相关新闻
- Redis Set 存储同分类新闻 ID
- `SRANDMEMBER` 随机取 12 条，排除当前后取 6 条
- 空分类用 `-1` 哨兵值防缓存穿透

#### 收藏
- Redis Set 存储用户收藏的新闻 ID
- `SISMEMBER` O(1) 判断是否已收藏

### 异常体系

所有业务异常返回 HTTP 200，通过 `code` 字段区分：

| 范围 | 模块 |
|---|---|
| 1xxxx | 通用错误（参数/权限/服务器） |
| 2xxxx | 用户模块 |
| 3xxxx | 新闻模块 |
| 4xxxx | 收藏模块 |
| 5xxxx | 历史模块 |

- `HandlerServiceException` 类装饰器自动为 Service 层方法添加异常拦截
- 全局 `@app.exception_handler(Exception)` 兜底未预期异常

## API 接口

启动后访问 `http://localhost:8000/docs` 查看 Swagger UI。

| 方法 | 路径 | 说明 | 认证 |
|---|---|---|---|
| POST | `/api/user/reg` | 用户注册 | - |
| POST | `/api/user/login` | 用户登录 | - |
| POST | `/api/user/logout` | 用户登出 | ✓ |
| DELETE | `/api/user/delete` | 注销账户 | ✓ |
| GET | `/api/user/info` | 获取用户信息 | ✓ |
| PUT | `/api/user/update` | 更新资料 | ✓ |
| PUT | `/api/user/updatepwd` | 修改密码 | ✓ |
| POST | `/api/user/resetpwd` | 重置密码 | - |
| POST | `/api/auth/sendCode` | 发送验证码 | - |
| POST | `/api/auth/refresh` | 刷新 Token | - |
| GET | `/api/news/categories` | 分类列表 | - |
| GET | `/api/news/list` | 新闻列表 | - |
| GET | `/api/news/detail/{id}` | 新闻详情 | - |
| GET | `/api/news/search` | 搜索新闻 | - |
| POST | `/api/user/news/fav/{news_id}` | 添加收藏 | ✓ |
| DELETE | `/api/user/news/fav/delete` | 取消收藏 | ✓ |
| GET | `/api/user/news/fav` | 收藏列表 | ✓ |
| GET | `/api/user/news/hist` | 浏览历史 | ✓ |
| DELETE | `/api/user/news/hist/delete` | 删除历史 | ✓ |

## 开发说明

### 启动热重载（排除日志目录）

```bash
uvicorn main:app --reload --reload-exclude "logs/*"
```

### 代码统计

```bash
# 统计 Python 代码行数（排除虚拟环境）
(Get-ChildItem -Recurse -Filter *.py -Exclude @('venv', '.venv') `
  | Where-Object { $_.FullName -notmatch 'venv|\\.venv|\\.git|__pycache__' } `
  | Get-Content | Measure-Object -Line).Lines
```

当前项目 Python 代码约 2400 行。

### 常见问题

**Q: 打开日志文件时前端不断刷新？**

A: `uvicorn --reload` 监控项目文件变化。日志文件写入触发 reload。启动时加 `--reload-exclude "logs/*"` 排除即可。

**Q: Token 过期太快？**

A: `.env` 中 `ACCESS_TOKEN_EXPIRE_MINUTES` 默认为 1 分钟，可按需调大。

**Q: 同一账号能登录几台设备？**

A: 最多 3 台。超出时最早登录的设备被踢下线。

**Q: 验证码收不到？**

A: 检查 `.env` 中 SMTP 配置。QQ 邮箱需开启 SMTP 服务并使用授权码而非密码。
