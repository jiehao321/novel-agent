# 🤖 Novel Agent - 多Agent小说创作系统

> 基于 LangGraph 的多 Agent 小说创作系统，自动完成从大纲规划到章节写作的全流程。

## 系统架构

```
用户 → 前端 → 总控Agent → 规划Agent → 写作Agent → 审核Agent → 输出
                     ↓
                  记忆层（世界观/角色/伏笔）
```

## Agent 阵容 (32个)

### 📋 规划阶段 (10 Agents)
- 需求分析 Agent
- 大纲生成 Agent
- 角色设计 Agent
- 世界观架构 Agent
- 原创性检查 Agent
- 心理建模 Agent
- 行为建模 Agent
- 伏笔规划 Agent
- 风格定制 Agent

### ✍️ 写作阶段 (10 Agents)
- 写作规划 Agent
- 写手 Agent
- 场景生成 Agent
- 对话 Agent
- 角色状态 Agent
- 伏笔管理 Agent
- 氛围营造 Agent
- 高潮设计 Agent
- 对话精修 Agent
- 描写强化 Agent

### 🔍 审核阶段 (10 Agents)
- 逻辑审核 Agent
- 敏感审核 Agent
- 原创性审核 Agent
- AI文审核 Agent
- 一致性审核 Agent
- 伏笔检查 Agent
- 文笔润色 Agent
- 情感共鸣 Agent
- 创新评估 Agent
- 综合评分 Agent

### 📖 完结阶段 (1 Agent)
- 完结审核 Agent

## 技术栈

- **后端**: Python, LangGraph, FastAPI
- **前端**: Next.js, React, TypeScript
- **数据库**: SQLite (结构化) + ChromaDB (向量)
- **LLM**: OpenAI / Anthropic / 本地模型

## 快速开始

```bash
# 克隆项目
git clone https://github.com/jiehao321/novel-agent.git
cd novel-agent

# 安装后端依赖
pip install -r requirements.txt

# 运行
python -m uvicorn backend.main:app --reload
```

## 功能特性

- ✅ 自动生成万字级大纲
- ✅ 完整角色档案（心理+行为）
- ✅ 世界观完整设定
- ✅ 伏笔系统管理
- ✅ 六维度即时审核
- ✅ 四维度深度审核
- ✅ 记忆层持久化
- ✅ 无限次修订
- ✅ 人工复审兜底

## 项目结构

```
novel-agent/
├── agents/           # Agent 定义
│   ├── planner/     # 规划阶段
│   ├── writer/      # 写作阶段
│   ├── reviewer/    # 审核阶段
│   └── memory/      # 记忆层
├── config/          # 配置文件
├── backend/         # 后端服务
├── frontend/        # 前端界面
└── README.md
```

## License

MIT
