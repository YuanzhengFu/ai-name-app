# AI 智能起名项目部署文档

本项目包含 FastAPI 后端和 uni-app 前端。后端依赖 MySQL、PostgreSQL、Redis、RabbitMQ、Ollama、Chroma、DeepSeek 和 SMTP 邮箱服务；前端建议使用 HBuilderX 打开 `uniapp-demo01/` 运行和打包。

## 1. 基础环境

后端 Python 环境使用 conda 中的 `fastapi-env`。

```powershell
conda activate fastapi-env
cd E:\ainame397project\FastAPIProject
pip install -r requirements.txt
```

前端当前没有 `package.json`，不要按普通 npm/Vite 项目处理。请使用 HBuilderX 打开 `E:\ainame397project\uniapp-demo01`。

## 2. 环境变量

复制根目录 `.env.example` 到后端目录：

```powershell
Copy-Item E:\ainame397project\.env.example E:\ainame397project\FastAPIProject\.env
```

后端配置读取 `FastAPIProject/.env`。至少需要配置以下变量：

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
```

不要把真实数据库密码、DeepSeek API Key、邮箱授权码、JWT 密钥写入文档、提交记录或聊天内容。

## 3. MySQL 初始化

MySQL 保存业务数据，包括用户、起名历史、知识库任务、会员套餐、额度流水和订单。

1. 安装并启动 MySQL 8.x。
2. 创建业务数据库，字符集使用 `utf8mb4`：

```sql
CREATE DATABASE ainame397
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

3. 创建或确认数据库账号有该库的读写、建表和迁移权限：

```sql
CREATE USER 'ainame'@'%' IDENTIFIED BY 'change-me';
GRANT ALL PRIVILEGES ON ainame397.* TO 'ainame'@'%';
FLUSH PRIVILEGES;
```

4. 将 `FastAPIProject/.env` 中的 `DB_URI` 改为实际连接串，例如：

```env
DB_URI=mysql+aiomysql://ainame:change-me@127.0.0.1:3306/ainame397?charset=utf8mb4
```

5. 执行业务表迁移：

```powershell
conda activate fastapi-env
cd E:\ainame397project\FastAPIProject
alembic upgrade head
```

## 4. PostgreSQL 初始化

PostgreSQL 用于 LangGraph checkpoint 记忆库。项目中同时保留了 `DB_URI1` 和 `LANGGRAPH_DB_URI`，实际 LangGraph 工作流读取 `LANGGRAPH_DB_URI`。

1. 安装并启动 PostgreSQL 14+。
2. 创建 checkpoint 数据库：

```sql
CREATE DATABASE ainame397;
```

3. 创建或确认账号权限：

```sql
CREATE USER ainame_pg WITH PASSWORD 'change-me';
GRANT ALL PRIVILEGES ON DATABASE ainame397 TO ainame_pg;
```

如果使用 PostgreSQL 15+，还需要进入目标库授权 schema：

```sql
\c ainame397
GRANT ALL ON SCHEMA public TO ainame_pg;
```

4. 配置 `FastAPIProject/.env`：

```env
LANGGRAPH_DB_URI=postgresql://ainame_pg:change-me@127.0.0.1:5432/ainame397
DB_URI1=postgresql+psycopg://ainame_pg:change-me@127.0.0.1:5432/ainame397
```

5. 初始化 LangGraph checkpoint 表：

```powershell
conda activate fastapi-env
cd E:\ainame397project\FastAPIProject
python init_pg_memory.py
```

## 5. Redis 初始化

Redis 用于邮箱验证码缓存和限流计数。

1. 安装并启动 Redis。
2. 确认本地可连接：

```powershell
redis-cli ping
```

返回 `PONG` 即可。

3. 配置 `FastAPIProject/.env`：

```env
REDIS_URL=redis://127.0.0.1:6379/0
EMAIL_CODE_TTL_SECONDS=300
EMAIL_CODE_EMAIL_COOLDOWN_SECONDS=60
EMAIL_CODE_EMAIL_HOURLY_LIMIT=5
EMAIL_CODE_IP_HOURLY_LIMIT=20
```

如果 Redis 设置了密码，连接串格式为：

```env
REDIS_URL=redis://:password@127.0.0.1:6379/0
```

## 6. RabbitMQ 初始化

RabbitMQ 用于知识库文件解析任务队列。后端上传文件后会向队列投递任务，`rag_worker.py` 负责消费。

1. 安装并启动 RabbitMQ。
2. 创建账号和虚拟主机：

```powershell
rabbitmqctl add_user admin admin123
rabbitmqctl add_vhost ainame
rabbitmqctl set_permissions -p ainame admin ".*" ".*" ".*"
```

3. 配置 `FastAPIProject/.env`：

```env
RABBITMQ_URL=amqp://admin:admin123@127.0.0.1:5672/ainame
RAG_QUEUE_NAME=rag_document_queue
```

4. 队列由代码自动声明，名称为 `rag_document_queue`。也可以提前在 RabbitMQ 管理后台确认该队列是否出现。

## 7. Ollama 初始化

Ollama 用于 RAG embedding，当前代码固定使用 `nomic-embed-text`。

1. 安装并启动 Ollama。
2. 拉取 embedding 模型：

```powershell
ollama pull nomic-embed-text
```

3. 验证模型可用：

```powershell
ollama list
```

需要能看到 `nomic-embed-text`。知识库解析 Worker 调用 `langchain_ollama.OllamaEmbeddings(model="nomic-embed-text")`，默认连接本机 Ollama 服务。

## 8. Chroma 初始化

Chroma 保存用户私有知识库向量数据。当前项目使用本地持久化目录，不需要单独启动 Chroma 服务。

1. 配置持久化目录：

```env
CHROMA_RAG_DB_PATH=chroma_rag_db
```

相对路径会解析到 `FastAPIProject/chroma_rag_db`。

2. 确保目录可写：

```powershell
cd E:\ainame397project\FastAPIProject
New-Item -ItemType Directory -Force chroma_rag_db
```

3. 首次上传并解析 TXT/PDF 知识库文件后，代码会自动创建 Chroma sqlite 文件和 collection。每个用户使用 `user_{user_id}_docs` collection。

`FastAPIProject/chroma_rag_db/` 是运行时数据目录，不应作为核心源码提交。

## 9. DeepSeek 初始化

DeepSeek 用于起名大模型生成，代码使用 `langchain_deepseek.ChatDeepSeek`，模型名为 `deepseek-chat`。

1. 在 DeepSeek 控制台创建 API Key。
2. 配置 `FastAPIProject/.env`：

```env
DEEPSEEK_API_KEY=your-deepseek-api-key
```

3. 确认运行机器可以访问 DeepSeek API。没有有效 API Key 时，后端启动或起名生成会失败。

## 10. SMTP 初始化

SMTP 用于注册邮箱验证码和邮件测试接口。

1. 准备邮箱服务商 SMTP 账号。QQ 邮箱通常使用授权码而不是登录密码。
2. 开启 SMTP 服务并获取授权码。
3. 配置 `FastAPIProject/.env`：

```env
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-email-auth-code
MAIL_FROM=your-email@example.com
MAIL_PORT=587
MAIL_SERVER=smtp.qq.com
MAIL_FROM_NAME=ainameapp
MAIL_STARTTLS=true
MAIL_SSL_TLS=false
```

常见配置：

- 端口 `587`：通常使用 `MAIL_STARTTLS=true`、`MAIL_SSL_TLS=false`。
- 端口 `465`：通常使用 `MAIL_STARTTLS=false`、`MAIL_SSL_TLS=true`。

启动后端后可测试：

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/mail/test?email=target@example.com"
```

## 11. 启动服务

先启动外部依赖：MySQL、PostgreSQL、Redis、RabbitMQ、Ollama。

然后启动后端：

```powershell
conda activate fastapi-env
cd E:\ainame397project\FastAPIProject
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

再启动知识库 Worker：

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
2. 确认 `uniapp-demo01/http/http.js` 中的后端地址：

```js
const BASE_URL = "http://127.0.0.1:8000";
```

3. 按 uni-app 项目方式运行到浏览器、模拟器或小程序环境。

## 12. 测试与检查

后端测试使用临时 SQLite 数据库，并 mock LangGraph/LLM、RabbitMQ 等外部依赖。常规测试命令：

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

## 13. 部署检查清单

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

## 14. 生产部署注意事项

- 生产环境必须替换 `JWT_SECRET_KEY`、数据库密码、RabbitMQ 密码、邮箱授权码和 DeepSeek API Key。
- `CORS_ALLOW_ORIGINS` 不要使用 `*`，应配置真实前端域名。
- `UPLOAD_DIR` 和 `CHROMA_RAG_DB_PATH` 需要挂载到持久化磁盘。
- RabbitMQ、Redis、MySQL、PostgreSQL 不建议暴露到公网。
- 当前充值流程默认 `PAYMENT_DEFAULT_PROVIDER=mock`，属于模拟支付；接入真实支付前不要用于生产收款。
- `FastAPIProject/uploads/`、`FastAPIProject/chroma_rag_db/`、`uniapp-demo01/unpackage/`、`__pycache__/` 属于运行或构建产物，不应作为核心源码维护。
