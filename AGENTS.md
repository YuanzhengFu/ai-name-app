# AGENTS.md

## 项目定位

本仓库是一个“AI 智能起名”全栈项目，包含 FastAPI 后端和 uni-app 前端。当前项目已经从基础起名接口扩展为完整应用雏形，覆盖注册登录、邮箱验证码、会员额度、支付宝沙箱充值、AI 起名、多轮反馈、项目管理、偏好模板、起名历史、收藏、名字评分、报告导出、企业私有知识库 RAG、异步解析任务、管理员后台和业务数据维护等能力。

后端 Python 环境使用 conda 中的 `fastapi-env`。运行测试、脚本、迁移和本地服务时优先使用该环境。

当前有效源码目录：

- `FastAPIProject/`：后端项目。
- `uniapp-demo01/`：前端项目。

旧目录名如 `hou/`、`qian/`、`ainame397/`、`ainame397q/` 已经过时，不应作为当前源码入口维护。

## 根目录说明

- `.env.example`：环境变量示例，只放占位值，不放真实密钥。
- `.gitignore`：忽略规则。
- `README.md`：项目说明。
- `AGENTS.md`：本文件，给维护者和代码代理使用的项目上下文。
- `.codex_git/`：当前工作区使用的 Git 元数据目录，不是业务源码。

真实配置通常位于 `FastAPIProject/.env`，可能包含数据库连接串、API Key、SMTP 授权码、JWT 密钥和支付私钥路径等敏感信息。不要把真实值写入文档、日志、提交信息或聊天内容。

## 后端结构

后端目录：`FastAPIProject/`

- `main.py`：FastAPI 应用入口，注册业务路由，并在 lifespan 中初始化和关闭 LangGraph 工作流。
- `dependencies.py`：公共依赖，包括数据库 session、邮件实例、当前用户和管理员鉴权。
- `settings/__init__.py`：读取 `FastAPIProject/.env` 和环境变量，集中配置数据库、JWT、邮件、CORS、Redis、RabbitMQ、上传目录、Chroma 路径和支付参数。
- `models/`：SQLAlchemy ORM 模型。
- `schemas/`：Pydantic 请求和响应结构。
- `repository/`：数据库访问封装。
- `routers/`：FastAPI 路由。
- `core/`：认证、工作流、会员额度、RAG、报告导出、评分、邮件、Redis、whois、管理员数据维护等核心逻辑。
- `alembictable/`：Alembic 迁移目录。
- `tests/`：pytest 自动化测试。
- `rag_worker.py`：知识库解析 Worker。
- `init_pg_memory.py`：初始化 LangGraph PostgreSQL checkpoint 表。
- `create_admin.py`：创建或更新管理员账号脚本。
- `manage_data.py`：管理员业务数据维护命令行脚本。
- `requirements.txt`：后端依赖。
- `test_main.http`：本地接口测试样例，可能包含历史测试 token，只能用于本地调试。

后端主要外部依赖：

- MySQL：业务数据库。
- PostgreSQL：LangGraph checkpoint 记忆库。
- Redis：邮箱验证码缓存与限流。
- RabbitMQ：知识库异步解析任务队列。
- Chroma：用户私有知识库向量库，当前为本地持久化目录。
- Ollama：RAG embedding，默认使用 `nomic-embed-text`。
- DeepSeek：大模型起名生成。
- SMTP 邮件服务：发送注册验证码。
- whois 服务：企业名 `.com` 域名状态查询。
- 支付宝沙箱：会员充值支付链接、异步通知验签和交易查询。

## 前端结构

前端目录：`uniapp-demo01/`

- `App.vue`：应用启动逻辑。
- `main.js`：uni-app/Vue 入口。
- `pages.json`：页面路由配置。
- `manifest.json`：uni-app 应用配置。
- `http/http.js`：请求封装。
- `utils/reportExport.js`：报告导出工具。
- `pages/login/login.vue`：登录页，包含后端 API 地址配置和测试连接。
- `pages/register/register.vue`：注册页。
- `pages/index/index.vue`：起名首页。
- `pages/profile/profile.vue`：个人中心。
- `pages/membership/membership.vue`：会员套餐和额度流水。
- `pages/projects/projects.vue`：命名项目列表。
- `pages/templates/templates.vue`：偏好模板页面。
- `pages/history/history.vue`：历史与收藏列表。
- `pages/history/detail.vue`：历史详情和继续反馈。
- `pages/history/compare.vue`：名字对比。
- `pages/admin/admin.vue`：管理员后台。
- `pages/about/about.vue`：关于页。
- `static/`：静态资源目录，其中存在重复源码遗留，不应当作主源码维护。
- `unpackage/`：HBuilderX 构建产物，不应作为源码维护。

前端当前没有 `package.json`，不要按普通 npm/Vite 项目处理。建议使用 HBuilderX 打开 `uniapp-demo01/` 运行、调试和打包。

## 请求与网络配置

前端请求统一封装在 `uniapp-demo01/http/http.js`：

- 默认 API 地址为 `http://127.0.0.1:8000`。
- 支持通过本地缓存 `api_base_url` 覆盖后端地址。
- 登录页提供后端地址输入框、恢复默认按钮和测试连接按钮。
- 自动读取本地 `token` 并添加 `Authorization: Bearer <token>`。
- 所有 2xx 状态码视为成功。
- 401 会清理本地登录态并跳转登录页。
- 支持普通 JSON 请求、文件上传和报告下载。

在 Edge 浏览器本机运行时，`http://127.0.0.1:8000` 通常可用，前提是后端服务已经启动。

在 HBuilderX 真机、模拟器或小程序环境中，`127.0.0.1` 往往指向设备自身，不是电脑后端。应在登录页把后端地址改为电脑局域网 IP，例如：

```text
http://192.168.x.x:8000
```

后端启动时建议使用：

```powershell
cd E:\ainame397project\FastAPIProject
conda activate fastapi-env
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 后端路由概览

基础接口：

- `GET /`
- `GET /hello/{name}`
- `GET /mail/test?email=...`

认证接口：

- `GET /auth/code?email=...`
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/password/reset`

用户接口：

- `GET /users/me`
- `PATCH /users/me`
- `POST /users/me/password`
- `POST /users/me/email`
- `GET /users/me/login-records`

起名接口：

- `POST /names/get_names`：旧版起名接口，也会消耗额度。
- `POST /names/generate`：首次生成名字，返回 `thread_id`、`project_id`、`names`、剩余额度。
- `POST /names/feedback`：基于已有 `thread_id` 多轮反馈生成。
- `GET /names/quota`：查询当前用户额度概览。

项目接口：

- `POST /projects`
- `GET /projects`
- `GET /projects/{project_id}`
- `GET /projects/{project_id}/export?format=pdf|image|txt`
- `PATCH /projects/{project_id}`
- `DELETE /projects/{project_id}`：归档项目，不是物理删除。

偏好模板接口：

- `POST /preference-templates`
- `GET /preference-templates`
- `PATCH /preference-templates/{template_id}`
- `DELETE /preference-templates/{template_id}`

历史与收藏接口：

- `GET /history`
- `GET /history/{history_id}`
- `POST /history/compare`
- `GET /history/{history_id}/export?format=pdf|image|txt`
- `PATCH /history/{history_id}/favorite`
- `DELETE /history/{history_id}`

知识库接口：

- `POST /knowledge/upload`
- `GET /knowledge/files`
- `GET /knowledge/tasks/{task_id}`
- `GET /knowledge/tasks/{task_id}/preview`
- `DELETE /knowledge/tasks/{task_id}`
- `POST /knowledge/tasks/{task_id}/reparse`
- `PATCH /knowledge/tasks/{task_id}/active`

会员接口：

- `GET /membership/plans`
- `GET /membership/me`
- `POST /membership/recharge`
- `GET /membership/orders/{order_id}`
- `POST /membership/orders/{order_id}/processing`
- `POST /membership/orders/{order_id}/mock-pay`：遗留接口，当前返回 410，不再用于增加额度。
- `POST /membership/orders/{order_id}/alipay-query`：主动查询支付宝交易状态并同步本地订单。
- `POST /membership/payment/notify/{provider}`：当前仅支持 `alipay` 通知。
- `GET /membership/transactions`

管理员接口：

- `GET /admin/me`
- `GET /admin/users`
- `GET /admin/name-histories`
- `GET /admin/generation-stats`
- `GET /admin/knowledge-tasks/stats`
- `GET /admin/knowledge-tasks`
- `POST /admin/knowledge-tasks/{task_id}/reparse`
- `POST /admin/knowledge-tasks/reparse`
- `GET /admin/membership/plans`
- `POST /admin/membership/plans`
- `PATCH /admin/membership/plans/{plan_id}`
- `POST /admin/users/{user_id}/credits`
- `POST /admin/users/{user_id}/password`
- `POST /admin/membership/orders/{order_id}/refund`

管理员业务数据维护接口：

- `GET /admin/data/tables`
- `GET /admin/data/{table}`
- `GET /admin/data/{table}/{record_id}`
- `POST /admin/data/{table}`
- `PATCH /admin/data/{table}/{record_id}`
- `DELETE /admin/data/{table}/{record_id}`

所有需要登录的接口都应复用 JWT Bearer Token 鉴权。管理员接口必须复用 `require_admin`。

## 核心数据模型

`User`：

- `id`
- `email`
- `username`
- `_password`
- `is_admin`
- `created_time`

`EmailCode`：

- `id`
- `email`
- `code`
- `created_time`

`LoginRecord`：

- `id`
- `user_id`
- `email`
- `ip_address`
- `user_agent`
- `success`
- `failure_reason`
- `created_time`

`NamingProject`：

- `id`
- `user_id`
- `title`
- `category`
- `description`
- `status`
- `created_time`
- `updated_time`

`NamingPreferenceTemplate`：

- `id`
- `user_id`
- `title`
- `category`
- `preferences`
- `is_default`
- `created_time`
- `updated_time`

`NameHistory`：

- `id`
- `user_id`
- `project_id`
- `thread_id`
- `category`
- `name`
- `reference`
- `moral`
- `domain`
- `domain_status`
- `domain_checks`
- `brand_warning`
- `pinyin`
- `english_name`
- `abbreviation`
- `score_total`
- `rhythm_score`
- `meaning_score`
- `spread_score`
- `domain_score`
- `score_explanation`
- `surname`
- `gender`
- `length`
- `other`
- `exclude`
- `is_favorite`
- `created_time`
- `updated_time`

起名历史当前设计是每个候选名字一条记录。收藏功能没有独立收藏表，通过 `name_history.is_favorite` 实现。

`KnowledgeTask`：

- `id`
- `user_id`
- `project_id`
- `filename`
- `file_path`
- `status`
- `error_message`
- `is_active`
- `chunk_count`
- `parse_log`
- `created_time`
- `updated_time`

知识库任务状态固定为：

- `queued`
- `processing`
- `done`
- `failed`

会员相关模型：

- `MembershipPlan`
- `UserMembership`
- `CreditTransaction`
- `RechargeOrder`

额度流水类型包括：

- `grant`
- `recharge`
- `consume`
- `refund`
- `admin_adjust`
- `payment_refund`

## 起名输入与前端流程

起名分类固定为：

- `人名`
- `企业名`
- `宠物名`

`NameIn` 主要字段：

- `category`
- `surname`
- `gender`
- `length`
- `other`
- `exclude`
- `birth_datetime`
- `wuxing`
- `desired_meaning`
- `industry`
- `style`
- `region`
- `project_id`
- `project_title`
- `project_description`

人名起名首页主流程会询问：

1. 姓氏。
2. 性别气质。
3. 字数要求：`不限`、`单字`、`两字`、`多字`。
4. 期望寓意。

人名场景的字数选择已经从高级信息移动到主问答流程。企业名和宠物名仍可在高级信息中保留字数要求。

## 起名工作流

`core/workflow.py` 使用 LangGraph 构建起名流程。

主要节点：

- `supervisor_node`
- `human_naming_node`
- `company_naming_node`
- `pet_naming_node`

路由规则：

- `人名` -> 人名节点。
- `企业名` -> 企业品牌节点。
- `宠物名` -> 宠物节点。

企业名节点额外执行：

- 根据用户 `user_id` 和输入需求检索 Chroma 私有知识库。
- 将检索资料作为 RAG 上下文传给大模型。
- 调用 DeepSeek 生成结构化候选名字。
- 对候选名字的 `.com` 域名执行 whois 查询。
- 多轮反馈时参考历史结果和用户反馈进行迭代。

起名接口外层负责：

- 会员额度扣减。
- 异常失败退回额度。
- 名字评分。
- 起名历史落库。
- 命名项目关联和更新时间维护。

LangGraph checkpoint 使用 PostgreSQL。FastAPI 启动时初始化 `naming_graph`，关闭时释放连接。

## 知识库任务流程

知识库上传是异步流程：

1. 前端在企业名场景上传 TXT/PDF 文件。
2. 后端保存文件到 `FastAPIProject/uploads/`。
3. 后端创建 `KnowledgeTask`，初始状态为 `queued`。
4. 后端投递 RabbitMQ 队列。
5. `rag_worker.py` 消费队列任务。
6. Worker 将任务状态更新为 `processing`。
7. Worker 调用 `process_and_stor_file` 解析文件并写入 Chroma。
8. 成功后状态更新为 `done`，并记录 `chunk_count`、`parse_log`。
9. 失败后状态更新为 `failed` 并写入 `error_message`。
10. 前端轮询 `GET /knowledge/tasks/{task_id}`。
11. 用户或管理员可重新解析任务。

注意：`core/rag_service.py` 中函数名 `process_and_stor_file` 有拼写问题，但 `rag_worker.py` 正按这个名字导入。除非同步更新所有调用链，不要单独改名。

RabbitMQ 连接和队列名通过配置读取：

- `RABBITMQ_URL`
- `RAG_QUEUE_NAME`

默认队列名：

```text
rag_document_queue
```

## 会员与额度系统

会员和额度逻辑位于 `core/membership_service.py`。

关键规则：

- 新用户首次创建额度账户时默认获得 `10` 次免费额度。
- 起名生成、旧版起名接口、多轮反馈都会消耗额度。
- 生成失败会退回本次消耗的额度。
- 额度不足时返回 `402 Payment Required`。
- 充值订单当前使用 `alipay` provider，生成支付宝沙箱 `page` 或 `wap` 支付链接。
- 支付宝异步通知会验签，并按交易状态将订单更新为 paid、processing 或 failed。
- 用户可调用 `/membership/orders/{order_id}/alipay-query` 主动同步支付宝订单状态。
- `/membership/orders/{order_id}/mock-pay` 是遗留关闭接口，当前返回 `410 Gone`，不要依赖它完成充值。
- `wechat` 相关配置项保留为后续扩展，当前业务主流程未完整接入微信支付。
- 管理员可以创建或更新套餐、退款订单、调整用户额度和重置用户密码。

## 管理员数据维护

后端管理员数据维护由 `core/admin_data_service.py` 统一实现，路由位于 `routers/admin_router.py`。

白名单表：

- `user`
- `email_code`
- `login_record`
- `naming_project`
- `naming_preference_template`
- `name_history`
- `knowledge_task`
- `membership_plan`
- `user_membership`
- `credit_transaction`
- `recharge_order`

安全规则：

- 只能维护白名单表。
- 每张表都有独立的可见字段、可创建字段、可编辑字段。
- 不暴露、不允许直接修改 `User._password`。
- 创建用户时必须通过 `password` 字段，由模型 setter 哈希后写入。
- 禁止删除当前登录管理员。
- 删除用户前检查关联业务数据，默认不做级联硬删。
- `credit_transaction` 默认只允许编辑 `remark`，避免破坏额度账本。

前端管理员后台 `pages/admin/admin.vue` 中有“数据维护”标签，使用 JSON 编辑允许字段。

命令行脚本：

```powershell
cd E:\ainame397project\FastAPIProject
conda activate fastapi-env
python manage_data.py tables
python manage_data.py list user --limit 20
python manage_data.py get user 1
python manage_data.py update membership_plan 1 --set name=新套餐
python manage_data.py update membership_plan 1 --set name=新套餐 --apply
python manage_data.py delete membership_plan 1
python manage_data.py delete membership_plan 1 --apply
python manage_data.py health
```

`create`、`update`、`delete` 默认只 dry-run，真正写入必须显式添加 `--apply`。

Windows 控制台如遇中文 JSON 输出编码问题，可设置：

```powershell
$env:PYTHONIOENCODING='utf-8'
```

## 报告导出

历史记录和项目支持导出起名方案报告。

后端实现：

- `core/report_service.py`
- `GET /history/{history_id}/export?format=pdf|image|txt`
- `GET /projects/{project_id}/export?format=pdf|image|txt`

前端实现：

- `uniapp-demo01/utils/reportExport.js`
- `http.downloadHistoryReport`
- `http.downloadProjectReport`

支持格式：

- `pdf`
- `image`
- `txt`

PDF 使用 reportlab，图片使用 PIL，文本使用 UTF-8。

## 本地运行

后端安装依赖：

```powershell
cd E:\ainame397project\FastAPIProject
conda activate fastapi-env
pip install -r requirements.txt
```

后端启动：

```powershell
cd E:\ainame397project\FastAPIProject
conda activate fastapi-env
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

数据库迁移：

```powershell
cd E:\ainame397project\FastAPIProject
conda activate fastapi-env
alembic upgrade head
```

初始化 LangGraph checkpoint：

```powershell
cd E:\ainame397project\FastAPIProject
conda activate fastapi-env
python init_pg_memory.py
```

启动知识库 Worker：

```powershell
cd E:\ainame397project\FastAPIProject
conda activate fastapi-env
python rag_worker.py
```

创建或更新管理员：

```powershell
cd E:\ainame397project\FastAPIProject
conda activate fastapi-env
python create_admin.py --email admin@example.com --username admin --password 123456
```

运行测试：

```powershell
cd E:\ainame397project\FastAPIProject
$env:PYTHONIOENCODING='utf-8'
conda run --no-capture-output -n fastapi-env pytest
```

后端全量 Python 编译检查：

```powershell
cd E:\ainame397project\FastAPIProject
$env:PYTHONIOENCODING='utf-8'
conda run --no-capture-output -n fastapi-env python -m compileall -q .
```

前端运行：

- 使用 HBuilderX 打开 `uniapp-demo01/`。
- 按 uni-app 项目方式运行到浏览器、模拟器、真机或小程序。
- 如果不是本机 Edge H5，优先在登录页配置电脑局域网 IP 作为后端地址。

## 环境变量

主要环境变量包括：

- `DB_URI`
- `DB_URI1`
- `LANGGRAPH_DB_URI`
- `DEEPSEEK_API_KEY`
- `MAIL_USERNAME`
- `MAIL_PASSWORD`
- `MAIL_FROM`
- `MAIL_PORT`
- `MAIL_SERVER`
- `MAIL_FROM_NAME`
- `MAIL_STARTTLS`
- `MAIL_SSL_TLS`
- `JWT_SECRET_KEY`
- `JWT_ACCESS_TOKEN_EXPIRES_DAYS`
- `JWT_REFRESH_TOKEN_EXPIRES_DAYS`
- `SQLALCHEMY_ECHO`
- `CORS_ALLOW_ORIGINS`
- `TRUST_PROXY_HEADERS`
- `REDIS_URL`
- `EMAIL_CODE_TTL_SECONDS`
- `EMAIL_CODE_EMAIL_COOLDOWN_SECONDS`
- `EMAIL_CODE_EMAIL_HOURLY_LIMIT`
- `EMAIL_CODE_IP_HOURLY_LIMIT`
- `RABBITMQ_URL`
- `RAG_QUEUE_NAME`
- `UPLOAD_DIR`
- `CHROMA_RAG_DB_PATH`
- `MAX_UPLOAD_BYTES`
- `ALLOWED_KNOWLEDGE_EXTENSIONS`
- `PAYMENT_DEFAULT_PROVIDER`
- `PAYMENT_PUBLIC_BASE_URL`
- `PAYMENT_RETURN_URL`
- `WECHAT_PAY_APPID`
- `WECHAT_PAY_MCH_ID`
- `WECHAT_PAY_API_V3_KEY`
- `WECHAT_PAY_SERIAL_NO`
- `WECHAT_PAY_PRIVATE_KEY_PATH`
- `ALIPAY_APP_ID`
- `ALIPAY_GATEWAY`
- `ALIPAY_PRIVATE_KEY_PATH`
- `ALIPAY_PUBLIC_KEY_PATH`

真实值应只放在本地 `.env` 或安全环境变量中。支付宝私钥、公钥文件不要提交到 Git，路径通过 `ALIPAY_PRIVATE_KEY_PATH`、`ALIPAY_PUBLIC_KEY_PATH` 配置。

## 测试现状

当前自动化测试位于 `FastAPIProject/tests/`，覆盖：

- 注册、登录、密码重置、登录记录和默认会员额度。
- 邮箱验证码限流。
- 会员充值、支付通知、退款。
- 起名生成、失败退回额度、历史落库。
- 项目关联生成和反馈。
- 历史对比。
- 偏好模板。
- 企业名增强逻辑。
- 管理员鉴权。
- 知识库上传、任务失败、单个和批量重试。
- 管理员数据维护接口的白名单、密码字段隐藏、敏感字段拒绝、当前管理员删除保护、套餐数据维护。

`tests/README.md` 说明测试使用临时 SQLite 数据库，并 mock LangGraph/LLM、RabbitMQ 等外部依赖。常规测试命令：

```powershell
cd E:\ainame397project\FastAPIProject
conda run -n fastapi-env python -m pytest -q
```

## 维护注意事项

- 不要把 `FastAPIProject/.env` 的真实内容写入文档、日志、提交信息或聊天。
- 不要把 `uploads/`、`chroma_rag_db/`、`unpackage/`、`__pycache__/`、`.idea/httpRequests/` 当作核心源码维护。
- `uniapp-demo01/static/` 下有重复源码遗留，维护前端时以根层 `uniapp-demo01/pages/`、`http/`、`utils/` 为准。
- 管理员数据维护不是通用 SQL 控制台，不应绕过白名单和字段限制。
- 生产部署前应收紧 CORS，配置明确允许域名，不建议长期使用 `*`。
- 支付宝当前面向沙箱联调，正式收款前需要完成生产应用配置、证书/密钥、回调地址、对账和退款链路校验；不要把 mock 支付当作可用充值链路。
- RAG、DeepSeek、RabbitMQ、Redis、PostgreSQL、Ollama、Chroma 任一外部服务不可用，都可能导致局部功能失败或变慢。
- `process_and_stor_file` 拼写错误是兼容现状，除非同步更新所有引用，不要单独改名。
- 如果 HBuilderX 或真机提示网络连接失败，先确认后端是否启动，再确认前端登录页 API 地址是否指向电脑局域网 IP。
