# AI 桌宠后端开发与学习路线图

这份计划旨在帮助你从零开始，逐步掌握腾讯 IEG AI 桌宠后端开发实习生所需的全部技能栈，并最终亲手孵化出这个项目。我们将采用“**理论学习 + 动手实践**”相结合的方式，每一步都会有具体的代码产出。

## User Review Required

> [!IMPORTANT]
> 这是一个长期的学习和开发计划，请查看以下路线图。如果有任何你想跳过的部分（比如你已经熟悉了基础），或者想要优先学习的部分，请告诉我，我们可以随时调整计划。
> 
> 另外，我们需要确定主要的开发语言方案。虽然岗位描述提到 Go 或 Python，但考虑到生态、Agent 框架（如 LangChain, 乃至我们自己实现 ReAct）以及快速迭代，我建议我们 **优先使用 Python** 作为主要开发语言。你是否同意？

## Proposed Changes

我们将整个孵化过程分为以下几个具有挑战性但可实现的阶段：

### Phase 1: 基础夯实与环境搭建 (Backend & Eng Basics)
* **Linux & Git**: 掌握基本的命令行操作和代码版本控制（分支管理、Commit 规范）。
* **Python 高级基础**: 确保对 Python 类型提示 (Type Hints)、异步编程 (asyncio) 有深入理解。
* **HTTP 服务初探**: 使用 `FastAPI` 搭建一个最基础的“Hello World”服务器，理解路由和请求/响应模型。

### Phase 2: AI 核心与 Agent 基础 (LLM & Agentic Concepts)
* **LLM API 对接**: 接入大模型 API，实现基础的对话功能配置。
* **Prompt Engineering**: 学习如何编写 System Prompt 来赋予桌宠“人设”。
* **ReAct 模式实现**: 从零写一个简单的 ReAct (Reasoning and Acting) 循环，理解 Agent 是如何思考和行动的。

### Phase 3: 工具调用与 MCP 协议 (Tool Use & Capabilities)
* **Skill/Tool 机制**: 让大模型学会调用本地函数（如：获取天气、查询系统状态）。
* **MCP (Model Context Protocol)**: 深入理解并接入 MCP 协议，为我们的桌宠开发标准化的插件系统，让它能和你的本地开发环境进行更复杂的互动。

### Phase 4: 高并发与企业级架构 (Advanced Backend Architecture)
* **数据库接入**: 引入 PostgreSQL 或 MySQL 保存桌宠的记忆和状态。
* **Redis 缓存**: 使用 Redis 处理高频状态更新，理解缓存设计。
* **gRPC 架构改造**: 将原来的 HTTP 接口改造为 gRPC（或者模拟 TRPC 的理念），理解微服务内部的 RPC 通信机制。
* **消息队列**: 引入 RabbitMQ 或 Kafka（轻量级可用 Redis Pub/Sub）处理异步任务（如桌宠的后台自动化巡回动作）。

### Phase 5: 研发效能与评测体系 (Engineering Quality & Eval Pipelines)
* **SDD (Spec-Driven Development)**: 学习如何先写 Spec，再写代码。练习利用 AI 辅助生成代码。
* **Harness 测试外壳建设**: 针对 Agent 输出的不确定性，设计测试框架对其输出进行验证（准确率、鲁棒性）。
* **Eval Pipeline**: 搭建一个简单的评测看板，定量分析我们桌宠的“智商”和表现。

## Open Questions

> [!CAUTION]
> 1. 你目前的 Python 编程基础和后端框架（如 FastAPI/Django/Flask）的使用经验如何？
> 2. 我们是否需要先从哪个特定的大模型平台（如 OpenAI, Gemini, 或者国内的文心/通义）API 开始对接？
> 3. 你准备好开始 Phase 1 了吗？

## Verification Plan

### Automated Tests
* 每个阶段结束时，我们都会编写对应的单元测试 (pytest) 来验证代码邏輯。
* 针对 AI 输出，我们会专门编写基于规则和基于 LLM-as-a-Judge 的测评脚本。

### Manual Verification
* 本地运行服务，通过 Postman 或提供简单的客户端脚手架进行人工交互测试。
