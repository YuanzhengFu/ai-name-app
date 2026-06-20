from fastapi import FastAPI,Depends
from fastapi_mail import FastMail, MessageSchema, MessageType
from routers.auth_router import router as auth_router
from routers.name_router import router as name_router
from routers.rag_router import router as rag_router
from routers.admin_router import router as admin_router
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from core.workflow import init_workflow_graph, close_workflow_graph

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 服务启动时，安全地初始化带记忆的工作流
    await init_workflow_graph()
    yield
    # 服务停止时，清理数据库连接
    await close_workflow_graph()

app = FastAPI(lifespan=lifespan)
app.include_router(auth_router)
app.include_router(name_router)
app.include_router(rag_router)
app.include_router(admin_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # 允许请求的源列表
    allow_credentials=True,    # 允许携带 Cookie/凭证
    allow_methods=["*"],       # 允许的请求方法（"GET", "POST", "PUT", "DELETE" 等，"*" 表示全部允许）
    allow_headers=["*"],       # 允许的请求头（"*" 表示全部允许）
)
@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

from dependencies import get_email
@app.get("/mail/test")
async def mail_test(email:str,mail:FastMail=Depends(get_email)):
        #  1.准备邮件对象
        message = MessageSchema(
            subject="ainame验证码",
            recipients=[email],
            body=f"Hello {email}",  # 验证码是生产的
            subtype=MessageType.plain)

        await  mail.send_message(message)
        return {"message": "邮件发送成功！"}
