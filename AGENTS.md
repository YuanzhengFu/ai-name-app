# AGENTS.md

## 项目概览

本仓库包含两个主要项目目录：

- `ainame397/`：后端，FastAPI + SQLAlchemy + Alembic + Redis + LangGraph/LangChain。
- `ainame397q/`：前端，uni-app + Vue 3，适合用 HBuilderX 运行和打包。

项目功能是“AI 智能起名”：

- 支持人名、企业名、宠物名生成。
- 企业名支持上传 TXT/PDF 私有知识库，后端用 Chroma 做 RAG 检索。
- 企业名生成会尝试查询 `.com` 域名注册状态。
- 登录后通过 JWT Bearer Token 调用起名、知识库上传和管理员接口。
- 已加入管理员能力：用户表有 `is_admin` 字段，管理员接口前缀为 `/admin`。

## 后端结构

后端目录：`ainame397/`

关键文件：

- `main.py`：FastAPI 应用入口，注册 auth、names、knowledge、admin 路由，并在生命周期中初始化/关闭 LangGraph 工作流。
- `dependencies.py`：公共依赖，包括数据库 session、邮件实例、管理员鉴权依赖 `require_admin`。
- `settings/__init__.py`：数据库、邮箱、JWT 等配置。当前包含敏感配置，后续应迁移到环境变量。
- `models/__init__.py`：SQLAlchemy 异步 engine、session factory、DeclarativeBase。
- `models/user.py`：用户模型和邮箱验证码模型。
- `repository/user_repo.py`：用户和邮箱验证码的数据访问对象。
- `schemas/user_schemas.py`：注册、登录、用户返回结构。
- `schemas/name_schemas.py`：起名输入、输出、反馈结构。
- `core/auth.py`：JWT 生成和校验。
- `core/workflow.py`：LangGraph 起名工作流，包含人名、企业名、宠物名节点。
- `core/rag_service.py`：文件解析、向量库写入、用户私有知识库检索。
- `core/tools.py`：`.com` 域名 whois 查询。
- `core/mailtools.py`：FastAPI-Mail 邮件配置。
- `core/redisconfig.py`：Redis 客户端配置。
- `routers/auth_router.py`：注册、登录、邮箱验证码。
- `routers/name_router.py`：起名生成和多轮反馈。
- `routers/rag_router.py`：知识库文件上传。
- `routers/admin_router.py`：管理员接口，目前包含 `GET /admin/me`。
- `create_admin.py`：创建或更新管理员账号的命令行脚本。
- `alembictable/`：Alembic 迁移目录。
- `test_main.http`：本地接口测试样例。

## 前端结构

前端目录：`ainame397q/`

关键文件：

- `main.js`：uni-app/Vue 入口。
- `App.vue`：应用启动时检查本地 token，没有 token 则跳转登录页。
- `pages.json`：页面路由配置。
- `manifest.json`：uni-app 应用配置，应用名为 `AI智能起名`。
- `http/http.js`：后端请求封装，统一添加 `Authorization: Bearer <token>`。
- `pages/login/login.vue`：登录页。
- `pages/register/register.vue`：注册页，包含邮箱验证码流程。
- `pages/index/index.vue`：起名主页面，包含分类切换、文件上传、起名生成、多轮反馈。
- `static/logo.png`：静态资源。
- `unpackage/`：uni-app 构建产物和缓存，不应作为主要源码维护。

## 后端接口

基础接口：

- `GET /`
- `GET /hello/{name}`
- `GET /mail/test?email=...`

认证接口：

- `GET /auth/code?email=...`
  - 发送 4 位邮箱验证码。
  - 验证码存入 Redis，过期时间 300 秒。
- `POST /auth/register`
  - 请求体字段：`email`、`username`、`password`、`confirm_password`、`code`。
  - 普通注册用户默认 `is_admin=false`。
- `POST /auth/login`
  - 请求体字段：`email`、`password`。
  - 返回 `user` 和 `token`。
  - `user` 中包含 `is_admin`。

起名接口：

- `POST /names/get_names`
  - 旧接口，返回 names。
  - 需要 Bearer token。
- `POST /names/generate`
  - 首次起名，返回 `thread_id` 和 `names`。
  - 需要 Bearer token。
- `POST /names/feedback`
  - 多轮反馈，使用上一轮 `thread_id`。
  - 需要 Bearer token。

知识库接口：

- `POST /knowledge/upload`
  - multipart 上传文件字段名：`file`。
  - 支持 TXT/PDF。
  - 文件保存到 `uploads/`，后台任务写入 Chroma。
  - 需要 Bearer token。

管理员接口：

- `GET /admin/me`
  - 验证当前 token 是否属于管理员。
  - 需要 Bearer token 且用户 `is_admin=true`。

## 主要数据模型

`User`：

- `id`
- `email`
- `username`
- `_password`
- `is_admin`

`EmailCode`：

- `id`
- `email`
- `code`
- `created_time`

起名返回结构 `NameSchema`：

- `name`
- `reference`
- `moral`
- `domain`
- `domain_status`

起名分类固定为：

- `人名`
- `企业名`
- `宠物名`

## 本地运行参考

后端通常从 `ainame397/` 目录运行：

```powershell
cd E:\ainame397project\ainame397
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

数据库迁移：

```powershell
cd E:\ainame397project\ainame397
alembic upgrade head
```

创建或更新管理员：

```powershell
cd E:\ainame397project\ainame397
python create_admin.py --email admin@example.com --username admin --password 123456
```

前端建议使用 HBuilderX 打开 `ainame397q/` 运行。当前没有 `package.json`，不应按普通 npm/Vite 项目处理。

前端开发环境后端地址在 `ainame397q/http/http.js`：

```js
http://192.168.0.105:8000
```

如果本机 IP 或后端端口变化，需要同步修改该地址。

## 外部依赖和本地服务

后端依赖多个本地/外部服务：

- MySQL：业务用户库，配置在 `settings/__init__.py` 的 `DB_URI`。
- PostgreSQL：LangGraph checkpoint 记忆库，配置在 `core/workflow.py` 的 `DB_URI`。
- Redis：邮箱验证码缓存，配置在 `core/redisconfig.py`。
- Ollama：RAG embedding 使用 `nomic-embed-text`，见 `core/rag_service.py`。
- Chroma：向量库存储目录为 `chroma_rag_db/`。
- DeepSeek：起名工作流使用 `ChatDeepSeek`。
- SMTP 邮箱：注册验证码发送。
- whois：企业名 `.com` 域名查询会连接 `whois.verisign-grs.com:43`。

## 已知风险和注意事项

1. `settings/__init__.py`、`core/workflow.py`、`core/nametools.py`、`init_pg_memory.py` 中存在硬编码连接串或 API Key。不要在文档、日志或提交说明中复制这些敏感值，后续应迁移到 `.env` 或系统环境变量。

2. `core/workflow.py` 使用的 PostgreSQL 连接串和 `init_pg_memory.py` 中的连接串数据库名不完全一致，初始化 LangGraph checkpoint 表时需要确认实际使用哪个库。

3. `core/workflow.py` 中 `naming_graph` 在 FastAPI lifespan 启动时初始化。如果直接调用 `generate_naming_v2` 而没有经过应用启动流程，`naming_graph` 可能为空。

4. `core/rag_service.py` 的函数名是 `process_and_stor_file`，拼写保留了现状，`rag_router.py` 也按这个名字导入。改名需要同步修改调用处。

5. `uploads/`、`chroma_rag_db/`、`unpackage/`、`__pycache__/` 都属于运行或构建产生的数据，不应手工维护为核心源码。

6. 前端 `App.vue` 启动时无 token 会跳转登录页。注册页和登录页本身也可能受这个全局逻辑影响，调试跳转行为时先检查这里。

7. 企业名会做 RAG 检索和 whois 查询，因此依赖本地 embedding 服务、Chroma 数据和网络端口。相关服务不可用时，企业名生成可能变慢或返回降级信息。

8. 后端当前 CORS 为 `allow_origins=["*"]` 且 `allow_credentials=True`。生产部署前建议收紧允许域名。

## 最近已做的代码变更

- JWT 已补充 `exp` 过期时间，并修正 access/refresh token 类型判断。
- token 解码返回值调整为 `int` 类型用户 id。
- 注册密码确认校验器已改为正确的 Pydantic `model_validator` 写法。
- `NameIn.exclude` 已改为 `default_factory=list`。
- 前端请求封装已支持所有 2xx 成功状态码，邮箱参数会做 URL 编码，上传 JSON 解析增加异常处理。
- 已增加管理员字段、管理员鉴权依赖、`/admin/me` 接口、管理员创建脚本和 Alembic 迁移。

## 后续维护建议

- 优先把所有密钥和连接串迁移到环境变量。
- 增加 `requirements.txt` 或 `pyproject.toml`，固定后端依赖版本。
- 补充 README，明确数据库、Redis、Ollama、PostgreSQL checkpoint 初始化步骤。
- 为认证、管理员权限、起名 schema 增加最小自动化测试。
- 为前端增加管理员页面时，应先复用 `http/http.js` 的 token 机制，并调用 `/admin/me` 判断权限。
