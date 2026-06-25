# AI 智能起名系统

本项目是一个面向 H5、移动端和本地演示场景的 AI 智能起名全栈应用。系统包含 FastAPI 后端和 uni-app 前端，支持人名、企业名和宠物名生成，并扩展了注册登录、会员额度、多轮反馈、命名项目、偏好模板、历史收藏、名字评分、报告导出、企业私有知识库 RAG、异步解析任务和管理员后台等能力。

前端源码位于 `uniapp-demo01/`，建议使用 HBuilderX 打开运行；后端源码位于 `FastAPIProject/`，Python 环境使用 conda 中的 `fastapi-env`。

## 主要功能

### 智能起名

- 支持 `人名`、`企业名`、`宠物名` 三类起名。
- 支持姓氏、性别气质、字数要求、期望寓意、行业、风格、地区、排除词等输入。
- 使用 LangGraph 组织起名流程，支持基于 `thread_id` 的多轮反馈。
- 起名结果保存为历史记录，并支持收藏、对比和继续反馈。
- 对候选名字进行音律、寓意、传播、域名等维度评分。

### 企业知识库 RAG

- 企业名场景支持上传 TXT/PDF 私有知识库文件。
- 上传后创建异步解析任务，通过 RabbitMQ 投递到 `rag_worker.py`。
- Worker 解析文件并写入 Chroma 本地向量库。
- 企业名生成时检索用户私有知识库，结合业务资料生成候选名字。
- 支持知识库任务状态查询、预览、启停和重新解析。

### 会员额度与订单

- 新用户默认获得免费起名额度。
- 起名生成和多轮反馈都会消耗额度，失败时自动退回。
- 支持会员套餐、充值订单、额度流水和 mock 支付流程。
- 管理员可以调整用户额度、维护套餐、重置用户密码和处理退款。

### 项目、模板与报告

- 支持创建命名项目，并将起名历史关联到项目。
- 支持偏好模板，便于复用常用起名要求。
- 历史记录和项目均支持导出 `pdf`、`image`、`txt` 报告。

### 管理员后台

- 管理员可查看用户、起名历史、生成统计和知识库任务。
- 支持单个或批量触发知识库任务重新解析。
- 提供白名单业务数据维护接口，避免直接暴露通用 SQL 控制台。
- 敏感字段受保护，用户密码哈希不会直接暴露或直接编辑。

## 技术架构

- 前端：uni-app、Vue。
- API：FastAPI、Uvicorn。
- 业务数据库：MySQL、SQLAlchemy、Alembic。
- 会话记忆：PostgreSQL、LangGraph checkpoint。
- 缓存与限流：Redis。
- 异步任务：RabbitMQ。
- 大语言模型：DeepSeek。
- RAG：Chroma、Ollama `nomic-embed-text`。
- 报告导出：reportlab、PIL。
- 测试：pytest、临时 SQLite、外部依赖 mock。

## 目录结构

```text
ainame397project/
├── FastAPIProject/              FastAPI 后端项目
│   ├── main.py                  应用入口
│   ├── dependencies.py          公共依赖和鉴权
│   ├── settings/                环境变量和配置
│   ├── models/                  SQLAlchemy ORM 模型
│   ├── schemas/                 Pydantic 请求和响应模型
│   ├── repository/              数据访问封装
│   ├── routers/                 API 路由
│   ├── core/                    起名、RAG、会员、报告、管理员等核心逻辑
│   ├── alembictable/            Alembic 迁移
│   ├── tests/                   pytest 自动化测试
│   ├── rag_worker.py            知识库解析 Worker
│   ├── create_admin.py          创建或更新管理员
│   ├── manage_data.py           管理员数据维护命令行脚本
│   └── requirements.txt         后端依赖
├── uniapp-demo01/               uni-app 前端项目
│   ├── pages/                   页面源码
│   ├── http/http.js             请求封装
│   ├── utils/reportExport.js    报告导出工具
│   ├── App.vue
│   ├── main.js
│   ├── pages.json
│   └── manifest.json
├── .env.example                 环境变量示例
├── AGENTS.md                    开发维护上下文
├── requirements.md              需求说明和验收标准
├── CHANGELOG.md                 更新记录
└── README.md                    项目说明
```

运行时目录如 `FastAPIProject/uploads/`、`FastAPIProject/chroma_rag_db/`、`uniapp-demo01/unpackage/`、`__pycache__/` 不应提交到 Git。

## 环境要求

- Windows 本地开发环境。
- Conda 环境：`fastapi-env`。
- MySQL 8.x。
- PostgreSQL 14+。
- Redis。
- RabbitMQ。
- Ollama，并安装 `nomic-embed-text`。
- DeepSeek API Key。
- SMTP 邮箱服务。
- HBuilderX。

## 安装依赖

后端 Python 环境使用 conda 中的 `fastapi-env`：

```powershell
conda activate fastapi-env
cd E:\ainame397project\FastAPIProject
pip install -r requirements.txt
```

前端当前没有 `package.json`，不要按普通 npm/Vite 项目处理。请使用 HBuilderX 打开：

```text
E:\ainame397project\uniapp-demo01
```

## 配置环境变量

复制根目录 `.env.example` 到后端目录：

```powershell
Copy-Item E:\ainame397project\.env.example E:\ainame397project\FastAPIProject\.env
```

后端配置读取 `FastAPIProject/.env`。至少需要配置：

```env
DB_URI=mysql+aiomysql://root:password@127.0.0.1:3306/ainame397?charset=utf8mb4
DB_URI1=postgresql+psycopg://postgres:password@127.0.0.1:5432/ainame
LANGGRAPH_DB_URI=postgresql://postgres:password@127.0.0.1:5432/ainame397

DEEPSEEK_API_KEY=your-deepseek-api-key

MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-email-auth-code
MAIL_FROM=your-email@example.com
MAIL_PORT=587
MAIL_SERVER=smtp.qq.com
MAIL_FROM_NAME=ainameapp
MAIL_STARTTLS=true
MAIL_SSL_TLS=false

JWT_SECRET_KEY=replace-with-a-long-random-secret
JWT_ACCESS_TOKEN_EXPIRES_DAYS=1
JWT_REFRESH_TOKEN_EXPIRES_DAYS=30

REDIS_URL=redis://127.0.0.1:6379/0
RABBITMQ_URL=amqp://admin:admin123@127.0.0.1:5672/
RAG_QUEUE_NAME=rag_document_queue

UPLOAD_DIR=uploads
CHROMA_RAG_DB_PATH=chroma_rag_db
MAX_UPLOAD_BYTES=10485760
ALLOWED_KNOWLEDGE_EXTENSIONS=.txt,.pdf

PAYMENT_DEFAULT_PROVIDER=mock
PAYMENT_PUBLIC_BASE_URL=http://127.0.0.1:8000
```

不要把真实数据库密码、DeepSeek API Key、邮箱授权码、JWT 密钥写入文档、提交记录或聊天内容。

## 初始化外部服务

### MySQL

MySQL 保存用户、起名历史、知识库任务、会员套餐、额度流水和订单。

```sql
CREATE DATABASE ainame397
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

执行迁移：

```powershell
conda activate fastapi-env
cd E:\ainame397project\FastAPIProject
alembic upgrade head
```

### PostgreSQL

PostgreSQL 用于 LangGraph checkpoint 记忆库。项目中同时保留了 `DB_URI1` 和 `LANGGRAPH_DB_URI`，实际 LangGraph 工作流读取 `LANGGRAPH_DB_URI`。

```sql
CREATE DATABASE ainame397;
```

初始化 LangGraph checkpoint 表：

```powershell
conda activate fastapi-env
cd E:\ainame397project\FastAPIProject
python init_pg_memory.py
```

### Redis

Redis 用于邮箱验证码缓存和限流计数：

```powershell
redis-cli ping
```

返回 `PONG` 即可。带密码连接示例：

```env
REDIS_URL=redis://:password@127.0.0.1:6379/0
```

### RabbitMQ

RabbitMQ 用于知识库文件解析任务队列：

```powershell
rabbitmqctl add_user admin admin123
rabbitmqctl add_vhost ainame
rabbitmqctl set_permissions -p ainame admin ".*" ".*" ".*"
```

配置示例：

```env
RABBITMQ_URL=amqp://admin:admin123@127.0.0.1:5672/ainame
RAG_QUEUE_NAME=rag_document_queue
```

### Ollama 和 Chroma

Ollama 用于 RAG embedding，当前使用 `nomic-embed-text`：

```powershell
ollama pull nomic-embed-text
ollama list
```

Chroma 使用本地持久化目录，不需要单独启动服务：

```env
CHROMA_RAG_DB_PATH=chroma_rag_db
```

### DeepSeek 和 SMTP

DeepSeek 用于起名大模型生成：

```env
DEEPSEEK_API_KEY=your-deepseek-api-key
```

SMTP 用于注册验证码和邮件测试接口。常见配置：

- 端口 `587`：通常使用 `MAIL_STARTTLS=true`、`MAIL_SSL_TLS=false`。
- 端口 `465`：通常使用 `MAIL_STARTTLS=false`、`MAIL_SSL_TLS=true`。

启动后端后可测试：

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/mail/test?email=target@example.com"
```

## 启动项目

先启动外部依赖：MySQL、PostgreSQL、Redis、RabbitMQ、Ollama。

启动后端：

```powershell
conda activate fastapi-env
cd E:\ainame397project\FastAPIProject
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

启动知识库 Worker：

```powershell
conda activate fastapi-env
cd E:\ainame397project\FastAPIProject
python rag_worker.py
```

创建或更新管理员账号：

```powershell
conda activate fastapi-env
cd E:\ainame397project\FastAPIProject
python create_admin.py --email admin@example.com --username admin --password 123456
```

前端运行：

1. 使用 HBuilderX 打开 `E:\ainame397project\uniapp-demo01`。
2. 默认后端地址为 `http://127.0.0.1:8000`。
3. 如果运行到真机、模拟器或小程序环境，在登录页将后端地址改为电脑局域网 IP，例如 `http://192.168.x.x:8000`。

## 测试与检查

后端测试使用临时 SQLite 数据库，并 mock LangGraph/LLM、RabbitMQ 等外部依赖。

```powershell
cd E:\ainame397project\FastAPIProject
conda run -n fastapi-env python -m pytest -q
```

后端全量 Python 编译检查：

```powershell
cd E:\ainame397project\FastAPIProject
$env:PYTHONIOENCODING='utf-8'
conda run --no-capture-output -n fastapi-env python -m compileall -q .
```

当前自动化测试覆盖：

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

## 部署检查清单

启动完成后按以下顺序检查：

1. `GET http://127.0.0.1:8000/` 返回 `Hello World`。
2. MySQL 已执行 `alembic upgrade head`，用户注册和登录接口可用。
3. PostgreSQL 已执行 `python init_pg_memory.py`，起名生成可创建 `thread_id`。
4. Redis `PING` 正常，邮箱验证码接口 `/auth/code` 可写入验证码缓存。
5. RabbitMQ 正常，上传知识库文件后任务进入 `queued`，Worker 启动后变为 `processing` 或 `done`。
6. Ollama 已安装 `nomic-embed-text`，知识库解析不会因 embedding 模型缺失失败。
7. Chroma 目录可写，解析完成后 `FastAPIProject/chroma_rag_db` 生成持久化文件。
8. DeepSeek API Key 有效，`/names/generate` 能返回候选名字。
9. SMTP 配置有效，注册验证码邮件可以送达。

## 安全提醒

- 生产环境必须替换 `JWT_SECRET_KEY`、数据库密码、RabbitMQ 密码、邮箱授权码和 DeepSeek API Key。
- `FastAPIProject/.env` 包含真实配置，禁止提交或分享。
- `CORS_ALLOW_ORIGINS` 不要使用 `*`，应配置真实前端域名。
- `UPLOAD_DIR` 和 `CHROMA_RAG_DB_PATH` 需要挂载到持久化磁盘。
- RabbitMQ、Redis、MySQL、PostgreSQL 不建议暴露到公网。
- 当前充值流程默认 `PAYMENT_DEFAULT_PROVIDER=mock`，属于模拟支付；接入真实支付前不要用于生产收款。
- `FastAPIProject/uploads/`、`FastAPIProject/chroma_rag_db/`、`uniapp-demo01/unpackage/`、`__pycache__/` 属于运行或构建产物，不应作为核心源码维护。
