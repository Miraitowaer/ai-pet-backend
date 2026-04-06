import os
import sys
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager
import uvicorn
from pydantic import BaseModel
from config import settings
from database import engine, Base

import grpc
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "protos"))
import protos.pet_pb2 as pet_pb2
from fastapi.middleware.cors import CORSMiddleware
import protos.pet_pb2_grpc as pet_pb2_grpc
import models  # [变更] 必须引入 models，否则 SQLAlchemy 扫描不到新建的 User 类！

# 生命周期事件：在服务器启动时自动连接数据库并建表
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 初始化数据库
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(
    title=settings.project_name,
    description="The backend service for the AI Desktop Pet",
    version=settings.version,
    lifespan=lifespan
)

# [变更] 新增 CORS 中间件，允许 Electron (localhost:5173 跨域)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": f"Hello, {settings.project_name}!",
        "debug": settings.debug
    }

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "ai-pet-backend"}

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default_user"  # 标识客户端/用户身份

class RegisterDTO(BaseModel):
    account_name: str
    password: str
    pet_name: str
    avatar: str

@app.post("/api/register")
async def register_account(req: RegisterDTO):
    try:
        async with grpc.aio.insecure_channel('localhost:50051') as channel:
            stub = pet_pb2_grpc.PetServiceStub(channel)
            rpc_req = pet_pb2.AuthRegisterReq(
                account_name=req.account_name, 
                password=req.password,
                pet_name=req.pet_name,
                avatar=req.avatar
            )
            response = await stub.RegisterAccount(rpc_req)
            return {"success": response.success, "message": response.message}
    except Exception as e:
        return {"success": False, "message": f"核心断连: ({str(e)})"}

class LoginDTO(BaseModel):
    account_name: str
    password: str

@app.post("/api/login")
async def login_account(req: LoginDTO):
    try:
        async with grpc.aio.insecure_channel('localhost:50051') as channel:
            stub = pet_pb2_grpc.PetServiceStub(channel)
            rpc_req = pet_pb2.AuthLoginReq(account_name=req.account_name, password=req.password)
            response = await stub.LoginAccount(rpc_req)
            return {
                "success": response.success, 
                "message": response.message,
                "pet_name": response.pet_name,
                "avatar": response.avatar
            }
    except Exception as e:
        return {"success": False, "message": f"核心断连: ({str(e)})"}

@app.post("/chat")
async def chat_with_pet(request: ChatRequest):
    """
    [重构后] API Gateway
    不再负责复杂的计算和数据库读写，它只负责缓存拦截和纯粹的微服务网络转发。
    """
    from services.redis_cache import get_cached_response, set_cached_response
    
    # --- 1. 拦截层：极其快速的 Redis 缓存检查 ---
    try:
        cached_reply = await get_cached_response(request.session_id, request.message)
        if cached_reply:
            print(f"[*] 【API网关】命中 Redis 缓存！直接拦截返回")
            return {"reply": cached_reply, "cached": True}
    except Exception as e:
        print(f"[*] Redis由于云端保护拦截无法连接，直接防雪崩穿透...")
        pass
        
    # --- 2. [变更点] 透传层：打包结构体，跨进程通过 protobuf 协议发射给 gRPC 计算节点 ---
    try:
        print(f"[*] 【API网关】发送二进制包给内部 gRPC 微服务引擎中...")
        async with grpc.aio.insecure_channel('localhost:50051') as channel:
            # 获取桩代码（类似于打通网线）
            stub = pet_pb2_grpc.PetServiceStub(channel)
            # 通过协议组装发送请求
            rpc_request = pet_pb2.ChatRequest(session_id=request.session_id, message=request.message)
            # 等待协程计算结果
            response = await stub.Chat(rpc_request)
            reply = response.reply
    except Exception as e:
        return {"reply": f"网关报错：无法连通内部AI微服务核心，由于：({str(e)})", "cached": False}
    
    # --- 3. 后置处理层：将得到的新鲜答案回写进缓存 ---
    try:
        await set_cached_response(request.session_id, request.message, reply)
    except Exception:
        pass
        
    return {"reply": reply, "cached": False}

@app.websocket("/ws")
async def websocket_desktop_pet(websocket: WebSocket, session_id: str = "desktop_pet_01"):
    """
    真正的全双工长网址隧道。桌宠启动后，将永远保持这个链接开启。
    """
    await websocket.accept()
    print(f"[*] 【WS接线员】桌面悬浮宠物已经唤醒并连入网关: {session_id}")
    from services.redis_cache import get_cached_response, set_cached_response
    
    try:
        while True:
            # 阻塞等待桌面上发来的文字
            data = await websocket.receive_text()
            print(f"[*] 【WS接线员】截获用户桌面投递: {data}")
            
            reply = None
            # --- 1. [修复] 拦截层：极其快速的 Redis 缓存检查 ---
            try:
                cached_reply = await get_cached_response(session_id, data)
                if cached_reply:
                    print(f"[*] 【WS接线员】命中 Redis 高速缓存！拦截转发，直接回流桌面！")
                    reply = cached_reply
            except Exception:
                pass
            
            if not reply:
                # --- 2. 透传层：没命中缓存，使用微服务架构转发大算力集群 ---
                try:
                    async with grpc.aio.insecure_channel('localhost:50051') as channel:
                        stub = pet_pb2_grpc.PetServiceStub(channel)
                        rpc_request = pet_pb2.ChatRequest(session_id=session_id, message=data)
                        response = await stub.Chat(rpc_request)
                        reply = response.reply
                        
                    # --- 3. [修复] 后置处理层：将得到的新鲜答案回写进缓存 ---
                    try:
                        await set_cached_response(session_id, data, reply)
                    except Exception:
                        pass
                        
                except Exception as e:
                    reply = f"哎呀，我的中枢大脑睡着了，通信失败...({str(e)})"
            
            # 把算出的答案秒传回桌面绘制气泡！
            await websocket.send_text(reply)
            
    except WebSocketDisconnect:
        print(f"[*] 【WS接线员】桌面悬浮宠物下线关闭长连接")

@app.post("/idle_trigger")
async def trigger_offline_action(session_id: str = "pinkpig_001"):
    """
    一个用来专门测试纯异步投递的实验接口。
    不会阻塞，它将任务封装通过 AMQP 扔给远端服务器的队列里。
    """
    # 虽然是相对缓慢的导入，但在框架外部可避免顶层循环依赖
    from tasks.pet_tasks import trigger_idle_interaction
    
    # [核心技术点] 使用 .delay() 它是以毫秒级瞬间返回的！
    # 后套大模型算个10秒都和本 HTTP 请求毫无关系！这就是非阻塞削峰。
    task_result = trigger_idle_interaction.delay(session_id)
    
    return {
        "status": "任务接收成功，已向 RabbitMQ 下发 MQ 队指令，后台将在消费能力充足时开始吞吐。",
        "task_id": task_result.id
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
