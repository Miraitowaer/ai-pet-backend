# AI 桌宠后端开发 - 任务看板

## Phase 1: 基础夯实与环境搭建 (Backend & Eng Basics)
- [x] 初始化项目基础结构
- [/] 配置 Python 虚拟环境与核心依赖 (`requirements.txt`)
- [x] 使用 `FastAPI` 实现第一个基础的 HTTP API (Hello World 服务器)
- [ ] 学习项目配置管理 (环境变量 `.env`)

## Phase 2: AI 核心与 Agent 基础 (LLM & Agentic Concepts)
- [ ] 选择并接入一款大语言模型 API
- [ ] 编写 System Prompt 赋予桌宠基础人设
- [ ] 实现基础的多轮对话逻辑
- [ ] 实现简易的 ReAct (Reasoning and Acting) 执行引擎原型

## Phase 3: 工具调用与 MCP 协议 (Tool Use & Capabilities)
- [ ] 封装基础工具 (获取系统时间、系统状态等本地能力)
- [ ] 让大模型学会并理解工具调用 (Function Calling)
- [ ] 学习并引入 MCP (Model Context Protocol) 核心概念，封装标准化插件接口

## Phase 4: 高并发与企业级架构 (Advanced Backend Architecture)
- [ ] 接入关系型数据库 (PostgreSQL/SQLite + SQLAlchemy) 存储对话记忆
- [ ] 引入 Redis 缓存机制处理高频状态更新
- [ ] 实战 gRPC：将部分核心逻辑抽离，构建 gRPC 服务端和客户端，理解 RPC 通信
- [ ] 引入轻量级消息队列处理后台任务 (如桌宠自动化闲时互动)

## Phase 5: 研发效能与评测体系 (Engineering Quality & Eval Pipelines)
- [ ] 学习 SDD (Spec-Driven Development) 撰写第一份 Spec
- [ ] 为核心逻辑补充 Pytest 单元测试外壳 (Harness)
- [ ] 搭建简易的 Eval Pipeline：通过自动化脚本测试 Agent 的工具调用准确率
