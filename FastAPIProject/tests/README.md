# 后端测试说明

从后端目录使用项目 conda 环境运行测试：

```powershell
cd E:\ainame397project\FastAPIProject
conda run -n fastapi-env python -m pytest -q
```

测试使用临时 SQLite 数据库，不连接 MySQL、PostgreSQL、Redis、RabbitMQ、DeepSeek、Chroma、SMTP 或 Ollama。LangGraph/LLM、RabbitMQ 等外部依赖在测试中会被 mock。

当前覆盖范围：

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
