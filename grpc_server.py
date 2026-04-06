import sys
import os
import asyncio
import grpc

# 使得 Python 能够找到 protobuf 目录下极其坑爹的相对路径包
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "protos"))
import protos.pet_pb2 as pet_pb2
import protos.pet_pb2_grpc as pet_pb2_grpc

from database import AsyncSessionLocal
from services.llm_service import get_pet_response

class PetServiceServicer(pet_pb2_grpc.PetServiceServicer):
    """
    内网微服务的核心处理类。它实现了我们在 pet.proto 里画下的那张图纸。
    """
    async def Chat(self, request, context):
        session_id = request.session_id
        message = request.message
        
        print(f"[*] gRPC Server 接收到来自 API 网关的中转请求: [{session_id}] {message}")
        
        # 因为在微服务独立进程中，没有 FastAPI 的依赖注入，我们需要自己管理 ORM Context
        async with AsyncSessionLocal() as db:
            reply = await get_pet_response(message, session_id, db)
            
        print("[*] gRPC Server 计算完成，发送二进制响应包返回给 API 网关！")
        return pet_pb2.ChatReply(reply=reply)

    async def RegisterAccount(self, request, context):
        from database import AsyncSessionLocal
        from models import Account
        from sqlalchemy import select, or_
        
        async with AsyncSessionLocal() as db:
            # 双端排他校验：账号不能重复，桌宠名也不能重复
            result = await db.execute(select(Account).where(
                or_(Account.account_name == request.account_name, Account.pet_name == request.pet_name)
            ))
            existing = result.scalars().first()
            if existing:
                if existing.account_name == request.account_name:
                    return pet_pb2.AuthRegisterReply(success=False, message=f"账号 '{request.account_name}' 已被占用。")
                else:
                    return pet_pb2.AuthRegisterReply(success=False, message=f"桌宠名 '{request.pet_name}' 已被别人叫啦。")
                
            new_acc = Account(
                account_name=request.account_name, 
                password=request.password, 
                pet_name=request.pet_name, 
                avatar=request.avatar
            )
            db.add(new_acc)
            await db.commit()
            return pet_pb2.AuthRegisterReply(success=True, message="时空注册大成功！请切换到【登录】唤醒它！")

    async def LoginAccount(self, request, context):
        from database import AsyncSessionLocal
        from models import Account
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Account).where(Account.account_name == request.account_name))
            acc = result.scalars().first()
            if not acc:
                return pet_pb2.AuthLoginReply(success=False, message="登录失败：星际查无此账号。")
            if acc.password != request.password:
                return pet_pb2.AuthLoginReply(success=False, message="登录失败：加密凭证错误。")
                
            return pet_pb2.AuthLoginReply(
                success=True, 
                message="验证通过！正在将灵魂注入桌宠躯壳...",
                pet_name=acc.pet_name,
                avatar=acc.avatar
            )

async def serve():
    server = grpc.aio.server()
    pet_pb2_grpc.add_PetServiceServicer_to_server(PetServiceServicer(), server)
    listen_addr = '[::]:50051'
    server.add_insecure_port(listen_addr)
    
    print(f"=========================================")
    print(f"🚀 AI Backend [gRPC Microservice] 已启动！")
    print(f"📡 监听内部调度端口: {listen_addr}")
    print(f"=========================================")
    
    await server.start()
    await server.wait_for_termination()

if __name__ == '__main__':
    asyncio.run(serve())
